const API_CANDIDATES = (() => {
  const { protocol, hostname } = window.location;
  const candidates = [
    "http://103.253.20.30:30013/api",
    `${protocol}//${hostname}:30013/api`,
    `${protocol}//${hostname}:${window.location.port || "30013"}/api`,
    "http://localhost:30013/api",
  ];
  return Array.from(new Set(candidates));
})();

let API_BASE = null;

const HEALTH_PATH = "/health";

const state = {
  indicators: [],
  groups: [],
  stocks: [],
  periods: [],
  selectedStock: "",
  searchTerm: "",
  groupFilter: "",
  periodMode: "quarter",
  periodCache: new Map(),
};

const els = {
  stock: document.getElementById("stockSelect"),
  group: document.getElementById("groupFilter"),
  search: document.getElementById("searchInput"),
  run: document.getElementById("runButton"),
  tableHeader: document.getElementById("tableHeader"),
  tableBody: document.getElementById("indicatorTableBody"),
  indicatorCount: document.getElementById("indicatorCount"),
  successCount: document.getElementById("successCount"),
  failedCount: document.getElementById("failedCount"),
  calcMeta: document.getElementById("calcMeta"),
  toast: document.getElementById("toast"),
  modeQuarter: document.getElementById("modeQuarter"),
  modeYear: document.getElementById("modeYear"),
};

const formatter = new Intl.NumberFormat("vi-VN", {
  maximumFractionDigits: 2,
});

const debounce = (fn, delay = 300) => {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
};

const periodKey = (period) => `${period.year}-Q${typeof period.quarter === "number" ? period.quarter : "?"}`;

const formatQuarter = (quarter) => {
  if (quarter === 5) return "FY";
  if (!quarter) return "Q?";
  return `Q${quarter}`;
};

const formatPeriodLabel = (period, mode) => {
  if (mode === "year") {
    return `FY ${period.year}`;
  }
  return `${formatQuarter(period.quarter)}-${period.year}`;
};

const showToast = (message, variant = "info") => {
  els.toast.textContent = message;
  els.toast.className = `toast show ${variant}`;
  els.toast.hidden = false;
  setTimeout(() => {
    els.toast.classList.remove("show");
    els.toast.hidden = true;
  }, 2500);
};

const fetchJson = async (url) => {
  const res = await fetch(url);
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `Request failed (${res.status})`);
  }
  return res.json();
};

const pingApi = async (base) => {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 3000);
  try {
    const response = await fetch(`${base}${HEALTH_PATH}`, { signal: controller.signal });
    if (!response.ok) {
      throw new Error(`Health returned ${response.status}`);
    }
  } finally {
    clearTimeout(timeout);
  }
};

const resolveApiBase = async () => {
  for (const candidate of API_CANDIDATES) {
    try {
      await pingApi(candidate);
      console.info(`[Gen57] Connected to API ${candidate}`);
      return candidate;
    } catch (error) {
      console.warn(`[Gen57] API candidate failed: ${candidate}`, error);
    }
  }
  throw new Error("No reachable API endpoint");
};

const buildUrl = (path) => {
  if (!API_BASE) {
    throw new Error("API base URL unresolved");
  }
  return `${API_BASE}${path}`;
};

const populateSelect = (selectEl, items, { placeholder = "-- Select --" } = {}) => {
  const fragment = document.createDocumentFragment();
  if (placeholder) {
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = placeholder;
    fragment.append(opt);
  }
  items.forEach(({ value, label }) => {
    const opt = document.createElement("option");
    opt.value = value;
    opt.textContent = label;
    fragment.append(opt);
  });
  selectEl.innerHTML = "";
  selectEl.append(fragment);
};

const updateIndicatorCount = () => {
  els.indicatorCount.textContent = state.indicators.length;
};

