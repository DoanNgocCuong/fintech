"""
Gross Margin Indicator.

This is a CalculatedIndicator that calculates Gross Margin from Revenue and Gross Profit.
According to 57BaseIndicators.json:
- ID: 8
- Indicator_Name: "Gross Margin"
- Definition: "Biên lợi nhuận gộp (%)"
- Get_Direct_From_DB: "no"
- TT200_Formula: "BCKQ HĐKD – Mẫu B02-DNNT – Mã 10, 18, 19, 22 (công thức: KQKD_18 / (KQKD_10 + KQKD_19 + KQKD_22))"
- Formula: "KQKD_18 / (KQKD_10 + KQKD_19 + KQKD_22)"
- Alternative_Formula: "GM = Gross Profit / Revenue"

Note: Gross Margin is calculated as Gross Profit divided by Revenue.
"""

from typing import Optional
from .id6_revenue import get_revenue_value
from .id7_gross_profit import get_gross_profit_value


def get_gross_margin_value(
    stock: str, 
    year: int, 
    quarter: Optional[int] = 5,
    legal_framework: Optional[str] = None
) -> Optional[float]:
    """
    Lấy giá trị Gross Margin (Biên lợi nhuận gộp, %) cho cổ phiếu và kỳ báo cáo chỉ định.

    - Gross Margin được tính từ Gross Profit và Revenue.
    - Công thức: KQKD_18 / (KQKD_10 + KQKD_19 + KQKD_22)
    - Công thức thay thế: GM = Gross Profit / Revenue
    - Kết quả là tỷ lệ phần trăm (dạng số thập phân, ví dụ: 0.25 = 25%)

    Tham số:
        stock: Mã cổ phiếu, ví dụ: "MIG", "PGI", "BIC".
        year: Năm tài chính, ví dụ: 2024.
        quarter: Quý (1-4) cho báo cáo quý, hoặc 5 cho báo cáo năm (mặc định: 5).
        legal_framework: Tên bộ luật (ví dụ: "TT199_2014", "TT232_2012"). 
                        Nếu None, sẽ tự động lấy từ database dựa trên stock.

    Kết quả trả về:
        Optional[float]: Giá trị Gross Margin (tỷ lệ phần trăm dạng số thập phân), 
                        hoặc None nếu thiếu Revenue hoặc Gross Profit, hoặc Revenue = 0.

    Ví dụ:
        >>> # Lấy Gross Margin năm của MIG năm 2024 (quarter=5)
        >>> gross_margin = get_gross_margin_value("MIG", 2024)
        >>> print(gross_margin)  # 0.25 = 25%
        0.25

        >>> # Lấy Gross Margin quý 2 của MIG năm 2024
        >>> gross_margin_q2 = get_gross_margin_value("MIG", 2024, quarter=2)
        >>> print(gross_margin_q2)
        0.30
    """
    # Get legal framework if not provided
    if legal_framework is None:
        from Gen57Metrics.utils_database_manager import get_legal_framework
        legal_framework = get_legal_framework(stock)
    
    revenue = get_revenue_value(stock, year, quarter, legal_framework)
    gross_profit = get_gross_profit_value(stock, year, quarter, legal_framework)

    if revenue in (None, 0) or gross_profit is None:
        return None

    return gross_profit / revenue
