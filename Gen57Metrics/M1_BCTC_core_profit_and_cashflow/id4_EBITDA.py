"""
EBITDA (Earnings Before Interest, Tax, Depreciation and Amortization) Indicator.

This is a CalculatedIndicator that computes EBITDA from EBIT and cash flow data.
According to 57BaseIndicators.json:
- ID: 4
- Indicator_Name: "EBITDA"
- Definition: "EBIT cộng khấu hao và phân bổ"
- Formula: "EBITDA = EBIT + D&A"
- TT200_Formula: "EBITDA = EBIT + (LCTT – Mã 02)"

Note:
- EBITDA = EBIT + Depreciation & Amortization (D&A).
- D&A được xấp xỉ từ Báo cáo lưu chuyển tiền tệ (LCTT), Mã 02.
"""

from typing import Optional

from Gen57Metrics.utils_database_manager import get_value_by_ma_so, get_legal_framework
from Gen57Metrics.M1_BCTC_core_profit_and_cashflow.id3_EBIT import get_EBIT_value

CASH_FLOW_TABLE = "cash_flow_statement_raw"
DA_CODE = 2  # LCTT – Mã 02: Khấu hao TSCĐ và BĐS đầu tư


def get_EBITDA_value(
    stock: str,
    year: int,
    quarter: Optional[int] = 5,
    legal_framework: Optional[str] = None,
) -> Optional[float]:
    """
    Get EBITDA (Earnings Before Interest, Tax, Depreciation and Amortization)
    for a given stock and period.

    - Công thức: EBITDA = EBIT + D&A
    - Công thức TT200: EBITDA = EBIT + (LCTT – Mã 02)
        * EBIT: tính từ BCKQ HĐKD (xem get_EBIT_value).
        * LCTT_02: Khấu hao TSCĐ và BĐS đầu tư từ Báo cáo Lưu chuyển Tiền tệ.

    Args:
        stock: Mã cổ phiếu, ví dụ: "MIG", "PGI", "BIC", "BVH".
        year: Năm tài chính, ví dụ: 2024.
        quarter: Quý (1-4) cho báo cáo quý, hoặc 5 cho báo cáo năm (mặc định: 5).
        legal_framework: Tên bộ luật (ví dụ: "TT199_2014", "TT232_2012").
                        Nếu None, sẽ tự động lấy từ database dựa trên stock.

    Returns:
        Optional[float]:
            - None nếu stock là BVH (không dùng EBITDA riêng cho BVH).
            - Hoặc giá trị EBITDA, nếu đủ dữ liệu.
    """
    # Get legal framework if not provided (giữ signature đồng nhất)
    if legal_framework is None:
        legal_framework = get_legal_framework(stock)

    # Trường hợp riêng: BVH → không sử dụng EBITDA, trả về None
    if stock and stock.strip().upper() == "BVH":
        return None

    # Lấy EBIT
    ebit = get_EBIT_value(stock, year, quarter, legal_framework)
    if ebit is None:
        return None

    # Lấy D&A từ LCTT – Mã 02
    da_value = get_value_by_ma_so(
        stock=stock,
        year=year,
        ma_so=DA_CODE,
        quarter=quarter,
        table_name=CASH_FLOW_TABLE,
    )

    if da_value is None:
        return None

    # Ở đây cũng KHÔNG dùng abs(), để EBITDA phản ánh đúng dấu theo báo cáo
    return float(ebit + da_value)


