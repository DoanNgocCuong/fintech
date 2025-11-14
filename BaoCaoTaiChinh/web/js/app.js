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
        
        // Debug: Check tree structure
        console.log('[DEBUG] Indicators data:', data.indicators);
        if (data.indicators && data.indicators.length > 0) {
            const firstIndicator = data.indicators[0];
            console.log('[DEBUG] First indicator:', {
                key: firstIndicator.key,
                has_children: firstIndicator.has_children,
                children: firstIndicator.children,
                level: firstIndicator.level,
                full_path: firstIndicator.full_path
            });
        }
        
        // Reset expanded paths when loading new data
        expandedPaths.clear();
        
        // Optionally: Auto-expand first level nodes (level 0) for better UX
        // Uncomment below if you want level 0 nodes expanded by default
        // data.indicators.forEach(ind => {
        //     if (ind.level === 0 && (ind.has_children || (ind.children && ind.children.length > 0))) {
        //         expandedPaths.add(ind.full_path);
        //     }
        // });
        
        // Apply search filter if exists
        const searchInput = document.getElementById('search-input');
        if (searchInput && searchInput.value) {
            filteredIndicators = filterIndicatorsInTree(data.indicators, searchInput.value);
        } else {
            filteredIndicators = data.indicators;
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

// Global state for expanded/collapsed nodes
let expandedPaths = new Set();

/**
 * Render table with tree structure
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
    indicatorHeader.style.minWidth = '300px';
    tableHeader.appendChild(indicatorHeader);
    
    sortedPeriods.forEach(period => {
        const th = document.createElement('th');
        th.textContent = period.label;
        th.style.textAlign = 'center';
        tableHeader.appendChild(th);
    });
    
    // Render tree structure
    renderTreeRows(indicators, tableBody, sortedPeriods, 0);
}

/**
 * Render tree rows recursively
 */
function renderTreeRows(nodes, tableBody, sortedPeriods, depth = 0) {
    if (!nodes || !Array.isArray(nodes)) {
        console.warn('[DEBUG] renderTreeRows: nodes is not an array', nodes);
        return;
    }
    
    console.log(`[DEBUG] renderTreeRows: depth=${depth}, nodes count=${nodes.length}`);
    
    nodes.forEach(node => {
        console.log(`[DEBUG] Rendering node: ${node.key}, level=${node.level}, has_children=${node.has_children}, children=${node.children ? node.children.length : 0}, full_path=${node.full_path}`);
        const row = document.createElement('tr');
        row.className = `tree-row level-${node.level || depth}`;
        row.dataset.fullPath = node.full_path || '';
        row.dataset.hasChildren = node.has_children || (node.children && node.children.length > 0) ? 'true' : 'false';
        
        // Indicator name cell with tree structure
        const indicatorCell = document.createElement('td');
        indicatorCell.className = 'indicator-cell';
        
        // Create tree structure
        const treeWrapper = document.createElement('div');
        treeWrapper.className = 'tree-wrapper';
        treeWrapper.style.paddingLeft = `${(node.level || depth) * 24}px`;
        
        // Toggle button for nodes with children
        const hasChildren = node.has_children || (node.children && node.children.length > 0);
        if (hasChildren) {
            const toggleBtn = document.createElement('button');
            toggleBtn.className = 'tree-toggle';
            toggleBtn.type = 'button'; // Prevent form submission
            const isExpanded = expandedPaths.has(node.full_path);
            toggleBtn.innerHTML = isExpanded 
                ? '<i class="fas fa-chevron-down"></i>' 
                : '<i class="fas fa-chevron-right"></i>';
            toggleBtn.onclick = (e) => {
                e.stopPropagation();
                e.preventDefault();
                console.log(`[DEBUG] Toggling node: ${node.full_path}, currently expanded: ${isExpanded}`);
                toggleTreeNode(node.full_path);
            };
            treeWrapper.appendChild(toggleBtn);
        } else {
            // Spacer for leaf nodes
            const spacer = document.createElement('span');
            spacer.className = 'tree-spacer';
            spacer.style.width = '20px';
            spacer.style.display = 'inline-block';
            treeWrapper.appendChild(spacer);
        }
        
        // Indicator label
        const labelSpan = document.createElement('span');
        labelSpan.className = 'indicator-label';
        labelSpan.textContent = node.label_vn || node.label;
        if (node.level === 0 || (node.has_children || (node.children && node.children.length > 0))) {
            labelSpan.style.fontWeight = '600';
        }
        treeWrapper.appendChild(labelSpan);
        
        indicatorCell.appendChild(treeWrapper);
        row.appendChild(indicatorCell);
        
        // Value cells
        sortedPeriods.forEach(period => {
            const cell = document.createElement('td');
            const value = node.values && node.values[period.label];
            
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
        
        // Render children if expanded (reuse hasChildren from above)
        const isExpanded = expandedPaths.has(node.full_path);
        
        if (hasChildren && isExpanded) {
            console.log(`[DEBUG] Rendering children of ${node.key}, count=${node.children.length}`);
            renderTreeRows(node.children, tableBody, sortedPeriods, depth + 1);
        } else if (hasChildren && !isExpanded) {
            console.log(`[DEBUG] Node ${node.key} has ${node.children.length} children but is collapsed`);
        }
    });
}

/**
 * Toggle tree node expand/collapse
 */
function toggleTreeNode(fullPath) {
    if (!fullPath) {
        console.warn('[DEBUG] toggleTreeNode: fullPath is empty');
        return;
    }
    
    const wasExpanded = expandedPaths.has(fullPath);
    if (wasExpanded) {
        expandedPaths.delete(fullPath);
        console.log(`[DEBUG] Collapsed node: ${fullPath}`);
    } else {
        expandedPaths.add(fullPath);
        console.log(`[DEBUG] Expanded node: ${fullPath}`);
    }
    
    // Re-render table with current filtered indicators
    if (tableData) {
        const searchInput = document.getElementById('search-input');
        let indicatorsToRender = tableData.indicators;
        
        if (searchInput && searchInput.value) {
            indicatorsToRender = filterIndicatorsInTree(tableData.indicators, searchInput.value);
        }
        
        renderTable(tableData, indicatorsToRender);
    }
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
    if (searchTerm.trim() === '') {
        // If search is empty, show all indicators
        filteredIndicators = tableData.indicators;
    } else {
        // Filter indicators (flatten tree first for search)
        filteredIndicators = filterIndicatorsInTree(tableData.indicators, searchTerm);
    }
    
    renderTable(tableData, filteredIndicators);
}

/**
 * Filter indicators in tree structure
 */
function filterIndicatorsInTree(nodes, searchTerm) {
    if (!nodes || !Array.isArray(nodes)) return [];
    
    const term = searchTerm.toLowerCase().trim();
    const filtered = [];
    
    nodes.forEach(node => {
        const label = (node.label_vn || node.label || '').toLowerCase();
        const key = (node.key || '').toLowerCase();
        const matches = label.includes(term) || key.includes(term);
        
        // If node matches, include it and all its children
        if (matches) {
            filtered.push(node);
        } else if (node.children && node.children.length > 0) {
            // Check children
            const filteredChildren = filterIndicatorsInTree(node.children, searchTerm);
            if (filteredChildren.length > 0) {
                // Create a copy of node with filtered children
                const nodeCopy = {...node, children: filteredChildren};
                filtered.push(nodeCopy);
                // Auto-expand parent if children match
                expandedPaths.add(node.full_path);
            }
        }
    });
    
    return filtered;
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

