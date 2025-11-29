# 📡 TÀI LIỆU MÓC NỐI FRONTEND - BACKEND

> **Hướng dẫn chi tiết về cách móc nối, logic hoạt động và source code demo**

---

## 📋 MỤC LỤC

1. [Tổng quan kiến trúc](#1-tổng-quan-kiến-trúc)
2. [Luồng hoạt động](#2-luồng-hoạt-động)
3. [Chi tiết Backend API](#3-chi-tiết-backend-api)
4. [Chi tiết Frontend Client](#4-chi-tiết-frontend-client)
5. [Logic Auto-Detection](#5-logic-auto-detection)
6. [Source Code Demo](#6-source-code-demo)
7. [Troubleshooting](#7-troubleshooting)
8. [Best Practices](#8-best-practices)

---

## 1. TỔNG QUAN KIẾN TRÚC

### 1.1. Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────────────┐
│                       CLIENT BROWSER                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         Frontend (HTML + JavaScript)                │   │
│  │  ┌──────────────────────────────────────────────┐   │   │
│  │  │  js/data.js - API Client                     │   │   │
│  │  │  - Auto-detect environment                   │   │   │
│  │  │  - Fetch config from backend                 │   │   │
│  │  │  - Make API calls                            │   │   │
│  │  └──────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ HTTP Request
                       │ (Fetch API)
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND SERVER                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         FastAPI Application (app.py)                │   │
│  │  ┌──────────────────────────────────────────────┐   │   │
│  │  │  Endpoints:                                  │   │   │
│  │  │  - GET  /api/config                          │   │   │
│  │  │  - GET  /api/companies                       │   │   │
│  │  │  - POST /api/metrics                         │   │   │
│  │  │  - GET  /api/health                          │   │   │
│  │  └──────────────────────────────────────────────┘   │   │
│  │  ┌──────────────────────────────────────────────┐   │   │
│  │  │  utils_config.py                             │   │   │
│  │  │  - Environment detection                     │   │   │
│  │  │  - Config management                         │   │   │
│  │  │  - CORS settings                             │   │   │
│  │  └──────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 1.2. Các thành phần chính

| Thành phần | File | Vai trò |
|------------|------|---------|
| **Backend API** | `app.py` | Xử lý requests, trả về data |
| **Config Manager** | `utils_config.py` | Quản lý cấu hình, detect environment |
| **Frontend Client** | `js/data.js` | Gọi API, xử lý data |
| **UI Components** | `index.html`, `js/ui.js` | Hiển thị dữ liệu |

---

## 2. LUỒNG HOẠT ĐỘNG

### 2.1. Luồng khởi động

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User truy cập: http://localhost/index.html              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Browser load HTML + JavaScript                          │
│    - Load js/data.js                                        │
│    - Khởi tạo DataService class                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Auto-detect environment                                 │
│    - Check window.location.hostname                        │
│    - Determine: local hay server?                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Fetch config from backend                               │
│    GET /api/config                                          │
│    ┌─────────────────────────────────────────────────┐     │
│    │ Request:                                        │     │
│    │   GET http://localhost:8000/api/config          │     │
│    │                                                 │     │
│    │ Response:                                       │     │
│    │   {                                             │     │
│    │     "api_base_url": "http://localhost:8000/api",│     │
│    │     "environment": "development",               │     │
│    │     "version": "1.0.0"                          │     │
│    │   }                                             │     │
│    └─────────────────────────────────────────────────┘     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. DataService sử dụng API_BASE_URL từ config              │
│    - Lưu vào this.API_BASE                                 │
│    - Sẵn sàng gọi các API khác                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Gọi API để load data                                    │
│    - GET /api/companies                                     │
│    - POST /api/metrics                                      │
└─────────────────────────────────────────────────────────────┘
```

### 2.2. Luồng gọi API

```javascript
// Frontend: js/data.js
async fetchMetrics(companyCode, period) {
    // 1. Tạo request URL
    const url = `${this.API_BASE}/metrics`;

    // 2. Gửi POST request
    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            company_code: companyCode,
            period: period
        })
    });

    // 3. Nhận response
    const data = await response.json();

    // 4. Xử lý data
    return data.metrics;
}
```

```
Frontend                          Backend
   │                                 │
   │  POST /api/metrics              │
   ├────────────────────────────────>│
   │  { company_code, period }       │
   │                                 │
   │                                 │ Process request
   │                                 │ - Validate input
   │                                 │ - Query database
   │                                 │ - Calculate metrics
   │                                 │
   │  200 OK                         │
   │<────────────────────────────────┤
   │  { metrics: [...] }             │
   │                                 │
   │  Process response               │
   │  - Update UI                    │
   │  - Display data                 │
   │                                 │
```

---

## 3. CHI TIẾT BACKEND API

### 3.1. Environment Detection

```python
# utils_config.py

import socket
import os

def is_local_environment():
    """
    Detect nếu đang chạy trên local hay server

    Returns:
        bool: True nếu local, False nếu server
    """
    # Method 1: Check hostname
    hostname = socket.gethostname()
    if hostname in ['localhost', '127.0.0.1', 'DESKTOP-*', 'LAPTOP-*']:
        return True

    # Method 2: Check IP address
    try:
        ip = socket.gethostbyname(hostname)
        if ip.startswith('192.168.') or ip.startswith('10.') or ip == '127.0.0.1':
            return True
    except:
        pass

    # Method 3: Check environment variable
    if os.getenv('ENVIRONMENT') == 'development':
        return True

    return False

def get_api_base_url():
    """
    Trả về API base URL dựa trên environment

    Returns:
        str: API base URL
    """
    if is_local_environment():
        # Local: dùng localhost
        host = os.getenv('API_HOST', 'localhost')
        port = os.getenv('API_PORT', '8000')
        return f"http://{host}:{port}/api"
    else:
        # Server: dùng IP public
        return "http://103.253.20.30:30015/api"

def get_frontend_config():
    """
    Config cho frontend
    Frontend KHÔNG dùng 0.0.0.0 vì browser không hiểu

    Returns:
        dict: Config object
    """
    return {
        "api_base_url": get_api_base_url(),
        "environment": "development" if is_local_environment() else "production",
        "version": "1.0.0",
        "features": {
            "realtime_updates": False,
            "export_excel": True,
            "export_pdf": True
        }
    }
```

### 3.2. Backend Endpoints

```python
# app.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from utils_config import get_frontend_config, is_local_environment
import uvicorn

app = FastAPI(title="Scoring Metrics API")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production nên giới hạn domain cụ thể
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# 1. CONFIG ENDPOINT - Frontend gọi đầu tiên
# ============================================================
@app.get("/api/config")
async def get_config():
    """
    Endpoint đầu tiên frontend gọi để lấy cấu hình

    Returns:
        - api_base_url: URL để gọi API (localhost hoặc IP public)
        - environment: development hoặc production
        - version: Version của API
        - features: Các tính năng enable/disable
    """
    return get_frontend_config()

# ============================================================
# 2. COMPANIES ENDPOINT - Lấy danh sách công ty
# ============================================================
@app.get("/api/companies")
async def get_companies():
    """
    Lấy danh sách tất cả công ty

    Returns:
        List[dict]: Danh sách công ty
        [
            {
                "code": "BVH",
                "name": "Bảo Việt Holdings",
                "industry": "Insurance"
            },
            ...
        ]
    """
    try:
        companies = load_companies_from_db()
        return {"companies": companies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# 3. METRICS ENDPOINT - Lấy chỉ số công ty
# ============================================================
@app.post("/api/metrics")
async def get_metrics(request: dict):
    """
    Tính toán và trả về các chỉ số tài chính

    Request Body:
        {
            "company_code": "BVH",
            "period": "2023"
        }

    Returns:
        {
            "metrics": {
                "liquidity": {...},
                "profitability": {...},
                "efficiency": {...},
                ...
            },
            "metadata": {
                "company_code": "BVH",
                "period": "2023",
                "generated_at": "2025-11-29T10:30:00"
            }
        }
    """
    try:
        company_code = request.get('company_code')
        period = request.get('period')

        if not company_code or not period:
            raise HTTPException(
                status_code=400,
                detail="Missing company_code or period"
            )

        metrics = calculate_metrics(company_code, period)

        return {
            "metrics": metrics,
            "metadata": {
                "company_code": company_code,
                "period": period,
                "generated_at": datetime.now().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# 4. HEALTH CHECK ENDPOINT
# ============================================================
@app.get("/api/health")
async def health_check():
    """
    Health check endpoint

    Returns:
        {
            "status": "healthy",
            "environment": "development",
            "timestamp": "2025-11-29T10:30:00"
        }
    """
    return {
        "status": "healthy",
        "environment": "development" if is_local_environment() else "production",
        "timestamp": datetime.now().isoformat()
    }

# ============================================================
# RUN SERVER
# ============================================================
if __name__ == "__main__":
    # Backend LUÔN dùng 0.0.0.0 để bind vào tất cả interfaces
    # - Local: vẫn truy cập được qua localhost, 127.0.0.1, hoặc 192.168.x.x
    # - Server: bắt buộc để expose ra ngoài qua IP public

    if is_local_environment():
        # Local development
        uvicorn.run(
            app,
            host="0.0.0.0",  # Bind tất cả interfaces
            port=8000,
            reload=True      # Auto-reload khi code thay đổi
        )
    else:
        # Production server
        uvicorn.run(
            app,
            host="0.0.0.0",  # Bind tất cả interfaces
            port=30015,
            workers=4        # Multiple workers cho production
        )
```

---

## 4. CHI TIẾT FRONTEND CLIENT

### 4.1. DataService Class

```javascript
// js/data.js

class DataService {
    constructor() {
        // KHÔNG hard-code URL ở đây
        // Sẽ được set sau khi fetch config từ backend
        this.API_BASE = null;
        this.isInitialized = false;
    }

    /**
     * Khởi tạo DataService
     * Bước 1: Detect environment
     * Bước 2: Fetch config từ backend
     * Bước 3: Set API_BASE_URL
     */
    async initialize() {
        if (this.isInitialized) {
            return; // Đã khởi tạo rồi
        }

        try {
            // Auto-detect environment
            const env = this.detectEnvironment();
            console.log(`[DataService] Environment detected: ${env}`);

            // Fetch config từ backend
            const config = await this.fetchConfig(env);
            console.log(`[DataService] Config loaded:`, config);

            // Set API base URL
            this.API_BASE = config.api_base_url;
            this.environment = config.environment;
            this.version = config.version;

            this.isInitialized = true;
            console.log(`[DataService] Initialized successfully`);
            console.log(`[DataService] API_BASE: ${this.API_BASE}`);
        } catch (error) {
            console.error('[DataService] Initialization failed:', error);
            // Fallback to default
            this.API_BASE = this.getDefaultApiUrl();
            console.warn(`[DataService] Using fallback URL: ${this.API_BASE}`);
        }
    }

    /**
     * Detect environment dựa trên hostname
     *
     * @returns {string} 'local' hoặc 'server'
     */
    detectEnvironment() {
        const hostname = window.location.hostname;

        // Local environments
        const localHosts = [
            'localhost',
            '127.0.0.1',
            '0.0.0.0',
            '::1'
        ];

        // Check IP range (192.168.x.x, 10.x.x.x)
        const isLocalIP = hostname.startsWith('192.168.') ||
                          hostname.startsWith('10.') ||
                          hostname.startsWith('172.');

        if (localHosts.includes(hostname) || isLocalIP) {
            return 'local';
        }

        return 'server';
    }

    /**
     * Fetch config từ backend
     *
     * @param {string} env - Environment: 'local' hoặc 'server'
     * @returns {Promise<Object>} Config object
     */
    async fetchConfig(env) {
        // Tạo config URL dựa trên environment
        let configUrl;

        if (env === 'local') {
            configUrl = 'http://localhost:8000/api/config';
        } else {
            configUrl = 'http://103.253.20.30:30015/api/config';
        }

        console.log(`[DataService] Fetching config from: ${configUrl}`);

        const response = await fetch(configUrl);

        if (!response.ok) {
            throw new Error(`Failed to fetch config: ${response.status}`);
        }

        return await response.json();
    }

    /**
     * Fallback URL nếu không fetch được config
     *
     * @returns {string} Default API URL
     */
    getDefaultApiUrl() {
        const hostname = window.location.hostname;

        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            return 'http://localhost:8000/api';
        }

        return 'http://103.253.20.30:30015/api';
    }

    /**
     * Kiểm tra xem đã khởi tạo chưa
     * Tự động gọi initialize() nếu chưa
     */
    async ensureInitialized() {
        if (!this.isInitialized) {
            await this.initialize();
        }
    }

    // ============================================================
    // API METHODS
    // ============================================================

    /**
     * Lấy danh sách công ty
     *
     * @returns {Promise<Array>} Danh sách công ty
     */
    async fetchCompanies() {
        await this.ensureInitialized();

        const url = `${this.API_BASE}/companies`;
        console.log(`[API] GET ${url}`);

        try {
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            console.log(`[API] Response:`, data);

            return data.companies || [];
        } catch (error) {
            console.error('[API] Error fetching companies:', error);
            throw error;
        }
    }

    /**
     * Lấy metrics của công ty
     *
     * @param {string} companyCode - Mã công ty (VD: "BVH")
     * @param {string} period - Kỳ báo cáo (VD: "2023")
     * @returns {Promise<Object>} Metrics data
     */
    async fetchMetrics(companyCode, period) {
        await this.ensureInitialized();

        const url = `${this.API_BASE}/metrics`;
        console.log(`[API] POST ${url}`);
        console.log(`[API] Request:`, { companyCode, period });

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    company_code: companyCode,
                    period: period
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            console.log(`[API] Response:`, data);

            return data.metrics || {};
        } catch (error) {
            console.error('[API] Error fetching metrics:', error);
            throw error;
        }
    }

    /**
     * Health check
     *
     * @returns {Promise<Object>} Health status
     */
    async checkHealth() {
        await this.ensureInitialized();

        const url = `${this.API_BASE}/health`;
        console.log(`[API] GET ${url}`);

        try {
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            console.log(`[API] Health check:`, data);

            return data;
        } catch (error) {
            console.error('[API] Health check failed:', error);
            throw error;
        }
    }
}

// Export singleton instance
const dataService = new DataService();
```

### 4.2. Sử dụng DataService trong UI

```javascript
// js/ui.js hoặc trong index.html

async function initApp() {
    try {
        // 1. Khởi tạo DataService
        await dataService.initialize();
        console.log('✅ DataService initialized');

        // 2. Health check (optional)
        const health = await dataService.checkHealth();
        console.log('✅ Backend healthy:', health);

        // 3. Load danh sách công ty
        const companies = await dataService.fetchCompanies();
        console.log('✅ Companies loaded:', companies.length);

        // 4. Populate UI
        populateCompanyDropdown(companies);

        // 5. Load metrics cho công ty mặc định
        if (companies.length > 0) {
            const defaultCompany = companies[0].code;
            await loadMetrics(defaultCompany, '2023');
        }

    } catch (error) {
        console.error('❌ App initialization failed:', error);
        showErrorMessage('Không thể kết nối đến server');
    }
}

async function loadMetrics(companyCode, period) {
    try {
        showLoadingSpinner();

        // Gọi API
        const metrics = await dataService.fetchMetrics(companyCode, period);
        console.log('✅ Metrics loaded:', metrics);

        // Update UI
        displayMetrics(metrics);

        hideLoadingSpinner();
    } catch (error) {
        console.error('❌ Failed to load metrics:', error);
        showErrorMessage('Không thể tải dữ liệu chỉ số');
        hideLoadingSpinner();
    }
}

// Khởi động app khi DOM ready
document.addEventListener('DOMContentLoaded', () => {
    initApp();
});
```

---

## 5. LOGIC AUTO-DETECTION

### 5.1. Frontend Detection Flow

```javascript
/**
 * LUỒNG DETECTION CHI TIẾT
 *
 * 1. Kiểm tra hostname
 *    - localhost → LOCAL
 *    - 127.0.0.1 → LOCAL
 *    - 192.168.x.x → LOCAL
 *    - 10.x.x.x → LOCAL
 *    - Khác → SERVER
 *
 * 2. Xác định config URL
 *    - LOCAL → http://localhost:8000/api/config
 *    - SERVER → http://103.253.20.30:30015/api/config
 *
 * 3. Fetch config từ backend
 *    - Success → Dùng api_base_url từ response
 *    - Fail → Fallback to default URL
 *
 * 4. Set API_BASE và sẵn sàng gọi API
 */

detectEnvironment() {
    const hostname = window.location.hostname;
    const port = window.location.port;

    console.group('🔍 Environment Detection');
    console.log('Hostname:', hostname);
    console.log('Port:', port);
    console.log('Full URL:', window.location.href);

    let env = 'server'; // Default

    // Check local patterns
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        env = 'local';
        console.log('✅ Detected: LOCAL (hostname match)');
    } else if (hostname.startsWith('192.168.') || hostname.startsWith('10.')) {
        env = 'local';
        console.log('✅ Detected: LOCAL (IP range)');
    } else {
        console.log('✅ Detected: SERVER (public IP)');
    }

    console.groupEnd();
    return env;
}
```

### 5.2. Backend Detection Flow

```python
def is_local_environment():
    """
    LUỒNG DETECTION CHI TIẾT

    1. Kiểm tra hostname
       - localhost, 127.0.0.1 → LOCAL
       - DESKTOP-*, LAPTOP-* → LOCAL
       - Khác → Tiếp tục kiểm tra

    2. Kiểm tra IP address
       - 192.168.x.x → LOCAL (Private network)
       - 10.x.x.x → LOCAL (Private network)
       - 127.0.0.1 → LOCAL (Loopback)
       - Khác → Tiếp tục kiểm tra

    3. Kiểm tra environment variable
       - ENVIRONMENT=development → LOCAL
       - Khác → SERVER

    Returns:
        bool: True nếu LOCAL, False nếu SERVER
    """
    import socket
    import os

    # 1. Check hostname
    hostname = socket.gethostname()
    print(f"[Detection] Hostname: {hostname}")

    local_patterns = ['localhost', '127.0.0.1', 'DESKTOP-', 'LAPTOP-']
    if any(pattern in hostname for pattern in local_patterns):
        print("[Detection] ✅ LOCAL (hostname match)")
        return True

    # 2. Check IP address
    try:
        ip = socket.gethostbyname(hostname)
        print(f"[Detection] IP: {ip}")

        if ip.startswith('192.168.') or ip.startswith('10.') or ip == '127.0.0.1':
            print("[Detection] ✅ LOCAL (IP range)")
            return True
    except Exception as e:
        print(f"[Detection] ⚠️ Cannot resolve IP: {e}")

    # 3. Check environment variable
    env = os.getenv('ENVIRONMENT', 'production')
    print(f"[Detection] ENVIRONMENT: {env}")

    if env == 'development':
        print("[Detection] ✅ LOCAL (env var)")
        return True

    print("[Detection] ✅ SERVER (default)")
    return False
```

---

## 6. SOURCE CODE DEMO

### 6.1. Demo đầy đủ: Load và hiển thị metrics

```html
<!-- index.html -->
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Scoring Metrics Demo</title>
    <style>
        .loading { display: none; }
        .error { color: red; }
        .success { color: green; }
    </style>
</head>
<body>
    <h1>Scoring Metrics Dashboard</h1>

    <!-- Status -->
    <div id="status">
        <p>API: <span id="api-url">...</span></p>
        <p>Environment: <span id="environment">...</span></p>
        <p>Health: <span id="health">...</span></p>
    </div>

    <!-- Company Selection -->
    <div>
        <label>Chọn công ty:</label>
        <select id="company-select">
            <option value="">-- Chọn công ty --</option>
        </select>

        <label>Kỳ báo cáo:</label>
        <select id="period-select">
            <option value="2023">2023</option>
            <option value="2024">2024</option>
        </select>

        <button onclick="loadData()">Tải dữ liệu</button>
    </div>

    <!-- Loading -->
    <div id="loading" class="loading">
        <p>Đang tải dữ liệu...</p>
    </div>

    <!-- Error -->
    <div id="error" class="error" style="display:none;"></div>

    <!-- Results -->
    <div id="results" style="display:none;">
        <h2>Kết quả phân tích</h2>
        <pre id="metrics-output"></pre>
    </div>

    <!-- Scripts -->
    <script src="js/data.js"></script>
    <script>
        // ========================================
        // APP INITIALIZATION
        // ========================================

        async function initApp() {
            try {
                console.log('🚀 Starting app initialization...');

                // 1. Initialize DataService
                await dataService.initialize();
                updateStatus();

                // 2. Health check
                const health = await dataService.checkHealth();
                document.getElementById('health').textContent = health.status;
                document.getElementById('health').className = 'success';

                // 3. Load companies
                const companies = await dataService.fetchCompanies();
                populateCompanySelect(companies);

                console.log('✅ App initialized successfully');

            } catch (error) {
                console.error('❌ App initialization failed:', error);
                showError('Không thể khởi động ứng dụng: ' + error.message);
            }
        }

        // ========================================
        // UI UPDATE FUNCTIONS
        // ========================================

        function updateStatus() {
            document.getElementById('api-url').textContent = dataService.API_BASE;
            document.getElementById('environment').textContent = dataService.environment;
        }

        function populateCompanySelect(companies) {
            const select = document.getElementById('company-select');

            companies.forEach(company => {
                const option = document.createElement('option');
                option.value = company.code;
                option.textContent = `${company.code} - ${company.name}`;
                select.appendChild(option);
            });

            console.log(`✅ Loaded ${companies.length} companies`);
        }

        function showLoading() {
            document.getElementById('loading').style.display = 'block';
            document.getElementById('error').style.display = 'none';
            document.getElementById('results').style.display = 'none';
        }

        function hideLoading() {
            document.getElementById('loading').style.display = 'none';
        }

        function showError(message) {
            const errorDiv = document.getElementById('error');
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
            hideLoading();
        }

        function showResults(metrics) {
            const resultsDiv = document.getElementById('results');
            const output = document.getElementById('metrics-output');

            output.textContent = JSON.stringify(metrics, null, 2);
            resultsDiv.style.display = 'block';
            hideLoading();
        }

        // ========================================
        // LOAD DATA FUNCTION
        // ========================================

        async function loadData() {
            const companyCode = document.getElementById('company-select').value;
            const period = document.getElementById('period-select').value;

            if (!companyCode) {
                alert('Vui lòng chọn công ty');
                return;
            }

            try {
                console.log(`📊 Loading metrics for ${companyCode} (${period})...`);
                showLoading();

                // Fetch metrics
                const metrics = await dataService.fetchMetrics(companyCode, period);

                console.log('✅ Metrics loaded:', metrics);
                showResults(metrics);

            } catch (error) {
                console.error('❌ Failed to load metrics:', error);
                showError('Không thể tải dữ liệu: ' + error.message);
            }
        }

        // ========================================
        // START APP
        // ========================================

        document.addEventListener('DOMContentLoaded', () => {
            initApp();
        });
    </script>
</body>
</html>
```

### 6.2. Demo Error Handling

```javascript
// Advanced error handling trong DataService

class DataService {
    // ... (code trước đó)

    /**
     * Wrapper cho fetch với retry logic
     */
    async fetchWithRetry(url, options = {}, maxRetries = 3) {
        let lastError;

        for (let i = 0; i < maxRetries; i++) {
            try {
                console.log(`[Fetch] Attempt ${i + 1}/${maxRetries}: ${url}`);

                const response = await fetch(url, options);

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                return await response.json();

            } catch (error) {
                lastError = error;
                console.warn(`[Fetch] Attempt ${i + 1} failed:`, error.message);

                if (i < maxRetries - 1) {
                    // Wait before retry (exponential backoff)
                    const waitTime = Math.pow(2, i) * 1000; // 1s, 2s, 4s
                    console.log(`[Fetch] Retrying in ${waitTime}ms...`);
                    await new Promise(resolve => setTimeout(resolve, waitTime));
                }
            }
        }

        throw new Error(`Failed after ${maxRetries} attempts: ${lastError.message}`);
    }

    /**
     * Fetch metrics với retry
     */
    async fetchMetrics(companyCode, period) {
        await this.ensureInitialized();

        const url = `${this.API_BASE}/metrics`;

        return await this.fetchWithRetry(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                company_code: companyCode,
                period: period
            })
        });
    }
}
```

### 6.3. Demo Caching

```javascript
// DataService với caching

class DataService {
    constructor() {
        this.API_BASE = null;
        this.isInitialized = false;

        // Cache
        this.cache = {
            companies: null,
            metrics: new Map(), // Key: "companyCode_period"
            config: null
        };

        // Cache TTL (Time To Live)
        this.cacheTTL = {
            companies: 5 * 60 * 1000,  // 5 phút
            metrics: 30 * 60 * 1000,   // 30 phút
            config: 60 * 60 * 1000     // 1 giờ
        };
    }

    /**
     * Get từ cache hoặc fetch mới
     */
    async fetchCompanies(forceRefresh = false) {
        // Check cache
        if (!forceRefresh && this.cache.companies) {
            const age = Date.now() - this.cache.companies.timestamp;

            if (age < this.cacheTTL.companies) {
                console.log('[Cache] Using cached companies');
                return this.cache.companies.data;
            }
        }

        // Fetch mới
        await this.ensureInitialized();
        const url = `${this.API_BASE}/companies`;

        const response = await fetch(url);
        const data = await response.json();
        const companies = data.companies || [];

        // Update cache
        this.cache.companies = {
            data: companies,
            timestamp: Date.now()
        };

        console.log('[Cache] Companies cached');
        return companies;
    }

    /**
     * Get metrics với cache
     */
    async fetchMetrics(companyCode, period, forceRefresh = false) {
        const cacheKey = `${companyCode}_${period}`;

        // Check cache
        if (!forceRefresh && this.cache.metrics.has(cacheKey)) {
            const cached = this.cache.metrics.get(cacheKey);
            const age = Date.now() - cached.timestamp;

            if (age < this.cacheTTL.metrics) {
                console.log(`[Cache] Using cached metrics for ${cacheKey}`);
                return cached.data;
            }
        }

        // Fetch mới
        await this.ensureInitialized();
        const url = `${this.API_BASE}/metrics`;

        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ company_code: companyCode, period: period })
        });

        const data = await response.json();
        const metrics = data.metrics || {};

        // Update cache
        this.cache.metrics.set(cacheKey, {
            data: metrics,
            timestamp: Date.now()
        });

        console.log(`[Cache] Metrics cached for ${cacheKey}`);
        return metrics;
    }

    /**
     * Clear cache
     */
    clearCache() {
        this.cache.companies = null;
        this.cache.metrics.clear();
        this.cache.config = null;
        console.log('[Cache] Cleared all cache');
    }
}
```

---

## 7. TROUBLESHOOTING

### 7.1. Common Issues

| Vấn đề | Nguyên nhân | Giải pháp |
|--------|-------------|-----------|
| **CORS Error** | Backend chưa config CORS | Thêm CORS middleware trong `app.py` |
| **404 Not Found** | Sai URL hoặc endpoint | Kiểm tra `API_BASE` và endpoint path |
| **Network Error** | Backend chưa chạy | Start backend: `python app.py` |
| **Timeout** | Request quá lâu | Tăng timeout hoặc optimize backend |
| **500 Server Error** | Lỗi trong backend code | Check backend logs |

### 7.2. Debug Checklist

```javascript
// Debug script - chạy trong Console

