# Financial Reports Dashboard - Complete Documentation

## 📋 Tổng quan

Dashboard hiển thị chi tiết báo cáo tài chính theo mã cổ phiếu với các tính năng:
- Chọn mã cổ phiếu
- Chọn loại báo cáo (Cân đối kế toán, Kết quả kinh doanh, Lưu chuyển tiền tệ)
- Hiển thị bảng với các chỉ tiêu tài chính theo quý/năm
- Tìm kiếm chỉ tiêu
- Xuất dữ liệu ra CSV

---

## 🚀 Cài đặt và Chạy

### 1. Cài đặt Dependencies

```bash
cd BaoCaoTaiChinh/web
pip install -r requirements.txt
```

**Dependencies:**
- `fastapi==0.104.1`
- `uvicorn[standard]==0.24.0`
- `psycopg2-binary==2.9.9`

### 2. Start Backend API

```bash
python app.py --host 0.0.0.0 --port 30011
```

Hoặc sử dụng file `start.bat` (Windows):
```bash
start.bat
```

API sẽ chạy tại:
- Local: `http://localhost:30011`
- Swagger UI: `http://localhost:30011/docs`
- ReDoc: `http://localhost:30011/redoc`

### 3. Frontend

Mở file `index_detail.html` trong trình duyệt hoặc sử dụng web server:

```bash
# Python
python -m http.server 8080

# Hoặc Node.js
npx http-server -p 8080
```

Truy cập: `http://localhost:8080/index_detail.html`

---

## 📁 Cấu trúc Files

```
BaoCaoTaiChinh/web/
├── index_detail.html          # HTML UI
├── css/
│   └── style.css              # CSS styling
├── js/
│   ├── data.js                # Data utilities (API calls, format)
│   └── app.js                 # Main application logic
├── app.py                     # FastAPI backend
├── utils_data_extractor.py    # Extract indicators from JSON
├── utils_database_manager.py  # Database utilities (from parent folder)
├── requirements.txt           # Python dependencies
├── start.bat                  # Windows startup script
└── README.md                  # This documentation
```

---

## 🔌 API Endpoints

### Base URL
- **Local**: `http://localhost:30011/api` (hoặc `http://localhost:8000/api`)
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

Lấy thống kê số lượng records trong mỗi bảng.

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

**Endpoint:** `GET /api/stocks`

Lấy danh sách mã cổ phiếu từ một bảng.

**Query Parameters:**
- `table` (optional, default: `income_statement_raw`): Tên bảng
  - `income_statement_raw` - Kết quả kinh doanh
  - `balance_sheet_raw` - Cân đối kế toán
  - `cash_flow_statement_raw` - Lưu chuyển tiền tệ

**Example:**
```
GET /api/stocks?table=balance_sheet_raw
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

**Endpoint:** `GET /api/years`

Lấy danh sách các năm có dữ liệu trong một bảng.

**Query Parameters:**
- `table` (optional, default: `income_statement_raw`): Tên bảng

**Response:**
```json
{
  "success": true,
  "years": [2024, 2023, 2022, 2021]
}
```

---

### 5. Get Balance Sheet Table Data

**Endpoint:** `GET /api/balance-sheet/table-data`

Lấy dữ liệu bảng cân đối kế toán cho một mã cổ phiếu.

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
      "year": 2025,
      "quarter": 5,
      "label": "Q5-2025"
    },
    {
      "year": 2025,
      "quarter": 4,
      "label": "Q4-2025"
    }
  ],
  "indicators": [
    {
      "key": "tong_cong_tai_san",
      "label": "Total assets",
      "label_vn": "Tổng tài sản",
      "ma_so": 270,
      "values": {
        "Q5-2025": 1000000000,
        "Q4-2025": 950000000
      }
    }
  ],
  "last_update": "2025-01-15T10:30:00"
}
```

**Note:** Periods được sort giảm dần theo năm và quý (Q5-2025, Q4-2025, Q3-2025, ...)

---

### 6. Get Income Statement Table Data

**Endpoint:** `GET /api/income-statement/table-data`

Lấy dữ liệu bảng kết quả kinh doanh cho một mã cổ phiếu.

**Query Parameters:**
- `stock` (required): Mã cổ phiếu

**Response:** Tương tự balance-sheet/table-data

---

### 7. Get Cash Flow Table Data

**Endpoint:** `GET /api/cash-flow/table-data`

Lấy dữ liệu bảng lưu chuyển tiền tệ cho một mã cổ phiếu.

**Query Parameters:**
- `stock` (required): Mã cổ phiếu

