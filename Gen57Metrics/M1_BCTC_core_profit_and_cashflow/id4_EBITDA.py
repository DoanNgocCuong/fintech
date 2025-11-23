"""
EBITDA Indicator.

This is a CalculatedIndicator that calculates EBITDA from EBIT and D&A.
According to 57BaseIndicators.json:
- ID: 4
- Indicator_Name: "EBITDA"
- Definition: "EBIT cộng khấu hao và phân bổ"
- Get_Direct_From_DB: "no"
- TT200_Formula: "EBITDA = EBIT + (LCTT – Mã 02)"
- Formula: "EBITDA = EBIT + LCTT_02"
- Alternative_Formula: "EBITDA = EBIT + D&A"

Note: EBITDA is calculated from EBIT and Depreciation & Amortization (D&A) from cash flow statement.
"""

from typing import Optional
from Gen57Metrics.utils_database_manager import get_value_by_ma_so, get_legal_framework
from .id3_EBIT import get_EBIT_value


def get_EBITDA_value(
    stock: str, 
    year: int, 
    quarter: Optional[int] = 5,
    legal_framework: Optional[str] = None
) -> Optional[float]:
    """
    Lấy giá trị EBITDA (Earnings Before Interest, Tax, Depreciation and Amortization) 
    cho cổ phiếu và kỳ báo cáo chỉ định.

    - EBITDA được tính từ EBIT và Khấu hao, phân bổ (D&A).
    - Công thức: EBITDA = EBIT + LCTT_02
    - Công thức thay thế: EBITDA = EBIT + D&A
    - Mã 02 (D&A) lấy từ cash flow statement (LCTT), không phải income statement

    Tham số:
        stock: Mã cổ phiếu, ví dụ: "MIG", "PGI", "BIC".
        year: Năm tài chính, ví dụ: 2024.
        quarter: Quý (1-4) cho báo cáo quý, hoặc 5 cho báo cáo năm (mặc định: 5).
        legal_framework: Tên bộ luật (ví dụ: "TT199_2014", "TT232_2012"). 
                        Nếu None, sẽ tự động lấy từ database dựa trên stock.

    Kết quả trả về:
        Optional[float]: Giá trị EBITDA, hoặc None nếu thiếu EBIT hoặc D&A.

    Ví dụ:
        >>> # Lấy EBITDA năm của MIG năm 2024 (quarter=5)
        >>> ebitda = get_EBITDA_value("MIG", 2024)
        >>> print(ebitda)
        1500000000.0

        >>> # Lấy EBITDA quý 2 của MIG năm 2024
        >>> ebitda_q2 = get_EBITDA_value("MIG", 2024, quarter=2)
        >>> print(ebitda_q2)
        400000000.0
    """
    # Get legal framework if not provided
    if legal_framework is None:
        legal_framework = get_legal_framework(stock)
    
    # Get EBIT value
    ebit = get_EBIT_value(stock, year, quarter, legal_framework)
    if ebit is None:
        return None
    
    # Map ma_so for D&A based on legal framework (currently same for all frameworks)
    ma_so_da = 2
    table_name = "cash_flow_statement_raw"
    
    # Mã 02: Depreciation and Amortization (D&A) from cash flow statement
    depreciation_amortization = get_value_by_ma_so(
        stock=stock,
        year=year,
        ma_so=ma_so_da,
        quarter=quarter,
        table_name=table_name
    )
    
    # If D&A is None, return None
    if depreciation_amortization is None:
        return None
    
    # EBITDA = EBIT + D&A
    return ebit + depreciation_amortization

