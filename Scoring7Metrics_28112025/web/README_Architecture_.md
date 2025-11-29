# Kiến trúc Hệ thống - Scoring 7 Metrics Dashboard

## 📋 Tổng quan

Hệ thống Dashboard hiển thị và phân tích dữ liệu **7 Tiêu chí Định tính** được lượng hóa từ tài liệu Đại hội cổ đông (AGM) của các công ty.

### Mục đích
- Hiển thị kết quả lượng hóa 7 tiêu chí định tính theo công ty và năm
- Truy vấn và trích dẫn các đoạn văn liên quan từ tài liệu gốc
- Phân tích và so sánh metrics qua các năm
- Export dữ liệu để phân tích sâu hơn

---

## 🏗️ Kiến trúc Tổng thể

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Web)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   HTML/JS     │  │   CSS/UI     │  │   Charts     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└───────────────────────────┬─────────────────────────────────┘
                             │ HTTP/REST API
┌────────────────────────────┴─────────────────────────────────┐
│                    Backend (FastAPI)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   API Routes  │  │ Data Extract │  │   DB Manager │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└───────────────────────────┬─────────────────────────────────┘
                             │ SQL Queries
┌────────────────────────────┴─────────────────────────────────┐
│              PostgreSQL Database                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  Table: company_json_documents                       │    │
│  │  - id, company_name, year, file_name                │    │
│  │  - json_raw (JSONB)                                 │    │
│  │  - parsed_data (JSONB)                              │    │
│  └──────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────┘
```

---

## 📁 Cấu trúc Thư mục (Dự kiến)

```
Scoring7Metrics_28112025/web/
├── app.py                          # FastAPI backend server
├── utils_database_manager.py       # Database connection & utilities
├── utils_data_extractor.py         # Extract metrics từ JSON
├── requirements.txt                # Python dependencies
├── start.bat                       # Windows startup script
├── start.sh                        # Linux/Mac startup script
│
├── index.html                      # Main dashboard UI
│
├── css/
│   └── style.css                   # Styling
│
├── js/
│   ├── data.js                     # API calls & data utilities
│   └── app.js                      # Main application logic
│
├── README.md                       # User documentation
└── README_Architecture.md          # This file
```

---

## 🗄️ Database Schema

### Database: `financial-reporting-database`

### Table: `company_json_documents`

```sql
CREATE TABLE IF NOT EXISTS "company_json_documents" (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    year INTEGER NOT NULL,
    file_name VARCHAR(500),
    json_raw JSONB NOT NULL,              -- Raw JSON từ extraction
    parsed_data JSONB,                    -- Parsed data với analysis_result
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_name, year)
);
```

#### Cấu trúc dữ liệu:

**⚠️ QUAN TRỌNG: UI sử dụng cột `parsed_data` (KHÔNG phải `json_raw`)**

**`json_raw`** - Raw JSON từ extraction process (chỉ để tham khảo, không dùng cho UI):
```json
{
  "analysis_result": [
    {
      "summary": "...",
      "group_id": "governance",
      "group_name": "Quản trị (Governance)",
      "evidences": [...],
      "governance_metrics": {...},
      "content_found": true
    }
  ]
}
```

**`parsed_data`** - ✅ **Structured data đã được parse - DÙNG CHO UI**:
```json
{
  "analysis_result": [
    {
      "metrics": {
        "governance": {
          "ten_chu_tich_hdqt": "Phạm Quang Tùng",
          "ten_tong_giam_doc": "Tôn Lâm Tùng",
          "so_thanh_vien_hdqt": null,
          "thay_doi_nhan_su": "Miễn nhiệm chức danh thành viên HĐQT..."
        }
      },
      "summary": "Năm 2013, BIC có sự thay đổi nhân sự cấp cao...",
      "group_id": "governance",
      "group_name": "Quản trị (Governance)",
      "evidences": [
        {
          "quote": "TM. HỘI ĐỒNG QUẢN TRỊ\nCHỦ TỊCH\nPhạm Quang Tùng",
          "source_ref": "BIC/2014/Tai_lieu_DHDCD/BIC_2014_5_1_1_zip/BIC_TAILIEU_DHCD_2014.md"
        }
      ],
      "content_found": true
    },
    {
      "metrics": {
        "incentive": {
          "esop_so_luong": "3300000",
          "trich_quy_khen_thuong": "13000000000"
        }
      },
      "summary": "Công ty thực hiện chương trình ESOP...",
      "group_id": "incentive",
      "group_name": "Chính sách đãi ngộ (Incentive)",
      "evidences": [...],
      "content_found": true
    }
    // ... các group khác
  ]
}
```

**Lý do sử dụng `parsed_data`:**
- ✅ Đã có cấu trúc `metrics` được organize theo `group_id` sẵn
- ✅ `summary` và `evidences` đã được extract và format sẵn
- ✅ Dễ dàng query và hiển thị trên UI
- ✅ Không cần parse lại từ `json_raw`

#### 7 Tiêu chí (Groups):
1. **governance** - Quản trị (Governance)
2. **incentive** - Chính sách đãi ngộ (Incentive)
3. **payout** - Chính sách chi trả (Payout)
4. **capital** - Vốn và huy động vốn (Capital)
5. **ownership** - Cơ cấu sở hữu (Ownership)
6. **strategy** - Chiến lược (Strategy)
7. **risk** - Rủi ro (Risk)

---

## ⚠️ QUAN TRỌNG: Sử dụng cột `parsed_data` cho UI

### Tại sao dùng `parsed_data`?

1. **Cấu trúc sẵn có:**
   - `parsed_data` đã có `metrics` được organize theo `group_id`
   - `summary` và `evidences` đã được extract và format sẵn
   - Không cần parse lại từ `json_raw`

2. **Hiệu suất:**
   - Query trực tiếp `parsed_data` nhanh hơn parse `json_raw`
   - Có thể dùng JSONB operators của PostgreSQL để query hiệu quả

3. **Dễ dàng extract:**
   - Metrics: `parsed_data->'analysis_result'->X->'metrics'->{group_id}`
   - Summary: `parsed_data->'analysis_result'->X->'summary'`
   - Evidences: `parsed_data->'analysis_result'->X->'evidences'`

### Implementation Pattern

**Backend (Python):**
```python
# Query parsed_data
cursor.execute(
    "SELECT parsed_data FROM company_json_documents WHERE company_name = %s AND year = %s",
    (company_name, year)
)
row = cursor.fetchone()
parsed_data = row[0]  # JSONB được convert tự động thành dict

