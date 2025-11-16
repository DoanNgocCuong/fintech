"""
CFO (Cash Flow from Operations) Indicator.

This is a DirectIndicator that retrieves CFO value directly from database.
According to 57BaseIndicators.json:
- ID: 1
- Indicator_Name: "CFO"
- Definition: "Dòng tiền thuần từ hoạt động kinh doanh"
- Get_Direct_From_DB: "yes"
- TT200_Formula: "LCTT (TT200) – Mã 20 (gián tiếp) hoặc Mã 21 (trực tiếp)"
"""

from typing import Optional
from Gen57Metrics.direct_indicator import DirectIndicator


# CFO Indicator instance
# According to JSON: ID=1, Get_Direct_From_DB="yes", ma_so=111
CFO_INDICATOR = DirectIndicator(
    indicator_id=1,
    indicator_name="CFO",
    definition="Dòng tiền thuần từ hoạt động kinh doanh",
    group="BCTC Core - Profit & Cashflow",
    ma_so=111,  # Mã số trong database
    formula="CFO = Net cash from operating activities",
    tt200_formula="LCTT (TT200) – Mã 20 (gián tiếp) hoặc Mã 21 (trực tiếp)",
    used_in_qgv="Q,G,V",
    used_in_4m="Meaning,Moat",
    weight_in_4m=0.05,
    weight_in_qgv=0.06
)


def get_CFO_value(stock: str, year: int, quarter: Optional[int] = None) -> Optional[float]:
    """
    Get CFO (Cash Flow from Operations) value for given stock and period.
    
    This is a convenience function that uses the CFO_INDICATOR instance.
    For programmatic use, you can also call CFO_INDICATOR.get_value() directly.
    
    Args:
        stock: Stock symbol (e.g., "MIG", "PGI", "BIC")
        year: Year (e.g., 2024)
        quarter: Quarter (1-4) or None for annual report
        
    Returns:
        Optional[float]: CFO value from database, or None if not found
        
    Example:
        >>> # Get annual CFO for MIG in 2024
        >>> cfo = get_CFO_value("MIG", 2024)
        >>> print(cfo)
        1234567890.0
        
        >>> # Get quarterly CFO for Q2 2024
        >>> cfo_q2 = get_CFO_value("MIG", 2024, quarter=2)
        >>> print(cfo_q2)
        9876543210.0
    """
    return CFO_INDICATOR.get_value(stock=stock, year=year, quarter=quarter)