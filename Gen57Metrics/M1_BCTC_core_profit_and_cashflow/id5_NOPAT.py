"""
NOPAT (Net Operating Profit After Tax) Indicator.

This is a DirectIndicator that retrieves NOPAT value directly from database.
According to 57BaseIndicators.json:
- ID: 5
- Indicator_Name: "NOPAT"
- Definition: "Lợi nhuận sau thuế từ hoạt động kinh doanh"
- Get_Direct_From_DB: "yes"
- TT200_Formula: "BCKQ HĐKD – Mẫu B02-DNNT – Mã 50, 51, 52 (công thức: KQKD_50 - KQKD_51 - KQKD_52) = KQKD_60"
- Formula: "KQKD_60"
- Alternative_Formula: "NOPAT = EBIT × (1 – Tax rate)"

Note: NOPAT = KQKD_50 - KQKD_51 - KQKD_52 = KQKD_60
Since the result equals KQKD_60, we retrieve it directly from income statement P2.
"""

from typing import Optional
from Gen57Metrics.utils_database_manager import get_value_by_ma_so, get_legal_framework


def get_NOPAT_value(
    stock: str, 
    year: int, 
    quarter: Optional[int] = 5,
    legal_framework: Optional[str] = None
) -> Optional[float]:
    """
    Lấy giá trị NOPAT (Net Operating Profit After Tax, Lợi nhuận sau thuế từ hoạt động kinh doanh) 
    cho cổ phiếu và kỳ báo cáo chỉ định.

    - NOPAT lấy từ Báo cáo kết quả hoạt động kinh doanh (BCKQ HĐKD), Mẫu B02-DNNT, sử dụng mã số 60.
    - Công thức: KQKD_50 - KQKD_51 - KQKD_52 = KQKD_60
    - Vì kết quả bằng KQKD_60, nên lấy trực tiếp từ mã số 60 (giống như NI).
    - Chỉ lấy từ bảng income_statement_p2_raw (P2), không lấy từ P1.
    - Công thức thay thế: NOPAT = EBIT × (1 – Tax rate)

    Tham số:
        stock: Mã cổ phiếu, ví dụ: "MIG", "PGI", "BIC".
        year: Năm tài chính, ví dụ: 2024.
        quarter: Quý (1-4) cho báo cáo quý, hoặc 5 cho báo cáo năm (mặc định: 5).
        legal_framework: Tên bộ luật (ví dụ: "TT199_2014", "TT232_2012"). 
                        Nếu None, sẽ tự động lấy từ database dựa trên stock.

    Kết quả trả về:
        Optional[float]: Giá trị NOPAT lấy từ database, hoặc None nếu không tìm thấy.

    Ví dụ:
        >>> # Lấy NOPAT năm của MIG năm 2024 (quarter=5)
        >>> nopat = get_NOPAT_value("MIG", 2024)
        >>> print(nopat)
        1234567890.0

        >>> # Lấy NOPAT quý 2 của MIG năm 2024
        >>> nopat_q2 = get_NOPAT_value("MIG", 2024, quarter=2)
        >>> print(nopat_q2)
        9876543210.0
    """
    # Get legal framework if not provided
    if legal_framework is None:
        legal_framework = get_legal_framework(stock)
    
    # Map ma_so based on legal framework (currently same for all frameworks)
    # NOPAT = KQKD_50 - KQKD_51 - KQKD_52 = KQKD_60
    # Since result equals KQKD_60, retrieve directly from ma_so 60
    ma_so = 60
    table_name = "income_statement_p2_raw"
    
    return get_value_by_ma_so(
        stock=stock,
        year=year,
        ma_so=ma_so,
        quarter=quarter,
        table_name=table_name
    )
