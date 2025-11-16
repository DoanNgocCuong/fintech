"""
Main function to convert markdown Báo cáo Tài chính (3 loại) to xlsx and JSON.

Module này xử lý cả 3 loại báo cáo tài chính từ file markdown:
1. Bảng Cân Đối Kế Toán
2. Báo cáo Kết quả Hoạt động Kinh doanh
3. Báo cáo Lưu chuyển Tiền tệ

CHỨC NĂNG:
----------
- process_all_financial_statements(): Xử lý cả 3 loại báo cáo từ một file markdown và lưu vào Excel + JSON

LOGIC:
------
1. Gọi break_pages_for_financial_statements() để xác định vị trí cả 3 loại báo cáo
2. Xử lý từng loại báo cáo:
   - Bảng Cân Đối Kế Toán: process_balance_sheet()
   - Kết quả Hoạt động Kinh doanh: process_income_statement()
   - Lưu chuyển Tiền tệ: process_cash_flow_statement()
3. Mỗi loại sẽ tạo file Excel và JSON riêng

YÊU CẦU:
--------
- pandas: Để xử lý dữ liệu và tạo Excel
- openpyxl: Để ghi file Excel (.xlsx)
- main_CanDoiKeToan_to_excelANDjson: Module để xử lý Bảng Cân Đối Kế Toán
- main_KetQuaHoatDongKinhDoanh_to_excelANDjson: Module để xử lý Kết quả Hoạt động Kinh doanh
- main_LuuChuyenTienTe_to_excelANDjson: Module để xử lý Lưu chuyển Tiền tệ
"""

import sys
from pathlib import Path
from typing import Optional, Dict, List, Tuple

# Import các hàm xử lý từ 3 module
from main_CanDoiKeToan_to_excelANDjson import process_balance_sheet
from main_KetQuaHoatDongKinhDoanh_to_excelANDjson import process_income_statement
from main_LuuChuyenTienTe_to_excelANDjson import process_cash_flow_statement

# Import hàm break pages để xác định vị trí
from main_breakPages_for_CanDoiKeToan_KetQuaHoatDongKinhDoanh_LuuChuyenTienTe import (
    break_pages_for_financial_statements
)
from utils_error_logger import (
    log_simple_error,
    MARKDOWN_TO_XLSX_LOG_CanDoiKeToan,
    MARKDOWN_TO_XLSX_LOG_KetQuaHoatDongKinhDoanh,
    MARKDOWN_TO_XLSX_LOG_LuuChuyenTienTe,
)