**Response:** Tương tự balance-sheet/table-data

---

### 8. Raw Data Endpoints

#### 8.1. Get Income Statements

**Endpoint:** `GET /api/income-statement`

**Query Parameters:**
- `stock` (optional): Mã cổ phiếu
- `year` (optional): Năm
- `quarter` (optional): Quý (1-4, hoặc NULL cho cuối năm)
- `limit` (optional, default: 100): Số lượng kết quả tối đa

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

**Query Parameters:** Tương tự income-statement

#### 8.3. Get Cash Flows

**Endpoint:** `GET /api/cash-flow`

**Query Parameters:** Tương tự income-statement

---

## 🎨 UI Features

### 1. Stock Selector
- Dropdown chọn mã cổ phiếu
- Load tự động từ API theo report type
- Auto-reload data khi chọn stock

### 2. Report Type Tabs
- **Cân đối kế toán** (Balance Sheet)
- **Lưu chuyển tiền tệ** (Cash Flow)
- **Kết quả kinh doanh** (Income Statement)
- Switch tab sẽ reload data

### 3. Search
- Tìm kiếm chỉ tiêu theo tên
- Real-time filtering
- Debounce 300ms

### 4. Data Table
- **Columns**: Các quý/năm (Q5-2025, Q4-2025, Q3-2025, ...) - sort giảm dần
- **Rows**: Các chỉ tiêu tài chính
- **Sticky header**: Header cố định khi scroll
- **Sticky first column**: Cột chỉ tiêu cố định khi scroll ngang
- **Format số**: Hiển thị số với dấu phẩy (1,000,000)
- **Null values**: Hiển thị `-` cho giá trị null

### 5. Summary Section
- Tổng số chỉ tiêu
- Số quý/năm
- Cập nhật lần cuối

### 6. Export Data
- Xuất dữ liệu ra CSV
- Format UTF-8 với BOM
- Filename: `bao_cao_{report_type}_{stock}_{timestamp}.csv`

---

## 📊 Data Structure & Indicators

### Balance Sheet Indicators

**Main Indicators:**
1. **Tổng tài sản** (Total assets) - Mã số: 270
2. **Tài sản ngắn hạn** (Current assets) - Mã số: 100
3. **Tài sản dài hạn** (Non-current assets) - Mã số: 200
4. **Tổng nợ phải trả** (Total liabilities) - Mã số: 300
5. **Nợ ngắn hạn** (Current liabilities) - Mã số: 310
6. **Nợ dài hạn** (Non-current liabilities) - Mã số: 330
7. **Tổng vốn chủ sở hữu** (Total equity) - Mã số: 400
8. **Tổng nguồn vốn** (Total liabilities & equity) - Mã số: 440

**JSON Path Examples:**
- Tổng tài sản: `can_doi_ke_toan.tai_san.tong_cong_tai_san_270.so_cuoi_nam`
- Tài sản ngắn hạn: `can_doi_ke_toan.tai_san.A_tai_san_ngan_han_100.so_cuoi_nam`
- Tài sản dài hạn: `can_doi_ke_toan.tai_san.B_tai_san_dai_han_200.so_cuoi_nam`

---

### Income Statement Indicators

**Main Indicators:**
1. **Doanh thu phí bảo hiểm** (Insurance premium revenue) - Mã số: 1
2. **Phí nhượng tái bảo hiểm** (Reinsurance premium) - Mã số: 2
3. **Doanh thu phí bảo hiểm thuần** (Net insurance premium revenue) - Mã số: 3
4. **Doanh thu thuần** (Total revenue) - Mã số: 10
5. **Chi bồi thường** (Claims expenses) - Mã số: 11
6. **Tổng chi phí** (Total operating expenses) - Mã số: 18
7. **Lợi nhuận gộp** (Gross profit) - Mã số: 19
8. **Lợi nhuận thuần** (Operating income) - Mã số: 30
9. **Lợi nhuận trước thuế** (Profit before tax) - Mã số: 50
10. **Lợi nhuận sau thuế** (Net income) - Mã số: 60
11. **Lợi nhuận công ty mẹ** (Net income parent company) - Mã số: 62

**JSON Path Examples:**
- Doanh thu phí bảo hiểm: `ket_qua_hoat_dong_kinh_doanh.01_doanh_thu_phi_bao_hiem.so_cuoi_nam`
- Doanh thu thuần: `ket_qua_hoat_dong_kinh_doanh.10_doanh_thu_thuan_hoat_dong_kinh_doanh_bao_hiem.so_cuoi_nam`
- Lợi nhuận sau thuế: `ket_qua_hoat_dong_kinh_doanh.60_loi_nhuan_sau_thue_thu_nhap_doanh_nghiep.so_cuoi_nam`

