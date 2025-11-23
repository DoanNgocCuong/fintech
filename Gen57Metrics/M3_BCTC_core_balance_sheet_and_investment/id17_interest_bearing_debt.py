"""
Interest-bearing Debt Indicator.

This is a DirectIndicator that calculates Interest-bearing Debt from multiple components.
According to 57BaseIndicators.json:
- ID: 17
- Indicator_Name: "Interest-bearing Debt"
- Definition: "Tổng nợ vay chịu lãi"
- Get_Direct_From_DB: "yes"
- TT200_Formula: "Bảng CĐKT – Mẫu B01-DNNT – Mã 311, 334 (công thức: CDKT_311 + CDKT_334)"
- Formula: "CDKT_311 + CDKT_334"
- Alternative_Formula: "Interest-bearing Debt = Short-term borrowings + Long-term borrowings + Bonds payable"

Note: Interest-bearing Debt is calculated from balance sheet (CDKT), using ma_so 311 and 334.
"""

from typing import Optional
from Gen57Metrics.utils_database_manager import get_value_by_ma_so, get_legal_framework

BALANCE_SHEET_TABLE = "balance_sheet_raw"
INTEREST_BEARING_DEBT_CODES = (311, 334)


def get_interest_bearing_debt_value(
    stock: str, 
    year: int, 
    quarter: Optional[int] = 5,
    legal_framework: Optional[str] = None
) -> Optional[float]:
    """
    Lấy giá trị Interest-bearing Debt (Tổng nợ vay chịu lãi) cho cổ phiếu và kỳ báo cáo chỉ định.

    - Interest-bearing Debt lấy từ Bảng Cân Đối Kế Toán (Bảng CĐKT), Mẫu B01-DNNT.
    - Công thức: CDKT_311 + CDKT_334
    - Lấy từ bảng balance_sheet_raw.
    - Công thức thay thế: Interest-bearing Debt = Short-term borrowings + Long-term borrowings + Bonds payable

    Tham số:
        stock: Mã cổ phiếu, ví dụ: "MIG", "PGI", "BIC".
        year: Năm tài chính, ví dụ: 2024.
        quarter: Quý (1-4) cho báo cáo quý, hoặc 5 cho báo cáo năm (mặc định: 5).
        legal_framework: Tên bộ luật (ví dụ: "TT199_2014", "TT232_2012"). 
                        Nếu None, sẽ tự động lấy từ database dựa trên stock.

    Kết quả trả về:
        Optional[float]: Giá trị Interest-bearing Debt (tổng của CDKT_311 + CDKT_334), 
                        hoặc None nếu thiếu bất kỳ thành phần nào.

    Ví dụ:
        >>> # Lấy Interest-bearing Debt năm của MIG năm 2024 (quarter=5)
        >>> debt = get_interest_bearing_debt_value("MIG", 2024)
        >>> print(debt)
        15000000000.0

        >>> # Lấy Interest-bearing Debt quý 2 của MIG năm 2024
        >>> debt_q2 = get_interest_bearing_debt_value("MIG", 2024, quarter=2)
        >>> print(debt_q2)
        14500000000.0
    """
    # Get legal framework if not provided
    if legal_framework is None:
        legal_framework = get_legal_framework(stock)
    
    # Map ma_so codes based on legal framework (currently same for all frameworks)
    values = []
    for code in INTEREST_BEARING_DEBT_CODES:
        value = get_value_by_ma_so(
            stock=stock,
            year=year,
            ma_so=code,
            quarter=quarter,
            table_name=BALANCE_SHEET_TABLE,
        )
        if value is None:
            # Nếu thiếu bất kỳ thành phần nào, trả về None
            return None
        values.append(value)
    
    if not values:
        return None
    
    return float(sum(values))

