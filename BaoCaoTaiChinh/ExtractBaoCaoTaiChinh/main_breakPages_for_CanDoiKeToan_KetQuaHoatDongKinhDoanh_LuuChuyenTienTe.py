"""
Module phát hiện và xác định vị trí các phần trong báo cáo tài chính.

MÔ TẢ:
-------
Module này phân tích file markdown và xác định vị trí (trang số) của:
1. Bảng cân đối kế toán
2. Báo cáo kết quả hoạt động kinh doanh
3. Báo cáo lưu chuyển tiền tệ

LOGIC CHI TIẾT:
---------------

Bước 1: Đọc và Parse File Markdown
-----------------------------------
- Đọc file markdown từ đường dẫn input
- Parse file thành các trang sử dụng parse_markdown_pages()
- Format markdown: "Trang N" hoặc separator "---" để phân chia trang

Bước 2: Giới Hạn Phạm Vi Kiểm Tra
----------------------------------
- Chỉ kiểm tra 30 trang đầu: pages[:30]
- Lý do: Các báo cáo tài chính chính thường nằm ở đầu file

Bước 3: Quét Từng Trang (30 Trang Đầu)
---------------------------------------
Với mỗi trang, thực hiện:

3.1. Kiểm Tra Bảng Markdown (ĐIỀU KIỆN BẮT BUỘC)
    - Sử dụng extract_markdown_tables() để tìm bảng trong trang
    - Nếu KHÔNG có bảng → Skip trang này, không detect
    - Nếu CÓ bảng → Tiếp tục bước 3.2
    
    Lý do: Chỉ detect khi trang có bảng thực sự, tránh false positive
    khi chỉ có text mô tả mà không có bảng dữ liệu.

3.2. Detect Các Phần Báo Cáo Tài Chính
    Với mỗi loại báo cáo, chỉ check nếu:
    - Chưa detect được loại đó (flag = False)
    - Trang có bảng (đã check ở bước 3.1)
    
    a) Detect "Bảng cân đối kế toán":
       - Gọi detect_candoiketoan(page_content)
       - Nếu detect được:
         * Thêm vào result: {"page": page_num}
         * Set flag detected_candoiketoan = True
         * STOP: Không check loại này ở các trang sau nữa
    
    b) Detect "Báo cáo kết quả hoạt động kinh doanh":
       - Gọi detect_ketquahoatdongkinhdoanh(page_content)
       - Nếu detect được:
         * Thêm vào result: {"page": page_num}
         * Set flag detected_ketquahoatdongkinhdoanh = True
         * STOP: Không check loại này ở các trang sau nữa
    
    c) Detect "Báo cáo lưu chuyển tiền tệ":
       - Gọi detect_luuchuyentiente(page_content)
       - Nếu detect được:
         * Thêm vào result: {"page": page_num}
         * Set flag detected_luuchuyentiente = True
         * STOP: Không check loại này ở các trang sau nữa

3.3. Dừng Sớm (Early Exit)
    - Nếu đã detect được cả 3 phần → BREAK (dừng vòng lặp)
    - Không cần check các trang còn lại

Bước 4: Trả Về Kết Quả
-----------------------
Dictionary chứa vị trí (trang số) của mỗi phần:
{
    "can_doi_ke_toan": [{"page": 5}],
    "ket_qua_hoat_dong_kinh_doanh": [{"page": 3}],
    "luu_chuyen_tien_te": [{"page": 7}]
}

VÍ DỤ QUY TRÌNH:
----------------
Input: File markdown có 69 trang

1. Parse → 69 trang
2. Chỉ check 30 trang đầu
3. Quét từng trang:
   - Page 1: No tables → Skip
   - Page 2: Found 2 tables → Check detect → Detect "Bảng cân đối kế toán" (page 2) → STOP checking can_doi_ke_toan
   - Page 3: Found 1 table → Check detect → Detect "Kết quả hoạt động kinh doanh" (page 3) → STOP checking ket_qua_hoat_dong_kinh_doanh
   - Page 4: Found 1 table → Check detect → Detect "Lưu chuyển tiền tệ" (page 4) → STOP checking luu_chuyen_tien_te
   - All 3 detected → BREAK (dừng sớm)

Output:
{
    "can_doi_ke_toan": [{"page": 2}],
    "ket_qua_hoat_dong_kinh_doanh": [{"page": 3}],
    "luu_chuyen_tien_te": [{"page": 4}]
}

ĐIỂM QUAN TRỌNG:
----------------
1. ĐIỀU KIỆN BẮT BUỘC: Trang PHẢI có bảng markdown mới detect
2. NGẮT KHI DETECT: Mỗi loại chỉ detect 1 lần, dừng check khi tìm thấy
3. DỪNG SỚM: Nếu đã tìm thấy cả 3 phần, dừng ngay không cần check tiếp
4. GIỚI HẠN: Chỉ check 30 trang đầu để tối ưu hiệu năng

CHỨC NĂNG:
----------
- break_pages_for_financial_statements(): Phân tích file markdown và trả về vị trí các phần

YÊU CẦU:
--------
- Các module detect:
    * utils_markdownCanDoiKeToanText_DetectTable_to_xlsx (detect_candoiketoan)
    * utils_markdownKetQuaHoatDongKinhDoanhText_DetectTable_to_xlsx (detect_ketquahoatdongkinhdoanh)
    * utils_markdownLuuChuyenTienTeText_DetectTable_to_xlsx (detect_luuchuyentiente)
    * utils_prepare_process (parse_markdown_pages)
    * utils_markdownTable_to_xlsx (extract_markdown_tables)
"""

