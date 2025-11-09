"""
Main function to convert markdown bao cao tai chinh to xlsx.

Module này sử dụng 3 modules để xử lý các loại báo cáo tài chính:
1. Bảng Cân Đối Kế Toán
2. Kết quả Hoạt động Kinh doanh
3. Lưu chuyển Tiền tệ

CHỨC NĂNG:
----------
- process_all_financial_statements(): Xử lý tất cả các loại báo cáo tài chính từ một file markdown

YÊU CẦU:
--------
- pandas: Để xử lý dữ liệu và tạo Excel
- openpyxl: Để ghi file Excel (.xlsx)
- 3 modules: utils_markdownCanDoiKeToanText_DetectTable_to_xlsx
            utils_markdownKetQuaHoatDongKinhDoanhText_DetectTable_to_xlsx
            utils_markdownLuuChuyenTienTeText_DetectTable_to_xlsx

CÀI ĐẶT:
---------
    pip install pandas openpyxl
"""

import sys
import re
from pathlib import Path
from typing import Optional, Dict, List, Tuple

try:
    import pandas as pd
except ImportError:
    pd = None

# Import utils_count để parse trang (từ thư mục parent)
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from utils_count import count_markdown_pages
except ImportError:
    # Fallback nếu không tìm thấy utils_count
    def count_markdown_pages(md_path: str) -> Optional[int]:
        return None

# Import detection functions và utilities
from utils_markdownCanDoiKeToanText_DetectTable_to_xlsx import detect_candoiketoan
from utils_markdownKetQuaHoatDongKinhDoanhText_DetectTable_to_xlsx import detect_ketquahoedongkinhdoanh
from utils_markdownLuuChuyenTienTeText_DetectTable_to_xlsx import detect_luuchuyentiente
from utils_markdownTable_to_xlsx import (
    extract_markdown_tables,
    _parse_markdown_table,
    _create_dataframe_from_rows,
    remove_diacritics
)
from difflib import SequenceMatcher


def detect_thuyetminhbaocaotaichinh(text: str, threshold: float = 0.8) -> bool:
    """
    Phát hiện xem văn bản có chứa "thuyết minh báo cáo tài chính" hay không.
    
    Logic:
    1. Lowercase toàn bộ văn bản
    2. Loại bỏ dấu tiếng Việt
    3. So khớp fuzzy 80% với "thuyet minh bao cao tai chinh"
    
    Args:
        text (str): Văn bản cần kiểm tra
        threshold (float): Ngưỡng so khớp (mặc định: 0.8 = 80%)
        
    Returns:
        bool: True nếu tìm thấy "thuyết minh báo cáo tài chính", False nếu không
        
    Ví dụ:
        >>> detect_thuyetminhbaocaotaichinh("THUYẾT MINH BÁO CÁO TÀI CHÍNH")  # True
        >>> detect_thuyetminhbaocaotaichinh("THUYET MINH BAO CAO TAI CHINH")   # True
        >>> detect_thuyetminhbaocaotaichinh("Thuyết minh báo cáo")             # True (fuzzy)
        >>> detect_thuyetminhbaocaotaichinh("Bảng cân đối kế toán")            # False
    """
    # Lowercase và loại bỏ dấu
    text_lower = text.lower()
    text_khong_dau = remove_diacritics(text_lower)
    
    # Pattern chuẩn để so khớp (ưu tiên pattern đầy đủ, sau đó là pattern ngắn hơn)
    # Chỉ focus vào "thuyet minh" để tránh match với "báo cáo tài chính" chung chung
    patterns = [
        "thuyet minh bao cao tai chinh",  # Pattern đầy đủ
        "thuyet minh bao cao",            # Pattern rút gọn
    ]
    
    # Kiểm tra từng pattern (ưu tiên pattern dài hơn)
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


