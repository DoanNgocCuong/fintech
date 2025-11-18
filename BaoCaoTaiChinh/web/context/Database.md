
## Tổng quan hệ thống lưu Database

### 1. Cấu hình Database

```14:20:utils_database_manager.py
DB_CONFIG: Dict[str, Any] = {
    'host': '103.253.20.30',
    'port': 29990,
    'database': 'financial-reporting-database',
    'user': 'postgres',
    'password': 'postgres',
}
```

- Database: PostgreSQL
- Host: 103.253.20.30:29990
- Database name: financial-reporting-database

### 2. Cấu trúc bảng (4 bảng)

Cả 3 bảng có cùng cấu trúc:

```43:54:utils_database_manager.py
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS "{table_name}" (
        id SERIAL PRIMARY KEY,
        stock VARCHAR(10) NOT NULL,
        year INTEGER NOT NULL,
        quarter INTEGER,
        source_filename VARCHAR(500),
        json_raw JSONB NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(stock, year, quarter)
    );
    """
```

Các bảng:

- `income_statement_p1_raw` (Kết quả hoạt động kinh doanh · Phần I)
- `income_statement_p2_raw` (Kết quả hoạt động kinh doanh · Phần II)
- `balance_sheet_raw` (Cân đối kế toán)
- `cash_flow_statement_raw` (Lưu chuyển tiền tệ)

Các trường:

- `id`: SERIAL PRIMARY KEY
- `stock`: VARCHAR(10) — mã cổ phiếu (BIC, PGI, ...)
- `year`: INTEGER — năm báo cáo
- `quarter`: INTEGER — quý (có thể NULL cho báo cáo năm)
- `source_filename`: VARCHAR(500) — tên file nguồn
- `json_raw`: JSONB — dữ liệu JSON
- `created_at`, `updated_at`: TIMESTAMP
- Unique constraint: (stock, year, quarter)

### 3. Cấu trúc dữ liệu JSON

#### Balance Sheet (`balance_template_json.json`):

```json
{
    "can_doi_ke_toan": {
        "tai_san": { ... },
        "nguon_von": { ... }
    }
}
```

#### Income Statement (`income_template_json_P1.json` / `income_template_json_P2.json`):

```json
{
    "ket_qua_hoat_dong_kinh_doanh": {
        "01_doanh_thu_phi_bao_hiem": { ... },
        ...
    }
}
```

#### Cash Flow (`cash_flow_template_json.json`):

```json
{
    "bao_cao_luu_chuyen_tien_te": {
        "I_luu_chuyen_tien_tu_hoat_dong_kinh_doanh_20": { ... },
        ...
    }
}
```


---