---

### Cash Flow Indicators

**Main Indicators:**
1. **Lưu chuyển tiền hoạt động** (Operating cash flow) - Mã số: 20
2. **Lưu chuyển tiền đầu tư** (Investing cash flow) - Mã số: 30
3. **Lưu chuyển tiền tài chính** (Financing cash flow) - Mã số: 40
4. **Lưu chuyển tiền thuần** (Net cash flow) - Mã số: 50
5. **Tiền đầu kỳ** (Cash at beginning) - Mã số: 60
6. **Tiền cuối kỳ** (Cash at end) - Mã số: 70

**JSON Path Examples:**
- Lưu chuyển tiền hoạt động: `bao_cao_luu_chuyen_tien_te.I_luu_chuyen_tien_tu_hoat_dong_kinh_doanh_20.so_cuoi_nam`
- Lưu chuyển tiền đầu tư: `bao_cao_luu_chuyen_tien_te.II_luu_chuyen_tien_tu_hoat_dong_dau_tu_30.so_cuoi_nam`
- Lưu chuyển tiền tài chính: `bao_cao_luu_chuyen_tien_te.III_luu_chuyen_tien_tu_hoat_dong_tai_chinh_40.so_cuoi_nam`

**Note:** Để xem đầy đủ các indicators, tham khảo file `INDICATOR_MAPPING_REFERENCE.md` (nếu cần)

---

## 🔧 Configuration

### API Base URL

Frontend tự động detect API base URL trong `js/data.js`:

```javascript
const API_BASE = (() => {
    const hostname = window.location.hostname;
    const protocol = window.location.protocol;
    const port = window.location.port;
    
    // If running on localhost, check port
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        if (port === '30011') {
            return 'http://localhost:30011/api';
        }
        if (port === '8000') {
            return 'http://localhost:8000/api';
        }
        // Default to 30011 for localhost
        return 'http://localhost:30011/api';
    }
    
    // If running on same server, use relative path
    if (port && (port === '8000' || port === '30011')) {
        return `${protocol}//${hostname}:${port}/api`;
    }
    
    // Default to production server
    return 'http://103.253.20.30:30011/api';
})();
```

### Report Type Mapping

```javascript
const REPORT_TYPE_MAP = {
    'balance': 'balance-sheet',
    'income': 'income-statement',
    'cashflow': 'cash-flow'
};

