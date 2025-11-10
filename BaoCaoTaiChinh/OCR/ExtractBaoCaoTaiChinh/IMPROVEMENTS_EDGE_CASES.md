# Cải thiện xử lý Edge Cases cho utils_markdownTable_to_xlsx.py

## Tổng quan

Module `utils_markdownTable_to_xlsx.py` đã được cải thiện để xử lý tốt hơn các edge cases khi chuyển đổi bảng Markdown sang Excel.

## Các Edge Cases đã được xử lý

### ✅ 1. Bảng có số cột không đều giữa các dòng

**Vấn đề:**
- Một số dòng có nhiều cột hơn header
- Một số dòng có ít cột hơn header
- Gây lỗi khi tạo DataFrame

**Giải pháp:**
- Thêm hàm `_normalize_row_columns()` để chuẩn hóa số cột
- Dòng thừa cột: Cắt bớt các cột thừa
- Dòng thiếu cột: Thêm các ô trống

**Ví dụ:**
```markdown
| Col1 | Col2 |
| --- | --- |
| A | B | C |  ← Thừa cột, sẽ bị cắt thành ['A', 'B']
| D |  ← Thiếu cột, sẽ được thêm thành ['D', '']
```

### ✅ 2. Header trống hoặc không có header

**Vấn đề:**
- Header có thể chứa các ô trống
- Gây lỗi khi tạo DataFrame với tên cột rỗng

**Giải pháp:**
- Thêm hàm `_normalize_headers()` để chuẩn hóa header
- Thay thế header trống bằng tên mặc định: `Column_1`, `Column_2`, ...

**Ví dụ:**
```markdown
| Col1 |  | Col3 |
| --- | --- | --- |
| A | B | C |
```
Header trống sẽ được thay thế thành: `['Col1', 'Column_2', 'Col3']`

### ✅ 3. Bảng có nhiều dòng separator liên tiếp

**Vấn đề:**
- Nhiều dòng separator có thể xuất hiện trong bảng
- Gây nhầm lẫn khi parse

**Giải pháp:**
- Hàm `_is_separator_line()` đã xử lý tốt
- Tất cả separator lines đều bị bỏ qua

**Ví dụ:**
```markdown
| Col1 | Col2 |
| --- | --- |
| --- | --- |  ← Separator thứ 2, bị bỏ qua
| A | B |
```

### ✅ 4. Ô có khoảng trắng thừa

**Vấn đề:**
- Các ô có thể chứa khoảng trắng thừa ở đầu/cuối
- Gây khó khăn khi xử lý dữ liệu

**Giải pháp:**
- Sử dụng `.strip()` cho mỗi cell khi parse
- Loại bỏ các ô trống ở đầu/cuối dòng (artifacts từ parsing)

**Ví dụ:**
```markdown
|  Col1  |  Col2  |
|  ---  |  ---  |
|  A  |  B  |
```
Tất cả khoảng trắng thừa sẽ được loại bỏ.

### ✅ 5. Bảng không có separator line

**Vấn đề:**
- Một số bảng Markdown không có separator line
- Code cần xử lý được cả hai trường hợp

**Giải pháp:**
- Code đã xử lý tốt: separator line là optional
- Nếu không có separator, vẫn parse bình thường

**Ví dụ:**
```markdown
| Col1 | Col2 |
| A | B |
```
Vẫn parse được bình thường.

### ✅ 6. Bảng có dòng trống

**Vấn đề:**
- Các dòng trống có thể xuất hiện giữa các dòng dữ liệu
- Gây nhầm lẫn khi parse

**Giải pháp:**
- Tất cả dòng trống đều bị bỏ qua

**Ví dụ:**
```markdown
| Col1 | Col2 |

| --- | --- |

| A | B |
```
Các dòng trống sẽ bị bỏ qua.

### ⚠️ 7. Ô chứa ký tự pipe (|) trong nội dung

**Vấn đề:**
- Markdown table standard không hỗ trợ escape pipe trong cells
- Ký tự `|` trong nội dung sẽ bị tách thành nhiều cột

**Giải pháp hiện tại:**
- Code sẽ parse pipe trong nội dung như delimiter bình thường
- Đây là giới hạn của định dạng Markdown table chuẩn
- **Lưu ý:** Nếu cần xử lý pipe trong nội dung, cần sử dụng format khác (ví dụ: HTML table)

**Ví dụ:**
```markdown
| Name | Description |
| --- | --- |
| Test | Value | with | pipe |
```
Sẽ được parse thành: `['Test', 'Value', 'with', 'pipe']` (4 cột thay vì 2)

**Khuyến nghị:**
- Tránh sử dụng ký tự `|` trong nội dung ô
- Nếu cần, thay thế bằng ký tự khác hoặc sử dụng format khác

## Các hàm mới được thêm

### `_normalize_row_columns(row: List[str], target_length: int) -> List[str]`

Chuẩn hóa số cột của một dòng về độ dài mục tiêu.

**Tham số:**
- `row`: Dòng cần chuẩn hóa
- `target_length`: Độ dài mục tiêu (số cột)

**Trả về:**
- Dòng đã được chuẩn hóa

**Ví dụ:**
```python
_normalize_row_columns(['A', 'B', 'C'], 2)  # ['A', 'B']
_normalize_row_columns(['A'], 3)  # ['A', '', '']
```

### `_normalize_headers(headers: List[str]) -> List[str]`

Chuẩn hóa header, thay thế các header trống bằng tên mặc định.

**Tham số:**
- `headers`: Danh sách header

**Trả về:**
- Danh sách header đã được chuẩn hóa

**Ví dụ:**
```python
_normalize_headers(['Col1', '', 'Col3'])  # ['Col1', 'Column_2', 'Col3']
```

## Các hàm đã được cải thiện

### `_parse_markdown_table(markdown_table: str) -> List[List[str]]`

**Cải thiện:**
- Loại bỏ các ô trống ở đầu/cuối dòng (artifacts từ parsing)
- Cải thiện documentation về edge cases
- Thêm lưu ý về pipe trong nội dung

### `_create_dataframe_from_rows(rows: List[List[str]]) -> pd.DataFrame`

**Cải thiện:**
- Chuẩn hóa header (thay thế header trống)
- Chuẩn hóa số cột của tất cả dòng dữ liệu về số cột của header
- Xử lý tốt các trường hợp số cột không đều

## Test Cases

Đã tạo file `test_utils_markdownTable_to_xlsx.py` với 23 test cases:

- ✅ Test separator line (3 tests)
- ✅ Test parse markdown table (10 tests)
- ✅ Test create dataframe (5 tests)
- ✅ Test markdown to xlsx conversion (5 tests)

**Kết quả:** Tất cả 23 test cases đều PASS ✅

## Backward Compatibility

Tất cả các cải thiện đều **backward compatible**:
- Code cũ vẫn hoạt động bình thường
- Chỉ thêm xử lý cho các edge cases
- Không thay đổi behavior cho các trường hợp chuẩn

## Kết luận

Module `utils_markdownTable_to_xlsx.py` hiện tại đã xử lý được:
- ✅ Bảng có số cột không đều
- ✅ Header trống
- ✅ Nhiều separator liên tiếp
- ✅ Khoảng trắng thừa
- ✅ Bảng không có separator
- ✅ Dòng trống
- ⚠️ Pipe trong nội dung (giới hạn của Markdown standard)

Code đã robust hơn và có thể xử lý được hầu hết các edge cases thường gặp trong thực tế.




