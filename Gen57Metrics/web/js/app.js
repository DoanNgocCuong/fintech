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
  selectedYear: "",
  selectedQuarter: "",
  searchTerm: "",
  groupFilter: "",
  values: [],
  metadata: null,
};

const els = {
  stock: document.getElementById("stockSelect"),
  year: document.getElementById("yearSelect"),
  quarter: document.getElementById("quarterSelect"),
  group: document.getElementById("groupFilter"),
  search: document.getElementById("searchInput"),
  run: document.getElementById("runButton"),
  tableBody: document.getElementById("indicatorTableBody"),
  indicatorCount: document.getElementById("indicatorCount"),
  successCount: document.getElementById("successCount"),
  failedCount: document.getElementById("failedCount"),
  calcMeta: document.getElementById("calcMeta"),
  toast: document.getElementById("toast"),
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

const loadBootstrap = async () => {
  const data = await fetchJson(buildUrl("/dashboard/bootstrap"));
  state.indicators = data.indicators || [];
  state.groups = data.groups || [];
  populateSelect(els.group, [{ value: "", label: "All groups" }, ...state.groups.map((g) => ({ value: g, label: g }))], { placeholder: null });
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

const loadPeriods = async (stock) => {
  if (!stock) {
    state.periods = [];
    populateSelect(els.year, [], { placeholder: "--" });
    populateSelect(els.quarter, [], { placeholder: "Annual (Q5)" });
    return;
  }
  const data = await fetchJson(buildUrl(`/periods?stock=${encodeURIComponent(stock)}`));
  state.periods = data.periods || [];

  const years = Array.from(new Set(state.periods.map((p) => p.year))).map((year) => ({
    value: year,
    label: year,
  }));
  populateSelect(els.year, years, { placeholder: "-- Year --" });

  // Build quarter select once (1-4 + annual)
  const quarters = [
    { value: "", label: "-- Quarter --" },
    { value: "1", label: "Q1" },
    { value: "2", label: "Q2" },
    { value: "3", label: "Q3" },
    { value: "4", label: "Q4" },
    { value: "5", label: "Q5 (Annual)" },
  ];
  populateSelect(els.quarter, quarters, { placeholder: null });

  if (state.periods.length) {
    const [{ year, quarter }] = state.periods;
    els.year.value = String(year);
    if (typeof quarter === "number") {
      els.quarter.value = String(quarter);
    } else {
      els.quarter.value = "";
    }
    state.selectedYear = els.year.value;
    state.selectedQuarter = els.quarter.value;
  }
};

const computeRows = () => {
  const valueMap = new Map(state.values.map((item) => [item.id, item.value]));
  return state.indicators
    .filter((item) => {
      const matchesGroup = state.groupFilter ? item.group === state.groupFilter : true;
      const search = state.searchTerm.trim().toLowerCase();
      if (!search) return matchesGroup;
      return (
        matchesGroup &&
        ((item.name || "").toLowerCase().includes(search) ||
          (item.definition || "").toLowerCase().includes(search) ||
          (item.formula || "").toLowerCase().includes(search))
      );
    })
    .map((item) => ({
      ...item,
      value: valueMap.has(item.id) ? valueMap.get(item.id) : null,
    }));
};

const updateIndicatorCount = () => {
  els.indicatorCount.textContent = state.indicators.length;
};

const renderTable = () => {
  const rows = computeRows();
  if (!rows.length) {
    els.tableBody.innerHTML = `<tr><td colspan="8" class="empty">No indicators match the current filters.</td></tr>`;
    return;
  }

  const html = rows
    .map((row) => {
      const value = row.value ?? null;
      const valueDisplay = value === null ? "-" : formatter.format(value);
      const usedBlock = [row.used_in_qgv, row.used_in_4m]
        .filter(Boolean)
        .map((text) => `<span class="value-chip">${text}</span>`)
        .join("");
      const weights = [
        row.weight_in_qgv ? `QGV: ${row.weight_in_qgv}` : "",
        row.weight_in_4m ? `4M: ${row.weight_in_4m}` : "",
      ]
        .filter(Boolean)
        .join(" · ");

      return `
        <tr>
          <td>${row.id ?? ""}</td>
          <td>${row.group ?? ""}</td>
          <td><strong>${row.name ?? ""}</strong></td>
          <td>${row.definition ?? ""}</td>
          <td>${row.formula ?? ""}</td>
          <td class="numeric">${valueDisplay}</td>
          <td>${usedBlock || "-"}</td>
          <td>${weights || "-"}</td>
        </tr>
      `;
    })
    .join("");

  els.tableBody.innerHTML = html;
};

const updateSummary = () => {
  const metadata = state.metadata || {};
  els.successCount.textContent = metadata.successful ?? 0;
  els.failedCount.textContent = metadata.failed ?? 0;
  els.calcMeta.textContent = metadata.calculated_at
    ? new Date(metadata.calculated_at).toLocaleString()
    : "–";
};

const calculateIndicators = async () => {
  const stock = state.selectedStock;
  const year = parseInt(state.selectedYear, 10);
  const quarter =
    state.selectedQuarter && !Number.isNaN(Number(state.selectedQuarter))
      ? parseInt(state.selectedQuarter, 10)
      : null;

  if (!stock || Number.isNaN(year)) {
    showToast("Please select stock and year.", "danger");
    return;
  }

  els.run.disabled = true;
  els.run.textContent = "Calculating…";

  try {
    const params = new URLSearchParams({
      stock,
      year: String(year),
    });
    if (quarter !== null && !Number.isNaN(quarter)) {
      params.append("quarter", String(quarter));
    }
    const data = await fetchJson(buildUrl(`/indicator-values?${params.toString()}`));
    state.values = data.indicators || [];
    state.metadata = data.metadata || null;
    renderTable();
    updateSummary();
    showToast("Indicators updated", "success");
  } catch (error) {
    console.error(error);
    showToast(error.message || "Failed to calculate indicators", "danger");
  } finally {
    els.run.disabled = false;
    els.run.textContent = "Calculate";
  }
};

const bindEvents = () => {
  els.stock.addEventListener("change", async (event) => {
    state.selectedStock = event.target.value;
    await loadPeriods(state.selectedStock);
  });

  els.year.addEventListener("change", (event) => {
    state.selectedYear = event.target.value;
  });

  els.quarter.addEventListener("change", (event) => {
    state.selectedQuarter = event.target.value;
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

  els.run.addEventListener("click", calculateIndicators);
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

