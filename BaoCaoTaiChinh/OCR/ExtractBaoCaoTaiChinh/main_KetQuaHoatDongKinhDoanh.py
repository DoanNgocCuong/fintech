"""
Main function to convert markdown Kết quả Hoạt động Kinh doanh to xlsx and JSON.

Module này chỉ xử lý Kết quả Hoạt động Kinh doanh từ file markdown.

CHỨC NĂNG:
----------
- process_income_statement(): Xử lý Kết quả Hoạt động Kinh doanh từ một file markdown và lưu vào Excel + JSON

LOGIC QUÉT TRANG:
-----------------
Module này sử dụng logic quét qua các trang của file markdown gốc:
1. parse_markdown_pages(): Parse markdown thành các trang (theo dòng "Trang N" hoặc separator "---")
   - Hàm này được import từ utils_prepare_process.py (dùng chung cho tất cả các loại báo cáo)
2. process_pages_for_financial_statements(): Quét qua từng trang để tìm và extract các bảng
   - Hàm generic này được import từ utils_prepare_process.py (dùng chung cho tất cả các loại báo cáo)
   - Sử dụng detect_ketquahoedongkinhdoanh để phát hiện Kết quả Hoạt động Kinh doanh
3. Giới hạn số trang xử lý với tham số max_pages (mặc định: 30 trang)
4. Bỏ qua các trang có chứa "thuyết minh báo cáo tài chính" (exclude_thuyetminh=True)

YÊU CẦU:
--------
- pandas: Để xử lý dữ liệu và tạo Excel
- openpyxl: Để ghi file Excel (.xlsx)
- utils_markdownKetQuaHoatDongKinhDoanhText_DetectTable_to_xlsx: Module để detect Kết quả Hoạt động Kinh doanh

Markdown File
    ↓
[1] Đọc file → content
    ↓
[2] parse_markdown_pages() → [(page_num, page_content), ...]
    ↓
[3] Giới hạn số trang (max_pages)
    ↓
[4] process_pages_for_financial_statements()
    ├─ Vòng lặp qua TỪNG TRANG:
    │  ├─ Bỏ qua trang có "thuyết minh"
    │  ├─ detect_ketquahoedongkinhdoanh(page_content) ← CHECK TỪNG TRANG
    │  └─ extract_markdown_tables(page_content) → [table1, table2, ...]
    ↓
[5] Parse tables → DataFrame → Excel

---
Excel File (.xlsx)
    ↓
[1] Load JSON template từ income_template_json.json
    ↓
[2] Đọc Excel file → pd.ExcelFile
    ↓
[3] Vòng lặp qua từng sheet:
    ├─ Đọc sheet → DataFrame
    ├─ find_ma_so_column(df) → Tìm cột "Mã số"
    ├─ find_value_column(df) → Tìm cột giá trị ("Năm nay", etc.)
    ├─ Vòng lặp qua từng dòng:
    │  ├─ parse_ma_so(ma_so_str) → Mã số (int)
    │  ├─ parse_number(value) → Giá trị (float)
    │  └─ update_json_with_ma_so(json_result, ma_so, value) → Cập nhật JSON
    ↓
[4] Lưu JSON file
    ↓
JSON File (.json)
"""

import sys
import json
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any

# Import các hàm dùng chung từ utils_prepare_process
from utils_prepare_process import (
    parse_markdown_pages,
    process_pages_for_financial_statements,
    parse_ma_so,
    parse_number,
    find_value_column,
    find_ma_so_column,
    update_json_with_ma_so,
    replace_null_in_dict
)

try:
    import pandas as pd
except ImportError:
    pd = None

# Load income template JSON from file
_INCOME_TEMPLATE_JSON_PATH = Path(__file__).parent / "income_template_json.json"

