"""
Module chung để chuyển đổi Excel (.xlsx) sang JSON cho tất cả các loại báo cáo tài chính.

Module này hỗ trợ 3 loại báo cáo:
1. Bảng Cân Đối Kế Toán (Balance Sheet)
2. Báo cáo Kết quả Hoạt động Kinh doanh (Income Statement)
3. Báo cáo Lưu chuyển Tiền tệ (Cash Flow Statement)

CHỨC NĂNG:
----------
- create_json_result(): Hàm chung để chuyển đổi Excel sang JSON
- Hỗ trợ tự động detect format số (VN format vs US format)
- Hỗ trợ mã số chính và mã số phụ (1.1, 1.2, etc.)
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any, Callable

try:
    import pandas as pd
except ImportError:
    pd = None

from utils_prepare_process import (
    find_ma_so_column,
    find_value_column,
    parse_ma_so,
    parse_ma_so_full,
    parse_number,
    update_json_with_ma_so,
    update_json_with_ma_so_full
)


def _replace_nan_with_string(data: Any) -> Any:
    """
    Recursively replace NaN (and pandas NA) with the string "nan"
    to avoid invalid JSON tokens.
    
    Args:
        data: Any data structure (dict, list, primitive)
        
    Returns:
        Data structure with NaN replaced by "nan" string
    """
    try:
        import math
    except Exception:
        math = None

    if data is None:
        return data

    # Handle float NaN
    if isinstance(data, float):
        if (math is not None and math.isnan(data)) or (pd is not None and pd.isna(data)):
            return "nan"
        return data

    # Handle pandas NA scalars
    if pd is not None:
        try:
            if pd.isna(data):
                return "nan"
        except Exception:
            pass

    if isinstance(data, dict):
        return {k: _replace_nan_with_string(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_replace_nan_with_string(v) for v in data]

    return data


def create_json_result(
    excel_file: str,
    json_template_func: Callable[[Optional[float]], Dict[str, Any]],
    output_json_file: Optional[str] = None,
    replace_null_with: Optional[float] = None,
    sanitize_nan: bool = True
) -> Dict[str, Any]:
    """
    Đọc file Excel và tạo JSON result từ các sheets đã tạo.
    
    Hàm chung này có thể dùng cho tất cả các loại báo cáo tài chính:
    - Bảng Cân Đối Kế Toán
    - Báo cáo Kết quả Hoạt động Kinh doanh
    - Báo cáo Lưu chuyển Tiền tệ
    
    LOGIC:
    ------
    1. Đọc file Excel (tất cả sheets)
    2. Với mỗi sheet:
       a. Tìm cột mã số và cột giá trị
       b. Duyệt từng dòng:
          - Parse mã số (hỗ trợ mã số phụ như 1.1, 1.2)
          - Parse giá trị (hỗ trợ format VN và US)
          - Map vào JSON template dựa trên mã số
    3. Lưu kết quả vào file JSON
    
    Args:
        excel_file (str): Đường dẫn đến file Excel đã tạo
        json_template_func (Callable): Hàm tạo JSON template. 
                                      Nhận tham số replace_null_with và trả về Dict
                                      Ví dụ: _get_balance_sheet_json_template
        output_json_file (Optional[str]): Đường dẫn đến file JSON output.
                                         Nếu None, tự động tạo tên file dựa trên excel_file
        replace_null_with (Optional[float]): Giá trị để thay thế cho null trong JSON template.
                                           Nếu None, giữ nguyên null.
                                           Nếu là số (ví dụ: 0), thay thế tất cả null thành số đó.
        sanitize_nan (bool): Nếu True, thay thế NaN bằng string "nan" để tránh lỗi JSON.
                            Mặc định: True
                                         
    Returns:
        Dict[str, Any]: JSON structure đã được cập nhật với các giá trị từ Excel
        
    Raises:
        FileNotFoundError: Nếu file Excel không tồn tại
        ImportError: Nếu pandas chưa được cài đặt
        
    Ví dụ:
        >>> from main_CanDoiKeToan_to_excelANDjson import _get_balance_sheet_json_template
        >>> result = create_json_result(
        ...     "BMI_2024_1_5_1_CanDoiKeToan.xlsx",
        ...     _get_balance_sheet_json_template
        ... )
        
        >>> from main_LuuChuyenTienTe_to_excelANDjson import _get_cash_flow_statement_json_template
        >>> result = create_json_result(
        ...     "BMI_2024_1_5_1_LuuChuyenTienTe.xlsx",
        ...     _get_cash_flow_statement_json_template,
        ...     replace_null_with=0
        ... )
    """
    if pd is None:
        raise ImportError("pandas is required. Install with: pip install pandas openpyxl")
    
    excel_path = Path(excel_file)
    
    if not excel_path.exists():
        raise FileNotFoundError(f"Excel file not found: {excel_file}")
    
    # Tạo JSON template với option replace null
    json_result = json_template_func(replace_null_with=replace_null_with)
    
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
            
            # Parse mã số đầy đủ (hỗ trợ mã số phụ như 1.1, 1.2, 01.1, 01.2)
            ma_so_full = parse_ma_so_full(str(ma_so_str))
            if ma_so_full is None:
                continue
            
            value = row.get(value_col)
            parsed_value = parse_number(value)
            
            # Thử cập nhật với mã số đầy đủ trước (hỗ trợ mã số phụ)
            updated = False
            if ma_so_full and '.' in ma_so_full:
                # Mã số phụ (1.1, 1.2, etc.) - dùng update_json_with_ma_so_full
                updated = update_json_with_ma_so_full(json_result, ma_so_full, parsed_value)
            else:
                # Mã số chính (1, 2, 3, etc.) - thử cả hai cách
                # Ưu tiên dùng update_json_with_ma_so_full (nếu template có ma_so dạng string)
                updated = update_json_with_ma_so_full(json_result, ma_so_full, parsed_value)
                if not updated:
                    # Fallback: dùng update_json_with_ma_so (nếu template có ma_so dạng int)
                    ma_so_int = parse_ma_so(str(ma_so_str))
                    if ma_so_int is not None:
                        updated = update_json_with_ma_so(json_result, ma_so_int, parsed_value)
            
            if updated:
                mapped_in_sheet += 1
                total_mapped += 1
                if parsed_value is not None:
                    try:
                        print(f"      OK Mapped ma so {ma_so_full}: {parsed_value:,.0f}")
                    except UnicodeEncodeError:
                        print(f"      OK Mapped ma so {ma_so_full}: {parsed_value}")
        
        print(f"    Mapped {mapped_in_sheet} value(s) in sheet {sheet_name}")
    
    print(f"\n  Total mapped: {total_mapped} value(s)")
    
    # Chuẩn hóa NaN trước khi lưu (nếu cần)
    if sanitize_nan:
        sanitized_result = _replace_nan_with_string(json_result)
    else:
        sanitized_result = json_result
    
    # Lưu vào file JSON nếu có output_file
    # SỐ ĐƯỢC LƯU DƯỚI DẠNG NUMBER (không có dấu phân cách hàng nghìn) - Đúng chuẩn JSON
    if output_json_file:
        output_path = Path(output_json_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(sanitized_result, f, ensure_ascii=False, indent=2, allow_nan=False)
        
        print(f"\n  JSON saved to: {output_json_file}")
    else:
        # Tự động tạo tên file JSON
        json_file = excel_path.parent / f"{excel_path.stem}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(sanitized_result, f, ensure_ascii=False, indent=2, allow_nan=False)
        
        print(f"\n  JSON saved to: {json_file}")
    
    return sanitized_result

