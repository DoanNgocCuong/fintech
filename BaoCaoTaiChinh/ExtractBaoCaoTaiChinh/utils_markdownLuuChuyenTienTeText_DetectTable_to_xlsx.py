"""
Module phát hiện "Báo cáo Lưu chuyển tiền tệ" và chuyển đổi bảng sang Excel.

MÔ TẢ:
-------
Module này thực hiện 3 bước đơn giản:
1. Phát hiện "báo cáo lưu chuyển tiền tệ" trong văn bản (fuzzy matching 80%)
2. Trích xuất tất cả các bảng markdown từ văn bản
3. Chuyển đổi các bảng sang file Excel (.xlsx)

CHỨC NĂNG:
----------
- detect_luuchuyentiente(): Phát hiện "báo cáo lưu chuyển tiền tệ" (fuzzy 80%)
- process_markdown_file_to_xlsx(): Xử lý file markdown và chuyển đổi sang Excel

YÊU CẦU:
--------
- pandas: Để xử lý dữ liệu và tạo Excel
- openpyxl: Để ghi file Excel (.xlsx)

CÀI ĐẶT:
---------
    pip install pandas openpyxl
"""

import re
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


def _create_compact(text: str) -> str:
    """
    Tạo phiên bản compact của text: lowercase, loại bỏ dấu, loại bỏ khoảng trắng và ký tự đặc biệt.
    Chỉ giữ lại các chữ cái (a-z).
    
    Thuật toán:
    - Lowercase text
    - Loại bỏ dấu tiếng Việt
    - Loại bỏ tất cả khoảng trắng và ký tự đặc biệt
    - Chỉ giữ lại chữ cái (a-z)
    
    Args:
        text (str): Văn bản cần compact hóa
        
    Returns:
        str: Text đã được compact (chỉ chữ cái, không dấu, không khoảng trắng)
        
    Ví dụ:
        >>> _create_compact("LƯU CHUYỂN TIỀN TỆ")
        'luuchuyentiente'
        >>> _create_compact("LUU CHUYEN TIEN TE")
        'luuchuyentiente'
    """
    # Lowercase và loại bỏ dấu
    text_lower = text.lower()
    text_khong_dau = remove_diacritics(text_lower)
    
    # Loại bỏ tất cả khoảng trắng và ký tự đặc biệt, chỉ giữ chữ cái
    compact = re.sub(r'[^a-z]', '', text_khong_dau)
    
    return compact


