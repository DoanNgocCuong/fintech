from Gen57Metrics.utils_database_manager import get_value_by_ma_so
from typing import Optional
from .EBIT import get_EBIT_value

def get_EBITDA_value(stock: str, year: int, quarter: int = None) -> Optional[float]:
    """
    Get EBITDA (Earnings Before Interest, Tax, Depreciation and Amortization) value for a stock.
    
    EBITDA = EBIT cộng khấu hao và phân bổ
    Formula: EBITDA = EBIT + D&A
    TT200_Formula: EBITDA = EBIT + (LCTT – Mã 02)
    
    Note: Mã 02 is from cash flow statement (LCTT), not income statement
    
    Args:
        stock (str): Stock code (e.g., "MIG", "PGI")
        year (int): Year (e.g., 2024)
        quarter (int, optional): Quarter (1, 2, 3, 4) or None for annual
        
    Returns:
        Optional[float]: EBITDA value or None if components not found
    """
    # Get EBIT value
    ebit = get_EBIT_value(stock, year, quarter)
    if ebit is None:
        return None
    
    # Mã 02: Depreciation and Amortization (D&A) from cash flow statement
    # Note: Cash flow table name might be different, check table_name parameter
    depreciation_amortization = get_value_by_ma_so(
        stock, year, 2, quarter, 
        table_name="cash_flow_raw"  # Assuming cash flow table name
    )
    
    # If D&A is None, return None
    if depreciation_amortization is None:
        return None
    
    # EBITDA = EBIT + D&A
    return ebit + depreciation_amortization

