from Gen57Metrics.utils_database_manager import get_value_by_ma_so
from typing import Optional

def get_EBIT_value(stock: str, year: int, quarter: int = None) -> Optional[float]:
    """
    Get EBIT (Earnings Before Interest and Tax) value for a stock.
    
    EBIT = Lợi nhuận trước lãi vay và thuế
    Formula: EBIT = Operating profit + Interest expense
    TT200_Formula: EBIT = (KQKD – Mã 50) + (KQKD – Mã 23)
    
    Args:
        stock (str): Stock code (e.g., "MIG", "PGI")
        year (int): Year (e.g., 2024)
        quarter (int, optional): Quarter (1, 2, 3, 4) or None for annual
        
    Returns:
        Optional[float]: EBIT value or None if components not found
    """
    # Mã 50: Operating profit (Lợi nhuận thuần từ hoạt động kinh doanh)
    operating_profit = get_value_by_ma_so(stock, year, 50, quarter)
    
    # Mã 23: Interest expense (Chi phí lãi vay)
    interest_expense = get_value_by_ma_so(stock, year, 23, quarter)
    
    # If either component is None, return None
    if operating_profit is None or interest_expense is None:
        return None
    
    # EBIT = Operating profit + Interest expense
    return operating_profit + interest_expense

