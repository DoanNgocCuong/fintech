"""
EBIT (Earnings Before Interest and Tax) Indicator.

This is a CalculatedIndicator that computes EBIT from income statement data.
According to 57BaseIndicators.json:
- ID: 3
- Indicator_Name: "EBIT"
- Definition: "Lợi nhuận trước lãi vay và thuế"
- Formula: "EBIT = Operating profit + Interest expense"
- TT200_Formula: "EBIT = (KQKD – Mã 50) + (KQKD – Mã 23)"

Note: EBIT is derived from income statement (KQKD), using:
    - ma_so 50: Operating profit (Lợi nhuận thuần từ hoạt động kinh doanh)
    - ma_so 23: Interest expense (Chi phí lãi vay)
Data is taken from income_statement_p2_raw (P2).
"""

from typing import Optional

from Gen57Metrics.utils_database_manager import get_value_by_ma_so, get_legal_framework

INCOME_STATEMENT_TABLE = "income_statement_p2_raw"
EBIT_OPERATING_PROFIT_CODE = 50
EBIT_INTEREST_EXPENSE_CODE = 23


def get_EBIT_value(
    stock: str,
    year: int,
    quarter: Optional[int] = 5,
    legal_framework: Optional[str] = None,
) -> Optional[float]:
    """
    Get EBIT (Earnings Before Interest and Tax) for a given stock and period.

    - EBIT lấy từ Báo cáo kết quả hoạt động kinh doanh (BCKQ HĐKD), Mẫu B02-DNNT.
    - Công thức TT200: EBIT = (KQKD_50) + (KQKD_23)
        * KQKD_50: Lợi nhuận thuần từ hoạt động kinh doanh.
        * KQKD_23: Chi phí lãi vay (thường là số âm trong báo cáo).
    - Chỉ lấy từ bảng income_statement_p2_raw (P2), không lấy từ P1.

    Args:
        stock: Mã cổ phiếu, ví dụ: "MIG", "PGI", "BIC", "BVH".
        year: Năm tài chính, ví dụ: 2024.
        quarter: Quý (1-4) cho báo cáo quý, hoặc 5 cho báo cáo năm (mặc định: 5).
        legal_framework: Tên bộ luật (ví dụ: "TT199_2014", "TT232_2012").
                        Nếu None, sẽ tự động lấy từ database dựa trên stock.

    Returns:
        Optional[float]:
            - None nếu stock là BVH (không dùng EBIT riêng cho BVH).
            - Hoặc giá trị EBIT, nếu đủ dữ liệu.
    """
    # Get legal framework if not provided (giữ cho interface đồng nhất)
    if legal_framework is None:
        legal_framework = get_legal_framework(stock)

    # Trường hợp riêng: BVH → không sử dụng EBIT, trả về None
    if stock and stock.strip().upper() == "BVH":
        return None

    # Lấy KQKD_50 (Operating profit)
    operating_profit = get_value_by_ma_so(
        stock=stock,
        year=year,
        ma_so=EBIT_OPERATING_PROFIT_CODE,
        quarter=quarter,
        table_name=INCOME_STATEMENT_TABLE,
    )

    # Lấy KQKD_23 (Interest expense)
    interest_expense = get_value_by_ma_so(
        stock=stock,
        year=year,
        ma_so=EBIT_INTEREST_EXPENSE_CODE,
        quarter=quarter,
        table_name=INCOME_STATEMENT_TABLE,
    )

    if operating_profit is None or interest_expense is None:
        return None

    # Ở đây KHÔNG dùng abs(), để giữ đúng dấu của EBIT
    return float(operating_profit + interest_expense)


