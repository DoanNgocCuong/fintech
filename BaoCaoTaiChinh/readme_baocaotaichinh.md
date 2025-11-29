## 📊 BaoCaoTaiChinh – Financial Reports Pipeline (End‑to‑End)

Hệ thống `BaoCaoTaiChinh` là **pipeline end‑to‑end** để:

- **Nhận input**: PDF/Word báo cáo tài chính.
- **OCR + bóc tách**: chuyển PDF → ảnh → markdown/xlsx/json chuẩn cấu trúc.
- **Nạp dữ liệu**: ghi vào PostgreSQL (các bảng `income_statement_*`, `balance_sheet_raw`, `cash_flow_statement_raw`, …).
- **Phục vụ dashboard**: API + UI để tra cứu báo cáo theo mã cổ phiếu, loại báo cáo, kỳ báo cáo.

Các folder chính:

- `OCR/` – Pipeline OCR PDF → markdown/xlsx/json (DOTS OCR + vLLM).
- `ExtractBaoCaoTaiChinh/` – Chuẩn hóa template, convert markdown/xlsx → json, đổ vào DB.
- `web/` – FastAPI backend + frontend dashboard để xem báo cáo tài chính.
- `docker/` – Cấu hình docker‑compose cho Postgres, web dashboard, v.v.

---

## 🧩 1. OCR – Từ PDF đến Markdown / Ảnh / Xử lý song song

Folder: `OCR/`

**Mục tiêu**: chuyển tài liệu BCTC (PDF) sang định dạng dễ bóc tách (markdown + ảnh) với chất lượng tốt, có khả năng chạy song song và scale.

**Thành phần tiêu biểu**:

- `main_dots_ocr_pdf_to_image_list_to_markdown_final.py`  
  - Pipeline chính: PDF → danh sách ảnh → markdown (bố cục + text).
  - Tích hợp với engine DOTS OCR / vLLM qua folder `dots.ocr/` và các script `sh_start_vllm_*.sh`.

- `image2text_v1_done.py`, `v1_dots_ocr_pdf_to_image_markdown.py`  
  - Các phiên bản/step nhỏ hơn cho việc convert ảnh → text/markdown.

- `main_parallel.py`, `main_parallel_run_nganh_bao_hiem.py`  
  - Chạy OCR **song song** cho nhiều file/tài liệu, tối ưu batch size / số worker.
  - Liên quan đến các util:
    - `utils_parallel_batch_size_max_worker.py`
    - `utils_test_ocr_parallel_number_workers_insted_of_locust_test.py`

- `data/`  
  - `*_test.pdf`, `*_test.md`, `out_images/`, `tmp_images/` – data mẫu để test OCR.
  - `data_processing/remove_and_unzip.py` – xử lý/unzip trước khi chạy OCR hàng loạt.

- `README.md`, `README_environment.md`, `requirements_*.txt`  
  - Mô tả chi tiết môi trường, cách cài đặt model, host/inference requirements.

**Luồng tổng quát (OCR)**:

```text
PDF BCTC (multi‑page)
    ↓
main_dots_ocr_pdf_to_image_list_to_markdown_final.py
    ↓
Ảnh từng trang + markdown (giữ cấu trúc bảng)
    ↓
Lưu vào thư mục trung gian (data/, tmp_images/, out_images/, …)
    ↓
Đầu vào cho bước Extract (Convert markdown → xlsx/json → DB)
```

---

## 🧮 2. ExtractBaoCaoTaiChinh – Chuẩn hóa & Nạp Dữ Liệu

Folder: `ExtractBaoCaoTaiChinh/`

**Mục tiêu**: chuẩn hóa dữ liệu BCTC theo **template thống nhất**, convert sang JSON, và nạp vào các bảng PostgreSQL phục vụ dashboard và các hệ thống downstream (như `Gen57Metrics`).

### 2.1. Template & reference

- `template/`
  - Chứa các mẫu Word/PDF cho:
    - Cân đối kế toán (`balance_template_json.json`, `TT200_2014_balance_template_json.json`, …)
    - Kết quả HĐKD (`*_income_template_json_P1.json`, `*_income_template_json_P2.json`)
    - Lưu chuyển tiền tệ (`*_cash_flow_template_json.json`)
  - Các sub‑folder như:
    - `LuuChuyenTienTe/`, `NhanTho_CDKT_KQKD/`, `PhiNhanTho_CDKT_KQKD/`, `TT200_2014/` – chứa file `.doc`, `.pdf`, `.md` làm chuẩn nghiệp vụ.

