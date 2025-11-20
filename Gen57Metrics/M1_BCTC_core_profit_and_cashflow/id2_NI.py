from Gen57Metrics.utils_database_manager import get_value_by_ma_so

def get_NI_value(stock: str, year: int, quarter: int = None):
    """
    Lấy giá trị Net Income (NI, Lợi nhuận sau thuế TNDN) cho cổ phiếu.
    Chỉ lấy từ bảng kết quả kinh doanh P2.

    TT200_Formula: KQKD – Mã 60 (chỉ P2)

    Args:
        stock (str): Stock code (e.g., "MIG", "PGI")
        year (int): Year (e.g., 2024)
        quarter (int, optional): Quarter (1, 2, 3, 4) or None for annual

    Returns:
        Optional[float]: Net Income value or None if not found
    """
    return get_value_by_ma_so(
        stock=stock,
        year=year,
        ma_so=60,
        quarter=quarter,
        table_name="income_statement_p2_raw"
    )
