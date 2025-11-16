# Financial Reports Dashboard API Documentation

## Base URL

- **Local**: `http://localhost:30011/api` (hoặc `http://localhost:8000/api`)
- **Production**: `http://103.253.20.30:30011/api`

## API Endpoints

### 1. Health Check

Kiểm tra trạng thái API server.

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

Lấy thống kê số lượng records trong mỗi bảng.

**Endpoint:** `GET /api/stats`

**Response:**
```json
{
  "success": true,
  "stats": {
    "income_statement_raw": 1234,
    "balance_sheet_raw": 1234,
    "cash_flow_statement_raw": 1234
  }
}
```

---

### 3. Get Stocks

Lấy danh sách mã cổ phiếu từ một bảng.

**Endpoint:** `GET /api/stocks`

**Query Parameters:**
- `table` (optional, default: `income_statement_raw`): Tên bảng
  - `income_statement_raw` - Kết quả kinh doanh
  - `balance_sheet_raw` - Cân đối kế toán
  - `cash_flow_statement_raw` - Lưu chuyển tiền tệ

**Example:**
```
GET /api/stocks?table=balance_sheet_raw
GET /api/stocks?table=cash_flow_statement_raw
```

**Response:**
```json
{
  "success": true,
  "stocks": ["ACB", "VCB", "HPG", "VNM"],
  "table": "balance_sheet_raw",
  "count": 4
}
```

---

### 4. Get Years

Lấy danh sách các năm có dữ liệu trong một bảng.

**Endpoint:** `GET /api/years`

**Query Parameters:**
- `table` (optional, default: `income_statement_raw`): Tên bảng
  - `income_statement_raw`
  - `balance_sheet_raw`
  - `cash_flow_statement_raw`

**Example:**
```
GET /api/years?table=balance_sheet_raw
```

**Response:**
```json
{
  "success": true,
  "years": [2024, 2023, 2022, 2021]
}
```

---

### 5. Get Balance Sheet Table Data

Lấy dữ liệu bảng cân đối kế toán cho một mã cổ phiếu.

**Endpoint:** `GET /api/balance-sheet/table-data`

**Query Parameters:**
- `stock` (required): Mã cổ phiếu (ví dụ: "ACB", "VCB")

**Example:**
```
GET /api/balance-sheet/table-data?stock=ACB
```

**Response:**
```json
{
  "success": true,
  "stock": "ACB",
  "report_type": "balance-sheet",
  "periods": [
    {
      "year": 2024,
      "quarter": 4,
      "label": "Q4-2024"
    },
    {
      "year": 2024,
      "quarter": 3,
      "label": "Q3-2024"
    }
  ],
  "indicators": [
    {
      "key": "tong_cong_tai_san",
      "label": "Total assets",
      "label_vn": "Tổng tài sản",
      "ma_so": 270,
      "values": {
        "Q4-2024": 1000000000,
        "Q3-2024": 950000000
      }
    }
  ],
  "last_update": "2024-01-15T10:30:00"
}
```

---

### 6. Get Income Statement Table Data

Lấy dữ liệu bảng kết quả kinh doanh cho một mã cổ phiếu.

**Endpoint:** `GET /api/income-statement/table-data`

**Query Parameters:**
- `stock` (required): Mã cổ phiếu

**Example:**
```
GET /api/income-statement/table-data?stock=VCB
```

**Response:**
```json
{
  "success": true,
  "stock": "VCB",
  "report_type": "income-statement",
  "periods": [
    {
      "year": 2024,
      "quarter": 4,
      "label": "Q4-2024"
    }
  ],
  "indicators": [
    {
      "key": "doanh_thu_thuan",
      "label": "Total revenue",
      "label_vn": "Doanh thu thuần hoạt động kinh doanh bảo hiểm",
      "ma_so": "10",
      "values": {
        "Q4-2024": 500000000
      }
    }
  ],
  "last_update": "2024-01-15T10:30:00"
}
```

---

### 7. Get Cash Flow Table Data

Lấy dữ liệu bảng lưu chuyển tiền tệ cho một mã cổ phiếu.