from pathlib import Path
from typing import Dict, List

# Import detect functions
from utils_markdownCanDoiKeToanText_DetectTable_to_xlsx import detect_candoiketoan
from utils_markdownKetQuaHoatDongKinhDoanhText_DetectTable_to_xlsx import detect_ketquahoatdongkinhdoanh
from utils_markdownLuuChuyenTienTeText_DetectTable_to_xlsx import detect_luuchuyentiente
from utils_prepare_process import parse_markdown_pages
from utils_markdownTable_to_xlsx import extract_markdown_tables


def break_pages_for_financial_statements(
    input_file: str
) -> Dict[str, List[Dict[str, any]]]:
    """
    Phân tích file markdown và xác định vị trí các phần trong báo cáo tài chính.
    
    Args:
        input_file (str): Đường dẫn đến file markdown đầu vào
        
    Returns:
        Dict[str, List[Dict[str, any]]]: Dictionary chứa vị trí các phần (chỉ check 30 trang đầu):
        {
            "can_doi_ke_toan": [
                {"page": 5}
            ],
            "ket_qua_hoat_dong_kinh_doanh": [
                {"page": 3}
            ],
            "luu_chuyen_tien_te": [
                {"page": 7}
            ]
        }
        
    Raises:
        FileNotFoundError: Nếu file đầu vào không tồn tại
    """
    input_path = Path(input_file)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Đọc file markdown
    print(f"Reading file: {input_file}")
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse markdown thành các trang
    print("Parsing markdown pages...")
    pages = parse_markdown_pages(content)
    print(f"  Found {len(pages)} page(s)")
    
    # Chỉ check 30 trang đầu
    pages_to_check = pages[:30]
    print(f"  Checking first {len(pages_to_check)} page(s) only")
    
    # Khởi tạo kết quả
    result = {
        "can_doi_ke_toan": [],
        "ket_qua_hoat_dong_kinh_doanh": [],
        "luu_chuyen_tien_te": []
    }
    
    # Flags để track xem đã detect được phần nào chưa (ngắt khi detect được)
    detected_candoiketoan = False
    detected_ketquahoatdongkinhdoanh = False
    detected_luuchuyentiente = False
    
    # Quét qua từng trang (chỉ 30 trang đầu)
    print("\nDetecting financial statements in each page...")
    for page_num, page_content in pages_to_check:
        print(f"\n  Page {page_num}:")
        
        # Kiểm tra xem trang có bảng markdown không
        tables = extract_markdown_tables(page_content)
        has_table = len(tables) > 0
        
        if not has_table:
            print(f"    [-] No tables found in page {page_num}, skipping detection")
            continue
        
        print(f"    [*] Found {len(tables)} table(s) in page {page_num}")
        
        # 1. Detect Bảng cân đối kế toán (chỉ check nếu chưa detect được và có bảng)
        if not detected_candoiketoan and detect_candoiketoan(page_content):
            result["can_doi_ke_toan"].append({
                "page": page_num
            })
            detected_candoiketoan = True
            print(f"    [+] Bảng cân đối kế toán detected (page {page_num}) - STOP checking this type")
        
        # 2. Detect Báo cáo kết quả hoạt động kinh doanh (chỉ check nếu chưa detect được và có bảng)
        if not detected_ketquahoatdongkinhdoanh and detect_ketquahoatdongkinhdoanh(page_content):
            result["ket_qua_hoat_dong_kinh_doanh"].append({
                "page": page_num
            })
            detected_ketquahoatdongkinhdoanh = True
            print(f"    [+] Kết quả hoạt động kinh doanh detected (page {page_num}) - STOP checking this type")
        
        # 3. Detect Báo cáo lưu chuyển tiền tệ (chỉ check nếu chưa detect được và có bảng)
        if not detected_luuchuyentiente and detect_luuchuyentiente(page_content):
            result["luu_chuyen_tien_te"].append({
                "page": page_num
            })
            detected_luuchuyentiente = True
            print(f"    [+] Lưu chuyển tiền tệ detected (page {page_num}) - STOP checking this type")
        
        # Nếu đã detect được cả 3 phần, có thể dừng sớm
        if detected_candoiketoan and detected_ketquahoatdongkinhdoanh and detected_luuchuyentiente:
            print(f"\n  All 3 financial statements detected. Stopping early at page {page_num}.")
            break
    
    # Tóm tắt kết quả
    print("\n" + "=" * 80)
    print("SUMMARY:")
    print("=" * 80)
    print(f"Bảng cân đối kế toán: {len(result['can_doi_ke_toan'])} page(s)")
    for item in result['can_doi_ke_toan']:
        print(f"  - Page {item['page']}")
    
    print(f"\nKết quả hoạt động kinh doanh: {len(result['ket_qua_hoat_dong_kinh_doanh'])} page(s)")
    for item in result['ket_qua_hoat_dong_kinh_doanh']:
        print(f"  - Page {item['page']}")
    
    print(f"\nLưu chuyển tiền tệ: {len(result['luu_chuyen_tien_te'])} page(s)")
    for item in result['luu_chuyen_tien_te']:
        print(f"  - Page {item['page']}")
    
    return result


def main():
    """
    Hàm chính để test module.
    """
    import sys
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        # Default file for testing
        input_file = Path(__file__).parent / "test" / "PGI_2024_1_5_1.md"
    
    try:
        result = break_pages_for_financial_statements(str(input_file))
        
        # In kết quả dạng JSON
        import json
        print("\n" + "=" * 80)
        print("JSON OUTPUT:")
        print("=" * 80)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()

