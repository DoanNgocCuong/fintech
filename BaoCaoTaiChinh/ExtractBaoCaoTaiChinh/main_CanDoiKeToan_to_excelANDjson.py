"""
Main function to convert markdown Bảng Cân Đối Kế Toán to xlsx and JSON.

Module này chỉ xử lý Bảng Cân Đối Kế Toán từ file markdown.

CHỨC NĂNG:
----------
- process_balance_sheet(): Xử lý Bảng Cân Đối Kế Toán từ một file markdown và lưu vào Excel + JSON

LOGIC QUÉT TRANG:
-----------------
Module này sử dụng logic quét qua các trang của file markdown gốc:
1. parse_markdown_pages(): Parse markdown thành các trang (theo dòng "Trang N" hoặc separator "---")
   - Hàm này được import từ utils_prepare_process.py (dùng chung cho tất cả các loại báo cáo)
2. process_pages_for_financial_statements(): Quét qua từng trang để tìm và extract các bảng
   - Hàm generic này được import từ utils_prepare_process.py (dùng chung cho tất cả các loại báo cáo)
   - Sử dụng detect_candoiketoan để phát hiện Bảng Cân Đối Kế Toán
3. Giới hạn số trang xử lý với tham số max_pages (mặc định: 30 trang)
4. Bỏ qua các trang có chứa "thuyết minh báo cáo tài chính" (exclude_thuyetminh=True)

YÊU CẦU:
--------
- pandas: Để xử lý dữ liệu và tạo Excel
- openpyxl: Để ghi file Excel (.xlsx)
- utils_markdownCanDoiKeToanText_DetectTable_to_xlsx: Module để detect Bảng Cân Đối Kế Toán

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
    │  ├─ detect_candoiketoan(page_content) ← CHECK TỪNG TRANG
    │  └─ extract_markdown_tables(page_content) → [table1, table2, ...]
    ↓
[5] Parse tables → DataFrame → Excel

---
Excel File (.xlsx)
    ↓
[1] Load JSON template từ balance_template_json.json
    ↓
[2] Đọc Excel file → pd.ExcelFile
    ↓
[3] Vòng lặp qua từng sheet:
    ├─ Đọc sheet → DataFrame
    ├─ find_ma_so_column(df) → Tìm cột "Mã số"
    ├─ find_value_column(df) → Tìm cột giá trị ("31/12/2024 VND", etc.)
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
    replace_null_in_dict,
)
from utils_error_logger import (
    log_simple_error,
    XLSX_TO_JSON_LOG_CanDoiKeToan,
    MARKDOWN_TO_XLSX_LOG_CanDoiKeToan,
)

try:
    import pandas as pd
except ImportError:
    pd = None

# Load balance template JSON from file
_BALANCE_TEMPLATE_JSON_PATH = Path(__file__).parent / "TT199_2014_NT_balance_template_json.json"

# Import detection functions và utilities
from utils_markdownCanDoiKeToanText_DetectTable_to_xlsx import detect_candoiketoan
from utils_markdownTable_to_xlsx import (
    _parse_markdown_table,
    _create_dataframe_from_rows,
    _remove_last_column,
    extract_markdown_tables
)
# Import hàm break pages để xác định vị trí các phần báo cáo tài chính
from main_breakPages_for_CanDoiKeToan_KetQuaHoatDongKinhDoanh_LuuChuyenTienTe import (
    break_pages_for_financial_statements
)

# Import JSON creation function (will be imported after function definitions to avoid circular import)
# We'll import it locally in the main() function or use a lazy import

# Các hàm utility đã được di chuyển vào utils_prepare_process.py:
# - parse_markdown_pages() -> parse_markdown_pages()
# - process_pages_for_balance_sheet() -> process_pages_for_financial_statements(pages, detect_candoiketoan)
# - parse_ma_so() -> parse_ma_so()
# - _parse_number() -> parse_number()
# - _find_value_column() -> find_value_column()
# - _find_ma_so_column() -> find_ma_so_column()
# - _update_json_with_ma_so() -> update_json_with_ma_so()
#
# Sử dụng các hàm từ utils_prepare_process thay vì định nghĩa lại ở đây.


def process_balance_sheet(
    input_file: str,
    output_file: Optional[str] = None,
    skip_missing: bool = True,
    max_pages: Optional[int] = 30,
    create_json: bool = True,
    replace_null_with: Optional[float] = None,
    page_locations: Optional[Dict] = None
) -> str:
    """
    Xử lý Bảng Cân Đối Kế Toán từ một file markdown và lưu vào một file Excel.
    
    Quy trình:
    1. Đọc file markdown
    2. Gọi break_pages_for_financial_statements() để xác định vị trí "Bảng cân đối kế toán"
    3. Lấy page number được detect (ví dụ: page 9)
    4. Xử lý các trang từ page được detect đến page + 3 (ví dụ: page 9, 10, 11, 12)
    5. Extract các bảng markdown từ các trang đó
    6. Ghi vào một file Excel với các sheets (mỗi bảng là một sheet)
    7. Tạo file JSON từ Excel (nếu create_json=True)
    
    LƯU Ý:
    - Sử dụng break_pages_for_financial_statements() để xác định chính xác vị trí
    - Chỉ xử lý 4 trang liên tiếp từ trang được detect (trang detect + 3 trang sau)
    - Bỏ qua các trang có chứa "thuyết minh báo cáo tài chính"
    
    Args:
        input_file (str): Đường dẫn đến file markdown đầu vào
        output_file (Optional[str]): Đường dẫn đến file Excel đầu ra.
                                    Nếu None, tự động tạo tên file dựa trên input_file
        skip_missing (bool): Nếu True, không raise error nếu không tìm thấy.
                            Nếu False, raise ValueError nếu không tìm thấy Bảng Cân Đối Kế Toán
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
        ValueError: Nếu skip_missing=False và không tìm thấy Bảng Cân Đối Kế Toán
        
    Ví dụ:
        >>> result = process_balance_sheet("BIC_2024_1_5_1.md")
        >>> print(result)
        'BIC_2024_1_5_1_CanDoiKeToan.xlsx'
        
        >>> result = process_balance_sheet("BIC_2024_1_5_1.md", max_pages=50)
        >>> # Xử lý 50 trang đầu tiên
        
        >>> result = process_balance_sheet("BIC_2024_1_5_1.md", create_json=False)
        >>> # Chỉ tạo Excel, không tạo JSON
    """
    if pd is None:
        raise ImportError("pandas is required. Install with: pip install pandas openpyxl")
    
    input_path = Path(input_file)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Xác định file output
    if output_file is None:
        output_file = str(input_path.parent / f"{input_path.stem}_CanDoiKeToan.xlsx")
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Đọc file markdown
    print("=" * 80)
    try:
        print(f"Processing Bảng Cân Đối Kế Toán from: {input_file}")
    except UnicodeEncodeError:
        print(f"Processing Bang Can Doi Ke Toan from: {input_file}")
    print("=" * 80)
    print(f"Reading file...")
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Bước 1: Sử dụng break_pages_for_financial_statements để xác định vị trí các phần
    # Nếu page_locations đã được truyền vào, dùng luôn (tránh detect lại)
    if page_locations is None:
        print("\n" + "-" * 80)
        print("Step 1: Detecting financial statement locations...")
        print("-" * 80)
        page_locations = break_pages_for_financial_statements(str(input_file))
    else:
        # Đã có page_locations từ bên ngoài, skip detect lại
        print("\n" + "-" * 80)
        print("Step 1: Using provided page locations (skip detection)...")
        print("-" * 80)
    
    # Lấy page number của "Bảng cân đối kế toán"
    can_doi_pages = []
    if page_locations.get("can_doi_ke_toan"):
        detected_page = page_locations["can_doi_ke_toan"][0]["page"]
        
        # Xác định page kết thúc: không được vượt quá page của "Kết quả hoạt động kinh doanh" (nếu có)
        end_page = detected_page + 4  # Mặc định: 4 trang (page, page+1, page+2, page+3)
        if page_locations.get("ket_qua_hoat_dong_kinh_doanh"):
            ket_qua_page = page_locations["ket_qua_hoat_dong_kinh_doanh"][0]["page"]
            # Không được đọc đến trang của "Kết quả hoạt động kinh doanh"
            end_page = min(end_page, ket_qua_page)
        
        can_doi_pages = list(range(detected_page, end_page))
        print(f"  Found 'Bảng cân đối kế toán' at page {detected_page}")
        print(f"  Will process pages: {can_doi_pages} (stopping before next statement)")
    else:
        print("  No 'Bảng cân đối kế toán' detected")
        if not skip_missing:
            raise ValueError("No 'Bảng cân đối kế toán' detected in file")
        return str(output_path)
    
    # Parse thành các trang
    print("\nParsing pages...")
    all_pages = parse_markdown_pages(content)
    total_pages = len(all_pages)
    print(f"  Found {total_pages} page(s) in total")
    
    # Chỉ lấy các trang cần xử lý (từ can_doi_pages)
    pages_dict = {page_num: page_content for page_num, page_content in all_pages}
    pages_to_process = []
    for page_num in can_doi_pages:
        if page_num in pages_dict:
            pages_to_process.append((page_num, pages_dict[page_num]))
    
    if not pages_to_process:
        print("  No pages to process")
        if not skip_missing:
            raise ValueError("No pages found for 'Bảng cân đối kế toán'")
        return str(output_path)
    
    print(f"  Processing {len(pages_to_process)} page(s): {[p[0] for p in pages_to_process]}")
    
    # Tạo Excel writer
    print(f"\nCreating Excel file: {output_file}")
    with pd.ExcelWriter(str(output_path), engine='openpyxl') as writer:
        sheet_count = 0
        # Xử lý Bảng Cân Đối Kế Toán - CHỈ XỬ LÝ CÁC TRANG ĐÃ ĐƯỢC XÁC ĐỊNH
        print("\n" + "-" * 80)
        print("Processing: BANG CAN DOI KE TOAN (Balance Sheet)")
        print("-" * 80)
        try:
            # FIX: Không cần detect lại vì đã xác định các trang cần xử lý rồi
            # Chỉ cần extract tables từ các trang đã được xác định
            result_pages = []
            for page_num, page_content in pages_to_process:
                # Extract tables từ trang
                tables = extract_markdown_tables(page_content)
                if tables:
                    result_pages.append((page_num, page_content, tables))
            
            if result_pages:
                print(f"  Found {len(result_pages)} page(s) with balance sheet")
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

                        df = _remove_last_column(df)
                        
                        # Sheet name (đặt tên theo số trang và số bảng)
                        if total_tables == 1:
                            sheet_name = "CanDoiKeToan"[:31]
                        elif len(result_pages) == 1:
                            sheet_name = f"CanDoiKeToan_T{table_idx}"[:31]
                        else:
                            sheet_name = f"CanDoi_P{page_num}_T{table_idx}"[:31]
                        
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                        sheet_count += 1
                        try:
                            print(f"    ✓ Added sheet: {sheet_name}")
                        except UnicodeEncodeError:
                            print(f"    Added sheet: {sheet_name}")
                        table_idx += 1
            else:
                try:
                    print("  ✗ No pages found with balance sheet")
                except UnicodeEncodeError:
                    print("  No pages found with balance sheet")
                if not skip_missing:
                    raise ValueError("No pages found with balance sheet")
        except Exception as e:
            error_msg = str(e)
            try:
                print(f"  ✗ Error: {error_msg}")
            except UnicodeEncodeError:
                print(f"  [ERROR] Error: {error_msg}")
            # Log error to file
            log_simple_error(
                MARKDOWN_TO_XLSX_LOG_CanDoiKeToan,
                str(input_file),
                'markdown_to_xlsx',
                f"Balance sheet processing failed: {error_msg}"
            )
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
            from utils_xlsx_to_json_balance import create_json_result
            
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
            error_msg = str(e)
            try:
                print(f"\n✗ Error creating JSON file: {error_msg}")
            except UnicodeEncodeError:
                print(f"\n[ERROR] Error creating JSON file: {error_msg}")
            # Log error to file
            log_simple_error(
                XLSX_TO_JSON_LOG_CanDoiKeToan,
                str(output_path),
                'xlsx_to_json',
                f"Failed to create JSON from Excel: {error_msg}"
            )
            # Không raise error, chỉ cảnh báo vì Excel đã được tạo thành công
    
    print("=" * 80)
    
    return str(output_path)



def _get_balance_sheet_json_template(
    replace_null_with: Optional[float] = None
) -> Dict[str, Any]:
    """
    Load cấu trúc JSON template cho Bảng Cân Đối Kế Toán từ file.
    
    Cấu trúc: Nested/hierarchical structure - mỗi section có ma_so, so_cuoi_nam và chứa các section con bên trong.
    
    Args:
        replace_null_with (Optional[float]): Giá trị để thay thế cho null trong JSON.
                                           Nếu None, giữ nguyên null (sẽ được convert thành None trong Python).
                                           Nếu là số (ví dụ: 0), thay thế tất cả null thành số đó.
    
    Returns:
        Dict[str, Any]: Cấu trúc JSON template với tất cả các mã số và giá trị
    
    Raises:
        FileNotFoundError: Nếu file balance_template_json.json không tồn tại
    
    Ví dụ:
        >>> template = _get_balance_sheet_json_template()  # Giữ nguyên null
        >>> template = _get_balance_sheet_json_template(replace_null_with=0)  # Thay null thành 0
    """
    if not _BALANCE_TEMPLATE_JSON_PATH.exists():
        raise FileNotFoundError(
            f"Balance template JSON file not found: {_BALANCE_TEMPLATE_JSON_PATH}"
        )
    
    # Load JSON từ file
    with open(_BALANCE_TEMPLATE_JSON_PATH, 'r', encoding='utf-8') as f:
        template = json.load(f)
    
    # Nếu có yêu cầu replace null, thực hiện deep copy và replace
    if replace_null_with is not None:
        template = replace_null_in_dict(template, replace_null_with)
    
    return template


# Các hàm utility đã được di chuyển vào utils_prepare_process.py:
# - parse_ma_so() -> parse_ma_so()
# - parse_number() -> parse_number()
# - find_value_column() -> find_value_column()
# - find_ma_so_column() -> find_ma_so_column()
# - update_json_with_ma_so() -> update_json_with_ma_so()
# - replace_null_in_dict() -> replace_null_in_dict()
# 
# Sử dụng các hàm từ utils_prepare_process thay vì định nghĩa lại ở đây.




def _get_display_path(md_file: Path, base_path: Path) -> str:
    """
    Lấy đường dẫn hiển thị cho file markdown.
    Nếu file nằm trong folder con, trả về đường dẫn tương đối.
    Nếu không, trả về tên file.
    
    Args:
        md_file (Path): Đường dẫn đến file markdown
        base_path (Path): Đường dẫn gốc (input folder hoặc file)
    
    Returns:
        str: Đường dẫn hiển thị
    """
    if base_path.is_dir():
        try:
            rel_path = md_file.relative_to(base_path)
            return str(rel_path) if str(rel_path) != md_file.name else md_file.name
        except ValueError:
            return str(md_file)
    else:
        return md_file.name


def main():
    """
    Hàm chính: Xử lý file markdown Bảng Cân Đối Kế Toán.
    Sử dụng:
        python main_CanDoiKeToan.py <input_file_or_folder>
    
    Nếu input là folder, sẽ xử lý tất cả file .md trong folder đó và tất cả các folder con (đệ quy).
    Nếu input là file, sẽ xử lý file đó.
    """
    input_path = None
    if len(sys.argv) >= 2:
        input_path = sys.argv[1]
    else:
        # Default file nếu không truyền argument
        input_path = str(Path(__file__).parent / "MIG_2024_1_5_1.md")
        if not Path(input_path).exists():
            print("Usage: python main_CanDoiKeToan.py <input_file_or_folder>")
            print("\nOr provide a markdown file or folder in the current directory.")
            sys.exit(1)
        print(f"Using default file: {input_path}")
    
    input_path_obj = Path(input_path)
    
    # Kiểm tra xem input là file hay folder
    if input_path_obj.is_file():
        # Xử lý một file
        md_files = [input_path_obj] if input_path_obj.suffix.lower() == '.md' else []
    elif input_path_obj.is_dir():
        # Xử lý tất cả file .md trong folder và các folder con (đệ quy)
        md_files = list(input_path_obj.rglob("*.md"))
        if not md_files:
            print(f"No .md files found in folder (including subfolders): {input_path}")
            sys.exit(1)
        print(f"Found {len(md_files)} .md file(s) in folder and subfolders: {input_path}")
    else:
        print(f"Error: Path does not exist: {input_path}")
        sys.exit(1)
    
    # Xử lý từng file .md
    successful_files = []
    failed_files = []
    
    # Sắp xếp các file để xử lý theo thứ tự (tên file)
    md_files = sorted(md_files)
    
    for idx, md_file in enumerate(md_files, 1):
        print("\n" + "=" * 80)
        display_name = _get_display_path(md_file, input_path_obj)
        print(f"Processing file {idx}/{len(md_files)}: {display_name}")
        print("=" * 80)
        
        try:
            result_path = process_balance_sheet(
                input_file=str(md_file),
                skip_missing=True,
                max_pages=30
            )
            print(f"\n✓ Successfully processed: {display_name}")
            print(f"  Output file: {result_path}")
            successful_files.append((display_name, result_path))
        except Exception as e:
            error_msg = str(e)
            try:
                print(f"\n✗ Error processing {display_name}: {error_msg}")
            except UnicodeEncodeError:
                print(f"\n[ERROR] Error processing {display_name}: {error_msg}")
            # Log error to file
            log_simple_error(
                MARKDOWN_TO_XLSX_LOG_CanDoiKeToan,
                str(md_file),
                'markdown_to_xlsx',
                f"Failed to process markdown file: {error_msg}"
            )
            failed_files.append((display_name, error_msg))
    
    # Tổng kết
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    print(f"Total files processed: {len(md_files)}")
    print(f"Successful: {len(successful_files)}")
    print(f"Failed: {len(failed_files)}")
    
    if successful_files:
        print("\nSuccessful files:")
        for file_name, output_path in successful_files:
            print(f"  ✓ {file_name} -> {output_path}")
    
    if failed_files:
        print("\nFailed files:")
        for file_name, error_msg in failed_files:
            print(f"  ✗ {file_name}: {error_msg}")
    
    print("\nDone!")
    
    # Exit với code 1 nếu có file nào đó failed
    if failed_files:
        sys.exit(1)
    

if __name__ == "__main__":
    main()
