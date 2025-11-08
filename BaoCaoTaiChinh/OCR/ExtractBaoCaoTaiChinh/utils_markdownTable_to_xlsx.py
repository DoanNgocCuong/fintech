"""
Module chuyển đổi bảng Markdown sang file Excel (.xlsx).

Module này cung cấp các hàm tiện ích để:
- Phân tích (parse) bảng định dạng Markdown
- Chuyển đổi bảng Markdown thành file Excel (.xlsx)
- Xử lý các định dạng bảng Markdown chuẩn với dòng phân cách (separator line)

Ví dụ về bảng Markdown:
| Mã số | CHỈ TIÊU | Thuyết minh | Năm nay | Năm trước (trình bày lại) |
| --- | --- | --- | --- | --- |
| 01 | 1. Doanh thu phí bảo hiểm (01 = 01.1 + 01.2 + 01.3) Trong đó: | 22 | 5.524.525.927.458 | 4.744.822.893.543 |
| 01.1 | - Phí bảo hiểm gốc |  | 5.437.581.358.498 | 4.929.987.887.081 |
| 01.2 | - Phí nhận tái bảo hiểm |  | 131.908.616.270 | 155.604.010.559 |
| 01.3 | - Tăng dự phòng phí bảo hiểm gốc và nhận tái bảo hiểm |  | (44.964.047.310) | (340.769.004.097) |
| 02 | 2. Phí nhượng tái bảo hiểm (02 = 02.1 + 02.2) Trong đó: | 23 | (1.535.954.562.964) | (1.390.619.914.418) |
| 02.1 | - Tổng phí nhượng tái bảo hiểm |  | (1.553.762.769.096) | (1.412.773.050.817) |
| 02.2 | - Tăng dự phòng phí nhượng tái bảo hiểm |  | 17.808.206.132 | 22.153.136.399 |
| 03 | 3. Doanh thu phí bảo hiểm thuần (03 = 01 + 02) |  | 3.988.571.364.494 | 3.354.202.979.125 |
| 04 | 4. Hoa hồng nhượng tái bảo hiểm và doanh thu khác hoạt động kinh doanh bảo hiểm (04 = 04.1 + 04.2) Trong đó: |  | 275.673.547.268 | 275.857.414.615 |
| 04.1 | - Hoa hồng nhượng tái bảo hiểm | 24 | 233.236.305.303 | 232.012.916.044 |
| 04.2 | - Doanh thu khác hoạt động kinh doanh bảo hiểm | 25 | 42.437.241.965 | 43.844.498.571 |
| 10 | 5. Doanh thu thuần hoạt động kinh doanh bảo hiểm (10 = 03 + 04) |  | 4.264.244.911.762 | 3.630.060.393.740 |
| 11 | 6. Chi bồi thường (11 = 11.1 + 11.2) Trong đó: |  | (1.298.314.539.639) | (1.067.078.808.068) |
| 11.1 | - Tổng chi bồi thường |  | (1.320.603.226.801) | (1.085.055.560.353) |
| 11.2 | - Các khoản giảm trừ |  | 22.288.687.162 | 17.976.752.285 |
| 12 | 7. Thu bồi thường nhượng tái bảo hiểm |  | 411.316.467.133 | 250.395.047.934 |
| 13 | 8. Tăng dự phòng bồi thường bảo hiểm gốc và nhận tái bảo hiểm |  | (237.722.275.126) | (132.964.379.369) |
| 14 | 9. Tăng dự phòng bồi thường nhượng tái bảo hiểm |  | 190.773.654.293 | 69.430.692.093 |
| 15 | 10. Tổng chi bồi thường bảo hiểm (15 = 11 + 12 + 13 + 14) | 26 | (933.946.693.339) | (880.217.447.410) |
| 16 | 11. Tăng dự phòng dao động lớn | 20.2 | (40.157.289.882) | (36.728.625.484) |

Yêu cầu:
    - pandas: Thư viện xử lý dữ liệu dạng bảng
    - openpyxl: Thư viện ghi file Excel (.xlsx)

Tác giả: Được tạo để xử lý báo cáo tài chính dạng Markdown
Ngày tạo: Module hỗ trợ chuyển đổi bảng báo cáo tài chính từ định dạng Markdown sang Excel
"""

import os
import re
import tempfile
import unicodedata
from pathlib import Path
from typing import List, Optional

try:
    import pandas as pd
except ImportError:
    pd = None