const REPORT_TABLE_MAP = {
    'balance': 'balance_sheet_raw',
    'income': 'income_statement_raw',
    'cashflow': 'cash_flow_statement_raw'
};
```

### Database Configuration

Database config trong `utils_database_manager.py`:

```python
DB_CONFIG = {
    'host': '103.253.20.30',
    'port': 29990,
    'database': 'financial-reporting-database',
    'user': 'postgres',
    'password': 'postgres',
}
```

**Tables:**
- `balance_sheet_raw` - Cân đối kế toán
- `income_statement_raw` - Kết quả kinh doanh
- `cash_flow_statement_raw` - Lưu chuyển tiền tệ

---

## 📝 Implementation Details

### Data Extraction

**File:** `utils_data_extractor.py`

**Functions:**
- `extract_value_from_json(json_data, path)`: Extract value từ JSON theo dot notation path
- `get_indicators_for_report_type(json_data, report_type)`: Get indicators cho một report type
- `get_balance_sheet_indicators(json_data)`: Get balance sheet indicators
- `get_income_statement_indicators(json_data)`: Get income statement indicators
- `get_cash_flow_indicators(json_data)`: Get cash flow indicators

**Current Implementation:**
- Extract **8 main indicators** cho Balance Sheet
- Extract **11 main indicators** cho Income Statement
- Extract **6 main indicators** cho Cash Flow

**Note:** Có thể mở rộng để extract tất cả indicators từ JSON bằng cách uncomment recursive extraction trong `utils_data_extractor.py`

### Backend Helper Function

**File:** `app.py`

**Helper Function:**
- `get_table_data_for_stock(stock, table_name, report_type)`: Helper function để get table data cho bất kỳ table nào
  - Query database
  - Extract periods (year, quarter)
  - Parse JSON data
  - Extract indicators
  - Sort periods giảm dần (Q5-2025, Q4-2025, ...)
  - Return formatted data

**Endpoints sử dụng helper function:**
- `/api/balance-sheet/table-data`
- `/api/income-statement/table-data`
- `/api/cash-flow/table-data`

---

## 🐛 Troubleshooting

### 1. API không kết nối được

**Lỗi:** `Failed to fetch` hoặc `CORS error`

**Giải pháp:**
- Kiểm tra API server đã chạy chưa: `python app.py --host 0.0.0.0 --port 30011`
- Kiểm tra CORS settings trong `app.py` (đã enable CORS cho tất cả origins)
- Kiểm tra API base URL trong `js/data.js`
- Kiểm tra firewall/network settings

### 2. Database Connection Error

**Lỗi:** `psycopg2 is required` hoặc `connection failed`

**Giải pháp:**
- Cài đặt dependencies: `pip install -r requirements.txt`
- Kiểm tra database connection settings trong `utils_database_manager.py`
- Kiểm tra database server đang chạy
- Kiểm tra network connectivity đến database server

### 3. Không có dữ liệu hiển thị

**Lỗi:** Table trống hoặc "No data"

**Giải pháp:**
- Kiểm tra stock đã được chọn chưa
- Kiểm tra database có dữ liệu cho stock đó chưa
- Kiểm tra console log trong browser để xem lỗi API
- Kiểm tra API response trong Network tab

### 4. Indicators không hiển thị

**Lỗi:** Chỉ có periods, không có indicators

**Giải pháp:**
- Kiểm tra JSON structure trong database
- Kiểm tra `utils_data_extractor.py` có extract đúng path không
- Kiểm tra console log để xem lỗi extract
- Verify JSON paths trong `INDICATOR_MAPPING_REFERENCE.md` (nếu có)

### 5. Periods không sort đúng

**Lỗi:** Periods không sort theo Q5-2025, Q4-2025, ...

**Giải pháp:**
- Backend đã sort periods trong `get_table_data_for_stock()`
- Frontend cũng sort trong `sortPeriods()` trong `js/data.js`
- Kiểm tra response từ API có sort đúng không

---

## 🔄 Mở rộng

### Thêm Indicators mới

1. Cập nhật `utils_data_extractor.py`:
   - Thêm path mới vào `main_indicator_paths` trong function tương ứng
   - Hoặc sử dụng `extract_indicators_recursive()` để extract tất cả indicators

2. Test với data thực để verify paths đúng

### Thêm Report Type mới

1. Tạo function extract trong `utils_data_extractor.py`:
   ```python
   def get_new_report_indicators(json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
       # Implementation
   ```

2. Cập nhật `get_indicators_for_report_type()` để support report type mới

3. Thêm API endpoint trong `app.py`:
   ```python
   @app.get("/api/new-report/table-data")
   async def get_new_report_table_data(stock: str = Query(...)):
       return await get_table_data_for_stock(stock, "new_table_raw", "new-report")
   ```

4. Cập nhật frontend:
   - Thêm tab mới trong `index_detail.html`
   - Cập nhật `REPORT_TYPE_MAP` và `REPORT_TABLE_MAP` trong `js/data.js`
   - Thêm event handler trong `js/app.js`

---

## 📋 Notes

### Quarter Handling
- Quarter `NULL` trong database được convert thành `5` (year-end)
- Period format: `Q{quarter}-{year}` (ví dụ: `Q5-2025`, `Q4-2025`)
- Periods được sort giảm dần: Q5-2025, Q4-2025, Q3-2025, ...

### Number Format
- Số được format với dấu phẩy (1,000,000)
- Format locale: `vi-VN`
- Null values hiển thị là `-`

### Data Extraction
- Hiện tại chỉ extract các indicators chính
- Có thể mở rộng để extract tất cả indicators từ JSON
- JSON paths sử dụng dot notation

### Performance
- Periods được sort ở backend để giảm tải frontend
- Frontend có duplicate sort để đảm bảo consistency
- API responses có thể cache nếu cần

---

## 📞 Support

Nếu có vấn đề:
1. Kiểm tra console log trong browser (F12)
2. Kiểm tra API logs trong terminal
3. Kiểm tra database connection
4. Kiểm tra JSON structure trong database
5. Verify API endpoints tại Swagger UI: `http://localhost:30011/docs`

---

## 📚 Additional Resources

- **API Documentation**: Xem `API.md` để biết chi tiết về tất cả API endpoints
- **Database Schema**: Xem `web_dashboard/check_data.sql` để biết database structure
- **Template JSONs**: Xem `ExtractBaoCaoTaiChinh/balance_template_json.json`, `income_template_json.json`, `cash_flow_template_json.json` để biết JSON structure

---

**Last Updated**: 2025-01-XX  
**Version**: 1.0.0