# Extract metrics
for item in parsed_data.get('analysis_result', []):
    group_id = item.get('group_id')
    metrics = item.get('metrics', {}).get(group_id, {})
    summary = item.get('summary')
    evidences = item.get('evidences', [])
```

**Frontend (JavaScript):**
```javascript
// API response đã có structure sẵn từ parsed_data
const response = await fetch('/api/company-data?company_name=BVH&year=2024');
const data = await response.json();

// data.metrics đã được organize theo group_id
const governanceMetrics = data.metrics.governance;
const governanceSummary = data.summary.governance;
const governanceEvidences = data.evidences.governance;
```

---

## 🔌 API Endpoints (Dự kiến)

### Base URL
- **Local**: `http://localhost:8000/api` (hoặc `http://localhost:30011/api`)
- **Production**: `http://103.253.20.30:30011/api`

### 1. Health Check
**Endpoint:** `GET /api/health`

**Response:**
```json
{
  "status": "ok",
  "message": "API is running"
}
```

---

### 2. Get Statistics
**Endpoint:** `GET /api/stats`

Lấy thống kê số lượng records theo công ty và năm.

**Response:**
```json
{
  "success": true,
  "stats": {
    "total_companies": 50,
    "total_years": 150,
    "companies_by_year": {
      "2024": 25,
      "2023": 20,
      "2022": 15
    }
  }
}
```

---

### 3. Get Companies
**Endpoint:** `GET /api/companies`

Lấy danh sách tất cả công ty có trong database.

**Query Parameters:**
- `search` (optional): Tìm kiếm theo tên công ty

**Response:**
```json
{
  "success": true,
  "companies": [
    "BVH",
    "BIC",
    "VCB",
    "ACB"
  ],
  "count": 4
}
```

---

### 4. Get Years
**Endpoint:** `GET /api/years`

Lấy danh sách các năm có dữ liệu.

