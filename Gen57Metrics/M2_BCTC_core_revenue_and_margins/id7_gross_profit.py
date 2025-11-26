"""
Gross Profit Indicator.

This is a DirectIndicator that retrieves Gross Profit value directly from database.
According to 57BaseIndicators.json:
- ID: 7
- Indicator_Name: "Gross Profit"
- Definition: "Lợi nhuận gộp về bán hàng và cung cấp dịch vụ (doanh thu - Giá vốn hàng bán (COGS))"
- Get_Direct_From_DB: "yes"
- TT200_Formula: "BCKQ HĐKD – Mẫu B02-DNNT – Mã 18 (công thức: KQKD_18)"
- Formula: "KQKD_18"
- Alternative_Formula: "Gross Profit = Revenue – COGS"

Note: Gross Profit is from income statement (KQKD), using ma_so 18 from P2 section only.
"""

from typing import Optional
from Gen57Metrics.utils_database_manager import get_value_by_ma_so, get_legal_framework

INCOME_STATEMENT_TABLE = "income_statement_p2_raw"
GROSS_PROFIT_CODE = 18


def get_gross_profit_value(
    stock: str, 
    year: int, 
    quarter: Optional[int] = 5,
    legal_framework: Optional[str] = None
) -> Optional[float]:
    """
    Lấy giá trị Gross Profit (Lợi nhuận gộp về bán hàng và cung cấp dịch vụ) 
    cho cổ phiếu và kỳ báo cáo chỉ định.

    - Gross Profit lấy từ Báo cáo kết quả hoạt động kinh doanh (BCKQ HĐKD), Mẫu B02-DNNT.
    - Mặc định (không phải BVH): 
        Gross Profit = KQKD_18 (mã số 18, template TT200 chuẩn).
    - Trường hợp riêng BVH (bảo hiểm):
        Gross Profit_BVH = KQKD_42
    - Chỉ lấy từ bảng income_statement_p2_raw (P2), không lấy từ P1.
    - Công thức thay thế: Gross Profit = Revenue – COGS

    Tham số:
        stock: Mã cổ phiếu, ví dụ: "MIG", "PGI", "BIC", "BVH".
        year: Năm tài chính, ví dụ: 2024.
        quarter: Quý (1-4) cho báo cáo quý, hoặc 5 cho báo cáo năm (mặc định: 5).
        legal_framework: Tên bộ luật (ví dụ: "TT199_2014", "TT232_2012"). 
                        Nếu None, sẽ tự động lấy từ database dựa trên stock.

    Kết quả trả về:
        Optional[float]: Giá trị Gross Profit lấy từ database, hoặc None nếu không tìm thấy.
    """
    # Get legal framework if not provided
    if legal_framework is None:
        legal_framework = get_legal_framework(stock)

    # Trường hợp riêng cho BVH: Gross Profit = KQKD_42
    if stock and stock.strip().upper() == "BVH":
        ma_so = 42
    else:
        # Mặc định: Gross Profit = KQKD_18
        ma_so = GROSS_PROFIT_CODE

    return get_value_by_ma_so(
        stock=stock,
        year=year,
        ma_so=ma_so,
        quarter=quarter,
        table_name=INCOME_STATEMENT_TABLE,
    )