// 1. Kiểm tra environment
console.log('Hostname:', window.location.hostname);
console.log('Port:', window.location.port);
console.log('Environment:', dataService.detectEnvironment());

// 2. Kiểm tra API URL
console.log('API Base:', dataService.API_BASE);

// 3. Test connectivity
fetch(dataService.API_BASE + '/health')
    .then(r => r.json())
    .then(d => console.log('Health check:', d))
    .catch(e => console.error('Health check failed:', e));

// 4. Test config endpoint
fetch(dataService.API_BASE.replace('/api', '') + '/api/config')
    .then(r => r.json())
    .then(d => console.log('Config:', d))
    .catch(e => console.error('Config failed:', e));

// 5. Kiểm tra cache
console.log('Cache:', dataService.cache);

// 6. Clear cache và reload
dataService.clearCache();
location.reload();
```

### 7.3. Backend Debug

```python
# Thêm debug logging vào app.py

import logging

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Thêm middleware để log requests
@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    logger.info(f"Headers: {request.headers}")

    response = await call_next(request)

    logger.info(f"Response: {response.status_code}")
    return response
```

---

## 8. BEST PRACTICES

### 8.1. Frontend Best Practices

✅ **DO:**
- Always await `dataService.initialize()` before using
- Use try-catch for all async operations
- Cache data when appropriate
- Show loading states
- Handle errors gracefully
- Log important events
- Use retry logic for critical requests

❌ **DON'T:**
- Don't hard-code API URLs
- Don't ignore errors
- Don't make excessive API calls
- Don't trust user input without validation
- Don't expose sensitive data in console logs

### 8.2. Backend Best Practices

✅ **DO:**
- Validate all input parameters
- Use proper HTTP status codes
- Return consistent response format
- Log errors with context
- Use environment variables for config
- Implement rate limiting
- Add request timeout

❌ **DON'T:**
- Don't expose internal errors to client
- Don't allow unrestricted CORS in production
- Don't run without proper error handling
- Don't use `0.0.0.0` in config URLs (frontend không hiểu)

### 8.3. Security Best Practices

```python
# Backend security

