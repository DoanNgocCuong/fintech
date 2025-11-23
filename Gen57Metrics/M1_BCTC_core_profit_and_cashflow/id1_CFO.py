"""
CFO (Cash Flow from Operations) Indicator.

This is a DirectIndicator that retrieves CFO value directly from database.
According to 57BaseIndicators.json:
- ID: 1
- Indicator_Name: "CFO"
- Definition: "Dòng tiền thuần từ hoạt động kinh doanh"
- Get_Direct_From_DB: "yes"
- TT200_Formula: "LCTT (TT200) – Mã 20 (gián tiếp) hoặc Mã 21 (trực tiếp)"

Note: CFO is from cash flow statement (LCTT), using ma_so 20 (indirect) or 21 (direct)
"""

from typing import Optional
from Gen57Metrics.utils_database_manager import get_value_by_ma_so, get_legal_framework


def get_CFO_value(
    stock: str, 
    year: int, 
    quarter: Optional[int] = None,
    legal_framework: Optional[str] = None
) -> Optional[float]:
    """
    Lấy giá trị CFO (Dòng tiền thuần từ hoạt động kinh doanh) cho cổ phiếu và kỳ báo cáo chỉ định.

    - CFO lấy từ Báo cáo lưu chuyển tiền tệ (LCTT), sử dụng mã số tương ứng với bộ luật.
    - Mã số được map dựa trên bộ luật (legal_framework):
      * TT199_2014: ma_so 20 (gián tiếp) hoặc 21 (trực tiếp)
      * TT232_2012: ma_so 20 (gián tiếp) hoặc 21 (trực tiếp)
    - Thử truy vấn mã số gián tiếp trước. Nếu không có dữ liệu thì thử tiếp mã số trực tiếp.

    Tham số:
        stock: Mã cổ phiếu, ví dụ: "MIG", "PGI", "BIC".
        year: Năm tài chính, ví dụ: 2024.
        quarter: Quý (1-4), hoặc None cho báo cáo năm.
        legal_framework: Tên bộ luật (ví dụ: "TT199_2014", "TT232_2012"). 
                        Nếu None, sẽ tự động lấy từ database dựa trên stock.

    Kết quả trả về:
        Optional[float]: Giá trị CFO lấy từ database, hoặc None nếu không tìm thấy.

    Ví dụ:
        >>> # Lấy CFO năm của MIG năm 2024
        >>> cfo = get_CFO_value("MIG", 2024)
        >>> print(cfo)
        1234567890.0

        >>> # Lấy CFO quý 2 của MIG năm 2024
        >>> cfo_q2 = get_CFO_value("MIG", 2024, quarter=2)
        >>> print(cfo_q2)
        9876543210.0
        
## Dòng tiền thuần từ hoạt động kinh doanh (Trực tiếp)
CFO = Tổng tiền thu vào từ bán hàng, cung cấp dịch vụ
    - Tổng tiền chi ra để mua hàng hóa, dịch vụ
    - Tổng tiền chi trả cho nhân viên
    - Chi phí quản lý doanh nghiệp
    - Chi phí trả lãi vay
    - Tiền nộp các loại thuế
    
## Dòng tiền thuần từ hoạt động kinh doanh (Gián tiếp)
CFO = Lợi nhuận trước thuế và lãi vay (EBIT)
    + Khấu hao tài sản cố định
    + Dự phòng (giảm giá hàng tồn kho, phải thu, đầu tư tài chính, ...)
    + Chi phí/lợi nhuận phi tiền mặt
    ± Thay đổi vốn lưu động:
        - Tăng (giảm) khoản phải thu
        - Tăng (giảm) hàng tồn kho
        - Tăng (giảm) khoản phải trả
    - Chi phí lãi vay thực trả
    - Thuế thu nhập doanh nghiệp thực trả    

    """
    # Get legal framework if not provided
    if legal_framework is None:
        legal_framework = get_legal_framework(stock)
    
    # Normalize legal framework name
    if legal_framework:
        legal_framework = legal_framework.strip().upper()
        if legal_framework == "TT199" or legal_framework.startswith("TT199"):
            legal_framework = "TT199_2014"
        elif legal_framework == "TT232" or legal_framework.startswith("TT232"):
            legal_framework = "TT232_2012"
    
    # Map ma_so based on legal framework
    # CFO uses ma_so 20 (indirect) or 21 (direct) for all frameworks
    table_name = "cash_flow_statement_raw"
    
    if legal_framework == "TT199_2014":
        # TT199_2014: ma_so 20 (indirect) or 21 (direct)
        ma_so_indirect = 20
        ma_so_direct = 20
    elif legal_framework == "TT232_2012":
        # TT232_2012: ma_so 20 (indirect) or 21 (direct)
        ma_so_indirect = 20
        ma_so_direct = 21
    else:
        # Default fallback
        ma_so_indirect = 20
        ma_so_direct = 21
    
    # CFO is from cash flow statement (LCTT)
    # Try indirect method first (ma_so 20)
    value = get_value_by_ma_so(
        stock=stock,
        year=year,
        ma_so=ma_so_indirect,
        quarter=quarter,
        table_name=table_name
    )
    
    # If indirect method not found, try direct method (ma_so 21)
    if value is None:
        value = get_value_by_ma_so(
            stock=stock,
            year=year,
            ma_so=ma_so_direct,
            quarter=quarter,
            table_name=table_name
        )
    
    return value