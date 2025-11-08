Giải thích ngắn gọn từng bước của code:

## Flow chính của module

### **Bước 1: Parse Markdown Table** (`_parse_markdown_table`)

```
Input: "| Col1 | Col2 |\n| --- | --- |\n| A | B |"
  ↓
1. Tách theo dòng (\n)
2. Bỏ qua dòng trống
3. Bỏ qua separator line (| --- | --- |)
4. Chỉ lấy dòng bắt đầu bằng |
5. Tách cells bằng ký tự |
6. Loại bỏ khoảng trắng thừa
  ↓
Output: [['Col1', 'Col2'], ['A', 'B']]
```

### **Bước 2: Normalize Headers** (`_normalize_headers`)

```
Input: ['Col1', '', 'Col3']  ← có header trống
  ↓
Thay thế header trống bằng tên mặc định
  ↓
Output: ['Col1', 'Column_2', 'Col3']
```

### **Bước 3: Normalize Rows** (`_normalize_row_columns`)

```
Input: 
  - Header: ['Col1', 'Col2']  (2 cột)
  - Row 1: ['A', 'B', 'C']    (3 cột - thừa)
  - Row 2: ['D']              (1 cột - thiếu)
  ↓
Chuẩn hóa về số cột của header:
  - Row 1: ['A', 'B']         ← cắt bớt
  - Row 2: ['D', '']          ← thêm ô trống
  ↓
Output: [['A', 'B'], ['D', '']]
```

### **Bước 4: Create DataFrame** (`_create_dataframe_from_rows`)

```
Input: 
  - Headers: ['Col1', 'Col2']
  - Rows: [['A', 'B'], ['D', '']]
  ↓
Tạo pandas DataFrame
  ↓
Output: DataFrame với 2 cột, 2 dòng dữ liệu
```

### **Bước 5: Save to Excel** (`markdownTable_to_xlsx`)

```
Input: DataFrame + output_path
  ↓
1. Kiểm tra pandas có sẵn không
2. Parse markdown → rows
3. Tạo DataFrame
4. Tạo thư mục output nếu chưa có
5. Ghi ra file .xlsx bằng openpyxl
  ↓
Output: Đường dẫn file Excel đã tạo
```

## Flow tổng thể

```
Markdown Table String
    ↓
_parse_markdown_table()      → List[List[str]] (rows)
    ↓
_normalize_headers()         → Headers chuẩn hóa
    ↓
_normalize_row_columns()     → Rows chuẩn hóa (cùng số cột)
    ↓
_create_dataframe_from_rows() → pandas DataFrame
    ↓
df.to_excel()                → File .xlsx
```

## Các hàm hỗ trợ

1. `_is_separator_line()` - Kiểm tra dòng `| --- | --- |`
2. `remove_diacritics()` - Loại bỏ dấu tiếng Việt
3. `extract_markdown_tables()` - Trích xuất nhiều bảng từ text

## Ví dụ thực tế

```python
# Input
table = """
| Mã số | CHỈ TIÊU |
| --- | --- |
| 01 | Doanh thu |
"""

# Step 1: Parse
rows = _parse_markdown_table(table)
# → [['Mã số', 'CHỈ TIÊU'], ['01', 'Doanh thu']]

# Step 2: Normalize
headers = _normalize_headers(rows[0])  # ['Mã số', 'CHỈ TIÊU']
normalized_rows = [_normalize_row_columns(row, len(headers)) for row in rows[1:]]

# Step 3: Create DataFrame
df = pd.DataFrame(normalized_rows, columns=headers)

# Step 4: Save
df.to_excel("output.xlsx", index=False)
```

Tóm lại: Parse → Normalize → DataFrame → Excel