**Query Parameters:**
- `company_name` (optional): Lọc theo công ty

**Response:**
```json
{
  "success": true,
  "years": [2024, 2023, 2022, 2021],
  "company": "BVH"
}
```

---

### 5. Get Company Data
**Endpoint:** `GET /api/company-data`

Lấy dữ liệu 7 tiêu chí cho một công ty và năm cụ thể. **Sử dụng cột `parsed_data` từ database.**

**Query Parameters:**
- `company_name` (required): Tên công ty
- `year` (required): Năm

**Implementation:**
- Query: `SELECT parsed_data FROM company_json_documents WHERE company_name = ? AND year = ?`
- Extract từ `parsed_data->'analysis_result'` array
- Group theo `group_id` và format response

**Response:**
```json
{
  "success": true,
  "company_name": "BVH",
  "year": 2024,
  "metrics": {
    "governance": {
      "ten_chu_tich_hdqt": "Nguyễn Văn A",
      "so_thanh_vien_hdqt": "7",
      "thay_doi_nhan_su": "..."
    },
    "incentive": {
      "esop_so_luong": "3300000",
      "trich_quy_khen_thuong": "13000000000"
    },
    "payout": {
      "chia_co_tuc": "10%",
      "tong_lnst_phan_phoi": "84978387781"
    },
    "capital": {
      "von_dieu_le_cu": "693000000000",
      "von_dieu_le_moi": "762300000000"
    },
    "ownership": {
      "co_dong_chien_luoc": "..."
    },
    "strategy": {
      "doanh_thu_ke_hoach": "1000000000000",
      "loi_nhuan_ke_hoach": "130000000000"
    },
    "risk": {
      "han_muc_rui_ro": "...",
      "ket_luan_kiem_toan": "Chấp nhận toàn phần"
    }
  },
  "summary": {
    "governance": "Năm 2024, BVH có sự thay đổi nhân sự...",
    "incentive": "...",
    ...
  },
  "evidences": {
    "governance": [
      {
        "quote": "TM. HỘI ĐỒNG QUẢN TRỊ\nCHỦ TỊCH\nNguyễn Văn A",
        "source_ref": "BVH/2024/Tai_lieu_DHDCD/..."
      }
    ],
    ...
  }
}
```

---

### 6. Get Company Timeline
**Endpoint:** `GET /api/company-timeline`

Lấy dữ liệu 7 tiêu chí cho một công ty qua nhiều năm (timeline).

**Query Parameters:**
- `company_name` (required): Tên công ty
- `years` (optional): Danh sách năm cụ thể (comma-separated)

**Response:**
```json
{
  "success": true,
  "company_name": "BVH",
  "timeline": [
    {
      "year": 2024,
      "metrics": {...},
      "summary": {...}
    },
    {
      "year": 2023,
      "metrics": {...},
      "summary": {...}
    }
  ]
}
```

---

### 7. Search Evidence
**Endpoint:** `GET /api/search-evidence`

Tìm kiếm trích dẫn (evidences) theo từ khóa.

