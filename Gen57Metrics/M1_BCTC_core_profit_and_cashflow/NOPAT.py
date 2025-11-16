from Gen57Metrics.utils_database_manager import get_value_by_ma_so
from typing import Optional
from .EBIT import get_EBIT_value

def get_NOPAT_value(stock: str, year: int, quarter: int = None) -> Optional[float]:
    """
    Get NOPAT (Net Operating Profit After Tax) value for a stock.
    
    NOPAT = Lợi nhuận sau thuế từ hoạt động kinh doanh
    Formula: NOPAT = EBIT × (1 – Tax rate)
    TT200_Formula: NOPAT = EBIT × (1 – (KQKD – Mã 51)/EBIT)
    
    Args:
        stock (str): Stock code (e.g., "MIG", "PGI")
        year (int): Year (e.g., 2024)
        quarter (int, optional): Quarter (1, 2, 3, 4) or None for annual
        
    Returns:
        Optional[float]: NOPAT value or None if components not found
        
    Note:
        Tax rate = Income tax expense / EBIT
        If EBIT is zero or negative, tax rate calculation may be invalid
    """
    # Get EBIT value
    ebit = get_EBIT_value(stock, year, quarter)
    if ebit is None or ebit == 0:
        return None
    
    # Mã 51: Income tax expense (Chi phí thuế thu nhập doanh nghiệp)
    income_tax_expense = get_value_by_ma_so(stock, year, 51, quarter)
    
    # If tax expense is None, return None
    if income_tax_expense is None:
        return None
    
    # Calculate tax rate
    tax_rate = income_tax_expense / ebit
    
    # NOPAT = EBIT × (1 – Tax rate)
    nopat = ebit * (1 - tax_rate)
    
    return nopat