**Endpoint:** `GET /api/cash-flow/table-data`

**Query Parameters:**
- `stock` (required): Mã cổ phiếu

**Example:**
```
GET /api/cash-flow/table-data?stock=HPG
```

**Response:**
```json
{
  "success": true,
  "stock": "HPG",
  "report_type": "cash-flow",
  "periods": [
    {
      "year": 2024,
      "quarter": 4,
      "label": "Q4-2024"
    }
  ],
  "indicators": [
    {
      "key": "luu_chuyen_tien_hoat_dong",
      "label": "Operating cash flow",
      "label_vn": "Lưu chuyển tiền thuần từ hoạt động kinh doanh",
      "ma_so": 20,
      "values": {
        "Q4-2024": 200000000
      }
    }
  ],
  "last_update": "2024-01-15T10:30:00"
}
```

---

### 8. Get Raw Data Endpoints

Các endpoint để lấy raw JSON data từ database.

#### 8.1. Get Income Statements

**Endpoint:** `GET /api/income-statement`

**Query Parameters:**
- `stock` (optional): Mã cổ phiếu
- `year` (optional): Năm
- `quarter` (optional): Quý (1-4, hoặc NULL cho cuối năm)
- `limit` (optional, default: 100): Số lượng kết quả tối đa

**Example:**
```
GET /api/income-statement?stock=ACB&year=2024&quarter=4
```

**Response:**
```json
{
  "success": true,
  "count": 1,
  "data": [
    {
      "stock": "ACB",
      "year": 2024,
      "quarter": 4,
      "source_filename": "ACB_2024_Q4.json",
      "json_raw": { ... },
      "created_at": "2024-01-15T10:30:00"
    }
  ]
}
```

#### 8.2. Get Balance Sheets

**Endpoint:** `GET /api/balance-sheet`

**Query Parameters:**
- `stock` (optional): Mã cổ phiếu
- `year` (optional): Năm
- `quarter` (optional): Quý
- `limit` (optional, default: 100): Số lượng kết quả tối đa

**Example:**
```
GET /api/balance-sheet?stock=VCB&year=2024
```

#### 8.3. Get Cash Flows

**Endpoint:** `GET /api/cash-flow`

**Query Parameters:**
- `stock` (optional): Mã cổ phiếu
- `year` (optional): Năm
- `quarter` (optional): Quý
- `limit` (optional, default: 100): Số lượng kết quả tối đa

**Example:**
```
GET /api/cash-flow?stock=HPG&year=2024&quarter=4
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Missing required parameter: stock"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Database error: connection failed"
}
```

---

## Notes

### Quarter Handling
- `quarter = NULL` trong database được convert thành `quarter = 5` (năm cuối)
- Period label format: `Q{quarter}-{year}` (ví dụ: `Q4-2024`, `Q5-2024`)

### Table Names
- `income_statement_raw` - Bảng kết quả kinh doanh
- `balance_sheet_raw` - Bảng cân đối kế toán
- `cash_flow_statement_raw` - Bảng lưu chuyển tiền tệ

### Report Types
- `balance-sheet` - Cân đối kế toán
- `income-statement` - Kết quả kinh doanh
- `cash-flow` - Lưu chuyển tiền tệ

---

## Interactive API Documentation

Khi server đang chạy, bạn có thể truy cập:

- **Swagger UI**: `http://localhost:30011/docs`
- **ReDoc**: `http://localhost:30011/redoc`

---

## Examples

### Get all stocks from balance sheet
```bash
curl "http://localhost:30011/api/stocks?table=balance_sheet_raw"
```

### Get table data for a stock
```bash
curl "http://localhost:30011/api/balance-sheet/table-data?stock=ACB"
```

### Get statistics
```bash
curl "http://localhost:30011/api/stats"
```

---

## Frontend Usage

Frontend JavaScript sử dụng các API này thông qua:
- `loadStocks(reportType)` - Gọi `/api/stocks`
- `loadTableData(stock, reportType)` - Gọi `/api/{report-type}/table-data`

API base URL được tự động detect dựa trên hostname và port của frontend.



