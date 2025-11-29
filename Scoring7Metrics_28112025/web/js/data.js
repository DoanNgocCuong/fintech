/**
 * Data utilities for Scoring 7 Metrics Dashboard
 * Sử dụng API để load dữ liệu từ parsed_data
 */

// API Base URL - Load từ backend config
let API_BASE = null;

/**
 * Check if running on localhost
 */
function isLocalhost() {
    const hostname = window.location.hostname;
    return hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '';
}

/**
 * Get backend port cho local (default: 30015)
 */
function getBackendPort() {
    // 1. Thử đọc từ meta tag
    const metaPort = document.querySelector('meta[name="api-backend-port"]');
    if (metaPort && metaPort.content) {
        const port = parseInt(metaPort.content);
        if (port) return port;
    }
    
    // 2. Default: 30015 (backend port)
    return 30015;
}

/**
 * Load API config từ backend
 * Logic:
 * - Local: luôn gọi localhost:30015
 * - Production: gọi API_PRODUCTION_URL từ backend config
 */
async function loadApiConfig() {
    try {
        const hostname = window.location.hostname;
        const protocol = window.location.protocol;
        const backendPort = getBackendPort();
        
        let configUrl = null;
        
        // LOCAL: luôn dùng localhost:30015
        if (isLocalhost()) {
            configUrl = `http://localhost:${backendPort}/api/config`;
            console.log(`🔵 Local mode: calling ${configUrl}`);
        }
        // PRODUCTION: gọi backend với port 30015 (hard code)
        else {
            // Production: luôn dùng backend port 30015 (không dùng frontend port)
            configUrl = `${protocol}//${hostname}:${backendPort}/api/config`;
            console.log(`🔵 Production mode: calling ${configUrl}`);
        }
        
        // Gọi config endpoint
        if (configUrl) {
            const response = await fetch(configUrl);
            const result = await response.json();
            
            if (result.success && result.config) {
                const config = result.config;
                
                // Local: dùng api_local_url (localhost:port) từ backend
                // Backend sẽ trả về port thực tế đang chạy (30015)
                if (isLocalhost()) {
                    // Ưu tiên dùng api_local_url từ backend (port thực tế)
                    // Nếu không có, dùng backendPort từ meta tag
                    let apiUrl = config.api_local_url;
                    if (!apiUrl || !apiUrl.includes('localhost')) {
                        // Fallback: dùng port từ meta tag
                        apiUrl = `http://localhost:${backendPort}`;
                    }
                    apiUrl = apiUrl + '/api';
                    console.log(`✅ Local API URL: ${apiUrl}`);
                    return apiUrl;
                }
                // Production: dùng api_base_url từ .env (đã có đầy đủ URL với port)
                else {
                    let apiUrl = config.api_base_url;
                    // Đảm bảo có /api suffix
                    if (!apiUrl.endswith('/api')) {
                        if (apiUrl.endswith('/')) {
                            apiUrl = apiUrl + 'api';
                        } else {
                            apiUrl = apiUrl + '/api';
                        }
                    }
                    console.log(`✅ Production API URL: ${apiUrl}`);
                    return apiUrl;
                }
            }
        }
    } catch (error) {
        console.warn('⚠️ Could not load config from backend:', error);
        console.warn('   Using fallback detection...');
    }
    
    // Fallback to default detection
    return detectApiBase();
}

/**
 * Detect API base URL (fallback)
 */
function detectApiBase() {
    const hostname = window.location.hostname;
    const protocol = window.location.protocol;
    const backendPort = getBackendPort();
    
    // LOCAL: luôn dùng localhost:30015
    if (isLocalhost()) {
        return `http://localhost:${backendPort}/api`;
    }
    
    // PRODUCTION: luôn dùng hostname:30015 (không dùng frontend port)
    // Backend luôn chạy trên port 30015, không phụ thuộc frontend port
    return `${protocol}//${hostname}:${backendPort}/api`;
}

// Initialize API_BASE - Set default first, then load from config
API_BASE = detectApiBase();

// Promise để đảm bảo config được load trước khi dùng
let configLoadedPromise = null;

/**
 * Initialize API config - Tự động gọi khi page load
 * Đảm bảo config được load trước khi các API calls khác
 */
async function initializeApiConfig() {
    if (configLoadedPromise) {
        return configLoadedPromise;
    }
    
    configLoadedPromise = (async () => {
        try {
            const url = await loadApiConfig();
            if (url) {
                API_BASE = url;
                console.log('✅ API Base URL loaded from config:', API_BASE);
                return url;
            }
        } catch (err) {
            console.warn('⚠️ Failed to load API config, using default:', err);
        }
        return API_BASE;
    })();
    
    return configLoadedPromise;
}

// Tự động initialize khi script load
// Đợi DOM ready để đảm bảo có thể gọi API
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        initializeApiConfig();
    });
} else {
    // DOM already loaded
    initializeApiConfig();
}

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
 * Ensure API_BASE is initialized before making API calls
 */
async function ensureApiBaseReady() {
    if (!configLoadedPromise) {
        await initializeApiConfig();
    } else {
        await configLoadedPromise;
    }
}

/**
 * Load companies from API
 */
async function loadCompanies(search = null) {
    // Đảm bảo API_BASE đã được load từ config
    await ensureApiBaseReady();
    
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
    // Đảm bảo API_BASE đã được load từ config
    await ensureApiBaseReady();
    
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
    // Đảm bảo API_BASE đã được load từ config
    await ensureApiBaseReady();
    
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
    // Đảm bảo API_BASE đã được load từ config
    await ensureApiBaseReady();
    
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
    // Đảm bảo API_BASE đã được load từ config
    await ensureApiBaseReady();
    
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

