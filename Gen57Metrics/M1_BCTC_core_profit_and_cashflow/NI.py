from Gen57Metrics.utils_database_manager import get_value_by_ma_so

def get_NI_value(stock: str, year: int, quarter: int = None):
    """
    Get Net Income (NI) value for a stock.
    
    NI = Lợi nhuận sau thuế thu nhập doanh nghiệp
    Formula: NI = Profit after tax
    TT200_Formula: KQKD – Mã 60
    
    Args:
        stock (str): Stock code (e.g., "MIG", "PGI")
        year (int): Year (e.g., 2024)
        quarter (int, optional): Quarter (1, 2, 3, 4) or None for annual
        
    Returns:
        Optional[float]: Net Income value or None if not found
    """
    return get_value_by_ma_so(stock, year, 60, quarter)