- `test/`  
  - Bộ dataset test gồm `.md`, `.xlsx`, `.json` để test round‑trip:
    - markdown → xlsx → json → DB
    - và ngược lại (debug mapping, check sai lệch).

### 2.2. Script chính

Các script theo **3 nhóm chính**:

1. **Tách & chuẩn hóa Markdown → Excel**
   - `utils_markdownCanDoiKeToanText_DetectTable_to_xlsx.py`
   - `utils_markdownKetQuaHoatDongKinhDoanhText_DetectTable_to_xlsx.py`
   - `utils_markdownLuuChuyenTienTeText_DetectTable_to_xlsx.py`
   - `utils_markdownTable_to_xlsx.py`
   - `main_markdownBaoCaoTaiChinh_to_xlsx.py`

   → Bóc tách bảng trong markdown (sau OCR) và ghi thành file Excel đúng layout chuẩn.

2. **Excel → JSON template**
   - `utils_xlsx_to_json_balance.py`
   - `utils_xlsx_to_json_income.py`
   - `utils_xlsx_to_json_cash_flow.py`
   - `utils_xlsx_to_json.py`
   - `regenerate_json.py`
   - `main_*_to_excelANDjson.py` (cho từng loại báo cáo)

   → Đọc bảng từ Excel, map vào **JSON chuẩn** theo từng Thông tư (TT199, TT200, TT232, …).

3. **JSON → Database**
   - `utils_database_manager.py` – kết nối DB, thực thi SQL.
   - `main_JSON3Tables_to_DB.py` – nạp full 3 bảng (CDKT, KQKD, LCTT).
   - `main_JSONCanDoiKeToan_to_DB.py`
   - `main_JSONKetQuaHoatDongKinhDoanh_to_DB.py`
   - `main_JSONLuuChuyenTienTe_to_DB.py`
   - `sql/` – chứa các script SQL (schema, kiểm tra dữ liệu, v.v.)

**Output mẫu**:

- Folder `outputDemoExtractExcel5Ma_2024/`
  - Ví dụ: `BIC_2024_1_5_1_BaoCaoTaiChinh.xlsx`, `BMI_2024_1_5_1_BaoCaoTaiChinh.xlsx`
  - Thể hiện **file Excel đã được chuẩn hóa** sau khi bóc tách từ BCTC gốc.

### 2.3. Error log & debugging

- `error_log_markdown_to_xlsx_*.txt`, `error_log_xlsx_to_json_*.txt`, `fail_*.txt`
  - Ghi lại các trường hợp:
    - Không detect được bảng.
    - Thiếu cột / sai mã số.
    - Lỗi mapping từ Excel sang JSON/DB.

**Luồng tổng quát (Extract)**:

```text
Markdown (từ OCR) / Excel gốc
    ↓
Detect bảng & chuẩn hóa Excel (utils_markdown* → main_markdownBaoCaoTaiChinh_to_xlsx.py)
    ↓
Excel chuẩn → JSON template (utils_xlsx_to_json_*.py, main_*_to_excelANDjson.py)
    ↓
JSON 3 bảng (CDKT, KQKD, LCTT)
    ↓
main_JSON*_to_DB.py + utils_database_manager.py
    ↓
PostgreSQL: income_statement_p1_raw, income_statement_p2_raw, balance_sheet_raw, cash_flow_statement_raw, …
```

---

## 🌐 3. Web – API + Dashboard hiển thị BCTC

Folder: `web/`

> Chi tiết: xem thêm `web/readme.md` và `API.md`. Dưới đây là tóm tắt ở mức hệ thống.

### 3.1. Backend (FastAPI)

- File chính: `app.py`  
  - Service FastAPI để đọc dữ liệu từ PostgreSQL (dùng `utils_database_manager.connect` + `DB_CONFIG`).
  - Expose API cho frontend:
    - `/api/health` – health check.
    - `/api/stats` – thống kê số bản ghi trong từng bảng raw.
    - `/api/stocks` – danh sách mã cổ phiếu theo từng bảng nguồn.
    - `/api/years` – danh sách năm có dữ liệu.
    - `/api/income-statement`, `/api/balance-sheet`, `/api/cash-flow` – trả **raw JSON**.
    - `/api/*/table-data` – trả **dạng bảng** (periods + indicators) đã được trích lọc.

