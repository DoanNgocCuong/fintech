import json
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import pandas as pd
except ImportError:
    pd = None

from main_CanDoiKeToan import _get_balance_sheet_json_template
from utils_prepare_process import (
    find_ma_so_column,
    find_value_column,
    parse_ma_so,
    parse_number,
    update_json_with_ma_so
)


def create_json_result(
    excel_file: str, 
    output_json_file: Optional[str] = None,
    replace_null_with: Optional[float] = None
) -> Dict[str, Any]:
    """
    Đọc file Excel và tạo JSON result từ các sheets đã tạo.
    
    Hàm này sẽ:
    1. Đọc file Excel
    2. Đi qua từng sheet
    3. Tìm các dòng có mã số tương ứng với JSON structure
    4. Lấy giá trị từ cột "Năm nay" hoặc "Số cuối năm"
    5. Map vào JSON structure
    
    Args:
        excel_file (str): Đường dẫn đến file Excel đã tạo
        output_json_file (Optional[str]): Đường dẫn đến file JSON output.
                                         Nếu None, tự động tạo tên file dựa trên excel_file
        replace_null_with (Optional[float]): Giá trị để thay thế cho null trong JSON template.
                                           Nếu None, giữ nguyên null.
                                           Nếu là số (ví dụ: 0), thay thế tất cả null thành số đó.
        
    Returns:
        Dict[str, Any]: JSON structure đã được cập nhật với các giá trị từ Excel
        
    Raises:
        FileNotFoundError: Nếu file Excel không tồn tại
        ImportError: Nếu pandas chưa được cài đặt
        
    Ví dụ:
        >>> json_result = create_json_result("BMI_2024_1_5_1_CanDoiKeToan.xlsx")
        >>> print(json_result["can_doi_ke_toan"]["tai_san"]["A_tai_san_ngan_han_100"]["I_tien_va_cac_khoan_tuong_duong_tien_110"]["1_tien_111"])
        {'ma_so': 111, 'so_cuoi_nam': 1234567890.0}
        
        >>> # Replace null với 0
        >>> json_result = create_json_result("BMI_2024_1_5_1_CanDoiKeToan.xlsx", replace_null_with=0)
    """
    if pd is None:
        raise ImportError("pandas is required. Install with: pip install pandas openpyxl")
    
    excel_path = Path(excel_file)
    
    if not excel_path.exists():
        raise FileNotFoundError(f"Excel file not found: {excel_file}")
    
    # Tạo JSON template với option replace null
    json_result = _get_balance_sheet_json_template(replace_null_with=replace_null_with)
    
    # Đọc file Excel
    print(f"Reading Excel file: {excel_file}")
    excel_file_obj = pd.ExcelFile(str(excel_path))
    sheet_names = excel_file_obj.sheet_names
    
    print(f"  Found {len(sheet_names)} sheet(s): {', '.join(sheet_names)}")
    
    # Đi qua từng sheet
    total_mapped = 0
    for sheet_name in sheet_names:
        print(f"\n  Processing sheet: {sheet_name}")
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        
        if df.empty:
            print(f"    Warning: Sheet {sheet_name} is empty, skipping...")
            continue
        
        # Tìm cột mã số và cột giá trị
        ma_so_col = find_ma_so_column(df)
        value_col = find_value_column(df)
        
        if not ma_so_col:
            print(f"    Warning: Cannot find 'Ma so' column in sheet {sheet_name}, skipping...")
            continue
        
        if not value_col:
            print(f"    Warning: Cannot find value column in sheet {sheet_name}, skipping...")
            continue
        
        # Print column names (avoid Unicode issues in Windows console)
        try:
            print(f"    Using columns: Ma so='{ma_so_col}', Value='{value_col}'")
        except UnicodeEncodeError:
            print(f"    Using columns: Ma so column found, Value column found")
        
        # Đi qua từng dòng và map giá trị
        mapped_in_sheet = 0
        for idx, row in df.iterrows():
            ma_so_str = row.get(ma_so_col)
            if pd.isna(ma_so_str):
                continue
            
            ma_so = parse_ma_so(str(ma_so_str))
            if ma_so is None:
                continue
            
            value = row.get(value_col)
            parsed_value = parse_number(value)
            
            # Cập nhật vào JSON
            if update_json_with_ma_so(json_result, ma_so, parsed_value):
                mapped_in_sheet += 1
                total_mapped += 1
                if parsed_value is not None:
                    try:
                        print(f"      OK Mapped ma so {ma_so}: {parsed_value:,.0f}")
                    except UnicodeEncodeError:
                        print(f"      OK Mapped ma so {ma_so}: {parsed_value}")
        
        print(f"    Mapped {mapped_in_sheet} value(s) in sheet {sheet_name}")
    
    print(f"\n  Total mapped: {total_mapped} value(s)")
    
    # Lưu vào file JSON nếu có output_file
    # SỐ ĐƯỢC LƯU DƯỚI DẠNG NUMBER (không có dấu phân cách hàng nghìn) - Đúng chuẩn JSON
    if output_json_file:
        output_path = Path(output_json_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_result, f, ensure_ascii=False, indent=2)
        
        print(f"\n  JSON saved to: {output_json_file}")
    else:
        # Tự động tạo tên file JSON
        json_file = excel_path.parent / f"{excel_path.stem}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_result, f, ensure_ascii=False, indent=2)
        
        print(f"\n  JSON saved to: {json_file}")
    
    return json_result
