"""
Module phát hiện "Báo cáo Kết quả hoạt động kinh doanh" và chuyển đổi bảng sang Excel.

MÔ TẢ:
-------
Module này thực hiện 3 bước đơn giản:
1. Phát hiện "báo cáo kết quả hoạt động kinh doanh" trong văn bản (fuzzy matching 80%)
2. Trích xuất tất cả các bảng markdown từ văn bản
3. Chuyển đổi các bảng sang file Excel (.xlsx)

CHỨC NĂNG:
----------
- detect_ketquahoedongkinhdoanh(): Phát hiện "báo cáo kết quả hoạt động kinh doanh" (fuzzy 80%)
- process_markdown_file_to_xlsx(): Xử lý file markdown và chuyển đổi sang Excel

YÊU CẦU:
--------
- pandas: Để xử lý dữ liệu và tạo Excel
- openpyxl: Để ghi file Excel (.xlsx)

CÀI ĐẶT:
---------
    pip install pandas openpyxl
"""

from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional

# Import functions from utils_markdownTable_to_xlsx
from utils_markdownTable_to_xlsx import (
    markdownTable_to_xlsx,
    extract_markdown_tables,
    remove_diacritics,
    _parse_markdown_table,
    _create_dataframe_from_rows,
    _is_separator_line
)


def _remove_markdown_tables(text: str) -> str:
    """
    Loại bỏ tất cả các bảng markdown khỏi văn bản, chỉ giữ lại phần text thông thường.
    
    Hàm này giúp tránh false positive khi check các từ khóa trong bảng markdown.
    Ví dụ: Tránh match "hoạt động kinh doanh" trong bảng "Lưu chuyển tiền từ hoạt động kinh doanh"
    với "kết quả hoạt động kinh doanh".
    
    Args:
        text (str): Văn bản chứa các bảng markdown
        
    Returns:
        str: Văn bản đã loại bỏ các bảng markdown
    """
    lines = text.split('\n')
    result_lines = []
    in_table = False
    
    for line in lines:
        stripped = line.strip()
        
        # Check if line is part of a table
        if stripped.startswith('|'):
            # Check if it's a separator line
            if _is_separator_line(stripped):
                # Skip separator line
                in_table = True
                continue
            
            # This is a table row, skip it
            in_table = True
            continue
        else:
            # End of table or regular text
            in_table = False
            result_lines.append(line)
    
    return '\n'.join(result_lines)


def detect_ketquahoedongkinhdoanh(text: str, threshold: float = 0.8) -> bool:
    """
    Phát hiện xem văn bản có chứa "báo cáo kết quả hoạt động kinh doanh" hay không.
    
    Logic:
    1. Loại bỏ tất cả các bảng markdown khỏi văn bản (chỉ check trong text thông thường)
    2. Loại trừ các pattern liên quan đến "lưu chuyển tiền tệ" hoặc "cash flow"
    3. Lowercase toàn bộ văn bản
    4. Loại bỏ dấu tiếng Việt
    5. So khớp fuzzy 80% với "bao cao ket qua hoat dong kinh doanh"
    
    Lưu ý:
        Hàm này KHÔNG tìm kiếm trong các bảng markdown, chỉ tìm trong phần text thông thường.
        Điều này giúp tránh false positive khi "hoạt động kinh doanh" xuất hiện trong bảng
        của "Báo cáo lưu chuyển tiền tệ" (ví dụ: "Lưu chuyển tiền từ hoạt động kinh doanh").
        Nếu trang có chứa "lưu chuyển tiền tệ" hoặc "cash flow", sẽ không match với "kết quả hoạt động kinh doanh".
    
    Args:
        text (str): Văn bản cần kiểm tra
        threshold (float): Ngưỡng so khớp (mặc định: 0.8 = 80%)
        
    Returns:
        bool: True nếu tìm thấy "báo cáo kết quả hoạt động kinh doanh", False nếu không
        
    Ví dụ:
        >>> detect_ketquahoedongkinhdoanh("BÁO CÁO KẾT QUẢ HOẠT ĐỘNG KINH DOANH")  # True
        >>> detect_ketquahoedongkinhdoanh("BAO CAO KET QUA HOAT DONG KINH DOANH")   # True
        >>> detect_ketquahoedongkinhdoanh("Kết quả hoạt động kinh doanh")           # True
        >>> detect_ketquahoedongkinhdoanh("BÁO CÁO LƯU CHUYỂN TIỀN TỆ")            # False
        >>> detect_ketquahoedongkinhdoanh("Lưu chuyển tiền từ hoạt động kinh doanh") # False (trong bảng)
        >>> detect_ketquahoedongkinhdoanh("Không có gì")                            # False
    """
    # Bước 1: Loại bỏ tất cả các bảng markdown (chỉ check trong text thông thường)
    text_without_tables = _remove_markdown_tables(text)
    
    # Bước 2: Loại trừ các pattern liên quan đến "lưu chuyển tiền tệ" hoặc "cash flow"
    # Nếu trang có chứa "lưu chuyển tiền tệ" hoặc "cash flow", không phải "kết quả hoạt động kinh doanh"
    text_lower = text_without_tables.lower()
    text_khong_dau = remove_diacritics(text_lower)
    
    # Kiểm tra xem có phải là "lưu chuyển tiền tệ" không
    cash_flow_patterns = [
        "luu chuyen tien te",
        "bao cao luu chuyen tien te",
        "cash flow",
        "statement of cash flows"
    ]
    
    for cash_flow_pattern in cash_flow_patterns:
        if cash_flow_pattern in text_khong_dau:
            # Đây là báo cáo lưu chuyển tiền tệ, không phải kết quả hoạt động kinh doanh
            return False
    
    # Bước 3: Kiểm tra các pattern của "kết quả hoạt động kinh doanh"
    # Pattern chuẩn để so khớp (các biến thể) - PHẢI có "ket qua" trong pattern
    patterns = [
        "bao cao ket qua hoat dong kinh doanh",
        "ket qua hoat dong kinh doanh",
        "bao cao ket qua kinh doanh"
    ]
    
    # Kiểm tra từng pattern
    for pattern in patterns:
        # Kiểm tra nếu pattern xuất hiện trực tiếp
        if pattern in text_khong_dau:
            return True
        
        # Fuzzy matching: tìm cụm từ có độ dài tương tự và so khớp
        words = text_khong_dau.split()
        pattern_words = pattern.split()
        
        if len(pattern_words) > len(words):
            continue
        
        for i in range(len(words) - len(pattern_words) + 1):
            candidate = ' '.join(words[i:i+len(pattern_words)])
            similarity = SequenceMatcher(None, pattern, candidate).ratio()
            
            if similarity >= threshold:
                return True
    
    return False


