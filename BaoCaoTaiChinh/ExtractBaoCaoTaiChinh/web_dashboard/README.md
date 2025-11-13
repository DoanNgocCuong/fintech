# Financial Reports Dashboard

Web dashboard để visualize và analyze dữ liệu từ database.

## Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Start API server:**
```bash
python app.py
```

3. **Open dashboard:**
Mở file `index.html` trong browser (hoặc dùng live server)

## Features

- 📊 **Statistics Dashboard**: Hiển thị tổng số records trong mỗi bảng
- 🔍 **Advanced Filtering**: Filter theo stock, year, quarter
- 📈 **Charts**: Visualize data bằng Chart.js
  - Bar chart: Records by Year
  - Doughnut chart: Records by Stock (Top 10)
- 📋 **Data Table**: Hiển thị chi tiết các records
- ⚡ **Real-time**: Auto-refresh stats mỗi 30 giây

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/stats` - Get statistics
- `GET /api/income-statement?stock=XXX&year=2024&quarter=5` - Get income statements
- `GET /api/balance-sheet?stock=XXX&year=2024&quarter=5` - Get balance sheets
- `GET /api/cash-flow?stock=XXX&year=2024&quarter=5` - Get cash flow statements
- `GET /api/stocks?table=income_statement_raw` - Get list of stocks
- `GET /api/years?table=income_statement_raw` - Get list of years

## Usage

1. Mở `index.html` trong browser
2. Chọn loại report (Income Statement / Balance Sheet / Cash Flow)
3. Filter theo stock, year, quarter (optional)
4. Click "Load Data" để xem data và charts
5. Click "View" để xem chi tiết từng record

## Database Connection

Dashboard kết nối đến database theo config trong `utils_database_manager.py`:
- Host: `103.253.20.30`
- Port: `29990`
- Database: `financial-reporting-database`

## Troubleshooting

- Nếu API offline: Kiểm tra xem `app.py` đã chạy chưa
- Nếu không có data: Kiểm tra database connection và xem đã có data chưa
- CORS errors: Đảm bảo Flask-CORS đã được install và enable