def parse_markdown_pages(content: str) -> List[Tuple[int, str]]:
    """
    Parse markdown content thành các trang.
    
    Format markdown:
        Trang 1
        
        <nội dung trang 1>
        
        ---
        
        Trang 2
        
        <nội dung trang 2>
    
    Args:
        content (str): Nội dung markdown
        
    Returns:
        List[Tuple[int, str]]: Danh sách các tuple (page_number, page_content)
    """
    pages = []
    lines = content.split('\n')
    
    # Tìm tất cả các dòng "Trang N"
    page_starts = []
    for i, line in enumerate(lines):
        match = re.match(r'^\s*Trang\s+(\d+)\s*$', line, re.IGNORECASE)
        if match:
            page_starts.append((i, int(match.group(1))))
    
    if not page_starts:
        # Nếu không tìm thấy "Trang N", tách theo separator '---'
        parts = re.split(r'\n-{3,}\s*\n', content)
        non_empty_parts = [p.strip() for p in parts if p.strip()]
        for idx, part in enumerate(non_empty_parts, 1):
            # Loại bỏ dòng "Trang N" nếu có trong phần
            part_lines = part.split('\n')
            filtered_lines = []
            for line in part_lines:
                # Bỏ qua dòng "Trang N" và separator "---"
                if not re.match(r'^\s*Trang\s+\d+\s*$', line, re.IGNORECASE):
                    if not re.match(r'^\s*-{3,}\s*$', line):
                        filtered_lines.append(line)
            if filtered_lines:
                pages.append((idx, '\n'.join(filtered_lines)))
        return pages
    
    # Tách theo các dòng "Trang N"
    for idx, (start_line, page_num) in enumerate(page_starts):
        # Xác định end_line
        if idx + 1 < len(page_starts):
            end_line = page_starts[idx + 1][0]
        else:
            end_line = len(lines)
        
        # Lấy nội dung trang (bỏ qua dòng "Trang N" và separator "---")
        page_lines = []
        for i in range(start_line + 1, end_line):  # Bỏ qua dòng "Trang N"
            line = lines[i]
            # Bỏ qua separator "---"
            if not re.match(r'^\s*-{3,}\s*$', line):
                page_lines.append(line)
        
        page_content = '\n'.join(page_lines).strip()
        if page_content:  # Chỉ thêm nếu có nội dung
            pages.append((page_num, page_content))
    
    return pages


def process_pages_for_financial_statements(
    pages: List[Tuple[int, str]],
    statement_type: str,
    exclude_thuyetminh: bool = True
) -> List[Tuple[int, str, List]]:
    """
    Đi qua từng trang để tìm và extract các bảng của một loại báo cáo tài chính.
    
    Args:
        pages (List[Tuple[int, str]]): Danh sách các trang (page_number, page_content)
        statement_type (str): Loại báo cáo: 'balance_sheet', 'income_statement', 'cash_flow'
        exclude_thuyetminh (bool): Nếu True, bỏ qua các trang có chứa "thuyết minh báo cáo tài chính"
        
    Returns:
        List[Tuple[int, str, List]]: Danh sách các tuple (page_number, page_content, tables)
    """
    # Xác định hàm detect tương ứng
    detect_functions = {
        'balance_sheet': detect_candoiketoan,
        'income_statement': detect_ketquahoedongkinhdoanh,
        'cash_flow': detect_luuchuyentiente
    }
    
    detect_func = detect_functions.get(statement_type)
    if not detect_func:
        return []
    
    result_pages = []
    
    for page_num, page_content in pages:
        # Bỏ qua các trang có chứa "thuyết minh báo cáo tài chính" nếu exclude_thuyetminh=True
        if exclude_thuyetminh and detect_thuyetminhbaocaotaichinh(page_content):
            print(f"  Skipping page {page_num}: contains 'Thuyet Minh Bao Cao Tai Chinh'")
            continue
        
        # Kiểm tra nếu trang có chứa loại báo cáo này
        if detect_func(page_content):
            # Extract tables từ trang
            tables = extract_markdown_tables(page_content)
            if tables:
                result_pages.append((page_num, page_content, tables))
    
    return result_pages


