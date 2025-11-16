"""
Module để chuyển đổi Excel (.xlsx) sang JSON cho Báo cáo Lưu chuyển Tiền tệ.

Module này giữ lại backward compatibility với code cũ.
Thực tế sử dụng utils_xlsx_to_json.create_json_result() chung.
"""

from typing import Optional, Dict, Any

from main_LuuChuyenTienTe_to_excelANDjson import _get_cash_flow_statement_json_template
from utils_xlsx_to_json import create_json_result as _create_json_result


def create_json_result(
    excel_file: str, 
    output_json_file: Optional[str] = None,
    replace_null_with: Optional[float] = None
) -> Dict[str, Any]:
    """
    Đọc file Excel và tạo JSON result từ các sheets đã tạo.
    
    Hàm này wrap lại utils_xlsx_to_json.create_json_result() với template
    của Báo cáo Lưu chuyển Tiền tệ để giữ backward compatibility.
    
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
        >>> json_result = create_json_result("BMI_2024_1_5_1_LuuChuyenTienTe.xlsx")
        >>> # Replace null với 0
        >>> json_result = create_json_result("BMI_2024_1_5_1_LuuChuyenTienTe.xlsx", replace_null_with=0)
    """
    return _create_json_result(
        excel_file=excel_file,
        json_template_func=_get_cash_flow_statement_json_template,
        output_json_file=output_json_file,
        replace_null_with=replace_null_with,
        sanitize_nan=False  # Cash flow statement không cần sanitize NaN
    )

