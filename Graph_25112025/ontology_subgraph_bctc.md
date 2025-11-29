
# Ontology Subgraph BCTC – FinAI (Có ví dụ property)

## 1. Node Types

### 1.1 `Company`

#### Định nghĩa

| Trường (Property) | Kiểu dữ liệu | Bắt buộc | Mô tả |
|-------------------|-------------|----------|-------|
| `company_code`    | String      | Yes      | Mã chứng khoán công ty (VD: `BVH`, `MIG`) |
| `company_name`    | String      | Yes      | Tên đầy đủ công ty |
| `exchange`        | String      | No       | Sở giao dịch (HOSE, HNX, UPCoM…) |
| `sector`          | String      | No       | Ngành cấp cao (VD: Tài chính, Bảo hiểm…) |
| `subsector`       | String      | No       | Ngành con (VD: Bảo hiểm phi nhân thọ, Nhân thọ…) |
| `country`         | String      | No       | Quốc gia (VD: VN) |
| `status`          | String      | No       | Trạng thái niêm yết / giao dịch |
| `note`            | String      | No       | Ghi chú thêm nếu cần |

#### Ví dụ property `Company`

```json
{
  "company_code": "BVH",
  "company_name": "Tập đoàn Bảo Việt",
  "exchange": "HOSE",
  "sector": "Tài chính",
  "subsector": "Bảo hiểm nhân thọ",
  "country": "VN",
  "status": "Listed",
  "note": "Công ty bảo hiểm đầu ngành, nhiều BCTC lịch sử trước TT232."
}
```

---

### 1.2 `MetricTable`

Node này đại diện **bảng metric tổng hợp** cho 1 công ty, 1 loại kỳ (năm/quý), gồm **cả định nghĩa metric + time series của từng metric**.

#### Định nghĩa

| Trường (Property)       | Kiểu dữ liệu   | Bắt buộc | Mô tả |
|-------------------------|----------------|----------|-------|
| `type`                  | String         | Yes      | Cố định: `"MetricTable"` |
| `company_code`          | String         | Yes      | Mã công ty (VD: `BVH`) |
| `period_type`           | String         | Yes      | Loại kỳ: `"annual"` / `"quarterly"` |
| `year_from`             | Integer        | Yes      | Năm bắt đầu của chuỗi dữ liệu |
| `year_to`               | Integer        | Yes      | Năm kết thúc của chuỗi dữ liệu |
| `currency`              | String         | No       | Đơn vị tiền tệ (VD: `"VND"`) |
| `standard`              | String         | No       | Chuẩn BCTC dùng để tính (VD: `"TT232"`, `"TT200"`) |
| `source_pipeline`       | String         | No       | Tên/phiên bản pipeline Python sinh ra metric (VD: `"FinAI_Python_v1.0"`) |
| `metric_defs_json`      | String (JSON)  | Yes      | JSON danh sách định nghĩa metric: tên, nhóm, định nghĩa, công thức, `depends_on` (mã TK) |
| `metric_timeseries_json`| String (JSON)  | Yes      | JSON map `{metric_name: [ {year, value, yoy?, qoq?} ] }` |
| `trend_summary_json`    | String (JSON)  | No       | JSON tóm tắt xu hướng các metric (Up/Down/Flat/Volatile) |
| `quality_flags_json`    | String (JSON)  | No       | JSON cờ chất lượng dữ liệu (thiếu, outlier, ước tính…) |
| `last_updated`          | String (ISO DateTime) | No | Thời điểm cập nhật gần nhất |

#### Ví dụ property `MetricTable`

