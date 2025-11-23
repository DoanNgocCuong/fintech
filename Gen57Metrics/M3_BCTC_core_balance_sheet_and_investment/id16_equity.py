"""
Equity Indicator.

This is a DirectIndicator that retrieves Equity value directly from database.
According to 57BaseIndicators.json:
- ID: 16
- Indicator_Name: "Equity"
- Definition: "Vốn chủ sở hữu"
- Get_Direct_From_DB: "yes"
- TT200_Formula: "Bảng CĐKT – Mẫu B01-DNNT – Mã 410 (công thức: CDKT_410)"
- Formula: "CDKT_410"
- Alternative_Formula: "Equity = Owner's equity"

Note: Equity is from balance sheet (CDKT), using ma_so 410.
"""

from typing import Optional
from Gen57Metrics.utils_database_manager import get_value_by_ma_so, get_legal_framework

BALANCE_SHEET_TABLE = "balance_sheet_raw"
EQUITY_CODE = 410


def get_equity_value(
    stock: str, 
    year: int, 
    quarter: Optional[int] = 5,
    legal_framework: Optional[str] = None
) -> Optional[float]:
    """
    Lấy giá trị Equity (Vốn chủ sở hữu) cho cổ phiếu và kỳ báo cáo chỉ định.

    - Equity lấy từ Bảng Cân Đối Kế Toán (Bảng CĐKT), Mẫu B01-DNNT, sử dụng mã số 410.
    - Lấy từ bảng balance_sheet_raw.
    - Công thức: CDKT_410
    - Công thức thay thế: Equity = Owner's equity

    Tham số:
        stock: Mã cổ phiếu, ví dụ: "MIG", "PGI", "BIC".
        year: Năm tài chính, ví dụ: 2024.
        quarter: Quý (1-4) cho báo cáo quý, hoặc 5 cho báo cáo năm (mặc định: 5).
        legal_framework: Tên bộ luật (ví dụ: "TT199_2014", "TT232_2012"). 
                        Nếu None, sẽ tự động lấy từ database dựa trên stock.

    Kết quả trả về:
        Optional[float]: Giá trị Equity lấy từ database, hoặc None nếu không tìm thấy.

    Ví dụ:
        >>> # Lấy Equity năm của MIG năm 2024 (quarter=5)
        >>> equity = get_equity_value("MIG", 2024)
        >>> print(equity)
        20000000000.0

        >>> # Lấy Equity quý 2 của MIG năm 2024
        >>> equity_q2 = get_equity_value("MIG", 2024, quarter=2)
        >>> print(equity_q2)
        19500000000.0
    """
    # Get legal framework if not provided
    if legal_framework is None:
        legal_framework = get_legal_framework(stock)
    
    # Map ma_so based on legal framework (currently same for all frameworks)
    ma_so = EQUITY_CODE
    
    return get_value_by_ma_so(
        stock=stock,
        year=year,
        ma_so=ma_so,
        quarter=quarter,
        table_name=BALANCE_SHEET_TABLE,
    )