def remove_diacritics(text: str) -> str:
    """
    Loại bỏ dấu tiếng Việt khỏi văn bản.
    
    Args:
        text (str): Văn bản đầu vào có dấu tiếng Việt
        
    Returns:
        str: Văn bản đã loại bỏ dấu
    """
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )


def _is_separator_line(line: str) -> bool:
    """
    Kiểm tra xem một dòng có phải là dòng phân cách trong bảng Markdown hay không.
    
    Dòng phân cách trong bảng Markdown thường có dạng: | --- | --- | --- |
    hoặc | :--- | :---: | ---: | (với căn chỉnh)
    
    Args:
        line (str): Dòng cần kiểm tra
        
    Returns:
        bool: True nếu dòng là dòng phân cách, False nếu không
        
    Ví dụ:
        >>> _is_separator_line("| --- | --- | --- |")
        True
        >>> _is_separator_line("| :---: | :---: |")
        True
        >>> _is_separator_line("| Mã số | CHỈ TIÊU |")
        False
    """
    if not line.startswith('|'):
        return False
    
    # Remove leading and trailing pipes, then split by pipe
    cells = [cell.strip() for cell in line.strip('|').split('|')]
    
    # Check if all cells contain only dashes, spaces, and colons
    # This is the markdown table separator pattern
    for cell in cells:
        # Remove all dashes, spaces, and colons
        remaining = re.sub(r'[\s\-:]+', '', cell)
        # If there's anything left, it's not a separator
        if remaining:
            return False
    
    # If all cells are empty or only contain dashes/spaces/colons, it's a separator
    return True


def _parse_markdown_table(markdown_table: str) -> List[List[str]]:
    """
    Phân tích chuỗi bảng Markdown thành danh sách các dòng dữ liệu.
    
    Hàm này sẽ:
    - Bỏ qua các dòng trống
    - Bỏ qua các dòng phân cách (separator lines)
    - Chỉ xử lý các dòng bắt đầu bằng ký tự '|'
    - Tách các ô trong mỗi dòng bằng ký tự '|'
    
    Args:
        markdown_table (str): Chuỗi chứa bảng định dạng Markdown
        
    Returns:
        List[List[str]]: Danh sách các dòng, mỗi dòng là danh sách các ô (cells)
                        Dòng đầu tiên thường là header
        
    Ví dụ:
        >>> table = "| Col1 | Col2 |\\n| --- | --- |\\n| A | B |"
        >>> rows = _parse_markdown_table(table)
        >>> print(rows)
        [['Col1', 'Col2'], ['A', 'B']]
    """
    lines = markdown_table.strip().split('\n')
    rows = []
    
    for line in lines:
        line = line.strip()
        # Skip empty lines
        if not line:
            continue
            
        # Skip separator lines (e.g., | --- | --- | or | ------- |)
        if _is_separator_line(line):
            continue
            
        # Skip lines that don't start with |
        if not line.startswith('|'):
            continue
            
        # Remove leading and trailing pipes, then split by pipe
        cells = [cell.strip() for cell in line.strip('|').split('|')]
        
        # Only add non-empty rows
        if cells and any(cell for cell in cells):
            rows.append(cells)
    
    return rows


def _normalize_row_columns(row: List[str], target_length: int) -> List[str]:
    """
    Chuẩn hóa số cột của một dòng về độ dài mục tiêu.
    
    Nếu dòng có ít cột hơn: thêm các ô trống
    Nếu dòng có nhiều cột hơn: cắt bớt các cột thừa
    
    Args:
        row (List[str]): Dòng cần chuẩn hóa
        target_length (int): Độ dài mục tiêu (số cột)
        
    Returns:
        List[str]: Dòng đã được chuẩn hóa
        
    Ví dụ:
        >>> _normalize_row_columns(['A', 'B', 'C'], 2)
        ['A', 'B']
        >>> _normalize_row_columns(['A'], 3)
        ['A', '', '']
    """
    if len(row) < target_length:
        # Thêm các ô trống nếu thiếu cột
        return row + [''] * (target_length - len(row))
    elif len(row) > target_length:
        # Cắt bớt nếu thừa cột
        return row[:target_length]
    else:
        return row