const getActivePeriods = () => {
  if (!state.periods.length) {
    return [];
  }
  if (state.periodMode === "year") {
    const annual = state.periods.filter((item) => item.quarter === 5);
    if (annual.length) {
      return annual;
    }
    const seenYears = new Set();
    const fallback = [];
    for (const period of state.periods) {
      if (seenYears.has(period.year)) continue;
      seenYears.add(period.year);
      fallback.push(period);
    }
    return fallback;
  }
  return state.periods;
};

const renderTable = () => {
  const baseHeaders = [
    "<th>ID</th>",
    "<th>Group</th>",
    "<th>Indicator</th>",
    "<th>Definition</th>",
    "<th>Formula</th>",
    "<th>Usage</th>",
    "<th>Weights</th>",
  ];
  const periods = getActivePeriods();
  const periodHeaders = periods.map(
    (period) => `<th class="period-value">${formatPeriodLabel(period, state.periodMode)}</th>`
  );

  const totalHeaders = [...baseHeaders, ...periodHeaders].join("");
  els.tableHeader.innerHTML = `<tr>${totalHeaders}</tr>`;

  const filteredIndicators = state.indicators.filter((item) => {
    const matchesGroup = state.groupFilter ? item.group === state.groupFilter : true;
    const term = state.searchTerm.trim().toLowerCase();
    if (!term) return matchesGroup;
    return (
      matchesGroup &&
      ((item.name || "").toLowerCase().includes(term) ||
        (item.definition || "").toLowerCase().includes(term) ||
        (item.formula || "").toLowerCase().includes(term))
    );
  });

  if (!filteredIndicators.length) {
    els.tableBody.innerHTML = `<tr><td colspan="${baseHeaders.length + periodHeaders.length}" class="empty">No indicators match the current filters.</td></tr>`;
    return;
  }

  if (!periods.length) {
    const message = state.selectedStock
      ? "No periods available for this view mode."
      : "Select a stock to view indicator values.";
    els.tableBody.innerHTML = `<tr><td colspan="${baseHeaders.length}" class="empty">${message}</td></tr>`;
    return;
  }

  const rows = filteredIndicators
    .map((indicator) => {
      const usedBlock = [indicator.used_in_qgv, indicator.used_in_4m]
        .filter(Boolean)
        .map((text) => `<span class="value-chip">${text}</span>`)
        .join("");
      const weights = [
        indicator.weight_in_qgv ? `QGV: ${indicator.weight_in_qgv}` : "",
        indicator.weight_in_4m ? `4M: ${indicator.weight_in_4m}` : "",
      ]
        .filter(Boolean)
        .join(" · ");

      const valueCells = periods
        .map((period) => {
          const cache = state.periodCache.get(periodKey(period));
          if (!cache) {
            return '<td class="period-value">Loading…</td>';
          }
          const value = cache.valuesById.get(indicator.id) ?? null;
          const display = value === null || Number.isNaN(value) ? "–" : formatter.format(value);
          return `<td class="period-value">${display}</td>`;
        })
        .join("");

      return `
        <tr>
          <td>${indicator.id ?? ""}</td>
          <td>${indicator.group ?? ""}</td>
          <td><strong>${indicator.name ?? ""}</strong></td>
          <td>${indicator.definition ?? ""}</td>
          <td>${indicator.formula ?? ""}</td>
          <td>${usedBlock || "-"}</td>
          <td>${weights || "-"}</td>
          ${valueCells}
        </tr>
      `;
    })
    .join("");

  els.tableBody.innerHTML = rows;
};

const updateSummary = () => {
  const periods = getActivePeriods();
  const dataset = periods
    .map((period) => state.periodCache.get(periodKey(period)))
    .find((entry) => entry && entry.metadata);

  const metadata = dataset?.metadata || {};
  els.successCount.textContent = metadata.successful ?? 0;
  els.failedCount.textContent = metadata.failed ?? 0;
  els.calcMeta.textContent = metadata.calculated_at
    ? new Date(metadata.calculated_at).toLocaleString()
    : "–";
};