from fastapi import Request, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

@app.post("/api/metrics")
@limiter.limit("10/minute")  # Max 10 requests per minute
async def get_metrics(request: Request, data: dict):
    # Validate input
    if not validate_input(data):
        raise HTTPException(status_code=400, detail="Invalid input")

    # Sanitize
    company_code = sanitize_string(data.get('company_code'))
    period = sanitize_string(data.get('period'))

    # Process
    # ...
```

```javascript
// Frontend security

class DataService {
    /**
     * Sanitize user input
     */
    sanitizeInput(input) {
        if (typeof input !== 'string') {
            return '';
        }

        // Remove special characters
        return input.replace(/[<>\"']/g, '');
    }

    /**
     * Validate company code
     */
    validateCompanyCode(code) {
        // Only allow alphanumeric
        return /^[A-Z0-9]+$/.test(code);
    }

    async fetchMetrics(companyCode, period) {
        // Validate before sending
        if (!this.validateCompanyCode(companyCode)) {
            throw new Error('Invalid company code');
        }

        // Sanitize
        companyCode = this.sanitizeInput(companyCode);
        period = this.sanitizeInput(period);

        // Proceed with API call
        // ...
    }
}
```

---

## 📝 TÓM TẮT

### Các điểm chính cần nhớ:

1. **Backend luôn dùng `0.0.0.0`** để bind tất cả interfaces
2. **Frontend KHÔNG bao giờ dùng `0.0.0.0`** - dùng localhost hoặc IP public
3. **Auto-detection** giúp tự động chọn URL phù hợp
4. **Config endpoint** (`/api/config`) là điểm khởi đầu của frontend
5. **Error handling** và **retry logic** giúp app ổn định hơn
6. **Caching** giảm số lượng API calls không cần thiết
7. **Logging** giúp debug dễ dàng hơn
8. **Security** luôn là ưu tiên hàng đầu

---

## 🔗 LIÊN KẾT LIÊN QUAN

- [README_HOST_LOGIC.md](README_HOST_LOGIC.md) - Chi tiết về host và port
- [README_ARCHITECTURE.md](README_ARCHITECTURE.md) - Kiến trúc tổng thể
- [FastAPI CORS Documentation](https://fastapi.tiangolo.com/tutorial/cors/)
- [Fetch API MDN](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)

---

**Tài liệu được tạo:** 2025-11-29
**Phiên bản:** 1.0.0
**Tác giả:** Claude Code Assistant
