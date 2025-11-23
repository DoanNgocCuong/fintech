"""
Earnings Growth Indicator.

This is a CalculatedIndicator that calculates Earnings Growth year-over-year.
According to 57BaseIndicators.json:
- ID: 10
- Indicator_Name: "Earnings Growth"
- Definition: "Tăng trưởng lợi nhuận sau thuế theo năm"
- Get_Direct_From_DB: "no"
- TT200_Formula: "BCKQ HĐKD – Mẫu B02-DNNT – Mã 60 (công thức: (KQKD_60_t - KQKD_60_t-1) / KQKD_60_t-1)"
- Formula: "(KQKD_60_t - KQKD_60_t-1) / KQKD_60_t-1"
- Alternative_Formula: "g_NI_t = NI_t / NI_{t-1} – 1"

Note: Earnings Growth compares current period Net Income with same period previous year.
"""

from typing import Optional
from Gen57Metrics.M1_BCTC_core_profit_and_cashflow.id2_NI import get_NI_value


def get_earnings_growth_value(
    stock: str,
    year: int,
    quarter: Optional[int] = 5,
    legal_framework: Optional[str] = None,
) -> Optional[float]:
    """
    Lấy giá trị Earnings Growth (Tăng trưởng lợi nhuận sau thuế theo năm) 
    cho cổ phiếu và kỳ báo cáo chỉ định.

    - Earnings Growth so sánh Net Income (NI) kỳ hiện tại với cùng kỳ năm trước.
    - Công thức: (KQKD_60_t - KQKD_60_t-1) / KQKD_60_t-1
    - Công thức thay thế: g_NI_t = NI_t / NI_{t-1} – 1
    - Sử dụng Net Income từ income statement P2 (KQKD_60).
    - Kết quả là tỷ lệ phần trăm (dạng số thập phân, ví dụ: 0.20 = 20% tăng trưởng)

    Tham số:
        stock: Mã cổ phiếu, ví dụ: "MIG", "PGI", "BIC".
        year: Năm tài chính, ví dụ: 2024.
        quarter: Quý (1-4) cho báo cáo quý, hoặc 5 cho báo cáo năm (mặc định: 5).
                 So sánh với cùng quý năm trước (ví dụ: Q2 2024 so với Q2 2023).
        legal_framework: Tên bộ luật (ví dụ: "TT199_2014", "TT232_2012"). 
                        Nếu None, sẽ tự động lấy từ database dựa trên stock.

    Kết quả trả về:
        Optional[float]: Giá trị Earnings Growth (tỷ lệ phần trăm dạng số thập phân), 
                        hoặc None nếu thiếu dữ liệu kỳ hiện tại hoặc kỳ trước, 
                        hoặc NI năm trước = 0.

    Ví dụ:
        >>> # Lấy Earnings Growth năm của MIG năm 2024 (quarter=5)
        >>> # So sánh NI 2024 với NI 2023
        >>> earnings_growth = get_earnings_growth_value("MIG", 2024)
        >>> print(earnings_growth)  # 0.20 = 20% tăng trưởng
        0.20

        >>> # Lấy Earnings Growth quý 2 của MIG năm 2024
        >>> # So sánh NI Q2 2024 với NI Q2 2023
        >>> earnings_growth_q2 = get_earnings_growth_value("MIG", 2024, quarter=2)
        >>> print(earnings_growth_q2)
        0.25
    """
    # Get legal framework if not provided
    if legal_framework is None:
        from Gen57Metrics.utils_database_manager import get_legal_framework
        legal_framework = get_legal_framework(stock)
    
    current = get_NI_value(stock, year, quarter, legal_framework)
    if current is None:
        return None

    previous = get_NI_value(stock, year - 1, quarter, legal_framework)
    if previous in (None, 0):
        return None

    return (current - previous) / previous