# Import detection functions và utilities
from utils_markdownKetQuaHoatDongKinhDoanhText_DetectTable_to_xlsx import detect_ketquahoedongkinhdoanh
from utils_markdownTable_to_xlsx import (
    _parse_markdown_table,
    _create_dataframe_from_rows
)

# Import JSON creation function (will be imported after function definitions to avoid circular import)
# We'll import it locally in the main() function or use a lazy import

# Các hàm utility đã được di chuyển vào utils_prepare_process.py:
# - parse_markdown_pages() -> parse_markdown_pages()
# - process_pages_for_income_statement() -> process_pages_for_financial_statements(pages, detect_ketquahoedongkinhdoanh)
# - parse_ma_so() -> parse_ma_so()
# - parse_number() -> parse_number()
# - find_value_column() -> find_value_column()
# - find_ma_so_column() -> find_ma_so_column()
# - update_json_with_ma_so() -> update_json_with_ma_so()
# - replace_null_in_dict() -> replace_null_in_dict()
#
# Sử dụng các hàm từ utils_prepare_process thay vì định nghĩa lại ở đây.


def process_income_statement(
    input_file: str,
    output_file: Optional[str] = None,
    skip_missing: bool = True,
    max_pages: Optional[int] = 30,
    create_json: bool = True,
    replace_null_with: Optional[float] = None
) -> str:
    """
    Xử lý Kết quả Hoạt động Kinh doanh từ một file markdown và lưu vào một file Excel.
    
    Quy trình:
    1. Đọc file markdown
    2. Parse thành các trang (theo dòng "Trang N" hoặc separator "---")
    3. Giới hạn chỉ xử lý max_pages trang đầu tiên (mặc định: 30 trang)
    4. Đi qua từng trang và kiểm tra từng trang có chứa "Kết quả Hoạt động Kinh doanh" không
    5. Extract các bảng markdown từ các trang tìm thấy
    6. Ghi vào một file Excel với các sheets (mỗi bảng là một sheet)
    7. Tạo file JSON từ Excel (nếu create_json=True)
    
    LƯU Ý:
    - Hàm kiểm tra "Kết quả Hoạt động Kinh doanh" trên TỪNG TRANG, không kiểm tra toàn bộ file
    - Chỉ xử lý các trang trong phạm vi max_pages (nếu có)
    - Bỏ qua các trang có chứa "thuyết minh báo cáo tài chính"
    
    Args:
        input_file (str): Đường dẫn đến file markdown đầu vào
        output_file (Optional[str]): Đường dẫn đến file Excel đầu ra.
                                    Nếu None, tự động tạo tên file dựa trên input_file
        skip_missing (bool): Nếu True, không raise error nếu không tìm thấy.
                            Nếu False, raise ValueError nếu không tìm thấy Kết quả Hoạt động Kinh doanh
        max_pages (Optional[int]): Số trang tối đa để xử lý. Mặc định: 30.
                                  Nếu None, xử lý tất cả các trang.
        create_json (bool): Nếu True, tạo file JSON từ Excel sau khi xử lý xong. Mặc định: True
        replace_null_with (Optional[float]): Giá trị để thay thế cho null trong JSON.
                                           Nếu None, giữ nguyên null.
                                           Nếu là số (ví dụ: 0), thay thế tất cả null thành số đó.
        
    Returns:
        str: Đường dẫn đến file Excel đã tạo
        
    Raises:
        FileNotFoundError: Nếu file đầu vào không tồn tại
        ImportError: Nếu pandas hoặc openpyxl chưa được cài đặt
        ValueError: Nếu skip_missing=False và không tìm thấy Kết quả Hoạt động Kinh doanh
        
    Ví dụ:
        >>> result = process_income_statement("BIC_2024_1_5_1.md")
        >>> print(result)
        'BIC_2024_1_5_1_KetQuaHoatDongKinhDoanh.xlsx'
        
        >>> result = process_income_statement("BIC_2024_1_5_1.md", max_pages=50)
        >>> # Xử lý 50 trang đầu tiên
        
        >>> result = process_income_statement("BIC_2024_1_5_1.md", create_json=False)
        >>> # Chỉ tạo Excel, không tạo JSON
    """
    if pd is None:
        raise ImportError("pandas is required. Install with: pip install pandas openpyxl")
    
    input_path = Path(input_file)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Xác định file output
    if output_file is None:
        output_file = str(input_path.parent / f"{input_path.stem}_KetQuaHoatDongKinhDoanh.xlsx")
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Đọc file markdown
    print("=" * 80)
    print(f"Processing Kết quả Hoạt động Kinh doanh from: {input_file}")
    print("=" * 80)
    print(f"Reading file...")
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse thành các trang - LOGIC QUÉT TRANG TỪ main_markdownBaoCaoTaiChinh_to_xlsx.py
    print("\nParsing pages...")
    pages = parse_markdown_pages(content)  # Parse markdown thành list các trang (page_number, page_content)
    total_pages = len(pages)
    print(f"  Found {total_pages} page(s)")
    
    # Giới hạn số trang xử lý - Chỉ xử lý max_pages trang đầu tiên
    if max_pages is not None and total_pages > max_pages:
        pages = pages[:max_pages]
        print(f"  Limiting processing to first {max_pages} page(s) (out of {total_pages} total)")
    elif max_pages is None:
        print(f"  Processing all {total_pages} page(s)")
    else:
        print(f"  Processing all {total_pages} page(s) (within limit of {max_pages})")
    
    # Tạo Excel writer
    print(f"\nCreating Excel file: {output_file}")
    with pd.ExcelWriter(str(output_path), engine='openpyxl') as writer:
        sheet_count = 0
        # Quét qua từng trang để tìm và extract các bảng của Kết quả Hoạt động Kinh doanh
        # Xử lý Kết quả Hoạt động Kinh doanh - QUÉT QUA TỪNG TRANG
        print("\n" + "-" * 80)
        print("Processing: KET QUA HOAT DONG KINH DOANH (Income Statement)")
        print("-" * 80)
        try:
            # Quét qua từng trang để tìm và extract các bảng của Kết quả Hoạt động Kinh doanh
            # Sử dụng hàm generic process_pages_for_financial_statements với detect_ketquahoedongkinhdoanh
            result_pages = process_pages_for_financial_statements(pages, detect_ketquahoedongkinhdoanh)
            if result_pages:
                print(f"  Found {len(result_pages)} page(s) with income statement")
                table_idx = 1
                total_tables = sum(len(tables) for _, _, tables in result_pages)
                
                # Xử lý từng trang và extract tables
                for page_num, page_content, tables in result_pages:
                    print(f"  Processing page {page_num}...")
                    for table_text in tables:
                        rows = _parse_markdown_table(table_text)
                        if not rows or len(rows) < 2:
                            continue
                        
                        df = _create_dataframe_from_rows(rows)
                        
                        # Sheet name (đặt tên theo số trang và số bảng)
                        if total_tables == 1:
                            sheet_name = "KetQuaHoatDongKinhDoanh"[:31]
                        elif len(result_pages) == 1:
                            sheet_name = f"KetQua_T{table_idx}"[:31]
                        else:
                            sheet_name = f"KetQua_P{page_num}_T{table_idx}"[:31]
                        
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                        sheet_count += 1
                        print(f"    ✓ Added sheet: {sheet_name}")
                        table_idx += 1
            else:
                print("  ✗ No pages found with income statement")
                if not skip_missing:
                    raise ValueError("No pages found with income statement")
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
            if not skip_missing:
                raise            
    
    # Tổng kết
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Output Excel file: {output_file}")
    print(f"Total sheets created: {sheet_count}")
    
    # Tạo JSON từ Excel nếu được yêu cầu
    json_file = None
    if create_json and sheet_count > 0:
        print("\n" + "-" * 80)
        print("Creating JSON file from Excel...")
        print("-" * 80)
        try:
            # Lazy import để tránh circular import
            from utils_xlsx_to_json_income import create_json_result
            
            # Tự động tạo tên file JSON từ Excel file
            json_output_file = str(output_path.parent / f"{output_path.stem}.json")
            
            # Tạo JSON
            create_json_result(
                excel_file=str(output_path),
                output_json_file=json_output_file,
                replace_null_with=replace_null_with
            )
            json_file = json_output_file
            print(f"\n✓ JSON file created: {json_file}")
        except Exception as e:
            print(f"\n✗ Error creating JSON file: {e}")
            # Không raise error, chỉ cảnh báo vì Excel đã được tạo thành công
    
    print("=" * 80)
    
    return str(output_path)