```json
{
  "type": "MetricTable",
  "company_code": "BVH",
  "period_type": "annual",
  "year_from": 2014,
  "year_to": 2023,
  "currency": "VND",
  "standard": "TT232",
  "source_pipeline": "FinAI_Python_v1.2",
  "metric_defs_json": "{\"ROE\": {\"group\": \"Profitability\", \"definition\": \"LNST / VCSH bình quân\", \"formula\": \"KQKD_60 / ((CDKT_410_begin + CDKT_410_end)/2)\", \"depends_on\": [\"KQKD_60\", \"CDKT_410\"] }}",
  "metric_timeseries_json": "{\"ROE\": [{\"year\": 2021, \"value\": 0.142}, {\"year\": 2022, \"value\": 0.151}, {\"year\": 2023, \"value\": 0.098}]}",
  "trend_summary_json": "{\"ROE\": \"Giảm từ 2022 đến 2023 do LNST giảm mạnh\"}",
  "quality_flags_json": "{\"ROE\": [\"OK\"]}",
  "last_updated": "2025-11-22T18:00:00+07:00"
}
```

*(Trong Neo4j thực tế, `metric_defs_json` và `metric_timeseries_json` là string JSON; Python sẽ parse/ghi lại khi cần.)*

---

### 1.3 `KQKD` (Báo cáo kết quả kinh doanh)

Node chứa **bảng số liệu KQKD theo mã chỉ tiêu**, dạng time series.

#### Định nghĩa

| Trường (Property)     | Kiểu dữ liệu   | Bắt buộc | Mô tả |
|-----------------------|----------------|----------|-------|
| `type`                | String         | Yes      | Cố định: `"KQKD"` |
| `company_code`        | String         | Yes      | Mã công ty |
| `period_type`         | String         | Yes      | `"annual"` / `"quarterly"` |
| `year_from`           | Integer        | Yes      | Năm bắt đầu |
| `year_to`             | Integer        | Yes      | Năm kết thúc |
| `standard`            | String         | No       | Chuẩn BCTC: `"TT232"`, `"TT200"`… |
| `currency`            | String         | No       | Đơn vị tiền tệ |
| `source_file`         | String         | No       | Đường dẫn / ID file gốc (Excel/CSV/DB) |
| `table_metadata`      | String (JSON)  | No       | JSON metadata mô tả bảng (ví dụ: mô tả tiếng Việt, mapping template…) |
| `line_items_json`     | String (JSON)  | Yes      | JSON map: `{ "60": { "name": "LNST", "values": [ {year, value}, ... ] }, ... }` |
| `checksum`            | String         | No       | Hash để kiểm soát thay đổi bảng gốc |
| `note`                | String         | No       | Ghi chú đặc thù (VD: chỉnh sửa theo thuyết minh…) |
| `last_updated`        | String (ISO DateTime) | No | Thời điểm cập nhật gần nhất |

#### Ví dụ property `KQKD`

```json
{
  "type": "KQKD",
  "company_code": "BVH",
  "period_type": "annual",
  "year_from": 2014,
  "year_to": 2023,
  "standard": "TT232",
  "currency": "VND",
  "source_file": "/data/bvh/KQKD_2014_2023.xlsx",
  "table_metadata": "{\"description\": \"Báo cáo kết quả hoạt động kinh doanh hợp nhất\"}",
  "line_items_json": "{\"60\": {\"name\": \"Lợi nhuận sau thuế\", \"values\": [{\"year\": 2021, \"value\": 1200}, {\"year\": 2022, \"value\": 1350}, {\"year\": 2023, \"value\": 900}]}, \"50\": {\"name\": \"Lợi nhuận trước thuế\", \"values\": [{\"year\": 2021, \"value\": 1500}]}}",
  "checksum": "sha256:abc123...",
  "note": "LNST 2023 giảm do tăng chi phí bồi thường; đã đối chiếu với thuyết minh.",
  "last_updated": "2025-11-22T17:30:00+07:00"
}
```

---

### 1.4 `CDKT` (Bảng cân đối kế toán)

#### Định nghĩa