def process_all_financial_statements(
    input_file: str,
    output_file: Optional[str] = None,
    skip_missing: bool = True,
    max_pages: Optional[int] = 30
) -> str:
    """
    Xử lý tất cả các loại báo cáo tài chính từ một file markdown và lưu vào một file Excel duy nhất.
    
    Tất cả các báo cáo sẽ được lưu vào một file Excel, mỗi loại báo cáo là một sheet:
    - Sheet "CanDoiKeToan": Bảng Cân Đối Kế Toán
    - Sheet "KetQuaHoatDongKinhDoanh": Kết quả Hoạt động Kinh doanh
    - Sheet "LuuChuyenTienTe": Lưu chuyển Tiền tệ
    
    Quy trình:
    1. Đọc file markdown
    2. Parse thành các trang (sử dụng utils_count.py)
    3. Giới hạn chỉ xử lý max_pages trang đầu tiên (mặc định: 30 trang)
    4. Đi qua từng trang để tìm các loại báo cáo
    5. Extract các bảng markdown
    6. Ghi tất cả vào một file Excel với nhiều sheets
    
    Args:
        input_file (str): Đường dẫn đến file markdown đầu vào
        output_file (Optional[str]): Đường dẫn đến file Excel đầu ra.
                                    Nếu None, tự động tạo tên file dựa trên input_file
        skip_missing (bool): Nếu True, bỏ qua các loại báo cáo không tìm thấy.
                            Nếu False, raise ValueError nếu không tìm thấy bất kỳ báo cáo nào
        max_pages (Optional[int]): Số trang tối đa để xử lý. Mặc định: 30.
                                  Nếu None, xử lý tất cả các trang.
        
    Returns:
        str: Đường dẫn đến file Excel đã tạo
        
    Raises:
        FileNotFoundError: Nếu file đầu vào không tồn tại
        ImportError: Nếu pandas hoặc openpyxl chưa được cài đặt
        ValueError: Nếu skip_missing=False và không tìm thấy bất kỳ loại báo cáo nào
        
    Ví dụ:
        >>> result = process_all_financial_statements("BIC_2024_1_5_1.md")
        >>> print(result)
        'BIC_2024_1_5_1_BaoCaoTaiChinh.xlsx'
        
        >>> result = process_all_financial_statements("BIC_2024_1_5_1.md", max_pages=50)
        >>> # Xử lý 50 trang đầu tiên
    """
    if pd is None:
        raise ImportError("pandas is required. Install with: pip install pandas openpyxl")
    
    input_path = Path(input_file)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Xác định file output
    if output_file is None:
        output_file = str(input_path.parent / f"{input_path.stem}_BaoCaoTaiChinh.xlsx")
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Đọc file markdown
    print("=" * 80)
    print(f"Processing financial statements from: {input_file}")
    print("=" * 80)
    print(f"Reading file...")
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse thành các trang
    print("\nParsing pages...")
    pages = parse_markdown_pages(content)
    total_pages = len(pages)
    print(f"  Found {total_pages} page(s)")
    
    # Giới hạn số trang xử lý
    if max_pages is not None and total_pages > max_pages:
        pages = pages[:max_pages]
        print(f"  Limiting processing to first {max_pages} page(s) (out of {total_pages} total)")
    elif max_pages is None:
        print(f"  Processing all {total_pages} page(s)")
    else:
        print(f"  Processing all {total_pages} page(s) (within limit of {max_pages})")
    
    # Phát hiện các loại báo cáo
    print("\nDetecting financial statements...")
    has_balance_sheet = detect_candoiketoan(content)
    has_income_statement = detect_ketquahoedongkinhdoanh(content)
    has_cash_flow = detect_luuchuyentiente(content)
    
    print(f"  - Balance Sheet: {'✓ Found' if has_balance_sheet else '✗ Not found'}")
    print(f"  - Income Statement: {'✓ Found' if has_income_statement else '✗ Not found'}")
    print(f"  - Cash Flow: {'✓ Found' if has_cash_flow else '✗ Not found'}")
    
    # Kiểm tra nếu không tìm thấy bất kỳ báo cáo nào
    found_count = sum([has_balance_sheet, has_income_statement, has_cash_flow])
    if found_count == 0:
        if skip_missing:
            raise ValueError(
                "No financial statements found in the file. "
                "Please check if the file contains any of the following: "
                "Bảng Cân Đối Kế Toán, Kết quả Hoạt động Kinh doanh, or Lưu chuyển Tiền tệ"
            )
        else:
            raise ValueError("No financial statements found in the file.")
    
    # Tạo Excel writer
    print(f"\nCreating Excel file: {output_file}")
    with pd.ExcelWriter(str(output_path), engine='openpyxl') as writer:
        sheet_count = 0
        
        # 1. Xử lý Bảng Cân Đối Kế Toán
        if has_balance_sheet:
            print("\n" + "-" * 80)
            print("Processing: BANG CAN DOI KE TOAN (Balance Sheet)")
            print("-" * 80)
            try:
                result_pages = process_pages_for_financial_statements(pages, 'balance_sheet')
                if result_pages:
                    print(f"  Found {len(result_pages)} page(s) with balance sheet")
                    table_idx = 1
                    total_tables = sum(len(tables) for _, _, tables in result_pages)
                    
                    for page_num, page_content, tables in result_pages:
                        print(f"  Processing page {page_num}...")
                        for table_text in tables:
                            rows = _parse_markdown_table(table_text)
                            if not rows or len(rows) < 2:
                                continue
                            
                            df = _create_dataframe_from_rows(rows)
                            
                            # Sheet name
                            if total_tables == 1:
                                sheet_name = "CanDoiKeToan"[:31]
                            elif len(result_pages) == 1:
                                sheet_name = f"CanDoiKeToan_T{table_idx}"[:31]
                            else:
                                sheet_name = f"CanDoi_P{page_num}_T{table_idx}"[:31]
                            
                            df.to_excel(writer, sheet_name=sheet_name, index=False)
                            sheet_count += 1
                            print(f"    ✓ Added sheet: {sheet_name}")
                            table_idx += 1
                else:
                    print("  ✗ No pages found with balance sheet")
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
                if not skip_missing:
                    raise
        
        # 2. Xử lý Kết quả Hoạt động Kinh doanh
        if has_income_statement:
            print("\n" + "-" * 80)
            print("Processing: KET QUA HOAT DONG KINH DOANH (Income Statement)")
            print("-" * 80)
            try:
                result_pages = process_pages_for_financial_statements(pages, 'income_statement')
                if result_pages:
                    print(f"  Found {len(result_pages)} page(s) with income statement")
                    table_idx = 1
                    total_tables = sum(len(tables) for _, _, tables in result_pages)
                    
                    for page_num, page_content, tables in result_pages:
                        print(f"  Processing page {page_num}...")
                        for table_text in tables:
                            rows = _parse_markdown_table(table_text)
                            if not rows or len(rows) < 2:
                                continue
                            
                            df = _create_dataframe_from_rows(rows)
                            
                            # Sheet name
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
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
                if not skip_missing:
                    raise
        
        # 3. Xử lý Lưu chuyển Tiền tệ
        if has_cash_flow:
            print("\n" + "-" * 80)
            print("Processing: LUU CHUYEN TIEN TE (Cash Flow Statement)")
            print("-" * 80)
            try:
                result_pages = process_pages_for_financial_statements(pages, 'cash_flow')
                if result_pages:
                    print(f"  Found {len(result_pages)} page(s) with cash flow")
                    table_idx = 1
                    total_tables = sum(len(tables) for _, _, tables in result_pages)
                    
                    for page_num, page_content, tables in result_pages:
                        print(f"  Processing page {page_num}...")
                        for table_text in tables:
                            rows = _parse_markdown_table(table_text)
                            if not rows or len(rows) < 2:
                                continue
                            
                            df = _create_dataframe_from_rows(rows)
                            
                            # Sheet name
                            if total_tables == 1:
                                sheet_name = "LuuChuyenTienTe"[:31]
                            elif len(result_pages) == 1:
                                sheet_name = f"LuuChuyen_T{table_idx}"[:31]
                            else:
                                sheet_name = f"LuuChuyen_P{page_num}_T{table_idx}"[:31]
                            
                            df.to_excel(writer, sheet_name=sheet_name, index=False)
                            sheet_count += 1
                            print(f"    ✓ Added sheet: {sheet_name}")
                            table_idx += 1
                else:
                    print("  ✗ No pages found with cash flow")
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
                if not skip_missing:
                    raise
    
    # Tổng kết
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Output file: {output_file}")
    print(f"Total sheets created: {sheet_count}")
    print(f"  - Balance Sheet: {'✓' if has_balance_sheet else '✗'}")
    print(f"  - Income Statement: {'✓' if has_income_statement else '✗'}")
    print(f"  - Cash Flow: {'✓' if has_cash_flow else '✗'}")
    print("=" * 80)
    
    return str(output_path)


