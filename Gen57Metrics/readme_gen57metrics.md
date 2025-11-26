## 📐 Gen57Metrics – 57 Financial Indicators Engine

`Gen57Metrics` là **engine tính toán 57 chỉ số tài chính chuẩn hóa** cho từng mã cổ phiếu, từng kỳ báo cáo, dựa trên dữ liệu BCTC đã được nạp từ hệ thống `BaoCaoTaiChinh`.

Hệ thống gồm:

- **Core calculation layer**: registry + mapper + calculator cho 57 indicators.
- **Batch runner**: chạy cho nhiều mã/nhiều năm/nhiều quý, tự động lưu vào DB.
- **Web dashboard**: API + UI để khám phá 57 indicators theo từng cổ phiếu.

---

## 🧩 1. Kiến trúc tổng thể

### 1.1. Data source (phụ thuộc vào BaoCaoTaiChinh)

`Gen57Metrics` **không tự ingest BCTC gốc**. Thay vào đó, nó đọc dữ liệu từ DB mà `BaoCaoTaiChinh` đã chuẩn hóa:

- Bảng nguồn chính:
  - `income_statement_p1_raw`, `income_statement_p2_raw`
  - `balance_sheet_raw`
  - `cash_flow_statement_raw`
- Kết nối DB: `utils_database_manager.py`  
  - Chứa `DB_CONFIG` (host, port, database, user, password).
  - Cung cấp các hàm tiện ích để query theo `stock`, `year`, `quarter`, `ma_so`.

> Yêu cầu: dữ liệu BCTC cho mã/khung thời gian cần tính phải **tồn tại sẵn** trong các bảng raw ở trên.

### 1.2. Core components

- `base_indicator.py`  
  - Base class cho mọi indicator (metadata, interface tính toán).

- `direct_indicator.py`  
  - Implement các **direct indicators**: lấy giá trị trực tiếp từ BCTC (theo `ma_so`).

- `indicator_registry.py` – **IndicatorRegistry**  
  - Load định nghĩa 57 indicators từ `57BaseIndicators.json`.
  - Lưu:
    - ID (1–57), tên, mô tả, group.
    - Cờ `Get_Direct_From_DB` (yes/null).
    - Dependencies (cho calculated indicators).

- `indicator_mapper.py` – **IndicatorMapper**  
  - Map `"Indicator_Name"` → hàm Python thực thi (cho calculated indicators).
  - Tự động register **direct indicators** dựa trên `ma_so` trong JSON.
  - Cho phép mở rộng: thêm hàm mới, map indicator mới.

- `indicator_calculator.py` – **IndicatorCalculator**  
  - Nhận input: `stock`, `year`, `quarter`, danh sách indicators (hoặc full 57).
  - Thực hiện:
    - Phân tích dependency graph, **topological sort** thứ tự tính.
    - Query DB qua `utils_database_manager` cho direct indicators.
    - Gọi hàm trong các module M1–M6 cho calculated indicators.
    - Caching intermediate để tránh query trùng lặp.
    - Ghi nhận:
      - Số indicator thành công/thất bại.
      - Thứ tự tính toán.
      - Danh sách indicator lỗi.

- `indicator_result_repository.py`  
  - Định nghĩa cách **lưu kết quả 57 indicators** vào DB (bảng `indicator_57` hoặc bảng tuỳ chọn).
  - Tạo table nếu chưa có, thực hiện upsert theo:
    - `stock`, `year`, `quarter`, `indicator_name`.

- `calculate_all_indicators.py`  
  - CLI + API tiện dụng:
    - Chạy cho 1 mã (`--stock`), 1 năm (`--year`), 1 quý (`--quarter`).
    - Chọn subset indicators (`--indicator CFO --indicator "Net Income (NI)"`).
    - Xuất JSON ra file.
    - Tùy chọn lưu DB hoặc bỏ qua (`--skip-db`).

- `main_run_batch.py`  
  - Batch runner nhiều mã / nhiều năm / nhiều quý:
    - Đọc mã từ file (`--stocks-file`), CLI (`--stocks`), hoặc DB (`--all-stocks`).
    - Lấy năm từ DB (`--all-years`) hoặc chỉ định (`--year`, `--years`).
    - Lặp qua tất cả combination và:
      - Gọi `calculate_all_indicators`.
      - In log chi tiết từng indicator.
      - Lưu kết quả vào DB thông qua `indicator_result_repository`.

---

## 🧮 2. Module nhóm chỉ số (M1–M6)

Các folder `M1_...` đến `M6_...` chứa **logic nghiệp vụ** cho từng nhóm chỉ số:

- `M1_BCTC_core_profit_and_cashflow/`
  - Các file: `id1_CFO.py`, `id2_NI.py`, `id3_EBIT.py`, `id4_EBITDA.py`, `id5_NOPAT.py`, …
  - Mỗi file thường implement hàm dạng:
    - `get_<IndicatorName>_value(stock, year, quarter, db_conn, ...)`
  - Tập trung vào chỉ số **lợi nhuận và dòng tiền cốt lõi**.

- `M2_BCTC_core_revenue_and_margins/`
  - `id6_revenue.py`, `id7_gross_profit.py`, `id8_gross_margin.py`, `id9_revenue_growth.py`, `id10_earnings_growth.py`, `id11_core_revenue.py`, …
  - Nhóm chỉ số doanh thu, biên lợi nhuận, tăng trưởng.

- `M3_BCTC_core_balance_sheet_and_investment/`
  - `id15_total_assets.py`, `id16_equity.py`, `id17_interest_bearing_debt.py`, `id18_cash_and_short_term_investments.py`, `id19_capex.py`, `id21_working_capital.py`, `id22_delta_working_capital.py`, `id23_accounts_receivable.py`, `id25_accounts_payable.py`, `id30_fcff.py`, …
  - Nhóm chỉ số tài sản, nợ, vốn chủ, dòng tiền tự do (FCFF), working capital, v.v.

- `M4_market_and_valuation/`, `M5_cost_of_capital_and_dcf/`, `M6_governance_and_disclosure/`
  - Hiện chủ yếu mới có `__init__.py`.
  - Dự kiến sẽ chứa:
    - P/E, P/B, EV/EBITDA, WACC, DCF, các chỉ số governance/disclosure, …

> `README1_.md` và `README2.md` trong root giải thích chi tiết **luồng logic và tình trạng hiện tại** (số indicator đã implement/test, TODO, …).

---

## 📤 3. Output format & bảng lưu kết quả

### 3.1. JSON output (per stock/year/quarter)

Ví dụ JSON được tạo bởi `calculate_all_indicators.py`:

```json
{
  "stock": "MIG",
  "year": 2024,
  "quarter": 2,
  "indicators_with_id": [
    {
      "id": 1,
      "name": "CFO",
      "value": 174481880282.0
    },
    {
      "id": 2,
      "name": "Net Income (NI)",
      "value": null
    }
  ],
  "metadata": {
    "calculated_at": "...",
    "total_indicators": 57,
    "successful": 8,
    "failed": 49,
    "failed_list": [...],
    "calculation_order": [...]
  }
}
```

- `indicators_with_id` luôn sort theo `id` (1–57).
- `value = null` nếu indicator không tính được (thiếu dữ liệu/logic chưa implement).

### 3.2. Bảng DB đích (ví dụ `indicator_57`)

- Được tạo/quản lý bởi `indicator_result_repository.py`.
- Schema khuyến nghị:

```text
id SERIAL PRIMARY KEY
stock VARCHAR(10)
year INTEGER
quarter SMALLINT DEFAULT 0  -- 0 = báo cáo năm
indicator_id INTEGER
indicator_name VARCHAR(255)
indicator_value DOUBLE PRECISION
calculation_metadata JSONB
created_at TIMESTAMP
updated_at TIMESTAMP
UNIQUE (stock, year, quarter, indicator_name)
```

- Quy ước:
  - `quarter = 1–4` cho quý.
  - `quarter = 0` hoặc `5` cho báo cáo năm, tuỳ theo phần còn lại của hệ thống (cần đồng bộ với cách lưu trong raw BCTC).

---

## 🚀 4. Cách dùng – CLI & Batch

### 4.1. Tính cho 1 mã (CLI đơn)

Chạy từ root project (thư mục chứa `Gen57Metrics/`):

```bash
cd Gen57Metrics

# Full 57 indicators cho MIG năm 2024, quý 2
python calculate_all_indicators.py --stock MIG --year 2024 --quarter 2

# Chỉ tính CFO
python calculate_all_indicators.py --stock MIG --year 2024 --quarter 2 --indicator CFO

# Chỉ tính một subset indicators
python calculate_all_indicators.py --stock MIG --year 2024 --quarter 2 \
  --indicator CFO \
  --indicator "Net Income (NI)"

# Đổi đường dẫn file JSON output
python calculate_all_indicators.py --stock MIG --year 2024 --quarter 2 \
  --output results/mig_2024_q2_all.json

# Tuỳ chọn pretty print / bỏ metadata
python calculate_all_indicators.py --stock MIG --year 2024 --quarter 2 --pretty --no-metadata

# Mặc định: kết quả có thể được lưu vào bảng indicator_57.
# Bỏ lưu DB:
python calculate_all_indicators.py --stock MIG --year 2024 --quarter 2 --skip-db
```