def _normalize_headers(headers: List[str]) -> List[str]:
    """
    Chuẩn hóa header, thay thế các header trống bằng tên mặc định.
    
    Args:
        headers (List[str]): Danh sách header
        
    Returns:
        List[str]: Danh sách header đã được chuẩn hóa
        
    Ví dụ:
        >>> _normalize_headers(['Col1', '', 'Col3'])
        ['Col1', 'Column_2', 'Col3']
    """
    normalized = []
    for idx, header in enumerate(headers):
        if not header or not header.strip():
            # Tạo tên cột mặc định nếu header trống
            normalized.append(f"Column_{idx + 1}")
        else:
            normalized.append(header.strip())
    return normalized


def _create_dataframe_from_rows(rows: List[List[str]]) -> pd.DataFrame:
    """
    Tạo pandas DataFrame từ danh sách các dòng đã được phân tích.
    
    Hàm này sẽ:
    - Lấy dòng đầu tiên làm tiêu đề cột (header)
    - Chuẩn hóa header (thay thế header trống)
    - Chuẩn hóa số cột của các dòng dữ liệu về cùng số cột với header
    - Tạo DataFrame với các cột tương ứng
    
    Args:
        rows (List[List[str]]): Danh sách các dòng, dòng đầu tiên là header
        
    Returns:
        pd.DataFrame: DataFrame chứa dữ liệu từ bảng Markdown
        
    Raises:
        ValueError: Nếu danh sách rows rỗng hoặc không có dữ liệu
        
    Ví dụ:
        >>> rows = [['Mã số', 'CHỈ TIÊU'], ['01', 'Doanh thu'], ['02', 'Chi phí']]
        >>> df = _create_dataframe_from_rows(rows)
        >>> print(df.columns.tolist())
        ['Mã số', 'CHỈ TIÊU']
        
    Edge Cases Handled:
        - Số cột không đều: Chuẩn hóa về số cột của header
        - Header trống: Thay thế bằng tên cột mặc định (Column_1, Column_2, ...)
    """
    if not rows:
        raise ValueError("No rows found in markdown table")
    
    # First row is header
    headers = rows[0]
    
    # Normalize headers (replace empty headers with default names)
    headers = _normalize_headers(headers)
    
    # Determine target number of columns from header
    num_columns = len(headers)
    
    # Remaining rows are data
    data_rows = rows[1:] if len(rows) > 1 else []
    
    # Normalize all data rows to have the same number of columns as header
    normalized_data_rows = [
        _normalize_row_columns(row, num_columns)
        for row in data_rows
    ]
    
    # Create DataFrame
    df = pd.DataFrame(normalized_data_rows, columns=headers)
    
    return df


def markdownTable_to_xlsx(
    markdown_table: str, 
    output_path: Optional[str] = None,
    sheet_name: str = "Sheet1"
) -> str:
    """
    Chuyển đổi bảng Markdown sang file Excel (.xlsx).
    
    Đây là hàm chính của module, thực hiện toàn bộ quy trình:
    1. Phân tích chuỗi bảng Markdown
    2. Tạo pandas DataFrame từ dữ liệu đã phân tích
    3. Ghi DataFrame ra file Excel (.xlsx)
    
    Args:
        markdown_table (str): Chuỗi chứa bảng định dạng Markdown
        output_path (Optional[str]): Đường dẫn file output. 
                                    Nếu None, sẽ tạo đường dẫn file tạm thời
        sheet_name (str): Tên sheet trong file Excel (mặc định: "Sheet1")
        
    Returns:
        str: Đường dẫn đến file Excel đã được tạo
        
    Raises:
        ValueError: Nếu bảng Markdown rỗng hoặc không hợp lệ
        ImportError: Nếu pandas hoặc openpyxl chưa được cài đặt
        
    Ví dụ:
        >>> table = \"\"\"
        ... | Mã số | CHỈ TIÊU | Năm nay |
        ... | --- | --- | --- |
        ... | 01 | Doanh thu | 1000000 |
        ... | 02 | Chi phí | 500000 |
        ... \"\"\"
        >>> path = markdownTable_to_xlsx(table, "baocao.xlsx", sheet_name="Báo cáo")
        >>> print(f"Đã lưu file: {path}")
        Đã lưu file: baocao.xlsx
        
    Lưu ý:
        - Cần cài đặt: pip install pandas openpyxl
        - File Excel sẽ được tạo với encoding UTF-8
        - Nếu thư mục chứa file output chưa tồn tại, sẽ được tạo tự động
    """
    # Check if pandas is available
    if pd is None:
        raise ImportError(
            "pandas is required. Install it with: pip install pandas openpyxl"
        )
    
    # Parse markdown table
    rows = _parse_markdown_table(markdown_table)
    
    if not rows:
        raise ValueError("No valid table data found in markdown table")
    
    # Create DataFrame
    df = _create_dataframe_from_rows(rows)
    
    # Generate output path if not provided
    if output_path is None:
        output_path = os.path.join(
            tempfile.gettempdir(), 
            f"markdown_table_{os.getpid()}.xlsx"
        )
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Save to Excel
    df.to_excel(
        output_path, 
        index=False, 
        sheet_name=sheet_name,
        engine='openpyxl'
    )
    
    return output_path


