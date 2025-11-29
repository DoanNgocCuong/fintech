/**
 * Data utilities for Scoring 7 Metrics Dashboard
 * Sử dụng API để load dữ liệu từ parsed_data
 */

// API Base URL
const API_BASE = (() => {
    const hostname = window.location.hostname;
    const protocol = window.location.protocol;
    const port = window.location.port;
    
    // If running on localhost
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        if (port === '8000') {
            return 'http://localhost:8000/api';
        }
        if (port === '30011') {
            return 'http://localhost:30011/api';
        }
        return 'http://localhost:8000/api';
    }
    
    // If running on same server
    if (port && (port === '8000' || port === '30011')) {
        return `${protocol}//${hostname}:${port}/api`;
    }
    
    // Default to production server
    return 'http://103.253.20.30:30011/api';
})();

// 7 Groups mapping
const GROUP_NAMES = {
    'governance': 'Quản trị (Governance)',
    'incentive': 'Chính sách đãi ngộ (Incentive)',
    'payout': 'Chính sách chi trả (Payout)',
    'capital': 'Vốn và huy động vốn (Capital)',
    'ownership': 'Cơ cấu sở hữu (Ownership)',
    'strategy': 'Chiến lược (Strategy)',
    'risk': 'Rủi ro (Risk)'
};

/**
 * Load companies from API
 */
async function loadCompanies(search = null) {
    try {
        let url = `${API_BASE}/companies`;
        if (search) {
            url += `?search=${encodeURIComponent(search)}`;
        }
        const response = await fetch(url);
        const result = await response.json();
        
        if (result.success && result.companies) {
            return result.companies;
        }
        return [];
    } catch (error) {
        console.error('Error loading companies:', error);
        return [];
    }
}

/**
 * Load years from API
 */
async function loadYears(companyName = null) {
    try {
        let url = `${API_BASE}/years`;
        if (companyName) {
            url += `?company_name=${encodeURIComponent(companyName)}`;
        }
        const response = await fetch(url);
        const result = await response.json();
        
        if (result.success && result.years) {
            return result.years;
        }
        return [];
    } catch (error) {
        console.error('Error loading years:', error);
        return [];
    }
}

/**
 * Load company data from API
 */
async function loadCompanyData(companyName, year) {
    try {
        const url = `${API_BASE}/company-data?company_name=${encodeURIComponent(companyName)}&year=${year}`;
        const response = await fetch(url);
        const result = await response.json();
        
        if (result.success) {
            return result;
        }
        return null;
    } catch (error) {
        console.error('Error loading company data:', error);
        return null;
    }
}

/**
 * Load company timeline from API
 */
async function loadTimeline(companyName, years = null) {
    try {
        let url = `${API_BASE}/company-timeline?company_name=${encodeURIComponent(companyName)}`;
        if (years) {
            url += `&years=${years}`;
        }
        const response = await fetch(url);
        const result = await response.json();
        
        if (result.success) {
            return result;
        }
        return null;
    } catch (error) {
        console.error('Error loading timeline:', error);
        return null;
    }
}

/**
 * Search evidence from API
 */
async function searchEvidence(keyword, companyName = null, year = null, groupId = null) {
    try {
        let url = `${API_BASE}/search-evidence?keyword=${encodeURIComponent(keyword)}`;
        if (companyName) {
            url += `&company_name=${encodeURIComponent(companyName)}`;
        }
        if (year) {
            url += `&year=${year}`;
        }
        if (groupId) {
            url += `&group_id=${encodeURIComponent(groupId)}`;
        }
        const response = await fetch(url);
        const result = await response.json();
        
        if (result.success) {
            return result.results;
        }
        return [];
    } catch (error) {
        console.error('Error searching evidence:', error);
        return [];
    }
}

/**
 * Format metrics để hiển thị
 */
function formatMetrics(metrics) {
    if (!metrics || typeof metrics !== 'object') {
        return {};
    }
    
    const formatted = {};
    for (const [key, value] of Object.entries(metrics)) {
        if (value === null || value === undefined) {
            formatted[key] = '-';
        } else if (typeof value === 'number') {
            formatted[key] = formatNumber(value);
        } else {
            formatted[key] = String(value);
        }
    }
    return formatted;
}

/**
 * Format number với comma separator
 */
function formatNumber(num) {
    if (num === null || num === undefined) {
        return '-';
    }
    return new Intl.NumberFormat('vi-VN').format(num);
}

/**
 * Format date
 */
function formatDate(dateString) {
    if (!dateString) return '-';
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('vi-VN');
    } catch (e) {
        return dateString;
    }
}