def _get_income_statement_json_template(
    replace_null_with: Optional[float] = None
) -> Dict[str, Any]:
    """
    Load cấu trúc JSON template cho Kết quả Hoạt động Kinh doanh từ file.
    
    Cấu trúc: Nested/hierarchical structure - mỗi section có ma_so, so_cuoi_nam và chứa các section con bên trong.
    
    Args:
        replace_null_with (Optional[float]): Giá trị để thay thế cho null trong JSON.
                                           Nếu None, giữ nguyên null (sẽ được convert thành None trong Python).
                                           Nếu là số (ví dụ: 0), thay thế tất cả null thành số đó.
    
    Returns:
        Dict[str, Any]: Cấu trúc JSON template với tất cả các mã số và giá trị
    
    Raises:
        FileNotFoundError: Nếu file income_template_json.json không tồn tại
    
    Ví dụ:
        >>> template = _get_income_statement_json_template()  # Giữ nguyên null
        >>> template = _get_income_statement_json_template(replace_null_with=0)  # Thay null thành 0
    """
    if not _INCOME_TEMPLATE_JSON_PATH.exists():
        raise FileNotFoundError(
            f"Income template JSON file not found: {_INCOME_TEMPLATE_JSON_PATH}"
        )
    
    # Load JSON từ file
    with open(_INCOME_TEMPLATE_JSON_PATH, 'r', encoding='utf-8') as f:
        template = json.load(f)
    
    # Nếu có yêu cầu replace null, thực hiện deep copy và replace
    if replace_null_with is not None:
        template = replace_null_in_dict(template, replace_null_with)
    
    return template