def process_markdown_file_to_xlsx(
    input_file: str,
    output_file: Optional[str] = None,
    detect_income_statement: bool = True,
    multiple_sheets: bool = True
) -> str:
    """
    Xử lý file markdown: phát hiện báo cáo kết quả hoạt động kinh doanh, trích xuất bảng và chuyển đổi sang Excel.
    
    Quy trình:
    1. Đọc file markdown
    2. Phát hiện "báo cáo kết quả hoạt động kinh doanh" (nếu detect_income_statement=True)
    3. Trích xuất tất cả các bảng markdown
    4. Chuyển đổi sang file Excel
    
    Args:
        input_file (str): Đường dẫn đến file markdown đầu vào
        output_file (Optional[str]): Đường dẫn đến file Excel đầu ra (tùy chọn).
                                    Nếu None, tự động tạo tên file dựa trên input_file
        detect_income_statement (bool): Nếu True, chỉ xử lý nếu phát hiện "báo cáo kết quả hoạt động kinh doanh".
                                       Nếu False, xử lý tất cả các bảng trong file
        multiple_sheets (bool): Nếu True, đặt tất cả bảng vào một file với nhiều sheets.
                                Nếu False, tạo file riêng cho mỗi bảng
        
    Returns:
        str: Đường dẫn đến file Excel đã tạo
        
    Raises:
        FileNotFoundError: Nếu file đầu vào không tồn tại
        ValueError: Nếu không phát hiện báo cáo kết quả hoạt động kinh doanh (khi detect_income_statement=True)
                   hoặc không tìm thấy bảng markdown nào trong file
    """
    input_path = Path(input_file)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Bước 1: Đọc file
    print(f"Reading file: {input_file}")
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Bước 2: Phát hiện "báo cáo kết quả hoạt động kinh doanh" (nếu cần)
    if detect_income_statement:
        print("Detecting 'Bao Cao Ket Qua Hoat Dong Kinh Doanh'...")
        if not detect_ketquahoedongkinhdoanh(content):
            raise ValueError(
                "File does not contain 'Bao Cao Ket Qua Hoat Dong Kinh Doanh'. "
                "Set detect_income_statement=False to process anyway."
            )
        print("Income statement detected!")
    
    # Bước 3: Trích xuất tất cả các bảng markdown
    print("Extracting markdown tables...")
    tables = extract_markdown_tables(content)
    print(f"  Found {len(tables)} table(s)")
    
    if not tables:
        raise ValueError("No markdown tables found in file")
    
    # Bước 4: Chuyển đổi sang Excel
    if output_file is None:
        output_file = str(input_path.parent / f"{input_path.stem}_KetQuaHoatDongKinhDoanh.xlsx")
    
    print(f"Converting to Excel: {output_file}")
    
    if multiple_sheets:
        # Tạo một file Excel với nhiều sheets
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("pandas is required. Install with: pip install pandas openpyxl")
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with pd.ExcelWriter(str(output_path), engine='openpyxl') as writer:
            for idx, table_text in enumerate(tables, 1):
                # Parse table
                rows = _parse_markdown_table(table_text)
                if not rows or len(rows) < 2:
                    continue
                
                # Create DataFrame
                df = _create_dataframe_from_rows(rows)
                
                # Sheet name (Excel has 31 char limit)
                sheet_name = f"KetQua_{idx}"[:31]
                
                # Write to sheet
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        result_path = str(output_path)
    else:
        # Tạo file riêng cho mỗi bảng
        output_files = []
        base_path = Path(output_file).parent / Path(output_file).stem
        
        for idx, table_text in enumerate(tables, 1):
            table_output_path = f"{base_path}_table_{idx}.xlsx"
            markdownTable_to_xlsx(
                table_text,
                output_path=table_output_path,
                sheet_name="KetQua"
            )
            output_files.append(table_output_path)
        
        result_path = output_files[0] if output_files else output_file
    
    print(f"Successfully saved to: {result_path}")
    return result_path


def main():
    """
    Hàm chính để xử lý file markdown và chuyển đổi bảng sang Excel.
    """
    input_file = Path(__file__).parent / "Example2_MarkdownKetQuaHoatDongKinhDoanh.md"
    
    try:
        result_path = process_markdown_file_to_xlsx(
            input_file=str(input_file),
            detect_income_statement=True,
            multiple_sheets=True
        )
        print(f"\nDone! Output file: {result_path}")
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()

