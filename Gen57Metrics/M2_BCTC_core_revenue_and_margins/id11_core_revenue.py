"""
Core Revenue Indicator.

This is a DirectIndicator that retrieves Core Revenue value directly from database.
According to 57BaseIndicators.json:
- ID: 11
- Indicator_Name: "Core Revenue"
- Definition: "Doanh thu cốt lõi (segment chính)"
- Get_Direct_From_DB: "yes"
- TT200_Formula: "BCKQ HĐKD – Mẫu B02-DNNT – Mã 10 (công thức: KQKD_10)"
- Formula: "KQKD_10"
- Alternative_Formula: "Core Revenue = Revenue from core business segments"

Note: Core Revenue is from income statement (KQKD), using ma_so 10 from P2 section only.
"""

from typing import Optional
from Gen57Metrics.utils_database_manager import get_value_by_ma_so, get_legal_framework

INCOME_STATEMENT_TABLE = "income_statement_p2_raw"
CORE_REVENUE_CODE = 10


def get_core_revenue_value(
    stock: str, 
    year: int, 
    quarter: Optional[int] = 5,
    legal_framework: Optional[str] = None
) -> Optional[float]:
    """
    Lấy giá trị Core Revenue (Doanh thu cốt lõi, segment chính) 
    cho cổ phiếu và kỳ báo cáo chỉ định.

    - Core Revenue lấy từ Báo cáo kết quả hoạt động kinh doanh (BCKQ HĐKD), Mẫu B02-DNNT.
    - Mặc định (không phải BVH): 
        Core Revenue = KQKD_10.
    - Trường hợp riêng BVH (bảo hiểm), theo mapping BVH:
        Core Revenue_BVH = KQKD_02 (Phí bảo hiểm gốc).
    - Chỉ lấy từ bảng income_statement_p2_raw (P2), không lấy từ P1.
    - Công thức thay thế: Core Revenue = Revenue from core business segments

    Tham số:
        stock: Mã cổ phiếu, ví dụ: "MIG", "PGI", "BIC", "BVH".
        year: Năm tài chính, ví dụ: 2024.
        quarter: Quý (1-4) cho báo cáo quý, hoặc 5 cho báo cáo năm (mặc định: 5).
        legal_framework: Tên bộ luật (ví dụ: "TT199_2014", "TT232_2012"). 
                        Nếu None, sẽ tự động lấy từ database dựa trên stock.

    Kết quả trả về:
        Optional[float]: Giá trị Core Revenue lấy từ database, hoặc None nếu không tìm thấy.
    """
    # Get legal framework if not provided
    if legal_framework is None:
        legal_framework = get_legal_framework(stock)

    # Trường hợp riêng cho BVH: Core Revenue = KQKD_02 (Phí bảo hiểm gốc)
    if stock and stock.strip().upper() == "BVH":
        ma_so = 2
    else:
        # Mặc định: Core Revenue = KQKD_10
        ma_so = CORE_REVENUE_CODE

    return get_value_by_ma_so(
        stock=stock,
        year=year,
        ma_so=ma_so,
        quarter=quarter,
        table_name=INCOME_STATEMENT_TABLE,
    )