# Các hàm utility đã được di chuyển vào utils_prepare_process.py:
# - parse_markdown_pages() -> parse_markdown_pages()
# - parse_ma_so() -> parse_ma_so()
# - parse_number() -> parse_number()
# - find_value_column() -> find_value_column()
# - find_ma_so_column() -> find_ma_so_column()
# - update_json_with_ma_so() -> update_json_with_ma_so()
# - replace_null_in_dict() -> replace_null_in_dict()
# 
# Sử dụng các hàm từ utils_prepare_process thay vì định nghĩa lại ở đây.




def main():
    """
    Hàm chính: Xử lý file markdown Kết quả Hoạt động Kinh doanh.
    Sử dụng:
        python main_KetQuaHoatDongKinhDoanh.py <input_file>
    """
    # Không dùng parameters/options  
    input_file = None
    if len(sys.argv) >= 2:
        input_file = sys.argv[1]
    else:
        # Default file nếu không truyền argument
        input_file = str(Path(__file__).parent / "MIG_2024_1_5_1.md")
        if not Path(input_file).exists():
            print("Usage: python main_KetQuaHoatDongKinhDoanh.py <input_file>")
            print("\nOr provide a markdown file in the current directory.")
            sys.exit(1)
        print(f"Using default file: {input_file}")
    
    try:
        result_path = process_income_statement(
            input_file=input_file,
            skip_missing=True,
            max_pages=30
        )
        print(f"\nOutput file: {result_path}")
        print("\nDone!")
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
    

if __name__ == "__main__":
    main()

