"""
Cash & Short-term Investments Indicator.

This is a DirectIndicator that calculates Cash & Short-term Investments from multiple components.
According to 57BaseIndicators.json:
- ID: 18
- Indicator_Name: "Cash & Short-term Investments"
- Definition: "Tiền và các khoản đầu tư tài chính ngắn hạn"
- Get_Direct_From_DB: "yes"
- TT200_Formula: "Bảng CĐKT – Mẫu B01-DNNT – Mã 110, 120 (công thức: CDKT_110 + CDKT_120)"
- Formula: "CDKT_110 + CDKT_120"
- Alternative_Formula: "Cash & STI = Cash and cash equivalents"

Note: Cash & Short-term Investments is calculated from balance sheet (CDKT), using ma_so 110 and 120.
"""

from typing import Optional
from Gen57Metrics.utils_database_manager import get_value_by_ma_so, get_legal_framework

BALANCE_SHEET_TABLE = "balance_sheet_raw"
CASH_AND_STI_CODES = (110, 120)


def get_cash_and_short_term_investments_value(
    stock: str, 
    year: int, 
    quarter: Optional[int] = 5,
    legal_framework: Optional[str] = None
) -> Optional[float]:
    """
    Lấy giá trị Cash & Short-term Investments (Tiền và các khoản đầu tư tài chính ngắn hạn) 
    cho cổ phiếu và kỳ báo cáo chỉ định.

    - Cash & Short-term Investments lấy từ Bảng Cân Đối Kế Toán (Bảng CĐKT), Mẫu B01-DNNT.
    - Công thức: CDKT_110 + CDKT_120
    - Lấy từ bảng balance_sheet_raw.
    - Công thức thay thế: Cash & STI = Cash and cash equivalents

    Tham số:
        stock: Mã cổ phiếu, ví dụ: "MIG", "PGI", "BIC".
        year: Năm tài chính, ví dụ: 2024.
        quarter: Quý (1-4) cho báo cáo quý, hoặc 5 cho báo cáo năm (mặc định: 5).
        legal_framework: Tên bộ luật (ví dụ: "TT199_2014", "TT232_2012"). 
                        Nếu None, sẽ tự động lấy từ database dựa trên stock.

    Kết quả trả về:
        Optional[float]: Giá trị Cash & Short-term Investments (tổng của CDKT_110 + CDKT_120), 
                        hoặc None nếu thiếu bất kỳ thành phần nào.

    Ví dụ:
        >>> # Lấy Cash & STI năm của MIG năm 2024 (quarter=5)
        >>> cash_sti = get_cash_and_short_term_investments_value("MIG", 2024)
        >>> print(cash_sti)
        5000000000.0

        >>> # Lấy Cash & STI quý 2 của MIG năm 2024
        >>> cash_sti_q2 = get_cash_and_short_term_investments_value("MIG", 2024, quarter=2)
        >>> print(cash_sti_q2)
        4800000000.0
    """
    # Get legal framework if not provided
    if legal_framework is None:
        legal_framework = get_legal_framework(stock)
    
    # Map ma_so codes based on legal framework (currently same for all frameworks)
    values = []
    for code in CASH_AND_STI_CODES:
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

