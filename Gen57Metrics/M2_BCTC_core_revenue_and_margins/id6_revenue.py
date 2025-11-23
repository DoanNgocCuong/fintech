"""
Revenue Indicator.

This is a DirectIndicator that calculates Revenue from multiple components.
According to 57BaseIndicators.json:
- ID: 6
- Indicator_Name: "Revenue"
- Definition: "Doanh thu thuần"
- Get_Direct_From_DB: "yes"
- TT200_Formula: "BCKQ HĐKD – Mẫu B02-DNNT – Mã 10, 19, 22 (công thức: KQKD_10 + KQKD_19 + KQKD_22)"
- Formula: "KQKD_10 + KQKD_19 + KQKD_22"
- Alternative_Formula: "Revenue = Net revenue from sales and services"

Note: Revenue is calculated from income statement (KQKD), using ma_so 10, 19, 22 from P2 section.
"""

from typing import Optional
from Gen57Metrics.utils_database_manager import get_value_by_ma_so, get_legal_framework

INCOME_STATEMENT_TABLE = "income_statement_p2_raw"
REVENUE_COMPONENT_CODES = (10, 19, 22)


def get_revenue_value(
    stock: str, 
    year: int, 
    quarter: Optional[int] = 5,
    legal_framework: Optional[str] = None
) -> Optional[float]:
    """
    Lấy giá trị Revenue (Doanh thu thuần) cho cổ phiếu và kỳ báo cáo chỉ định.

    - Revenue lấy từ Báo cáo kết quả hoạt động kinh doanh (BCKQ HĐKD), Mẫu B02-DNNT.
    - Công thức: KQKD_10 + KQKD_19 + KQKD_22
    - Chỉ lấy từ bảng income_statement_p2_raw (P2), không lấy từ P1.
    - Công thức thay thế: Revenue = Net revenue from sales and services

    Tham số:
        stock: Mã cổ phiếu, ví dụ: "MIG", "PGI", "BIC".
        year: Năm tài chính, ví dụ: 2024.
        quarter: Quý (1-4) cho báo cáo quý, hoặc 5 cho báo cáo năm (mặc định: 5).
        legal_framework: Tên bộ luật (ví dụ: "TT199_2014", "TT232_2012"). 
                        Nếu None, sẽ tự động lấy từ database dựa trên stock.

    Kết quả trả về:
        Optional[float]: Giá trị Revenue (tổng của KQKD_10 + KQKD_19 + KQKD_22), 
                        hoặc None nếu thiếu bất kỳ thành phần nào.

    Ví dụ:
        >>> # Lấy Revenue năm của MIG năm 2024 (quarter=5)
        >>> revenue = get_revenue_value("MIG", 2024)
        >>> print(revenue)
        12345678900.0

        >>> # Lấy Revenue quý 2 của MIG năm 2024
        >>> revenue_q2 = get_revenue_value("MIG", 2024, quarter=2)
        >>> print(revenue_q2)
        9876543210.0
    """
    # Get legal framework if not provided
    if legal_framework is None:
        legal_framework = get_legal_framework(stock)
    
    # Map ma_so codes based on legal framework (currently same for all frameworks)
    values = []
    for code in REVENUE_COMPONENT_CODES:
        value = get_value_by_ma_so(
            stock=stock,
            year=year,
            ma_so=code,
            quarter=quarter,
            table_name=INCOME_STATEMENT_TABLE,
        )
        if value is None:
            # Nếu thiếu bất kỳ thành phần nào, trả về None
            return None
        values.append(value)
    
    if not values:
        return None
    
    return float(sum(values))
