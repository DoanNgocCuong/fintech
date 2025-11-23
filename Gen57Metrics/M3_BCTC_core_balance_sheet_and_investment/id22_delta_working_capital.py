"""
ΔWorking Capital (Change in Working Capital) Indicator.

This is a CalculatedIndicator that calculates change in Working Capital year-over-year.
According to 57BaseIndicators.json:
- ID: 22
- Indicator_Name: "ΔWorking Capital"
- Definition: "Thay đổi vốn lưu động hoạt động"
- Get_Direct_From_DB: "no"
- TT200_Formula: "Bảng CĐKT – Mẫu B01-DNNT – Mã 130, 140, 312 (công thức: (CDKT_130_t + CDKT_140_t - CDKT_312_t) - (CDKT_130_t-1 + CDKT_140_t-1 - CDKT_312_t-1))"
- Formula: "(CDKT_130_t + CDKT_140_t - CDKT_312_t) - (CDKT_130_t-1 + CDKT_140_t-1 - CDKT_312_t-1)"
- Alternative_Formula: "ΔWC_t = WC_t – WC_{t-1}"

Note: ΔWorking Capital compares current period Working Capital with same period previous year.
"""

from typing import Optional
from .id21_working_capital import get_working_capital_value


def get_delta_working_capital_value(
    stock: str,
    year: int,
    quarter: Optional[int] = 5,
    legal_framework: Optional[str] = None,
) -> Optional[float]:
    """
    Lấy giá trị ΔWorking Capital (Thay đổi vốn lưu động hoạt động) cho cổ phiếu và kỳ báo cáo chỉ định.

    - ΔWorking Capital so sánh Working Capital kỳ hiện tại với cùng kỳ năm trước.
    - Công thức: (CDKT_130_t + CDKT_140_t - CDKT_312_t) - (CDKT_130_t-1 + CDKT_140_t-1 - CDKT_312_t-1)
    - Sử dụng Working Capital từ balance sheet (CDKT).
    - Công thức thay thế: ΔWC_t = WC_t – WC_{t-1}
    - Kết quả dương = tăng vốn lưu động, âm = giảm vốn lưu động

    Tham số:
        stock: Mã cổ phiếu, ví dụ: "MIG", "PGI", "BIC".
        year: Năm tài chính, ví dụ: 2024.
        quarter: Quý (1-4) cho báo cáo quý, hoặc 5 cho báo cáo năm (mặc định: 5).
                 So sánh với cùng quý năm trước (ví dụ: Q2 2024 so với Q2 2023).
        legal_framework: Tên bộ luật (ví dụ: "TT199_2014", "TT232_2012"). 
                        Nếu None, sẽ tự động lấy từ database dựa trên stock.

    Kết quả trả về:
        Optional[float]: Giá trị ΔWorking Capital, hoặc None nếu thiếu dữ liệu kỳ hiện tại hoặc kỳ trước.

    Ví dụ:
        >>> # Lấy ΔWorking Capital năm của MIG năm 2024 (quarter=5)
        >>> # So sánh WC 2024 với WC 2023
        >>> delta_wc = get_delta_working_capital_value("MIG", 2024)
        >>> print(delta_wc)
        500000000.0  # Tăng 500 triệu

        >>> # Lấy ΔWorking Capital quý 2 của MIG năm 2024
        >>> # So sánh WC Q2 2024 với WC Q2 2023
        >>> delta_wc_q2 = get_delta_working_capital_value("MIG", 2024, quarter=2)
        >>> print(delta_wc_q2)
        300000000.0
    """
    # Get legal framework if not provided
    if legal_framework is None:
        from Gen57Metrics.utils_database_manager import get_legal_framework
        legal_framework = get_legal_framework(stock)
    
    current = get_working_capital_value(stock, year, quarter, legal_framework)
    if current is None:
        return None

    previous = get_working_capital_value(stock, year - 1, quarter, legal_framework)
    if previous is None:
        return None

    # Sử dụng abs() cho tất cả giá trị trong phép tính
    return float(abs(current) - abs(previous))

