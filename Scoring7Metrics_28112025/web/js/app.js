/**
 * Main application logic for Scoring 7 Metrics Dashboard
 */

// Global state
let currentCompany = '';
let currentYear = null;
let currentGroup = 'governance';
let currentData = null;
let searchKeyword = '';

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    init();
});

/**
 * Initialize application
 */
async function init() {
    console.log('Initializing Scoring 7 Metrics Dashboard...');
    
    // Load companies
    await loadCompaniesList();
    
    // Setup event listeners
    setupEventListeners();
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Search input debounce
    let searchTimeout;
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                onSearchChange();
            }, 300);
        });
    }
}

/**
 * Load companies list
 */
async function loadCompaniesList() {
    const select = document.getElementById('company-select');
    if (!select) return;
    
    try {
        const companies = await loadCompanies();
        select.innerHTML = '<option value="">-- Chọn công ty --</option>';
        companies.forEach(company => {
            const option = document.createElement('option');
            option.value = company;
            option.textContent = company;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading companies:', error);
        showError('Không thể tải danh sách công ty');
    }
}

/**
 * Handle company change
 */
async function onCompanyChange() {
    const select = document.getElementById('company-select');
    currentCompany = select.value;
    
    if (!currentCompany) {
        clearYearSelect();
        clearContent();
        return;
    }
    
    // Load years for this company
    await loadYearsList(currentCompany);
    
    // Clear content
    clearContent();
}

/**
 * Load years list
 */
async function loadYearsList(companyName) {
    const select = document.getElementById('year-select');
    if (!select) return;
    
    try {
        const years = await loadYears(companyName);
        select.innerHTML = '<option value="">-- Chọn năm --</option>';
        years.forEach(year => {
            const option = document.createElement('option');
            option.value = year;
            option.textContent = year;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading years:', error);
        showError('Không thể tải danh sách năm');
    }
}

/**
 * Handle year change
 */
async function onYearChange() {
    const select = document.getElementById('year-select');
    currentYear = select.value ? parseInt(select.value) : null;
    
    if (!currentCompany || !currentYear) {
        clearContent();
        return;
    }
    
    // Load company data
    await loadCompanyDataForDisplay();
}

/**
 * Load company data and display
 */
async function loadCompanyDataForDisplay() {
    if (!currentCompany || !currentYear) return;
    
    showLoading(true);
    hideError();
    
    try {
        const data = await loadCompanyData(currentCompany, currentYear);
        
        if (!data || !data.success) {
            showError(`Không tìm thấy dữ liệu cho ${currentCompany} năm ${currentYear}`);
            clearContent();
            return;
        }
        
        currentData = data;
        renderContent();
    } catch (error) {
        console.error('Error loading company data:', error);
        showError('Không thể tải dữ liệu. Vui lòng thử lại.');
        clearContent();
    } finally {
        showLoading(false);
    }
}

/**
 * Handle tab change
 */
function onTabChange(groupId) {
    currentGroup = groupId;
    
    // Update active tab
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelector(`.tab[data-group="${groupId}"]`)?.classList.add('active');
    
    // Re-render content
    if (currentData) {
        renderContent();
    }
}

/**
 * Handle search change
 */
function onSearchChange() {
    const input = document.getElementById('search-input');
    searchKeyword = input.value.trim();
    
    if (currentData) {
        renderContent();
    }
}

/**
 * Render content
 */
function renderContent() {
    if (!currentData) return;
    
    renderSummary();
    renderMetrics();
    renderEvidences();
}

/**
 * Render summary
 */
function renderSummary() {
    const container = document.getElementById('summary-content');
    if (!container) return;
    
    const summaries = currentData.summary || {};
    const summary = summaries[currentGroup] || '';
    
    if (summary) {
        container.innerHTML = `<p>${escapeHtml(summary)}</p>`;
    } else {
        container.innerHTML = '<p class="placeholder">Không có tóm tắt cho tiêu chí này</p>';
    }
}

/**
 * Render metrics
 */
function renderMetrics() {
    const container = document.getElementById('metrics-content');
    if (!container) return;
    
    const metrics = currentData.metrics || {};
    const groupMetrics = metrics[currentGroup] || {};
    
    if (Object.keys(groupMetrics).length === 0) {
        container.innerHTML = '<p class="placeholder">Không có metrics cho tiêu chí này</p>';
        return;
    }
    
    // Filter by search keyword if provided
    let filteredMetrics = groupMetrics;
    if (searchKeyword) {
        filteredMetrics = {};
        for (const [key, value] of Object.entries(groupMetrics)) {
            if (key.toLowerCase().includes(searchKeyword.toLowerCase()) ||
                String(value).toLowerCase().includes(searchKeyword.toLowerCase())) {
                filteredMetrics[key] = value;
            }
        }
    }
    
    if (Object.keys(filteredMetrics).length === 0) {
        container.innerHTML = '<p class="placeholder">Không tìm thấy metrics phù hợp</p>';
        return;
    }
    
    // Render metrics grid
    const grid = document.createElement('div');
    grid.className = 'metrics-grid';
    
    for (const [key, value] of Object.entries(filteredMetrics)) {
        const card = document.createElement('div');
        card.className = 'metric-card';
        
        const label = document.createElement('div');
        label.className = 'metric-label';
        label.textContent = formatMetricKey(key);
        
        const val = document.createElement('div');
        val.className = 'metric-value';
        val.textContent = value === null || value === undefined ? '-' : String(value);
        
        card.appendChild(label);
        card.appendChild(val);
        grid.appendChild(card);
    }
    
    container.innerHTML = '';
    container.appendChild(grid);
}

/**
 * Render evidences
 */
function renderEvidences() {
    const container = document.getElementById('evidences-content');
    if (!container) return;
    
    const evidences = currentData.evidences || {};
    let groupEvidences = evidences[currentGroup] || [];
    
    // Filter by search keyword if provided
    if (searchKeyword && groupEvidences.length > 0) {
        groupEvidences = groupEvidences.filter(ev => {
            const quote = ev.quote || '';
            const source = ev.source_ref || '';
            return quote.toLowerCase().includes(searchKeyword.toLowerCase()) ||
                   source.toLowerCase().includes(searchKeyword.toLowerCase());
        });
    }
    
    if (groupEvidences.length === 0) {
        container.innerHTML = '<p class="placeholder">Không có trích dẫn cho tiêu chí này</p>';
        return;
    }
    
    container.innerHTML = '';
    groupEvidences.forEach(evidence => {
        const item = document.createElement('div');
        item.className = 'evidence-item';
        
        const quote = document.createElement('div');
        quote.className = 'evidence-quote';
        quote.textContent = evidence.quote || '';
        
        const source = document.createElement('div');
        source.className = 'evidence-source';
        source.textContent = `Nguồn: ${evidence.source_ref || 'N/A'}`;
        
        item.appendChild(quote);
        item.appendChild(source);
        container.appendChild(item);
    });
}

/**
 * Format metric key for display
 */
function formatMetricKey(key) {
    return key
        .replace(/_/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase());
}

/**
 * Clear year select
 */
function clearYearSelect() {
    const select = document.getElementById('year-select');
    if (select) {
        select.innerHTML = '<option value="">-- Chọn năm --</option>';
    }
}

/**
 * Clear content
 */
function clearContent() {
    currentData = null;
    document.getElementById('summary-content').innerHTML = '<p class="placeholder">Chọn công ty và năm để xem tóm tắt</p>';
    document.getElementById('metrics-content').innerHTML = '<p class="placeholder">Chọn công ty và năm để xem metrics</p>';
    document.getElementById('evidences-content').innerHTML = '<p class="placeholder">Chọn công ty và năm để xem trích dẫn</p>';
}

/**
 * Show loading
 */
function showLoading(show) {
    const loading = document.getElementById('loading');
    if (loading) {
        loading.style.display = show ? 'flex' : 'none';
    }
}

/**
 * Show error
 */
function showError(message) {
    const errorDiv = document.getElementById('error-message');
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }
}

/**
 * Hide error
 */
function hideError() {
    const errorDiv = document.getElementById('error-message');
    if (errorDiv) {
        errorDiv.style.display = 'none';
    }
}

/**
 * Export data
 */
function exportData() {
    if (!currentData) {
        alert('Không có dữ liệu để xuất');
        return;
    }
    
    const dataStr = JSON.stringify(currentData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `7metrics_${currentCompany}_${currentYear}_${new Date().getTime()}.json`;
    link.click();
    URL.revokeObjectURL(url);
}

/**
 * Escape HTML
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}


