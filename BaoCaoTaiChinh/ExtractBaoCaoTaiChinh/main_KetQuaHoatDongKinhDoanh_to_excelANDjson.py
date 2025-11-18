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
   - Sử dụng detect_ketquahoatdongkinhdoanh để phát hiện Kết quả Hoạt động Kinh doanh
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
    │  ├─ detect_ketquahoatdongkinhdoanh(page_content) ← CHECK TỪNG TRANG
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
from collections import defaultdict
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any

# Import các hàm dùng chung từ utils_prepare_process
from utils_prepare_process import (
    parse_markdown_pages,
    process_pages_for_financial_statements,
    parse_ma_so,
    replace_null_in_dict,
)
from utils_error_logger import (
    log_simple_error,
    XLSX_TO_JSON_LOG_KetQuaHoatDongKinhDoanh,
    MARKDOWN_TO_XLSX_LOG_KetQuaHoatDongKinhDoanh,
)

try:
    import pandas as pd
except ImportError:
    pd = None

# Income templates per section
_INCOME_TEMPLATE_JSON_PATHS = {
    "P1": Path(__file__).parent / "income_template_json_P1.json",
    "P2": Path(__file__).parent / "income_template_json_P2.json",
}
_DEFAULT_INCOME_SECTION = "P2"

