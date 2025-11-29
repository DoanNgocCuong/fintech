Đang kiểm tra các câu lệnh SQL trong `utils_database_manager.py`:

[1 tool called]

Các câu lệnh SQL đang dùng trong code:

## Tổng hợp các câu lệnh SQL

### 1. **Get Company Data** (`get_company_data`)

```sql
SELECT parsed_data, file_name, created_at, updated_at
FROM company_json_documents
WHERE company_name = %s AND year = %s
LIMIT 1
```

- Lấy `parsed_data` và metadata cho một công ty và năm

---

### 2. **Get Companies List** (`get_companies_list`)

**Không có search:**

```sql
SELECT DISTINCT company_name
FROM company_json_documents
ORDER BY company_name
```

**Có search:**

```sql
SELECT DISTINCT company_name
FROM company_json_documents
WHERE company_name ILIKE %s
ORDER BY company_name
```

- `ILIKE` để tìm kiếm không phân biệt hoa thường

---

### 3. **Get Years List** (`get_years_list`)

**Không filter theo công ty:**

```sql
SELECT DISTINCT year
FROM company_json_documents
ORDER BY year DESC
```

**Có filter theo công ty:**

```sql
SELECT DISTINCT year
FROM company_json_documents
WHERE company_name = %s
ORDER BY year DESC
```

---

### 4. **Search Evidence** (`search_evidence`)

```sql
SELECT company_name, year, parsed_data
FROM company_json_documents
WHERE parsed_data::text LIKE %s
  AND company_name = %s  -- (optional)
  AND year = %s          -- (optional)
```

- Dùng `parsed_data::text LIKE` để tìm kiếm trong JSONB
- Sau đó filter trong Python code

---

### 5. **Get Stats** (`get_stats`)

**Total companies:**

```sql
SELECT COUNT(DISTINCT company_name) FROM company_json_documents
```

**Total years:**

```sql
SELECT COUNT(DISTINCT year) FROM company_json_documents
```

**Total records:**

```sql
SELECT COUNT(*) FROM company_json_documents
```

**Companies by year:**

```sql
SELECT year, COUNT(DISTINCT company_name) as count
FROM company_json_documents
GROUP BY year
ORDER BY year DESC
```

---

## Đặc điểm

1. Tất cả queries đều query từ bảng `company_json_documents`
2. Sử dụng cột `parsed_data` (JSONB) - không dùng `json_raw`
3. Parameterized queries với `%s` để tránh SQL injection
4. Dùng `ILIKE` cho tìm kiếm company name (case-insensitive)
5. Dùng `parsed_data::text LIKE` để tìm kiếm trong JSONB

## Lưu ý

- Query `parsed_data` trực tiếp, không parse `json_raw`
- Filtering trong Python sau khi lấy `parsed_data` từ database
- Có thể tối ưu bằng JSONB operators của PostgreSQL nếu cần

Bạn muốn tôi tối ưu các queries này không?
