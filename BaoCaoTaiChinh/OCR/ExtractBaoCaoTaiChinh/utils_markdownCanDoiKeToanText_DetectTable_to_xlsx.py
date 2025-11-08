"""
Module phát hiện "Bảng Cân Đối Kế Toán" và chuyển đổi bảng sang Excel.

MÔ TẢ:
-------
Module này thực hiện 3 bước đơn giản:
1. Phát hiện "bảng cân đối kế toán" trong văn bản (fuzzy matching 80%)
    Logic:
    1. Lowercase toàn bộ văn bản
    2. Loại bỏ dấu tiếng Việt
    3. So khớp fuzzy 80% với "bang can doi ke toan"
2. Trích xuất tất cả các bảng markdown từ văn bản
3. Chuyển đổi các bảng sang file Excel (.xlsx)

CHỨC NĂNG:
----------
- detect_candoiketoan(): Phát hiện "bảng cân đối kế toán" (fuzzy 80%)
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
    _create_dataframe_from_rows
)


def detect_candoiketoan(text: str, threshold: float = 0.8) -> bool:
    """
    Phát hiện xem văn bản có chứa "bảng cân đối kế toán" hay không.
    
    Logic:
    1. Lowercase toàn bộ văn bản
    2. Loại bỏ dấu tiếng Việt
    3. So khớp fuzzy 80% với "bang can doi ke toan"
    
    Args:
        text (str): Văn bản cần kiểm tra
        threshold (float): Ngưỡng so khớp (mặc định: 0.8 = 80%)
        
    Returns:
        bool: True nếu tìm thấy "bảng cân đối kế toán", False nếu không
        
    Ví dụ:
        >>> detect_candoiketoan("BẢNG CÂN ĐỐI KẾ TOÁN")  # True
        >>> detect_candoiketoan("BANG CAN DOI KE TOAN")   # True
        >>> detect_candoiketoan("Không có gì")            # False
    """
    # Lowercase và loại bỏ dấu
    text_lower = text.lower()
    text_khong_dau = remove_diacritics(text_lower)
    
    # Pattern chuẩn để so khớp
    pattern = "bang can doi ke toan"
    
    # Tìm tất cả các cụm từ có độ dài tương tự trong text
    words = text_khong_dau.split()
    pattern_words = pattern.split()
    
    # Kiểm tra nếu pattern xuất hiện trực tiếp
    if pattern in text_khong_dau:
        return True
    
    # Fuzzy matching: tìm cụm từ có độ dài tương tự và so khớp
    for i in range(len(words) - len(pattern_words) + 1):
        candidate = ' '.join(words[i:i+len(pattern_words)])
        similarity = SequenceMatcher(None, pattern, candidate).ratio()
        
        if similarity >= threshold:
            return True
    
    return False


def process_markdown_file_to_xlsx(
    input_file: str,
    output_file: Optional[str] = None,
    detect_balance_sheet: bool = True,
    multiple_sheets: bool = True
) -> str:
    """
    Xử lý file markdown: phát hiện bảng cân đối kế toán, trích xuất bảng và chuyển đổi sang Excel.
    
    Quy trình:
    1. Đọc file markdown
    2. Phát hiện "bảng cân đối kế toán" (nếu detect_balance_sheet=True)
    3. Trích xuất tất cả các bảng markdown
    4. Chuyển đổi sang file Excel
    
    Args:
        input_file (str): Đường dẫn đến file markdown đầu vào
        output_file (Optional[str]): Đường dẫn đến file Excel đầu ra (tùy chọn).
                                    Nếu None, tự động tạo tên file dựa trên input_file
        detect_balance_sheet (bool): Nếu True, chỉ xử lý nếu phát hiện "bảng cân đối kế toán".
                                     Nếu False, xử lý tất cả các bảng trong file
        multiple_sheets (bool): Nếu True, đặt tất cả bảng vào một file với nhiều sheets.
                                Nếu False, tạo file riêng cho mỗi bảng
        
    Returns:
        str: Đường dẫn đến file Excel đã tạo
        
    Raises:
        FileNotFoundError: Nếu file đầu vào không tồn tại
        ValueError: Nếu không phát hiện bảng cân đối kế toán (khi detect_balance_sheet=True)
                   hoặc không tìm thấy bảng markdown nào trong file
    """
    input_path = Path(input_file)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Bước 1: Đọc file
    print(f"Reading file: {input_file}")
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Bước 2: Phát hiện "bảng cân đối kế toán" (nếu cần)
    if detect_balance_sheet:
        print("Detecting 'Bang Can Doi Ke Toan'...")
        if not detect_candoiketoan(content):
            raise ValueError(
                "File does not contain 'Bang Can Doi Ke Toan'. "
                "Set detect_balance_sheet=False to process anyway."
            )
        print("Balance sheet detected!")
    
    # Bước 3: Trích xuất tất cả các bảng markdown
    print("Extracting markdown tables...")
    tables = extract_markdown_tables(content)
    print(f"  Found {len(tables)} table(s)")
    
    if not tables:
        raise ValueError("No markdown tables found in file")
    
    # Bước 4: Chuyển đổi sang Excel
    if output_file is None:
        output_file = str(input_path.parent / f"{input_path.stem}_CanDoiKeToan.xlsx")
    
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
                sheet_name = f"Bang_{idx}"[:31]
                
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
                sheet_name="Bang"
            )
            output_files.append(table_output_path)
        
        result_path = output_files[0] if output_files else output_file
    
    print(f"Successfully saved to: {result_path}")
    return result_path


def main():
    """
    Hàm chính để xử lý file markdown và chuyển đổi bảng sang Excel.
    """
    input_file = Path(__file__).parent / "Example2_MarkdownCanDoiKeToan.md"
    
    try:
        result_path = process_markdown_file_to_xlsx(
            input_file=str(input_file),
            detect_balance_sheet=True,
            multiple_sheets=True
        )
        print(f"\nDone! Output file: {result_path}")
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()