**Query Parameters:**
- `keyword` (required): Từ khóa tìm kiếm
- `company_name` (optional): Lọc theo công ty
- `year` (optional): Lọc theo năm
- `group_id` (optional): Lọc theo tiêu chí (governance, incentive, ...)

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "company_name": "BVH",
      "year": 2024,
      "group_id": "governance",
      "quote": "...",
      "source_ref": "..."
    }
  ],
  "count": 1
}
```

---

### 8. Get Metrics by Group
**Endpoint:** `GET /api/metrics-by-group`

Lấy metrics của một tiêu chí cụ thể cho nhiều công ty/năm.

**Query Parameters:**
- `group_id` (required): Tiêu chí (governance, incentive, payout, capital, ownership, strategy, risk)
- `company_name` (optional): Lọc theo công ty
- `year` (optional): Lọc theo năm

**Response:**
```json
{
  "success": true,
  "group_id": "governance",
  "group_name": "Quản trị (Governance)",
  "data": [
    {
      "company_name": "BVH",
      "year": 2024,
      "metrics": {
        "ten_chu_tich_hdqt": "...",
        "so_thanh_vien_hdqt": "7"
      }
    }
  ]
}
```

---

## 🔧 Backend Implementation

### 1. `app.py` - FastAPI Server

**Cấu trúc chính:**
- FastAPI application với CORS middleware
- API routes cho các endpoints
- Helper functions để query database và extract data

**Dependencies:**
- `fastapi==0.104.1`
- `uvicorn[standard]==0.24.0`
- `psycopg2-binary==2.9.9`

---

### 2. `utils_database_manager.py` - Database Manager

**Functions:**
- `connect()`: Kết nối PostgreSQL
- `create_table_if_not_exists()`: Tạo bảng nếu chưa có
- `get_company_data(company_name, year)`: Lấy dữ liệu công ty từ **`parsed_data`**
  ```python
  # Query parsed_data column
  SELECT parsed_data FROM company_json_documents 
  WHERE company_name = %s AND year = %s
  ```
- `get_companies_list()`: Lấy danh sách công ty
- `get_years_list(company_name=None)`: Lấy danh sách năm
- `search_evidence(keyword, filters)`: Tìm kiếm trích dẫn trong **`parsed_data`**

**Database Config:**
```python
DB_CONFIG = {
    'host': '103.253.20.30',
    'port': 29990,
    'database': 'financial-reporting-database',
    'user': 'postgres',
    'password': 'postgres',
}
```

---

### 3. `utils_data_extractor.py` - Data Extractor

**⚠️ QUAN TRỌNG: Tất cả functions làm việc với `parsed_data` (KHÔNG phải `json_raw`)**

**Functions:**
- `extract_metrics_from_parsed_data(parsed_data, group_id)`: Extract metrics cho một tiêu chí từ `parsed_data->'analysis_result'`
  ```python
  # Tìm item có group_id tương ứng trong analysis_result array
  for item in parsed_data.get('analysis_result', []):
      if item.get('group_id') == group_id:
          return item.get('metrics', {}).get(group_id, {})
  ```
- `extract_all_metrics(parsed_data)`: Extract tất cả metrics từ `parsed_data->'analysis_result'`
- `extract_summary(parsed_data, group_id)`: Extract summary từ `parsed_data->'analysis_result'->X->'summary'`
- `extract_evidences(parsed_data, group_id)`: Extract evidences từ `parsed_data->'analysis_result'->X->'evidences'`
- `get_metrics_by_group(parsed_data, group_id)`: Lấy metrics theo group từ `parsed_data`
- `parse_parsed_data_jsonb(parsed_data_jsonb)`: Parse JSONB thành Python dict (nếu cần)

**7 Groups:**
- `governance` - Quản trị
- `incentive` - Chính sách đãi ngộ
- `payout` - Chính sách chi trả
- `capital` - Vốn và huy động vốn
- `ownership` - Cơ cấu sở hữu
- `strategy` - Chiến lược
- `risk` - Rủi ro

---

## 🎨 Frontend Implementation

### 1. `index.html` - Main Dashboard

**Features:**
- **Company Selector**: Dropdown chọn công ty
- **Year Selector**: Dropdown chọn năm
- **7 Metrics Tabs**: Tab cho từng tiêu chí
- **Metrics Display**: Hiển thị metrics dạng bảng/card
- **Summary Section**: Hiển thị summary cho mỗi tiêu chí
- **Evidence Viewer**: Hiển thị trích dẫn với source reference
- **Search**: Tìm kiếm trong evidences
- **Export**: Xuất dữ liệu ra CSV/JSON

### 2. `js/data.js` - Data Utilities

**Functions:**
- `loadCompanies()`: Load danh sách công ty
- `loadYears(company_name)`: Load danh sách năm
- `loadCompanyData(company_name, year)`: Load dữ liệu công ty
- `loadTimeline(company_name)`: Load timeline
- `searchEvidence(keyword, filters)`: Tìm kiếm evidence
- `formatMetrics(metrics)`: Format metrics để hiển thị

### 3. `js/app.js` - Application Logic

**Functions:**
- `init()`: Khởi tạo app
- `handleCompanyChange()`: Xử lý khi chọn công ty
- `handleYearChange()`: Xử lý khi chọn năm
- `handleTabChange()`: Xử lý khi chuyển tab
- `renderMetrics()`: Render metrics
- `renderSummary()`: Render summary
- `renderEvidences()`: Render evidences

---

## 🚀 Cài đặt và Chạy

### 1. Cài đặt Dependencies

```bash
cd Scoring7Metrics_28112025/web
pip install -r requirements.txt
```

### 2. Cấu hình Database

Cập nhật `DB_CONFIG` trong `utils_database_manager.py` nếu cần.

### 3. Start Backend API

```bash
python app.py --host 0.0.0.0 --port 8000
```

Hoặc sử dụng file `start.bat` (Windows):
```bash
start.bat
```

### 4. Frontend

Mở file `index.html` trong trình duyệt hoặc sử dụng web server:
```bash
python -m http.server 8080
```

Truy cập: `http://localhost:8080/index.html`