### 4.2. Batch nhiều mã/nhiều năm (main_run_batch.py)

File: `main_run_batch.py`

Ví dụ:

```bash
cd Gen57Metrics

# 1) Chạy cho danh sách mã đọc từ file
python main_run_batch.py --stocks-file stocks_example.txt --year 2024 --quarter 5

# 2) Chạy cho danh sách mã truyền thẳng từ CLI
python main_run_batch.py --stocks MIG PGI BIC --year 2024 --quarter 5

# 3) Chạy cho tất cả mã lấy từ DB (bảng company)
python main_run_batch.py --all-stocks --year 2024 --quarter 5

# 4) Chạy cho nhiều năm / nhiều quý
python main_run_batch.py --stocks MIG --years 2022 2023 2024 --quarters 1 2 3 4 5

# 5) Lấy tất cả năm cho 1 mã từ DB
python main_run_batch.py --stocks MIG --all-years --quarter 5

# 6) Xuất summary batch ra file JSON
python main_run_batch.py --stocks MIG PGI --year 2024 --quarter 5 --output batch_summary.json
```

Batch runner sẽ:

- In log tiến trình (số task, thành công/thất bại).
- Gọi `calculate_all_indicators` cho từng combination.
- Cố gắng lưu kết quả vào bảng `indicator_57` (hoặc bảng được cấu hình).

---

## 🌐 5. Web Dashboard – Gen57Metrics/web

Folder: `web/`

> Chi tiết xem thêm `web/README.md`. Dưới đây là tóm tắt.

### 5.1. Backend (FastAPI)

- File: `web/app.py`
- Chức năng chính:
  - `/api/indicators` – metadata 57 indicators từ `57BaseIndicators.json`.
  - `/api/stocks` & `/api/periods` – danh sách mã/kỳ báo cáo có sẵn, dựa vào DB.
  - `/api/indicator-values` – tính toán giá trị 57 chỉ số on‑demand bằng `IndicatorCalculator`.
  - `/api/dashboard/bootstrap` – trả 1 payload tổng hợp để frontend khởi tạo nhanh.
- Dùng chung `utils_database_manager.DB_CONFIG` với core engine.

### 5.2. Frontend

- `index.html`, `css/style.css`, `js/app.js`
  - Chọn stock/year/quarter.
  - Lọc theo group, search theo tên indicator.
  - Hiển thị:
    - Definition, formula, flags (Get_Direct_From_DB, …).
    - Giá trị thực tế theo kỳ.
    - Summary: tổng số chỉ số, số thành công/thất bại.

**Cách chạy nhanh**:

```bash
cd Gen57Metrics/web
pip install -r requirements.txt
uvicorn app:app --reload --port 30100

# Serve static:
python -m http.server 8081
# Mở: http://localhost:8081/index.html
```

Frontend tự detect API base khi chạy local.

---

## 🧱 6. Mối quan hệ với BaoCaoTaiChinh

- `BaoCaoTaiChinh`:
  - Xử lý **ingestion**: OCR → Extract → JSON → DB (raw tables).
  - Chuẩn hóa BCTC theo chuẩn template/Thông tư.

- `Gen57Metrics`:
  - Dùng dữ liệu từ các bảng raw đó để:
    - Tính toán 57 chỉ số ở tầng phân tích.
    - Lưu kết quả vào bảng riêng (`indicator_57`).
    - Expose API/dashboard để visualize các chỉ số.

Tóm lại:

```text
PDF/Word BCTC
  ↓  (BaoCaoTaiChinh/OCR + Extract)
PostgreSQL (income_statement_*, balance_sheet_raw, cash_flow_statement_raw, …)
  ↓  (Gen57Metrics core)
57 Indicators / bảng indicator_57 + Dashboard Gen57Metrics/web
```

---

## 📌 Ghi chú & hướng mở rộng

- Nhiều indicators hiện **chưa implement đủ** (xem `README1_.md`, `README2.md` để biết danh sách TODO).
- Cần bổ sung:
  - Hàm tính toán cho các indicator còn thiếu trong M2–M6.
  - Unit test cho từng nhóm chỉ số.
  - Tối ưu performance cho batch lớn (số lượng mã, năm, quý cao).
- Khi thay đổi schema BCTC hoặc cách lưu trữ:
  - Cần đồng bộ lại `utils_database_manager` và các hàm direct indicators (theo `ma_so`).


