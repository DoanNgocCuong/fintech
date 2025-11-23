"""
Net Income (NI) Indicator.

This is a DirectIndicator that retrieves NI value directly from database.
According to 57BaseIndicators.json:
- ID: 2
- Indicator_Name: "Net Income (NI)"
- Definition: "Lợi nhuận sau thuế thu nhập doanh nghiệp"
- Get_Direct_From_DB: "yes"
- TT200_Formula: "BCKQ HĐKD – Mẫu B02-DNNT – Mã 60 (công thức: KQKD_60)"

Note: NI is from income statement (KQKD), using ma_so 60 from P2 section only.
"""

from typing import Optional
from Gen57Metrics.utils_database_manager import get_value_by_ma_so, get_legal_framework


def get_NI_value(
    stock: str, 
    year: int, 
    quarter: Optional[int] = 5,
    legal_framework: Optional[str] = None
) -> Optional[float]:
    """
    Lấy giá trị Net Income (NI, Lợi nhuận sau thuế thu nhập doanh nghiệp) cho cổ phiếu và kỳ báo cáo chỉ định.

    - NI lấy từ Báo cáo kết quả hoạt động kinh doanh (BCKQ HĐKD), Mẫu B02-DNNT, sử dụng mã số tương ứng với bộ luật.
    - Mã số được map dựa trên bộ luật (legal_framework):
      * TT199_2014: ma_so 60
      * TT232_2012: ma_so 60
    - Chỉ lấy từ bảng income_statement_p2_raw (P2), không lấy từ P1.
    - Công thức: KQKD_60

    Tham số:
        stock: Mã cổ phiếu, ví dụ: "MIG", "PGI", "BIC".
        year: Năm tài chính, ví dụ: 2024.
        quarter: Quý (1-4) cho báo cáo quý, hoặc 5 cho báo cáo năm (mặc định: 5).
        legal_framework: Tên bộ luật (ví dụ: "TT199_2014", "TT232_2012"). 
                        Nếu None, sẽ tự động lấy từ database dựa trên stock.

    Kết quả trả về:
        Optional[float]: Giá trị NI lấy từ database, hoặc None nếu không tìm thấy.

    Ví dụ:
        >>> # Lấy NI năm của MIG năm 2024 (quarter=5)
        >>> ni = get_NI_value("MIG", 2024)
        >>> print(ni)
        1234567890.0

        >>> # Lấy NI quý 2 của MIG năm 2024
        >>> ni_q2 = get_NI_value("MIG", 2024, quarter=2)
        >>> print(ni_q2)
        9876543210.0
    """
    # Get legal framework if not provided
    if legal_framework is None:
        legal_framework = get_legal_framework(stock)
    
    # Normalize legal framework name
    if legal_framework:
        legal_framework = legal_framework.strip().upper()
        if legal_framework == "TT199" or legal_framework.startswith("TT199"):
            legal_framework = "TT199_2014"
        elif legal_framework == "TT232" or legal_framework.startswith("TT232"):
            legal_framework = "TT232_2012"
    
    # Map ma_so based on legal framework
    # NI uses ma_so 60 for all frameworks
    table_name = "income_statement_p2_raw"
    
    if legal_framework == "TT199_2014":
        ma_so = 60
    elif legal_framework == "TT232_2012":
        ma_so = 60
    else:
        # Default fallback
        ma_so = 60
    
    return get_value_by_ma_so(
        stock=stock,
        year=year,
        ma_so=ma_so,
        quarter=quarter,
        table_name=table_name
    )