| Trường (Property)     | Kiểu dữ liệu   | Bắt buộc | Mô tả |
|-----------------------|----------------|----------|-------|
| `type`                | String         | Yes      | Cố định: `"CDKT"` |
| `company_code`        | String         | Yes      | Mã công ty |
| `period_type`         | String         | Yes      | `"annual"` / `"quarterly"` |
| `year_from`           | Integer        | Yes      | Năm bắt đầu |
| `year_to`             | Integer        | Yes      | Năm kết thúc |
| `standard`            | String         | No       | Chuẩn BCTC: `"TT232"`, `"TT200"`… |
| `currency`            | String         | No       | Đơn vị tiền tệ |
| `source_file`         | String         | No       | Đường dẫn / ID file gốc |
| `table_metadata`      | String (JSON)  | No       | Metadata mô tả bảng CDKT |
| `line_items_json`     | String (JSON)  | Yes      | JSON map: `{ "410": { "name": "Vốn chủ sở hữu", "values": [ {year, value}, ... ] }, ... }` |
| `begin_end_flag`      | Boolean        | No       | Cho biết có tách giá trị đầu kỳ/cuối kỳ hay không |
| `checksum`            | String         | No       | Hash để kiểm soát thay đổi |
| `note`                | String         | No       | Ghi chú đặc thù |
| `last_updated`        | String (ISO DateTime) | No | Thời điểm cập nhật |

#### Ví dụ property `CDKT`

```json
{
  "type": "CDKT",
  "company_code": "BVH",
  "period_type": "annual",
  "year_from": 2014,
  "year_to": 2023,
  "standard": "TT232",
  "currency": "VND",
  "source_file": "/data/bvh/CDKT_2014_2023.xlsx",
  "table_metadata": "{\"description\": \"Bảng cân đối kế toán hợp nhất\"}",
  "line_items_json": "{\"410\": {\"name\": \"Vốn chủ sở hữu\", \"values\": [{\"year\": 2021, \"value\": 8500}, {\"year\": 2022, \"value\": 9000}, {\"year\": 2023, \"value\": 8800}]}, \"270\": {\"name\": \"Tổng tài sản\", \"values\": [{\"year\": 2021, \"value\": 32000}]}}",
  "begin_end_flag": true,
  "checksum": "sha256:def456...",
  "note": "VCSH 2023 giảm nhẹ do chia cổ tức tiền mặt.",
  "last_updated": "2025-11-22T17:40:00+07:00"
}
```

---

### 1.5 `LCTT` (Báo cáo lưu chuyển tiền tệ)

#### Định nghĩa

| Trường (Property)     | Kiểu dữ liệu   | Bắt buộc | Mô tả |
|-----------------------|----------------|----------|-------|
| `type`                | String         | Yes      | Cố định: `"LCTT"` |
| `company_code`        | String         | Yes      | Mã công ty |
| `period_type`         | String         | Yes      | `"annual"` / `"quarterly"` |
| `year_from`           | Integer        | Yes      | Năm bắt đầu |
| `year_to`             | Integer        | Yes      | Năm kết thúc |
| `standard`            | String         | No       | Chuẩn BCTC |
| `currency`            | String         | No       | Đơn vị tiền tệ |
| `method`              | String         | No       | `"Direct"` / `"Indirect"` |
| `source_file`         | String         | No       | Đường dẫn / ID file gốc |
| `table_metadata`      | String (JSON)  | No       | Metadata mô tả bảng LCTT |
| `line_items_json`     | String (JSON)  | Yes      | JSON map: các dòng chính: CFO, CFI, CFF… với time series |
| `checksum`            | String         | No       | Hash bảng gốc |
| `note`                | String         | No       | Ghi chú |
| `last_updated`        | String (ISO DateTime) | No | Thời điểm cập nhật |

#### Ví dụ property `LCTT`