- Helper quan trọng:

  - `get_table_data_for_stock(stock, table_name, report_type)`  
    - Query DB theo `stock`.
    - Ghép `year`, `quarter` thành period (`Q{quarter}-{year}`, với `quarter=None` → 5).
    - Parse JSON (`json_raw`).
    - Dùng `utils_data_extractor.get_indicators_for_report_type()` để extract các **chỉ tiêu chính**.
    - Trả về:
      - `periods`: danh sách kỳ (sort giảm dần: Q5-2025, Q4-2025, …).
      - `indicators`: danh sách chỉ tiêu có `values` cho từng period.

- CORS mở (`allow_origins=["*"]`) → frontend có thể host độc lập (http server khác port).

### 3.2. Frontend (HTML/JS/CSS)

- `index_detail.html` – UI chính.
- `css/style.css` – style responsive.
- `js/data.js` – trung gian làm việc với API:
  - Tự động detect `API_BASE` theo `window.location`.
  - Map `REPORT_TYPE_MAP` (`balance`, `income`, `cashflow`) và `INCOME_SECTION_TABLES` (P1/P2).
  - Hàm `loadStocks`, `loadTableData`, `sortPeriods`, …  

- `js/app.js` – logic UI:
  - Chọn mã cổ phiếu, loại báo cáo, section P1/P2.
  - Render bảng chỉ tiêu (cột = kỳ, dòng = chỉ tiêu).
  - Search chỉ tiêu, export CSV (`bao_cao_{report_type}_{stock}_{timestamp}.csv`).

**Luồng tổng quát (Web)**:

```text
User chọn stock + report type trên UI
    ↓
Frontend (app.js, data.js) gọi API /api/* từ FastAPI
    ↓
app.py truy vấn PostgreSQL, dùng utils_data_extractor để extract indicators
    ↓
JSON response (periods + indicators) trả về cho frontend
    ↓
JS render table, summary, export CSV
```

---

## 🧪 4. Cách chạy end‑to‑end (tối thiểu)

### 4.1. Chuẩn bị dữ liệu (tối thiểu)

1. Đảm bảo đã OCR xong một số file PDF (hoặc có sẵn markdown/xlsx test) trong `OCR/data/`.
2. Dùng các script trong `ExtractBaoCaoTaiChinh/` để:
   - Convert markdown → xlsx (`main_markdownBaoCaoTaiChinh_to_xlsx.py`).
   - Convert xlsx → json (`main_*_to_excelANDjson.py`).
   - Nạp json → DB (`main_JSON*_to_DB.py` hoặc `main_JSON3Tables_to_DB.py`).

### 4.2. Chạy API + Dashboard

```bash
cd BaoCaoTaiChinh/web
pip install -r requirements.txt
python app.py --host 0.0.0.0 --port 30011
```

Sau đó:

- Mở `index_detail.html` trực tiếp, hoặc:

```bash
python -m http.server 8080
# rồi mở: http://localhost:8080/index_detail.html
```

---

## 🔄 5. Quan hệ với Gen57Metrics

Hệ thống `Gen57Metrics` (57 chỉ số) **đọc dữ liệu đầu vào** từ các bảng mà `BaoCaoTaiChinh` tạo ra:

- `income_statement_p1_raw`, `income_statement_p2_raw`
- `balance_sheet_raw`
- `cash_flow_statement_raw`

Vì vậy:

- `BaoCaoTaiChinh` = **layer ingestion + chuẩn hóa BCTC vào DB**.
- `Gen57Metrics` = **layer tính toán indicators cấp cao (57 chỉ số) + dashboard metrics**.

---

## 📌 Ghi chú vận hành

- Nên chạy OCR và Extract theo **batch nhỏ trước** để kiểm tra:
  - Bảng có khớp template không.
  - JSON và DB có dữ liệu đầy đủ cho các mã test.
- Theo dõi các file `error_log_*.txt` và `fail_*.txt` trong `ExtractBaoCaoTaiChinh/` để fix mapping.
- Khi thay đổi template hoặc Thông tư mới:
  - Cập nhật lại các file `*_template_json*.json`.
  - Rerun các bước convert + load DB tương ứng.