const cachePeriodData = (period, data) => {
  const valuesById = new Map((data.indicators || []).map((item) => [item.id ?? item.ID, item.value ?? null]));
  state.periodCache.set(periodKey(period), {
    period,
    metadata: data.metadata || null,
    valuesById,
  });
};

const fetchPeriodValues = async (period) => {
  const params = new URLSearchParams({
    stock: state.selectedStock,
    year: String(period.year),
  });
  if (typeof period.quarter === "number") {
    params.append("quarter", String(period.quarter));
  }
  const data = await fetchJson(buildUrl(`/indicator-values?${params.toString()}`));
  cachePeriodData(period, data);
};

const refreshValues = async ({ force = false } = {}) => {
  if (!state.selectedStock) {
    showToast("Please choose a stock first.", "danger");
    return;
  }

  const periods = getActivePeriods();
  if (!periods.length) {
    showToast("No periods available to load.", "danger");
    return;
  }

  els.run.disabled = true;
  els.run.textContent = "Refreshing…";

  try {
    for (const period of periods) {
      const key = periodKey(period);
      if (!force && state.periodCache.has(key)) {
        continue;
      }
      await fetchPeriodValues(period);
    }
    renderTable();
    updateSummary();
    showToast("Indicator values updated.", "success");
  } catch (error) {
    console.error(error);
    showToast(error.message || "Failed to load values", "danger");
  } finally {
    els.run.disabled = false;
    els.run.textContent = "Refresh values";
  }
};

const setPeriodMode = (mode) => {
  if (state.periodMode === mode) return;
  state.periodMode = mode;
  els.modeQuarter.classList.toggle("active", mode === "quarter");
  els.modeYear.classList.toggle("active", mode === "year");
  renderTable();
  refreshValues();
};

const handleStockChange = async (stock) => {
  state.selectedStock = stock;
  state.periodCache.clear();

  if (!stock) {
    state.periods = [];
    renderTable();
    updateSummary();
    return;
  }

  const data = await fetchJson(buildUrl(`/periods?stock=${encodeURIComponent(stock)}`));
  state.periods = (data.periods || []).map((period) => ({
    year: period.year,
    quarter: typeof period.quarter === "number" ? period.quarter : null,
  }));

  renderTable();
  refreshValues({ force: true });
};

const bindEvents = () => {
  els.stock.addEventListener("change", (event) => {
    handleStockChange(event.target.value);
  });

  els.group.addEventListener("change", (event) => {
    state.groupFilter = event.target.value;
    renderTable();
  });

  els.search.addEventListener(
    "input",
    debounce((event) => {
      state.searchTerm = event.target.value;
      renderTable();
    }, 250)
  );

  els.run.addEventListener("click", () => refreshValues({ force: true }));

  els.modeQuarter.addEventListener("click", () => setPeriodMode("quarter"));
  els.modeYear.addEventListener("click", () => setPeriodMode("year"));
};

const loadBootstrap = async () => {
  const data = await fetchJson(buildUrl("/dashboard/bootstrap"));
  state.indicators = data.indicators || [];
  state.groups = data.groups || [];
  populateSelect(
    els.group,
    [{ value: "", label: "All groups" }, ...state.groups.map((group) => ({ value: group, label: group }))],
    { placeholder: null }
  );
  updateIndicatorCount();
};

const loadStocks = async () => {
  const data = await fetchJson(buildUrl("/stocks"));
  state.stocks = data.stocks || [];
  populateSelect(
    els.stock,
    state.stocks.map((stock) => ({ value: stock, label: stock })),
    { placeholder: "-- Pick stock --" }
  );
};

const init = async () => {
  try {
    API_BASE = await resolveApiBase();
    await Promise.all([loadBootstrap(), loadStocks()]);
    bindEvents();
    renderTable();
    showToast(`Connected to ${API_BASE}`, "info");
  } catch (error) {
    console.error(error);
    showToast("Failed to bootstrap dashboard", "danger");
  }
};

document.addEventListener("DOMContentLoaded", init);

