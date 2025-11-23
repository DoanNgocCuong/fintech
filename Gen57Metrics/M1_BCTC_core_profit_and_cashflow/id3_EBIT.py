"""
EBIT Indicator.

This is a DirectIndicator that retrieves EBIT value directly from database.
According to 57BaseIndicators.json:
- ID: 3
- Indicator_Name: "EBIT"
- Definition: "Lợi nhuận trước lãi vay và thuế"
- Get_Direct_From_DB: "yes"
- TT200_Formula: "BCKQ HĐKD – Mẫu B02-DNNT – Mã 50 (công thức: KQKD_50)"

Note: EBIT is from income statement (KQKD), using ma_so 50 from P2 section only.
"""

from typing import Optional
from Gen57Metrics.utils_database_manager import get_value_by_ma_so, get_legal_framework


def get_EBIT_value(
    stock: str, 
    year: int, 
    quarter: Optional[int] = 5,
    legal_framework: Optional[str] = None
) -> Optional[float]:
    """
    Lấy giá trị EBIT (Lợi nhuận trước lãi vay và thuế) cho cổ phiếu và kỳ báo cáo chỉ định.

    - EBIT lấy từ Báo cáo kết quả hoạt động kinh doanh (BCKQ HĐKD), Mẫu B02-DNNT, sử dụng mã số 50.
    - Chỉ lấy từ bảng income_statement_p2_raw (P2), không lấy từ P1.
    - Công thức: KQKD_50

    Tham số:
        stock: Mã cổ phiếu, ví dụ: "MIG", "PGI", "BIC".
        year: Năm tài chính, ví dụ: 2024.
        quarter: Quý (1-4) cho báo cáo quý, hoặc 5 cho báo cáo năm (mặc định: 5).
        legal_framework: Tên bộ luật (ví dụ: "TT199_2014", "TT232_2012"). 
                        Nếu None, sẽ tự động lấy từ database dựa trên stock.

    Kết quả trả về:
        Optional[float]: Giá trị EBIT lấy từ database, hoặc None nếu không tìm thấy.

    Ví dụ:
        >>> # Lấy EBIT năm của MIG năm 2024 (quarter=5)
        >>> ebit = get_EBIT_value("MIG", 2024)
        >>> print(ebit)
        1234567890.0

        >>> # Lấy EBIT quý 2 của MIG năm 2024
        >>> ebit_q2 = get_EBIT_value("MIG", 2024, quarter=2)
        >>> print(ebit_q2)
        987654321.0
    """
    # Get legal framework if not provided
    if legal_framework is None:
        legal_framework = get_legal_framework(stock)
    
    # Map ma_so based on legal framework (currently same for all frameworks)
    ma_so = 50
    table_name = "income_statement_p2_raw"
    
    return get_value_by_ma_so(
        stock=stock,
        year=year,
        ma_so=ma_so,
        quarter=quarter,
        table_name=table_name
    )