def extract_markdown_tables(text: str) -> List[str]:
    """
    Trích xuất tất cả các bảng markdown từ văn bản.
    
    Một bảng được định nghĩa là các dòng liên tiếp bắt đầu bằng '|' 
    (không bao gồm dòng separator như | --- | --- |).
    
    Args:
        text (str): Văn bản chứa các bảng markdown
        
    Returns:
        List[str]: Danh sách các chuỗi bảng (mỗi bảng là một chuỗi nhiều dòng)
    """
    lines = text.split('\n')
    tables = []
    current_table_lines = []
    in_table = False
    
    for line in lines:
        stripped = line.strip()
        
        # Check if line is part of a table
        if stripped.startswith('|'):
            # Check if it's a separator line
            if _is_separator_line(stripped):
                # Add separator to current table if we're in a table
                if in_table:
                    current_table_lines.append(line)
                continue
            
            # Start or continue table
            if not in_table:
                in_table = True
                current_table_lines = []
            
            current_table_lines.append(line)
        else:
            # End of table
            if in_table and current_table_lines:
                # Only add table if it has at least header + 1 data row
                table_text = '\n'.join(current_table_lines)
                rows = _parse_markdown_table(table_text)
                
                if len(rows) >= 2:  # At least header + 1 data row
                    tables.append(table_text)
                
                current_table_lines = []
                in_table = False
    
    # Handle table at end of text
    if in_table and current_table_lines:
        table_text = '\n'.join(current_table_lines)
        rows = _parse_markdown_table(table_text)
        if len(rows) >= 2:
            tables.append(table_text)
    
    return tables


def main():
    """
    Hàm chính để chuyển đổi bảng Markdown từ file sang file Excel.
    
    Hàm này thực hiện:
    1. Đọc file markdownTableExample.md từ thư mục hiện tại
    2. Phân tích nội dung bảng Markdown
    3. Chuyển đổi sang file Excel với tên Example1_MarkdownTable.xlsx
    4. Hiển thị thông tin về số dòng và số cột đã chuyển đổi
    
    File đầu vào:
        - markdownTableExample.md: File chứa bảng Markdown cần chuyển đổi
        
    File đầu ra:
        - Example1_MarkdownTable.xlsx: File Excel chứa dữ liệu đã chuyển đổi
        - Sheet name: "Bảng Cân Đối"
        
    Raises:
        FileNotFoundError: Nếu không tìm thấy file markdownTableExample.md
        
    Ví dụ sử dụng:
        python utils_markdownTable_to_xlsx.py
    """
    # Get the directory of the current file
    current_dir = Path(__file__).parent
    
    # Path to the markdown file
    markdown_file_path = current_dir / "Example1_test.md"
    
    # Check if file exists
    if not markdown_file_path.exists():
        raise FileNotFoundError(
            f"Markdown file not found: {markdown_file_path}"
        )
    
    # Read markdown table from file
    print(f"Reading markdown table from: {markdown_file_path}")
    with open(markdown_file_path, 'r', encoding='utf-8') as f:
        markdown_table = f.read()
    
    # Generate output path (same directory, with .xlsx extension)
    output_path = current_dir / "Example1_MarkdownTable.xlsx"
    
    # Convert to Excel
    print(f"Converting to Excel...")
    result_path = markdownTable_to_xlsx(
        markdown_table, 
        output_path=str(output_path),
        sheet_name="Bảng Cân Đối"
    )
    
    # Count rows for information
    rows = _parse_markdown_table(markdown_table)
    row_count = len(rows) - 1 if len(rows) > 1 else 0  # Exclude header
    
    print(f"Successfully saved to: {result_path}")
    print(f"   Total rows (excluding header): {row_count}")
    print(f"   Total columns: {len(rows[0]) if rows else 0}")

if __name__ == "__main__":
    main()