/**
 * Main application logic for financial reports dashboard
 */

// Global state
let currentStock = '';
let currentReportType = 'balance';
let tableData = null;
let filteredIndicators = [];
let allStocks = [];

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

/**
 * Initialize application
 */
async function initializeApp() {
    console.log('Initializing app...');
    
    // Load stocks for default report type
    await loadStocksForReport(currentReportType);
    
    // Set up event listeners
    setupEventListeners();
    
    console.log('App initialized');
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Search input
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(onSearchChange, 300));
    }
}

/**
 * Load stocks for a report type
 */
async function loadStocksForReport(reportType) {
    try {
        showLoading();
        allStocks = await loadStocks(reportType);
        populateStockSelector(allStocks);
        hideLoading();
    } catch (error) {
        console.error('Error loading stocks:', error);
        hideLoading();
        showNoData();
    }
}

/**
 * Populate stock selector
 */
function populateStockSelector(stocks) {
    const selector = document.getElementById('stock-select');
    if (!selector) return;
    
    selector.innerHTML = '<option value="">-- Chọn mã cổ phiếu --</option>';
    
    stocks.forEach(stock => {
        const option = document.createElement('option');
        option.value = stock;
        option.textContent = stock;
        selector.appendChild(option);
    });
}

/**
 * Handle stock change
 */
async function onStockChange() {
    const selector = document.getElementById('stock-select');
    if (!selector) return;
    
    const stock = selector.value;
    if (!stock) {
        showNoData();
        return;
    }
    
    currentStock = stock;
    await loadTableDataForStock(stock, currentReportType);
}

/**
 * Handle tab change
 */
async function onTabChange(reportType) {
    // Update active tab
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    const activeTab = document.querySelector(`[data-report="${reportType}"]`);
    if (activeTab) {
        activeTab.classList.add('active');
    }
    
    currentReportType = reportType;
    
    // Reload stocks for new report type
    await loadStocksForReport(reportType);
    
    // If stock is selected, reload table data
    if (currentStock) {
        await loadTableDataForStock(currentStock, reportType);
    } else {
        showNoData();
    }
}

/**
 * Load table data for stock and report type
 */
async function loadTableDataForStock(stock, reportType) {
    try {
        showLoading();
        
        const data = await loadTableData(stock, reportType);
        
        if (!data || !data.indicators || data.indicators.length === 0) {
            showNoData();
            return;
        }
        
        tableData = data;
        filteredIndicators = data.indicators;
        
        // Apply search filter if exists
        const searchInput = document.getElementById('search-input');
        if (searchInput && searchInput.value) {
            filteredIndicators = filterIndicators(data.indicators, searchInput.value);
        }
        
        renderTable(data, filteredIndicators);
        updateSummary(data);
        hideLoading();
        showTable();
    } catch (error) {
        console.error('Error loading table data:', error);
        hideLoading();
        showNoData();
    }
}

/**
 * Render table with data
 */
function renderTable(data, indicators) {
    const tableHeader = document.getElementById('table-header');
    const tableBody = document.getElementById('table-body');
    
    if (!tableHeader || !tableBody) return;
    
    // Clear existing content
    tableHeader.innerHTML = '';
    tableBody.innerHTML = '';
    
    // Sort periods
    const sortedPeriods = sortPeriods([...data.periods]);
    
    // Create header row
    const indicatorHeader = document.createElement('th');
    indicatorHeader.textContent = 'Chỉ tiêu';
    indicatorHeader.style.minWidth = '250px';
    tableHeader.appendChild(indicatorHeader);
    
    sortedPeriods.forEach(period => {
        const th = document.createElement('th');
        th.textContent = period.label;
        th.style.textAlign = 'center';
        tableHeader.appendChild(th);
    });
    
    // Create data rows
    indicators.forEach(indicator => {
        const row = document.createElement('tr');
        
        // Indicator name cell
        const indicatorCell = document.createElement('td');
        indicatorCell.textContent = indicator.label_vn || indicator.label;
        indicatorCell.style.fontWeight = '500';
        row.appendChild(indicatorCell);
        
        // Value cells
        sortedPeriods.forEach(period => {
            const cell = document.createElement('td');
            const value = indicator.values[period.label];
            
            if (value !== null && value !== undefined) {
                cell.textContent = formatNumber(value);
                cell.className = 'number';
            } else {
                cell.textContent = '-';
                cell.className = 'number empty';
            }
            
            cell.style.textAlign = 'right';
            row.appendChild(cell);
        });
        
        tableBody.appendChild(row);
    });
}

/**
 * Update summary section
 */
function updateSummary(data) {
    const summarySection = document.getElementById('summary-section');
    const totalIndicators = document.getElementById('total-indicators');
    const totalPeriods = document.getElementById('total-periods');
    const lastUpdate = document.getElementById('last-update');
    
    if (summarySection) {
        summarySection.style.display = 'block';
    }
    
    if (totalIndicators) {
        totalIndicators.textContent = data.indicators ? data.indicators.length : 0;
    }
    
    if (totalPeriods) {
        totalPeriods.textContent = data.periods ? data.periods.length : 0;
    }
    
    if (lastUpdate) {
        lastUpdate.textContent = new Date().toLocaleString('vi-VN');
    }
}

/**
 * Handle search change
 */
function onSearchChange() {
    const searchInput = document.getElementById('search-input');
    if (!searchInput || !tableData) return;
    
    const searchTerm = searchInput.value;
    filteredIndicators = filterIndicators(tableData.indicators, searchTerm);
    
    renderTable(tableData, filteredIndicators);
}

/**
 * Export data
 */
function exportData() {
    if (!tableData || !currentStock) {
        alert('Vui lòng chọn mã cổ phiếu để xuất dữ liệu');
        return;
    }
    
    exportToCSV(tableData, currentStock, currentReportType);
}

/**
 * Show loading state
 */
function showLoading() {
    const loading = document.getElementById('loading');
    const noData = document.getElementById('no-data');
    const tableWrapper = document.getElementById('table-wrapper');
    
    if (loading) loading.style.display = 'flex';
    if (noData) noData.style.display = 'none';
    if (tableWrapper) tableWrapper.style.display = 'none';
}

/**
 * Hide loading state
 */
function hideLoading() {
    const loading = document.getElementById('loading');
    if (loading) loading.style.display = 'none';
}

/**
 * Show no data state
 */
function showNoData() {
    const loading = document.getElementById('loading');
    const noData = document.getElementById('no-data');
    const tableWrapper = document.getElementById('table-wrapper');
    const summarySection = document.getElementById('summary-section');
    
    if (loading) loading.style.display = 'none';
    if (noData) noData.style.display = 'flex';
    if (tableWrapper) tableWrapper.style.display = 'none';
    if (summarySection) summarySection.style.display = 'none';
}

/**
 * Show table
 */
function showTable() {
    const loading = document.getElementById('loading');
    const noData = document.getElementById('no-data');
    const tableWrapper = document.getElementById('table-wrapper');
    
    if (loading) loading.style.display = 'none';
    if (noData) noData.style.display = 'none';
    if (tableWrapper) tableWrapper.style.display = 'block';
}

/**
 * Debounce function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

