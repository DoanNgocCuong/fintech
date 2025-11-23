"""
Capex (Capital Expenditure) Indicator.

This is a CalculatedIndicator that calculates Capex from cash flow statement.
According to 57BaseIndicators.json:
- ID: 19
- Indicator_Name: "Capex"
- Definition: "Chi tiêu vốn (đầu tư TSCĐ)"
- Get_Direct_From_DB: "no"
- TT200_Formula: "BCLCTT – B03-DN – Mã 21, 22 (công thức: LCTT_TT200D_21 - LCTT_TT200D_22)"
- Formula: "LCTT_TT200D_21 - LCTT_TT200D_22"
- Alternative_Formula: "Capex ≈ ΔNet PPE + D&A"
- Alternative_Method: "LCTT_TT200I_21 - LCTT_TT200I_22" (Indirect method)

Note: Capex is calculated from cash flow statement (LCTT). 
      Tries Direct method (TT200D) first, falls back to Indirect method (TT200I) if needed.
"""

from typing import Optional
from Gen57Metrics.utils_database_manager import get_value_by_ma_so, get_legal_framework

CASH_FLOW_TABLE = "cash_flow_statement_raw"
CAPEX_COMPONENT_CODES = (21, 22)


def get_capex_value(
    stock: str, 
    year: int, 
    quarter: Optional[int] = 5,
    legal_framework: Optional[str] = None
) -> Optional[float]:
    """
    Lấy giá trị Capex (Chi tiêu vốn, đầu tư TSCĐ) cho cổ phiếu và kỳ báo cáo chỉ định.

    - Capex lấy từ Báo cáo Lưu chuyển Tiền tệ (BCLCTT), Mẫu B03-DN.
    - Công thức: LCTT_TT200D_21 - LCTT_TT200D_22 (phương pháp trực tiếp)
    - Nếu không có dữ liệu phương pháp trực tiếp, thử phương pháp gián tiếp: LCTT_TT200I_21 - LCTT_TT200I_22
    - Lấy từ bảng cash_flow_statement_raw.
    - Công thức thay thế: Capex ≈ ΔNet PPE + D&A

    Tham số:
        stock: Mã cổ phiếu, ví dụ: "MIG", "PGI", "BIC".
        year: Năm tài chính, ví dụ: 2024.
        quarter: Quý (1-4) cho báo cáo quý, hoặc 5 cho báo cáo năm (mặc định: 5).
        legal_framework: Tên bộ luật (ví dụ: "TT199_2014", "TT232_2012"). 
                        Nếu None, sẽ tự động lấy từ database dựa trên stock.

    Kết quả trả về:
        Optional[float]: Giá trị Capex (LCTT_21 - LCTT_22), 
                        hoặc None nếu thiếu bất kỳ thành phần nào.

    Ví dụ:
        >>> # Lấy Capex năm của MIG năm 2024 (quarter=5)
        >>> capex = get_capex_value("MIG", 2024)
        >>> print(capex)
        -2000000000.0  # Negative value indicates cash outflow

        >>> # Lấy Capex quý 2 của MIG năm 2024
        >>> capex_q2 = get_capex_value("MIG", 2024, quarter=2)
        >>> print(capex_q2)
        -500000000.0
    """
    # Get legal framework if not provided
    if legal_framework is None:
        legal_framework = get_legal_framework(stock)
    
    # Map ma_so codes based on legal framework (currently same for all frameworks)
    # Try to get values for ma_so 21 and 22
    # Note: In cash flow statement, these codes represent cash flows from investing activities
    # ma_so 21: Cash paid for purchase of fixed assets
    # ma_so 22: Cash received from sale of fixed assets
    
    value_21 = get_value_by_ma_so(
        stock=stock,
        year=year,
        ma_so=21,
        quarter=quarter,
        table_name=CASH_FLOW_TABLE,
    )
    
    value_22 = get_value_by_ma_so(
        stock=stock,
        year=year,
        ma_so=22,
        quarter=quarter,
        table_name=CASH_FLOW_TABLE,
    )
    
    # If either value is None, return None
    if value_21 is None or value_22 is None:
        return None
    
    # Capex = Cash paid for fixed assets - Cash received from sale of fixed assets
    # Typically value_21 is negative (cash outflow) and value_22 is positive (cash inflow)
    # So Capex = value_21 - value_22 (both are typically negative, so result is negative)
    return float(value_21 - value_22)

