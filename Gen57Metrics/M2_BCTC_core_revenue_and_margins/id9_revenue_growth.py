"""
Revenue Growth Indicator.

This is a CalculatedIndicator that calculates Revenue Growth year-over-year.
According to 57BaseIndicators.json:
- ID: 9
- Indicator_Name: "Revenue Growth"
- Definition: "Tăng trưởng doanh thu theo năm"
- Get_Direct_From_DB: "no"
- TT200_Formula: "BCKQ HĐKD – Mẫu B02-DNNT – Mã 10, 19, 22 (công thức: ((KQKD_10_t + KQKD_19_t + KQKD_22_t) - (KQKD_10_t-1 + KQKD_19_t-1 + KQKD_22_t-1)) / (KQKD_10_t-1 + KQKD_19_t-1 + KQKD_22_t-1))"
- Formula: "((KQKD_10_t + KQKD_19_t + KQKD_22_t) - (KQKD_10_t-1 + KQKD_19_t-1 + KQKD_22_t-1)) / (KQKD_10_t-1 + KQKD_19_t-1 + KQKD_22_t-1)"
- Alternative_Formula: "g_Rev_t = Revenue_t / Revenue_{t-1} – 1"

Note: Revenue Growth compares current period revenue with same period previous year.
"""

from typing import Optional
from .id6_revenue import get_revenue_value


def get_revenue_growth_value(
    stock: str,
    year: int,
    quarter: Optional[int] = 5,
    legal_framework: Optional[str] = None,
) -> Optional[float]:
    """
    Lấy giá trị Revenue Growth (Tăng trưởng doanh thu theo năm) cho cổ phiếu và kỳ báo cáo chỉ định.

    - Revenue Growth so sánh doanh thu kỳ hiện tại với cùng kỳ năm trước.
    - Công thức: ((KQKD_10_t + KQKD_19_t + KQKD_22_t) - (KQKD_10_t-1 + KQKD_19_t-1 + KQKD_22_t-1)) / (KQKD_10_t-1 + KQKD_19_t-1 + KQKD_22_t-1)
    - Công thức thay thế: g_Rev_t = Revenue_t / Revenue_{t-1} – 1
    - Kết quả là tỷ lệ phần trăm (dạng số thập phân, ví dụ: 0.15 = 15% tăng trưởng)

    Tham số:
        stock: Mã cổ phiếu, ví dụ: "MIG", "PGI", "BIC".
        year: Năm tài chính, ví dụ: 2024.
        quarter: Quý (1-4) cho báo cáo quý, hoặc 5 cho báo cáo năm (mặc định: 5).
                 So sánh với cùng quý năm trước (ví dụ: Q2 2024 so với Q2 2023).
        legal_framework: Tên bộ luật (ví dụ: "TT199_2014", "TT232_2012"). 
                        Nếu None, sẽ tự động lấy từ database dựa trên stock.

    Kết quả trả về:
        Optional[float]: Giá trị Revenue Growth (tỷ lệ phần trăm dạng số thập phân), 
                        hoặc None nếu thiếu dữ liệu kỳ hiện tại hoặc kỳ trước, 
                        hoặc Revenue năm trước = 0.

    Ví dụ:
        >>> # Lấy Revenue Growth năm của MIG năm 2024 (quarter=5)
        >>> # So sánh Revenue 2024 với Revenue 2023
        >>> revenue_growth = get_revenue_growth_value("MIG", 2024)
        >>> print(revenue_growth)  # 0.15 = 15% tăng trưởng
        0.15

        >>> # Lấy Revenue Growth quý 2 của MIG năm 2024
        >>> # So sánh Revenue Q2 2024 với Revenue Q2 2023
        >>> revenue_growth_q2 = get_revenue_growth_value("MIG", 2024, quarter=2)
        >>> print(revenue_growth_q2)
        0.20
    """
    # Get legal framework if not provided
    if legal_framework is None:
        from Gen57Metrics.utils_database_manager import get_legal_framework
        legal_framework = get_legal_framework(stock)
    
    current = get_revenue_value(stock, year, quarter, legal_framework)
    if current is None:
        return None

    previous = get_revenue_value(stock, year - 1, quarter, legal_framework)
    if previous in (None, 0):
        return None

    return (current - previous) / previous