def detect_all_financial_statements(input_file: str) -> Dict[str, bool]:
    """
    Phát hiện các loại báo cáo tài chính có trong file markdown.
    
    Args:
        input_file (str): Đường dẫn đến file markdown đầu vào
        
    Returns:
        Dict[str, bool]: Dictionary chứa kết quả phát hiện:
            {
                'balance_sheet': True/False,
                'income_statement': True/False,
                'cash_flow': True/False
            }
    """
    input_path = Path(input_file)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Đọc file
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Phát hiện các loại báo cáo
    results = {
        'balance_sheet': detect_candoiketoan(content),
        'income_statement': detect_ketquahoedongkinhdoanh(content),
        'cash_flow': detect_luuchuyentiente(content)
    }
    
    return results


def main():
    """
    Hàm chính để xử lý file markdown báo cáo tài chính.
    
    Sử dụng:
        python main_markdownBaoCaoTaiChinh_to_xlsx.py <input_file> [output_dir]
    
    Ví dụ:
        python main_markdownBaoCaoTaiChinh_to_xlsx.py BIC_2024_1_5_1.md
        python main_markdownBaoCaoTaiChinh_to_xlsx.py BIC_2024_1_5_1.md ./output
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Convert markdown financial statements to Excel files'
    )
    parser.add_argument(
        'input_file',
        type=str,
        help='Path to input markdown file'
    )
    parser.add_argument(
        '--output-file',
        type=str,
        default=None,
        help='Output Excel file path (default: {input_file}_BaoCaoTaiChinh.xlsx)'
    )
    parser.add_argument(
        '--skip-missing',
        action='store_true',
        default=True,
        help='Skip missing financial statements (default: True)'
    )
    parser.add_argument(
        '--no-skip-missing',
        action='store_false',
        dest='skip_missing',
        help='Raise error if any financial statement is missing'
    )
    parser.add_argument(
        '--detect-only',
        action='store_true',
        help='Only detect financial statements, do not process'
    )
    parser.add_argument(
        '--max-pages',
        type=int,
        default=30,
        help='Maximum number of pages to process (default: 30). Set to 0 to process all pages.'
    )
    
    args = parser.parse_args()
    
    try:
        if args.detect_only:
            # Chỉ phát hiện, không xử lý
            print("Detecting financial statements...")
            results = detect_all_financial_statements(args.input_file)
            print("\nDetection Results:")
            print(f"  - Balance Sheet: {'✓ Found' if results['balance_sheet'] else '✗ Not found'}")
            print(f"  - Income Statement: {'✓ Found' if results['income_statement'] else '✗ Not found'}")
            print(f"  - Cash Flow: {'✓ Found' if results['cash_flow'] else '✗ Not found'}")
        else:
            # Xử lý tất cả
            max_pages = None if args.max_pages == 0 else args.max_pages
            result_path = process_all_financial_statements(
                input_file=args.input_file,
                output_file=args.output_file,
                skip_missing=args.skip_missing,
                max_pages=max_pages
            )
            
            print(f"\nOutput file: {result_path}")
        
        print("\nDone!")
        
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Nếu chạy trực tiếp mà không có arguments, sử dụng file mặc định
    if len(sys.argv) == 1:
        # Sử dụng file mặc định từ thư mục hiện tại
        default_file = Path(__file__).parent / "BMI_2024_1_5_1.md"
        
        if default_file.exists():
            print(f"Using default file: {default_file}")
            print()
            result_path = process_all_financial_statements(
                input_file=str(default_file),
                skip_missing=True,
                max_pages=30
            )
            
            print(f"\nOutput file: {result_path}")
        else:
            print("Usage: python main_markdownBaoCaoTaiChinh_to_xlsx.py <input_file> [output_dir]")
            print("\nOr provide a markdown file in the current directory.")
            sys.exit(1)
    else:
        main()
