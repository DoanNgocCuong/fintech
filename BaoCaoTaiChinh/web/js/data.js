/**
 * Data utilities for financial reports dashboard
 */

// API Base URL
// Auto-detect based on current hostname
const API_BASE = (() => {
    const hostname = window.location.hostname;
    const protocol = window.location.protocol;
    const port = window.location.port;
    
    // If running on localhost or 127.0.0.1, check port
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        // If port is 30011, use 30011
        if (port === '30011') {
            return 'http://localhost:30011/api';
        }
        // If port is 8000, use 8000
        if (port === '8000') {
            return 'http://localhost:8000/api';
        }
        // Default to 30011 for localhost if no port specified
        return 'http://localhost:30011/api';
    }
    
    // If running on same server, use relative path
    if (port && (port === '8000' || port === '30011')) {
        return `${protocol}//${hostname}:${port}/api`;
    }
    
    // Default to production server
    return 'http://103.253.20.30:30011/api';
})();

// Report type mapping
const REPORT_TYPE_MAP = {
    'balance': 'balance-sheet',
    'income': 'income-statement',
    'cashflow': 'cash-flow'
};

const INCOME_SECTION_TABLES = {
    'P1': 'income_statement_p1_raw',
    'P2': 'income_statement_p2_raw'
};

const DEFAULT_INCOME_SECTION = 'P2';

/**
 * Load stocks from API
 */
async function loadStocks(reportType = 'balance', section = null) {
    try {
        let tableName = 'balance_sheet_raw';
        if (reportType === 'income') {
            const sectionKey = normalizeIncomeSection(section);
            tableName = INCOME_SECTION_TABLES[sectionKey];
        } else if (reportType === 'cashflow') {
            tableName = 'cash_flow_statement_raw';
        }
        const response = await fetch(`${API_BASE}/stocks?table=${tableName}`);
        const result = await response.json();
        
        if (result.success && result.stocks) {
            return result.stocks;
        }
        return [];
    } catch (error) {
        console.error('Error loading stocks:', error);
        return [];
    }
}

/**
 * Load table data for a stock and report type
 */
async function loadTableData(stock, reportType, section = null) {
    try {
        const reportTypeApi = REPORT_TYPE_MAP[reportType] || 'balance-sheet';
        let url = `${API_BASE}/${reportTypeApi}/table-data?stock=${stock}`;
        if (reportType === 'income') {
            const sectionKey = normalizeIncomeSection(section);
            url += `&section=${sectionKey}`;
        }
        const response = await fetch(url);
        const result = await response.json();
        
        if (result.success) {
            return result;
        }
        return null;
    } catch (error) {
        console.error('Error loading table data:', error);
        return null;
    }
}

/**
 * Format number with comma separator
 */
function formatNumber(value) {
    if (value === null || value === undefined || value === '') {
        return '-';
    }
    
    const num = typeof value === 'string' ? parseFloat(value) : value;
    if (isNaN(num)) {
        return '-';
    }
    
    return num.toLocaleString('vi-VN', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    });
}

/**
 * Format period label (Q1-2025)
 */
function formatPeriodLabel(year, quarter) {
    if (quarter === null || quarter === undefined) {
        quarter = 5; // Year-end
    }
    return `Q${quarter}-${year}`;
}

/**
 * Sort periods by year and quarter (descending)
 */
function sortPeriods(periods) {
    return periods.sort((a, b) => {
        if (a.year !== b.year) {
            return b.year - a.year;
        }
        return (b.quarter || 5) - (a.quarter || 5);
    });
}

/**
 * Filter indicators by search term
 */
function filterIndicators(indicators, searchTerm) {
    if (!searchTerm || searchTerm.trim() === '') {
        return indicators;
    }
    
    const term = searchTerm.toLowerCase().trim();
    return indicators.filter(indicator => {
        const label = (indicator.label_vn || indicator.label || '').toLowerCase();
        const key = (indicator.key || '').toLowerCase();
        return label.includes(term) || key.includes(term);
    });
}

/**
 * Export data to CSV
 */
function exportToCSV(data, stock, reportType, section = null) {
    if (!data || !data.indicators || !data.periods) {
        alert('Không có dữ liệu để xuất');
        return;
    }
    
    const reportTypeLabels = {
        'balance': 'Cân đối kế toán',
        'income': 'Kết quả kinh doanh',
        'cashflow': 'Lưu chuyển tiền tệ'
    };
    
    let reportLabel = reportTypeLabels[reportType] || reportType;
    if (reportType === 'income' && section) {
        reportLabel += section === 'P1' ? ' (Phần I)' : ' (Phần II)';
    }
    
    let csv = `Báo cáo: ${reportLabel}\n`;
    csv += `Mã cổ phiếu: ${stock}\n`;
    csv += `Ngày xuất: ${new Date().toLocaleString('vi-VN')}\n\n`;
    
    // Header row
    csv += 'Chỉ tiêu,';
    data.periods.forEach(period => {
        csv += `${period.label},`;
    });
    csv += '\n';
    
    // Data rows
    data.indicators.forEach(indicator => {
        csv += `"${indicator.label_vn || indicator.label}",`;
        data.periods.forEach(period => {
            const value = indicator.values[period.label];
            csv += value !== null && value !== undefined ? `"${formatNumber(value)}",` : '"-",';
        });
        csv += '\n';
    });
    
    // Create blob and download
    const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    const sectionSuffix = section ? `_${section.toLowerCase()}` : '';
    link.setAttribute('download', `bao_cao_${reportType}${sectionSuffix}_${stock}_${new Date().getTime()}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function normalizeIncomeSection(section) {
    if (!section) return DEFAULT_INCOME_SECTION;
    const key = String(section).trim().toUpperCase();
    return INCOME_SECTION_TABLES[key] ? key : DEFAULT_INCOME_SECTION;
}