def _remove_markdown_tables(text: str) -> str:
    """
    Loại bỏ tất cả các bảng markdown khỏi văn bản, chỉ giữ lại phần text thông thường.
    
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


def detect_luuchuyentiente(text: str, threshold: float = 0.8) -> bool:
    """
    Phát hiện xem văn bản có chứa "báo cáo lưu chuyển tiền tệ" hay không.
    
    Logic sử dụng thuật toán: score = ratio(compact, REFERENCE) với sliding window
    
    1. Loại bỏ tất cả các bảng markdown khỏi văn bản (chỉ check trong text thông thường)
    2. Loại trừ các pattern liên quan đến "kết quả hoạt động kinh doanh" hoặc "bảng cân đối kế toán"
    3. Tạo compact version của text: lowercase, loại bỏ dấu, loại bỏ khoảng trắng, chỉ giữ chữ cái
    4. Tạo compact version của pattern REFERENCE
    5. Kiểm tra exact match: nếu reference xuất hiện trực tiếp trong compact text
    6. So khớp fuzzy theo character-level: sử dụng sliding window để tìm pattern ở bất kỳ đâu trong text
    7. Tính score = ratio(candidate, REFERENCE) và so sánh với threshold (mặc định 0.8 = 80%)
    
    Lưu ý:
        Hàm này KHÔNG tìm kiếm trong các bảng markdown, chỉ tìm trong phần text thông thường.
        Điều này giúp tránh false positive khi "lưu chuyển tiền tệ" xuất hiện trong dữ liệu bảng khác.
        Nếu trang có chứa "kết quả hoạt động kinh doanh" hoặc "bảng cân đối kế toán", 
        sẽ không match với "lưu chuyển tiền tệ".
    
    Args:
        text (str): Văn bản cần kiểm tra
        threshold (float): Ngưỡng so khớp (mặc định: 0.8 = 80%)
        
    Returns:
        bool: True nếu tìm thấy "báo cáo lưu chuyển tiền tệ", False nếu không
        
    Ví dụ:
        >>> detect_luuchuyentiente("BÁO CÁO LƯU CHUYỂN TIỀN TỆ")  # True
        >>> detect_luuchuyentiente("BAO CAO LUU CHUYEN TIEN TE")   # True
        >>> detect_luuchuyentiente("Lưu chuyển tiền tệ")           # True
        >>> detect_luuchuyentiente("Statement of cash flows")       # True (có thể)
        >>> detect_luuchuyentiente("BÁO CÁO KẾT QUẢ HOẠT ĐỘNG KINH DOANH")  # False
        >>> detect_luuchuyentiente("BẢNG CÂN ĐỐI KẾ TOÁN")  # False
        >>> detect_luuchuyentiente("Không có gì")                   # False
    """
    # Bước 1: Loại bỏ tất cả các bảng markdown
    text_without_tables = _remove_markdown_tables(text)
    
    # Bước 2: Loại trừ các pattern liên quan đến các báo cáo tài chính khác
    # Nếu trang có chứa "kết quả hoạt động kinh doanh" hoặc "bảng cân đối kế toán",
    # không phải "lưu chuyển tiền tệ"
    text_lower = text_without_tables.lower()
    text_khong_dau = remove_diacritics(text_lower)
    
    # Kiểm tra xem có phải là các báo cáo tài chính khác không
    other_statements_patterns = [
        "ket qua hoat dong kinh doanh",
        "bao cao ket qua hoat dong kinh doanh",
        "bang can doi ke toan",
        "income statement",
        "balance sheet"
    ]
    
    for other_pattern in other_statements_patterns:
        if other_pattern in text_khong_dau:
            # Đây là báo cáo tài chính khác, không phải lưu chuyển tiền tệ
            return False
    
    # Bước 3: Tạo compact version của text
    text_compact = _create_compact(text_without_tables)
    
    # Bước 4: Kiểm tra các pattern của "lưu chuyển tiền tệ"
    # Pattern chuẩn để so khớp (các biến thể)
    patterns = [
        "bao cao luu chuyen tien te",
        "luu chuyen tien te",
        "statement of cash flows",  # Tiếng Anh
        "cash flows"  # Rút gọn
    ]
    
    # Kiểm tra từng pattern
    for pattern in patterns:
        # Tạo compact version của pattern
        pattern_compact = _create_compact(pattern)
        
        # Kiểm tra nếu pattern xuất hiện trực tiếp trong compact text (exact match)
        if pattern_compact in text_compact:
            return True
        
        # Bước 5: So khớp fuzzy theo character-level - sử dụng sliding window
        # Sử dụng thuật toán: score = ratio(candidate, REFERENCE)
        # 
        # Sử dụng hàm có sẵn: SequenceMatcher.ratio() từ difflib (Python standard library)
        # - ratio() trả về giá trị 0.0 - 1.0 (tương đương 0% - 100%)
        # - Không cần chia 100 vì ratio() đã trả về 0-1
        #
        # Sliding window: Dịch chuyển cửa sổ qua text_compact để tìm cụm có độ dài bằng pattern
        ref_len = len(pattern_compact)
        text_len = len(text_compact)
        
        # Nếu text ngắn hơn pattern, không thể match
        if text_len < ref_len:
            continue
        
        # Dịch chuyển cửa sổ (sliding window) qua text_compact
        # Tìm cụm có độ dài bằng pattern_compact và tính similarity score
        for i in range(text_len - ref_len + 1):
            candidate_compact = text_compact[i:i + ref_len]
            # Sử dụng hàm có sẵn: SequenceMatcher.ratio() từ difflib
            score = SequenceMatcher(None, pattern_compact, candidate_compact).ratio()
            
            if score >= threshold:
                return True
    
    return False


def process_markdown_file_to_xlsx(
    input_file: str,
    output_file: Optional[str] = None,
    detect_cash_flow: bool = True,
    multiple_sheets: bool = True
) -> str:
    """
    Xử lý file markdown: phát hiện báo cáo lưu chuyển tiền tệ, trích xuất bảng và chuyển đổi sang Excel.
    
    Quy trình:
    1. Đọc file markdown
    2. Phát hiện "báo cáo lưu chuyển tiền tệ" (nếu detect_cash_flow=True)
    3. Trích xuất tất cả các bảng markdown
    4. Chuyển đổi sang file Excel
    
    Args:
        input_file (str): Đường dẫn đến file markdown đầu vào
        output_file (Optional[str]): Đường dẫn đến file Excel đầu ra (tùy chọn).
                                    Nếu None, tự động tạo tên file dựa trên input_file
        detect_cash_flow (bool): Nếu True, chỉ xử lý nếu phát hiện "báo cáo lưu chuyển tiền tệ".
                                Nếu False, xử lý tất cả các bảng trong file
        multiple_sheets (bool): Nếu True, đặt tất cả bảng vào một file với nhiều sheets.
                                Nếu False, tạo file riêng cho mỗi bảng
        
    Returns:
        str: Đường dẫn đến file Excel đã tạo
        
    Raises:
        FileNotFoundError: Nếu file đầu vào không tồn tại
        ValueError: Nếu không phát hiện báo cáo lưu chuyển tiền tệ (khi detect_cash_flow=True)
                   hoặc không tìm thấy bảng markdown nào trong file
    """
    input_path = Path(input_file)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Bước 1: Đọc file
    print(f"Reading file: {input_file}")
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Bước 2: Phát hiện "báo cáo lưu chuyển tiền tệ" (nếu cần)
    if detect_cash_flow:
        print("Detecting 'Bao Cao Luu Chuyen Tien Te'...")
        if not detect_luuchuyentiente(content):
            raise ValueError(
                "File does not contain 'Bao Cao Luu Chuyen Tien Te'. "
                "Set detect_cash_flow=False to process anyway."
            )
        print("Cash flow statement detected!")
    
    # Bước 3: Trích xuất tất cả các bảng markdown
    print("Extracting markdown tables...")
    tables = extract_markdown_tables(content)
    print(f"  Found {len(tables)} table(s)")
    
    if not tables:
        raise ValueError("No markdown tables found in file")
    
    # Bước 4: Chuyển đổi sang Excel
    if output_file is None:
        output_file = str(input_path.parent / f"{input_path.stem}_LuuChuyenTienTe.xlsx")
    
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
                sheet_name = f"LuuChuyen_{idx}"[:31]
                
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
                sheet_name="LuuChuyen"
            )
            output_files.append(table_output_path)
        
        result_path = output_files[0] if output_files else output_file
    
    print(f"Successfully saved to: {result_path}")
    return result_path


def main():
    """
    Hàm chính để xử lý file markdown và chuyển đổi bảng sang Excel.
    """
    input_file = Path(__file__).parent / "Example_LuuChuyenTienTe.md"
    
    try:
        result_path = process_markdown_file_to_xlsx(
            input_file=str(input_file),
            detect_cash_flow=True,
            multiple_sheets=True
        )
        print(f"\nDone! Output file: {result_path}")
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()