---

## 📊 Data Flow

```
1. User chọn Company + Year
   ↓
2. Frontend gọi API: GET /api/company-data?company_name=BVH&year=2024
   ↓
3. Backend query database: 
   SELECT parsed_data FROM company_json_documents 
   WHERE company_name='BVH' AND year=2024
   ↓
4. Backend parse parsed_data JSONB thành Python dict
   ↓
5. Backend extract từ parsed_data->'analysis_result' array:
   - Loop qua từng item trong analysis_result
   - Extract metrics từ item->'metrics'->{group_id}
   - Extract summary từ item->'summary'
   - Extract evidences từ item->'evidences'
   - Group theo group_id (governance, incentive, payout, ...)
   ↓
6. Backend format response với metrics, summary, evidences
   ↓
7. Frontend nhận response và render UI
   ↓
8. User xem metrics, summary, evidences cho 7 tiêu chí
```

**⚠️ Lưu ý:**
- Backend **CHỈ query cột `parsed_data`** (không query `json_raw`)
- Tất cả extraction logic làm việc với `parsed_data->'analysis_result'` array
- Không cần parse lại từ `json_raw` vì `parsed_data` đã có cấu trúc sẵn

---

## 🔍 Query Examples

### ⚠️ TẤT CẢ QUERIES SỬ DỤNG CỘT `parsed_data` (KHÔNG dùng `json_raw`)

### 1. Lấy dữ liệu BVH năm 2024 (chỉ lấy parsed_data)

```sql
SELECT 
    company_name,
    year,
    parsed_data  -- ✅ CHỈ query parsed_data
FROM company_json_documents
WHERE company_name = 'BVH' AND year = 2024;
```

### 2. Extract tất cả metrics từ parsed_data

```sql
SELECT 
    company_name,
    year,
    parsed_data->'analysis_result' as analysis_result_array
FROM company_json_documents
WHERE company_name = 'BVH' AND year = 2024;
```

### 3. Extract metrics governance cho BVH

```sql
-- Tìm item có group_id = 'governance' trong analysis_result array
SELECT 
    company_name,
    year,
    jsonb_array_elements(parsed_data->'analysis_result')->'metrics'->'governance' as governance_metrics
FROM company_json_documents
WHERE company_name = 'BVH'
  AND parsed_data->'analysis_result' @> '[{"group_id": "governance"}]'::jsonb
ORDER BY year DESC;
```

### 4. Extract summary cho governance

```sql
SELECT 
    company_name,
    year,
    jsonb_array_elements(parsed_data->'analysis_result')->>'summary' as summary
FROM company_json_documents
WHERE company_name = 'BVH'
  AND parsed_data->'analysis_result' @> '[{"group_id": "governance"}]'::jsonb;
```

### 5. Extract evidences cho governance

```sql
SELECT 
    company_name,
    year,
    jsonb_array_elements(
        jsonb_array_elements(parsed_data->'analysis_result')->'evidences'
    ) as evidence
FROM company_json_documents
WHERE company_name = 'BVH'
  AND parsed_data->'analysis_result' @> '[{"group_id": "governance"}]'::jsonb;
```

### 6. Tìm kiếm "PHRL" trong parsed_data

```sql
SELECT 
    company_name,
    year,
    parsed_data->'analysis_result'->0->>'summary' as summary
FROM company_json_documents
WHERE parsed_data::text LIKE '%PHRL%';
```

### 7. Tìm kiếm "độc lập" trong evidences của parsed_data