```json
{
  "type": "LCTT",
  "company_code": "BVH",
  "period_type": "annual",
  "year_from": 2014,
  "year_to": 2023,
  "standard": "TT232",
  "currency": "VND",
  "method": "Indirect",
  "source_file": "/data/bvh/LCTT_2014_2023.xlsx",
  "table_metadata": "{\"description\": \"Báo cáo lưu chuyển tiền tệ hợp nhất\"}",
  "line_items_json": "{\"CFO\": {\"name\": \"Dòng tiền từ HĐKD\", \"values\": [{\"year\": 2021, \"value\": 1100}, {\"year\": 2022, \"value\": 1250}, {\\"year\\": 2023, \\"value\\": 900}]}}",
  "checksum": "sha256:ghi789...",
  "note": "CFO 2023 giảm cùng chiều với LNST, cảnh báo chất lượng earnings.",
  "last_updated": "2025-11-22T17:50:00+07:00"
}
```

---

## 2. Quan hệ (Edges) trong subgraph BCTC

### 2.1 Quan hệ giữa `Company` và 3 bảng BCTC

| Tên quan hệ       | From      | To        | Ý nghĩa | Bội số (Cardinality) | Ghi chú |
|-------------------|----------|-----------|--------|----------------------|--------|
| `HAS_FS`          | `Company` | `KQKD`   | Công ty có bộ báo cáo KQKD | 1 Company → N KQKD (theo năm/kỳ) | Nếu 1 node KQKD chứa nhiều năm, thường là 1 Company → 1 KQKD/period_type |
| `HAS_FS`          | `Company` | `CDKT`   | Công ty có bảng CDKT | 1 → N | |
| `HAS_FS`          | `Company` | `LCTT`   | Công ty có bảng LCTT | 1 → N | |

---

### 2.2 Quan hệ giữa `Company` và `MetricTable`

| Tên quan hệ           | From      | To            | Ý nghĩa | Bội số | Ghi chú |
|-----------------------|----------|---------------|--------|--------|--------|
| `HAS_METRIC_TABLE`    | `Company` | `MetricTable` | Công ty có bảng metric tổng hợp (đã tính) | 1 → N (VD: 1 node cho annual, 1 node cho quarterly) | |

---

### 2.3 Quan hệ giữa `MetricTable` và 3 bảng BCTC

| Tên quan hệ     | From          | To      | Ý nghĩa | Bội số | Ghi chú |
|-----------------|--------------|---------|--------|--------|--------|
| `DERIVED_FROM`  | `MetricTable` | `KQKD` | Bảng metric được tính dựa trên dữ liệu KQKD | 1 → 1 (per company/period_type) | |
| `DERIVED_FROM`  | `MetricTable` | `CDKT` | Bảng metric được tính dựa trên dữ liệu CDKT | 1 → 1 | |
| `DERIVED_FROM`  | `MetricTable` | `LCTT` | Bảng metric được tính dựa trên dữ liệu LCTT | 1 → 1 | |

---

## 3. Ghi chú thiết kế

- **Logic tính toán**: thực hiện ngoài graph (Python/SQL), Neo4j chỉ lưu **kết quả + metadata + mapping mã TK**.
- **line_items_json**: là nơi liên kết tự nhiên giữa:
  - BCTC (KQKD/CDKT/LCTT)  
  - và `metric_defs_json` của `MetricTable` (thông qua `depends_on`).
- Cấu trúc này cho phép:
  - Query sâu về xu hướng (ROE, ROA, CFO, Debt/Equity…) trong 10+ năm.
  - LLM trả lời câu kiểu: _“ROE tăng/giảm do LNST hay do VCSH?”_ chỉ bằng cách:
    - lấy time series từ `metric_timeseries_json`
    - + `line_items_json` của KQKD/CDKT
    - + `depends_on` trong `metric_defs_json`.

Subgraph này đủ gọn cho MVP, và vẫn mở đường nâng cấp sau này (thêm node chi tiết như `FS_LineItem`, `MetricValue` nếu cần granular hơn).