# Import detection functions và utilities
from utils_markdownKetQuaHoatDongKinhDoanhText_DetectTable_to_xlsx import (
    detect_ketquahoatdongkinhdoanh,
    detect_income_statement_section_tag,
)
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
# - process_pages_for_income_statement() -> process_pages_for_financial_statements(pages, detect_ketquahoatdongkinhdoanh)
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
    replace_null_with: Optional[float] = None,
    page_locations: Optional[Dict] = None
) -> str:
    """
    Xử lý Kết quả Hoạt động Kinh doanh từ một file markdown và lưu vào một file Excel.
    
    Quy trình:
    1. Đọc file markdown
    2. Gọi break_pages_for_financial_statements() để xác định vị trí "Kết quả hoạt động kinh doanh"
    3. Lấy page number được detect (ví dụ: page 13)
    4. Xử lý các trang từ page được detect đến page + 3 (ví dụ: page 13, 14, 15, 16)
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
    
    if not input_path.is_file():
        raise ValueError(f"Input path is not a file: {input_file}")
    
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
    
    # Lấy page number của "Kết quả hoạt động kinh doanh"
    ket_qua_pages = []
    if page_locations.get("ket_qua_hoat_dong_kinh_doanh"):
        detected_page = page_locations["ket_qua_hoat_dong_kinh_doanh"][0]["page"]
        
        # Xác định page kết thúc: không được vượt quá page của "Lưu chuyển tiền tệ" (nếu có)
        end_page = detected_page + 4  # Mặc định: 4 trang (page, page+1, page+2, page+3)
        if page_locations.get("luu_chuyen_tien_te"):
            luu_chuyen_page = page_locations["luu_chuyen_tien_te"][0]["page"]
            # Không được đọc đến trang của "Lưu chuyển tiền tệ"
            end_page = min(end_page, luu_chuyen_page)
        
        ket_qua_pages = list(range(detected_page, end_page))
        print(f"  Found 'Kết quả hoạt động kinh doanh' at page {detected_page}")
        print(f"  Will process pages: {ket_qua_pages} (stopping before next statement)")
    else:
        print("  No 'Kết quả hoạt động kinh doanh' detected")
        if not skip_missing:
            raise ValueError("No 'Kết quả hoạt động kinh doanh' detected in file")
        return str(output_path)
    
    # Parse thành các trang
    print("\nParsing pages...")
    all_pages = parse_markdown_pages(content)
    total_pages = len(all_pages)
    print(f"  Found {total_pages} page(s) in total")
    
    # Chỉ lấy các trang cần xử lý (từ ket_qua_pages)
    pages_dict = {page_num: page_content for page_num, page_content in all_pages}
    pages_to_process = []
    for page_num in ket_qua_pages:
        if page_num in pages_dict:
            pages_to_process.append((page_num, pages_dict[page_num]))
    
    if not pages_to_process:
        print("  No pages to process")
        if not skip_missing:
            raise ValueError("No pages found for 'Kết quả hoạt động kinh doanh'")
        return str(output_path)
    
    print(f"  Processing {len(pages_to_process)} page(s): {[p[0] for p in pages_to_process]}")
    
    print("\n" + "-" * 80)
    print("Processing: KET QUA HOAT DONG KINH DOANH (Income Statement)")
    print("-" * 80)

    sectioned_pages: List[Tuple[str, int, List[str]]] = []
    first_page_section = _DEFAULT_INCOME_SECTION
    if pages_to_process:
        first_page_content = pages_to_process[0][1]
        first_page_section = detect_income_statement_section_tag(first_page_content)

    for idx, (page_num, page_content) in enumerate(pages_to_process):
        section = "P1" if (idx == 0 and first_page_section == "P1") else "P2"
        tables = extract_markdown_tables(page_content)
        if tables:
            sectioned_pages.append((section, page_num, tables))

    if not sectioned_pages:
        print("  ✗ No pages found with income statement")
        if not skip_missing:
            raise ValueError("No pages found with income statement")
    else:
        print(f"  Found {len(sectioned_pages)} page(s) with income statement")

    section_tables: Dict[str, List[Tuple[int, List[str]]]] = defaultdict(list)
    for section, page_num, tables in sectioned_pages:
        section_tables[section].append((page_num, tables))

    excel_files: Dict[str, str] = {}
    sheet_count_by_section: Dict[str, int] = {}

    for section, page_table_list in section_tables.items():
        if not page_table_list:
            continue

        section_output_path = output_path.parent / f"{output_path.stem}_{section}.xlsx"
        print(f"\nCreating Excel file for section {section}: {section_output_path}")

        try:
            with pd.ExcelWriter(str(section_output_path), engine='openpyxl') as writer:
                sheet_counter = 0
                table_idx = 1
                total_tables = sum(len(tables) for _, tables in page_table_list)

                for page_num, tables in page_table_list:
                    print(f"  Processing page {page_num} (section {section})...")
                    for table_text in tables:
                        rows = _parse_markdown_table(table_text)
                        if not rows or len(rows) < 2:
                            continue

                        df = _create_dataframe_from_rows(rows)
                        df = _remove_last_column(df)

                        if total_tables == 1:
                            sheet_name = f"KetQua_{section}"[:31]
                        elif len(page_table_list) == 1:
                            sheet_name = f"KetQua_{section}_T{table_idx}"[:31]
                        else:
                            sheet_name = f"{section}_P{page_num}_T{table_idx}"[:31]

                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                        sheet_counter += 1
                        print(f"    ✓ Added sheet: {sheet_name}")
                        table_idx += 1

                if sheet_counter > 0:
                    excel_files[section] = str(section_output_path)
                    sheet_count_by_section[section] = sheet_counter
                else:
                    print(f"  ✗ No valid tables found for section {section}, skipping file.")
                    section_output_path.unlink(missing_ok=True)  # Remove empty file if created
        except Exception as e:
            error_msg = str(e)
            try:
                print(f"  ✗ Error processing section {section}: {error_msg}")
            except UnicodeEncodeError:
                print(f"  [ERROR] Error processing section {section}: {error_msg}")
            log_simple_error(
                MARKDOWN_TO_XLSX_LOG_KetQuaHoatDongKinhDoanh,
                str(input_file),
                'markdown_to_xlsx',
                f"Income statement processing failed for section {section}: {error_msg}"
            )
            if not skip_missing:
                raise
    
    # Tổng kết Excel
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    total_sheets_created = sum(sheet_count_by_section.values())
    if excel_files:
        print(f"Total sections exported: {len(excel_files)}")
        for section, path in excel_files.items():
            sheets = sheet_count_by_section.get(section, 0)
            print(f"  ✓ Section {section}: {path} ({sheets} sheet(s))")
    else:
        print("  ✗ No Excel files were created.")
    print(f"Total sheets created: {total_sheets_created}")
    
    # Tạo JSON từ Excel nếu được yêu cầu
    json_files: Dict[str, str] = {}
    if create_json and excel_files:
        print("\n" + "-" * 80)
        print("Creating JSON files from Excel...")
        print("-" * 80)
        from utils_xlsx_to_json_income import create_json_result
        for section, excel_file in excel_files.items():
            try:
                json_output_file = str(Path(excel_file).with_suffix(".json"))
                create_json_result(
                    excel_file=excel_file,
                    output_json_file=json_output_file,
                    replace_null_with=replace_null_with,
                    section=section
                )
                json_files[section] = json_output_file
                print(f"  ✓ JSON ({section}) created: {json_output_file}")
            except Exception as e:
                error_msg = str(e)
                try:
                    print(f"  ✗ Error creating JSON for section {section}: {error_msg}")
                except UnicodeEncodeError:
                    print(f"  [ERROR] Error creating JSON for section {section}: {error_msg}")
                log_simple_error(
                    XLSX_TO_JSON_LOG_KetQuaHoatDongKinhDoanh,
                    excel_file,
                    'xlsx_to_json',
                    f"Failed to create JSON from Excel ({section}): {error_msg}"
                )
                if not skip_missing:
                    raise
    
    print("=" * 80)
    
    primary_excel = excel_files.get("P2") or excel_files.get("P1")
    return primary_excel if primary_excel else str(output_path)



def _get_income_statement_json_template(
    section: str = _DEFAULT_INCOME_SECTION,
    replace_null_with: Optional[float] = None
) -> Dict[str, Any]:
    """
    Load cấu trúc JSON template cho Kết quả Hoạt động Kinh doanh theo từng phần (P1/P2).
    
    Cấu trúc: Nested/hierarchical structure - mỗi section có ma_so, so_cuoi_nam và chứa các section con bên trong.
    
    Args:
        section (str): Section identifier ("P1" hoặc "P2"). Default: P2.
        replace_null_with (Optional[float]): Giá trị để thay thế cho null trong JSON.
                                           Nếu None, giữ nguyên null (sẽ được convert thành None trong Python).
                                           Nếu là số (ví dụ: 0), thay thế tất cả null thành số đó.
    
    Returns:
        Dict[str, Any]: Cấu trúc JSON template với tất cả các mã số và giá trị
    
    Raises:
        FileNotFoundError: Nếu template tương ứng không tồn tại
        ValueError: Nếu section không hợp lệ
    
    Ví dụ:
        >>> template = _get_income_statement_json_template("P1")  # Giữ nguyên null
        >>> template = _get_income_statement_json_template("P2", replace_null_with=0)  # Thay null thành 0
    """
    section_key = (section or _DEFAULT_INCOME_SECTION).upper()
    template_path = _INCOME_TEMPLATE_JSON_PATHS.get(section_key)
    if template_path is None:
        raise ValueError(f"Unsupported income statement section: {section}")
    if not template_path.exists():
        raise FileNotFoundError(
            f"Income template JSON file not found for section {section_key}: {template_path}"
        )
    
    # Load JSON từ file
    with open(template_path, 'r', encoding='utf-8') as f:
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
    Hàm chính: Xử lý file markdown Kết quả Hoạt động Kinh doanh.
    Sử dụng:
        python main_KetQuaHoatDongKinhDoanh.py <input_file_or_folder>
    
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
            print("Usage: python main_KetQuaHoatDongKinhDoanh.py <input_file_or_folder>")
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
            result_path = process_income_statement(
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
                MARKDOWN_TO_XLSX_LOG_KetQuaHoatDongKinhDoanh,
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