```sql
SELECT 
    company_name,
    year,
    jsonb_array_elements(
        jsonb_array_elements(parsed_data->'analysis_result')->'evidences'
    )->>'quote' as quote
FROM company_json_documents
WHERE parsed_data::text LIKE '%độc lập%';
```

### 8. Lấy tất cả metrics cho một công ty (tất cả groups)

```sql
SELECT 
    company_name,
    year,
    jsonb_array_elements(parsed_data->'analysis_result')->'metrics' as all_metrics
FROM company_json_documents
WHERE company_name = 'BVH'
ORDER BY year DESC;
```

---

## 🎯 So sánh với BaoCaoTaiChinh/web

| Aspect | BaoCaoTaiChinh/web | Scoring7Metrics/web |
|--------|-------------------|---------------------|
| **Database Table** | `income_statement_p1_raw`, `balance_sheet_raw`, ... | `company_json_documents` |
| **Data Structure** | Financial statements (structured) | 7 Metrics (semi-structured) |
| **Key Fields** | `stock`, `year`, `quarter`, `json_raw` | `company_name`, `year`, **`parsed_data`** (UI dùng) |
| **Data Source for UI** | `json_raw` | **`parsed_data`** ✅ |
| **Report Types** | Balance Sheet, Income Statement, Cash Flow | 7 Groups (Governance, Incentive, ...) |
| **Metrics** | Financial indicators (numbers) | Qualitative metrics (text + numbers) |
| **Evidences** | Không có | Có (trích dẫn từ tài liệu gốc) |
| **Timeline** | Theo quý (Q1-Q4, Q5) | Theo năm |

---

## 📝 Notes

### 1. Company Name Format
- Có thể là: `"BVH"`, `"BVH Holdings"`, `"Bao Viet Holdings"`, `"Tập đoàn Bảo Việt"`
- Cần normalize hoặc search với `ILIKE` trong SQL

### 2. JSON Structure - ⚠️ SỬ DỤNG `parsed_data` (KHÔNG dùng `json_raw`)

**`parsed_data` Structure:**
```json
{
  "analysis_result": [
    {
      "metrics": {
        "governance": {...},  // Metrics đã được organize theo group_id
        "incentive": {...},
        ...
      },
      "summary": "...",       // Summary cho group này
      "group_id": "governance",
      "group_name": "Quản trị (Governance)",
      "evidences": [          // Array các trích dẫn
        {
          "quote": "...",
          "source_ref": "..."
        }
      ],
      "content_found": true
    }
  ]
}
```

**Cách extract:**
- Loop qua `parsed_data->'analysis_result'` array
- Mỗi item có `group_id` để identify tiêu chí
- Metrics nằm trong `item->'metrics'->{group_id}`
- Summary nằm trong `item->'summary'`
- Evidences nằm trong `item->'evidences'` (array)

### 3. Metrics Extraction từ `parsed_data`
- ✅ Metrics đã được organize sẵn trong `parsed_data->'analysis_result'->X->'metrics'->{group_id}`
- ✅ Không cần parse lại từ `json_raw`
- ✅ Chỉ cần query `parsed_data` và extract trực tiếp

### 4. Evidence Search trong `parsed_data`
- ✅ Evidences nằm trong `parsed_data->'analysis_result'->X->'evidences'`
- ✅ Mỗi evidence có: `quote`, `source_ref`
- ✅ Có thể search bằng SQL: `WHERE parsed_data::text LIKE '%keyword%'`

---

## 🔄 Mở rộng

### Thêm Metrics mới
1. Cập nhật extraction logic trong `utils_data_extractor.py`
2. Thêm API endpoint mới trong `app.py`
3. Cập nhật frontend để hiển thị metrics mới

### Thêm Group mới
1. Cập nhật `GROUP_IDS` constant
2. Thêm extraction logic cho group mới
3. Thêm tab mới trong frontend

### Thêm Visualization
- Charts cho metrics qua các năm
- Comparison giữa các công ty
- Trend analysis

---

## 📞 Support

Nếu có vấn đề:
1. Kiểm tra console log trong browser (F12)
2. Kiểm tra API logs trong terminal
3. Kiểm tra database connection
4. Verify API endpoints tại Swagger UI: `http://localhost:8000/docs`

---

**Last Updated**: 2025-01-XX  
**Version**: 1.0.0