def process_all_financial_statements(
    input_file: str,
    output_dir: Optional[str] = None,
    skip_missing: bool = True,
    create_json: bool = True,
    replace_null_with: Optional[float] = None
) -> Dict[str, str]:
    """
    Xử lý cả 3 loại báo cáo tài chính từ một file markdown và lưu vào các file Excel + JSON.
    
    Quy trình:
    1. Gọi break_pages_for_financial_statements() để xác định vị trí cả 3 loại báo cáo
    2. Xử lý từng loại báo cáo:
       - Bảng Cân Đối Kế Toán
       - Kết quả Hoạt động Kinh doanh
       - Lưu chuyển Tiền tệ
    3. Mỗi loại sẽ tạo file Excel và JSON riêng
    
    Args:
        input_file (str): Đường dẫn đến file markdown đầu vào
        output_dir (Optional[str]): Thư mục để lưu các file output.
                                   Nếu None, lưu cùng thư mục với input_file
        skip_missing (bool): Nếu True, không raise error nếu không tìm thấy một loại báo cáo.
                            Nếu False, raise ValueError nếu thiếu bất kỳ loại nào
        create_json (bool): Nếu True, tạo file JSON từ Excel sau khi xử lý xong. Mặc định: True
        replace_null_with (Optional[float]): Giá trị để thay thế cho null trong JSON.
                                           Nếu None, giữ nguyên null.
                                           Nếu là số (ví dụ: 0), thay thế tất cả null thành số đó.
        
    Returns:
        Dict[str, str]: Dictionary chứa đường dẫn các file đã tạo:
        {
            "can_doi_ke_toan": "path/to/file_CanDoiKeToan.xlsx",
            "ket_qua_hoat_dong_kinh_doanh": "path/to/file_KetQuaHoatDongKinhDoanh.xlsx",
            "luu_chuyen_tien_te": "path/to/file_LuuChuyenTienTe.xlsx"
        }
        
    Raises:
        FileNotFoundError: Nếu file đầu vào không tồn tại
        ImportError: Nếu pandas hoặc openpyxl chưa được cài đặt
        ValueError: Nếu skip_missing=False và không tìm thấy một loại báo cáo nào đó
        
    Ví dụ:
        >>> results = process_all_financial_statements("BIC_2024_1_5_1.md")
        >>> print(results)
        {
            "can_doi_ke_toan": "BIC_2024_1_5_1_CanDoiKeToan.xlsx",
            "ket_qua_hoat_dong_kinh_doanh": "BIC_2024_1_5_1_KetQuaHoatDongKinhDoanh.xlsx",
            "luu_chuyen_tien_te": "BIC_2024_1_5_1_LuuChuyenTienTe.xlsx"
        }
    """
    input_path = Path(input_file)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    if not input_path.is_file():
        raise ValueError(f"Input path is not a file: {input_file}")
    
    # Xác định thư mục output
    if output_dir is None:
        output_dir = str(input_path.parent)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Kết quả
    results = {
        "can_doi_ke_toan": None,
        "ket_qua_hoat_dong_kinh_doanh": None,
        "luu_chuyen_tien_te": None
    }
    
    print("=" * 80)
    print(f"Processing ALL Financial Statements from: {input_file}")
    print("=" * 80)
    
    # Bước 1: Xác định vị trí các phần báo cáo tài chính
    print("\n" + "-" * 80)
    print("Step 1: Detecting financial statement locations...")
    print("-" * 80)
    try:
        page_locations = break_pages_for_financial_statements(str(input_file))
        
        # Kiểm tra xem có phần nào được detect không
        has_candoi = bool(page_locations.get("can_doi_ke_toan"))
        has_ketqua = bool(page_locations.get("ket_qua_hoat_dong_kinh_doanh"))
        has_luuchuyen = bool(page_locations.get("luu_chuyen_tien_te"))
        
        print(f"\nDetection Results:")
        print(f"  - Bảng cân đối kế toán: {'✓ Found' if has_candoi else '✗ Not found'}")
        print(f"  - Kết quả hoạt động kinh doanh: {'✓ Found' if has_ketqua else '✗ Not found'}")
        print(f"  - Lưu chuyển tiền tệ: {'✓ Found' if has_luuchuyen else '✗ Not found'}")
        
        if not (has_candoi or has_ketqua or has_luuchuyen):
            error_msg = "No financial statements detected in file"
            print(f"\n✗ {error_msg}")
            if not skip_missing:
                raise ValueError(error_msg)
            return results
        
    except Exception as e:
        error_msg = f"Error detecting financial statements: {str(e)}"
        print(f"\n✗ {error_msg}")
        if not skip_missing:
            raise
        return results
    
    # Bước 2: Xử lý từng loại báo cáo
    print("\n" + "=" * 80)
    print("Step 2: Processing each financial statement...")
    print("=" * 80)
    
    # 2.1. Xử lý Bảng Cân Đối Kế Toán
    print("\n" + "-" * 80)
    print("2.1. Processing: BANG CAN DOI KE TOAN (Balance Sheet)")
    print("-" * 80)
    try:
        result_path = process_balance_sheet(
            input_file=str(input_file),
            output_file=None,  # Tự động tạo tên file
            skip_missing=skip_missing,
            max_pages=None,  # Không giới hạn, vì đã xác định vị trí rồi
            create_json=create_json,
            replace_null_with=replace_null_with
        )
        results["can_doi_ke_toan"] = result_path
        print(f"\n✓ Successfully processed: {result_path}")
    except Exception as e:
        error_msg = str(e)
        try:
            print(f"\n✗ Error processing Balance Sheet: {error_msg}")
        except UnicodeEncodeError:
            print(f"\n[ERROR] Error processing Balance Sheet: {error_msg}")
        log_simple_error(
            MARKDOWN_TO_XLSX_LOG_CanDoiKeToan,
            str(input_file),
            'markdown_to_xlsx',
            f"Failed to process balance sheet: {error_msg}"
        )
        if not skip_missing:
            raise
        results["can_doi_ke_toan"] = None
    
    # 2.2. Xử lý Kết quả Hoạt động Kinh doanh
    print("\n" + "-" * 80)
    print("2.2. Processing: KET QUA HOAT DONG KINH DOANH (Income Statement)")
    print("-" * 80)
    try:
        result_path = process_income_statement(
            input_file=str(input_file),
            output_file=None,  # Tự động tạo tên file
            skip_missing=skip_missing,
            max_pages=None,  # Không giới hạn, vì đã xác định vị trí rồi
            create_json=create_json,
            replace_null_with=replace_null_with
        )
        results["ket_qua_hoat_dong_kinh_doanh"] = result_path
        print(f"\n✓ Successfully processed: {result_path}")
    except Exception as e:
        error_msg = str(e)
        try:
            print(f"\n✗ Error processing Income Statement: {error_msg}")
        except UnicodeEncodeError:
            print(f"\n[ERROR] Error processing Income Statement: {error_msg}")
        log_simple_error(
            MARKDOWN_TO_XLSX_LOG_KetQuaHoatDongKinhDoanh,
            str(input_file),
            'markdown_to_xlsx',
            f"Failed to process income statement: {error_msg}"
        )
        if not skip_missing:
            raise
        results["ket_qua_hoat_dong_kinh_doanh"] = None
    
    # 2.3. Xử lý Lưu chuyển Tiền tệ
    print("\n" + "-" * 80)
    print("2.3. Processing: LUU CHUYEN TIEN TE (Cash Flow Statement)")
    print("-" * 80)
    try:
        result_path = process_cash_flow_statement(
            input_file=str(input_file),
            output_file=None,  # Tự động tạo tên file
            skip_missing=skip_missing,
            max_pages=None,  # Không giới hạn, vì đã xác định vị trí rồi
            create_json=create_json,
            replace_null_with=replace_null_with
        )
        results["luu_chuyen_tien_te"] = result_path
        print(f"\n✓ Successfully processed: {result_path}")
    except Exception as e:
        error_msg = str(e)
        try:
            print(f"\n✗ Error processing Cash Flow Statement: {error_msg}")
        except UnicodeEncodeError:
            print(f"\n[ERROR] Error processing Cash Flow Statement: {error_msg}")
        log_simple_error(
            MARKDOWN_TO_XLSX_LOG_LuuChuyenTienTe,
            str(input_file),
            'markdown_to_xlsx',
            f"Failed to process cash flow statement: {error_msg}"
        )
        if not skip_missing:
            raise
        results["luu_chuyen_tien_te"] = None
    
    # Tổng kết
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    success_count = sum(1 for v in results.values() if v is not None)
    total_count = len(results)
    print(f"Successfully processed: {success_count}/{total_count} financial statements")
    
    if results["can_doi_ke_toan"]:
        print(f"  ✓ Bảng cân đối kế toán: {results['can_doi_ke_toan']}")
    else:
        print(f"  ✗ Bảng cân đối kế toán: Not processed")
    
    if results["ket_qua_hoat_dong_kinh_doanh"]:
        print(f"  ✓ Kết quả hoạt động kinh doanh: {results['ket_qua_hoat_dong_kinh_doanh']}")
    else:
        print(f"  ✗ Kết quả hoạt động kinh doanh: Not processed")
    
    if results["luu_chuyen_tien_te"]:
        print(f"  ✓ Lưu chuyển tiền tệ: {results['luu_chuyen_tien_te']}")
    else:
        print(f"  ✗ Lưu chuyển tiền tệ: Not processed")
    
    print("=" * 80)
    
    return results


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
    Hàm chính: Xử lý file markdown cho cả 3 loại báo cáo tài chính.
    Sử dụng:
        python main_3Tables_to_excelANDjson.py <input_file_or_folder>
    
    Nếu input là folder, sẽ xử lý tất cả file .md trong folder đó và tất cả các folder con (đệ quy).
    Nếu input là file, sẽ xử lý file đó.
    """
    input_path = None
    if len(sys.argv) >= 2:
        input_path = sys.argv[1]
    else:
        # Default file nếu không truyền argument
        input_path = str(Path(__file__).parent / "test" / "PGI_2024_1_5_1.md")
        if not Path(input_path).exists():
            print("Usage: python main_3Tables_to_excelANDjson.py <input_file_or_folder>")
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
            results = process_all_financial_statements(
                input_file=str(md_file),
                skip_missing=True,
                create_json=True
            )
            
            # Kiểm tra xem có file nào được tạo thành công không
            success_count = sum(1 for v in results.values() if v is not None)
            if success_count > 0:
                print(f"\n✓ Successfully processed: {display_name}")
                print(f"  Created {success_count} file(s)")
                successful_files.append((display_name, results))
            else:
                print(f"\n✗ No files created for: {display_name}")
                failed_files.append((display_name, "No financial statements detected"))
                
        except Exception as e:
            error_msg = str(e)
            try:
                print(f"\n✗ Error processing {display_name}: {error_msg}")
            except UnicodeEncodeError:
                print(f"\n[ERROR] Error processing {display_name}: {error_msg}")
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
        for file_name, results in successful_files:
            print(f"  ✓ {file_name}")
            for statement_type, file_path in results.items():
                if file_path:
                    print(f"      - {statement_type}: {file_path}")
    
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

