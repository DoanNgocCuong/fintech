# Modules Xử lý Báo cáo Tài chính

Tài liệu này mô tả 3 modules để xử lý các loại báo cáo tài chính từ Markdown sang Excel.

## Tổng quan

Có 3 modules chính để xử lý các loại báo cáo tài chính:

1. **Bảng Cân Đối Kế Toán** (`utils_markdownCanDoiKeToanText_DetectTable_to_xlsx.py`)
2. **Kết quả Hoạt động Kinh doanh** (`utils_markdownKetQuaHoatDongKinhDoanhText_DetectTable_to_xlsx.py`)
3. **Lưu chuyển Tiền tệ** (`utils_markdownLuuChuyenTienTeText_DetectTable_to_xlsx.py`)

## Cấu trúc Module

Tất cả 3 modules đều có cấu trúc tương tự:

```
1. detect_<type>()           - Phát hiện loại báo cáo trong văn bản
2. process_markdown_file_to_xlsx() - Xử lý file và chuyển đổi sang Excel
3. main()                    - Hàm chính để chạy script
```

## 1. Bảng Cân Đối Kế Toán

### File: `utils_markdownCanDoiKeToanText_DetectTable_to_xlsx.py`

### Chức năng:
- Phát hiện "bảng cân đối kế toán" trong văn bản
- Trích xuất các bảng markdown
- Chuyển đổi sang Excel

### Pattern Detection:
```python
pattern = "bang can doi ke toan"
```

### Sử dụng:
```python
from utils_markdownCanDoiKeToanText_DetectTable_to_xlsx import process_markdown_file_to_xlsx

result_path = process_markdown_file_to_xlsx(
    input_file="BIC_2024_1_5_1.md",
    detect_balance_sheet=True,
    multiple_sheets=True
)
```

### Output:
- File: `{input_file}_CanDoiKeToan.xlsx`
- Sheet names: `Bang_1`, `Bang_2`, ...

## 2. Kết quả Hoạt động Kinh doanh

### File: `utils_markdownKetQuaHoatDongKinhDoanhText_DetectTable_to_xlsx.py`

### Chức năng:
- Phát hiện "báo cáo kết quả hoạt động kinh doanh" trong văn bản
- Trích xuất các bảng markdown
- Chuyển đổi sang Excel

### Pattern Detection:
```python
patterns = [
    "bao cao ket qua hoat dong kinh doanh",
    "ket qua hoat dong kinh doanh",
    "bao cao ket qua kinh doanh"
]
```

### Sử dụng:
```python
from utils_markdownKetQuaHoatDongKinhDoanhText_DetectTable_to_xlsx import process_markdown_file_to_xlsx

result_path = process_markdown_file_to_xlsx(
    input_file="BIC_2024_1_5_1.md",
    detect_income_statement=True,
    multiple_sheets=True
)
```

### Output:
- File: `{input_file}_KetQuaHoatDongKinhDoanh.xlsx`
- Sheet names: `KetQua_1`, `KetQua_2`, ...

## 3. Lưu chuyển Tiền tệ

### File: `utils_markdownLuuChuyenTienTeText_DetectTable_to_xlsx.py`

### Chức năng:
- Phát hiện "báo cáo lưu chuyển tiền tệ" trong văn bản
- Trích xuất các bảng markdown
- Chuyển đổi sang Excel

### Pattern Detection:
```python
patterns = [
    "bao cao luu chuyen tien te",
    "luu chuyen tien te",
    "statement of cash flows",  # Tiếng Anh
    "cash flows"  # Rút gọn
]
```

### Sử dụng:
```python
from utils_markdownLuuChuyenTienTeText_DetectTable_to_xlsx import process_markdown_file_to_xlsx

result_path = process_markdown_file_to_xlsx(
    input_file="BIC_2024_1_5_1.md",
    detect_cash_flow=True,
    multiple_sheets=True
)
```

### Output:
- File: `{input_file}_LuuChuyenTienTe.xlsx`
- Sheet names: `LuuChuyen_1`, `LuuChuyen_2`, ...

## So sánh 3 Modules

| Module | Pattern chính | Tham số detect | Output file suffix |
|--------|---------------|----------------|-------------------|
| CanDoiKeToan | "bang can doi ke toan" | `detect_balance_sheet` | `_CanDoiKeToan.xlsx` |
| KetQuaHoatDongKinhDoanh | "ket qua hoat dong kinh doanh" | `detect_income_statement` | `_KetQuaHoatDongKinhDoanh.xlsx` |
| LuuChuyenTienTe | "luu chuyen tien te" | `detect_cash_flow` | `_LuuChuyenTienTe.xlsx` |

## Dependencies

Tất cả modules đều yêu cầu:
- `pandas` - Xử lý dữ liệu và tạo Excel
- `openpyxl` - Ghi file Excel (.xlsx)
- `utils_markdownTable_to_xlsx` - Module cơ sở để parse và chuyển đổi bảng

## Cài đặt

```bash
pip install pandas openpyxl
```

## Ví dụ sử dụng tổng hợp

```python
from pathlib import Path
from utils_markdownCanDoiKeToanText_DetectTable_to_xlsx import process_markdown_file_to_xlsx as process_balance_sheet
from utils_markdownKetQuaHoatDongKinhDoanhText_DetectTable_to_xlsx import process_markdown_file_to_xlsx as process_income_statement
from utils_markdownLuuChuyenTienTeText_DetectTable_to_xlsx import process_markdown_file_to_xlsx as process_cash_flow

input_file = "BIC_2024_1_5_1.md"

# Xử lý Bảng Cân Đối Kế Toán
try:
    balance_sheet_path = process_balance_sheet(
        input_file=input_file,
        detect_balance_sheet=True,
        multiple_sheets=True
    )
    print(f"Balance sheet: {balance_sheet_path}")
except ValueError as e:
    print(f"Balance sheet not found: {e}")

# Xử lý Kết quả Hoạt động Kinh doanh
try:
    income_statement_path = process_income_statement(
        input_file=input_file,
        detect_income_statement=True,
        multiple_sheets=True
    )
    print(f"Income statement: {income_statement_path}")
except ValueError as e:
    print(f"Income statement not found: {e}")

# Xử lý Lưu chuyển Tiền tệ
try:
    cash_flow_path = process_cash_flow(
        input_file=input_file,
        detect_cash_flow=True,
        multiple_sheets=True
    )
    print(f"Cash flow: {cash_flow_path}")
except ValueError as e:
    print(f"Cash flow not found: {e}")
```

## Notes

1. **Fuzzy Matching**: Tất cả modules sử dụng fuzzy matching với threshold 80% để phát hiện pattern
2. **Multiple Sheets**: Mặc định, tất cả bảng được đặt vào một file Excel với nhiều sheets
3. **Error Handling**: Nếu không tìm thấy pattern, sẽ raise `ValueError` (trừ khi set `detect_*=False`)
4. **Encoding**: Tất cả files đều sử dụng UTF-8 encoding

## Tương lai

Có thể mở rộng thêm:
- Thuyết minh báo cáo tài chính
- Báo cáo tài chính hợp nhất
- Các báo cáo khác theo yêu cầu




