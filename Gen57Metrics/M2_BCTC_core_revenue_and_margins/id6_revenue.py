"""
Revenue Indicator.

This is a DirectIndicator that calculates Revenue from multiple components.
According to 57BaseIndicators.json:
- ID: 6
- Indicator_Name: "Revenue"
- Definition: "Doanh thu thuần"
- Get_Direct_From_DB: "yes"
- TT200_Formula: "BCKQ HĐKD – Mẫu B02-DNNT – Mã 10, 19, 22 (công thức: KQKD_10 + KQKD_19 + KQKD_22)"
- Formula: "KQKD_10 + KQKD_19 + KQKD_22"
- Alternative_Formula: "Revenue = Net revenue from sales and services"

Note: Revenue is calculated from income statement (KQKD), using ma_so 10, 19, 22 from P2 section.
"""

from typing import Optional
from Gen57Metrics.utils_database_manager import get_value_by_ma_so, get_legal_framework

INCOME_STATEMENT_TABLE = "income_statement_p2_raw"
REVENUE_COMPONENT_CODES = (10, 19, 22)


def get_revenue_value(
    stock: str, 
    year: int, 
    quarter: Optional[int] = 5,
    legal_framework: Optional[str] = None
) -> Optional[float]:
    """
    Lấy giá trị Revenue (Doanh thu thuần) cho cổ phiếu và kỳ báo cáo chỉ định.

    - Revenue lấy từ Báo cáo kết quả hoạt động kinh doanh (BCKQ HĐKD), Mẫu B02-DNNT.
    - Mặc định (không phải BVH): Công thức chuẩn TT200:
        Revenue = KQKD_10 + KQKD_19 + KQKD_22
    - Trường hợp riêng BVH (bảo hiểm): sử dụng template BVH:
        Revenue_BVH = KQKD_15
    - Chỉ lấy từ bảng income_statement_p2_raw (P2), không lấy từ P1.
    - Công thức thay thế: Revenue = Net revenue from sales and services

    Tham số:
        stock: Mã cổ phiếu, ví dụ: "MIG", "PGI", "BIC", "BVH".
        year: Năm tài chính, ví dụ: 2024.
        quarter: Quý (1-4) cho báo cáo quý, hoặc 5 cho báo cáo năm (mặc định: 5).
        legal_framework: Tên bộ luật (ví dụ: "TT199_2014", "TT232_2012"). 
                        Nếu None, sẽ tự động lấy từ database dựa trên stock.

    Kết quả trả về:
        Optional[float]: 
            - Đối với BVH: Giá trị KQKD_15.
            - Đối với các mã khác: Tổng của KQKD_10 + KQKD_19 + KQKD_22.
            Trả về None nếu thiếu dữ liệu.
    """
    # Get legal framework if not provided
    if legal_framework is None:
        legal_framework = get_legal_framework(stock)

    # Trường hợp riêng cho BVH: Revenue = KQKD_15
    if stock and stock.strip().upper() == "BVH":
        value = get_value_by_ma_so(
            stock=stock,
            year=year,
            ma_so=15,  # KQKD_15 theo template BVH
            quarter=quarter,
            table_name=INCOME_STATEMENT_TABLE,
        )
        if value is None:
            return None
        return float(abs(value))

    # Mặc định cho các mã khác: Revenue = KQKD_10 + KQKD_19 + KQKD_22
    values = []
    for code in REVENUE_COMPONENT_CODES:
        value = get_value_by_ma_so(
            stock=stock,
            year=year,
            ma_so=code,
            quarter=quarter,
            table_name=INCOME_STATEMENT_TABLE,
        )
        if value is None:
            # Nếu thiếu bất kỳ thành phần nào, trả về None
            return None
        values.append(value)

    if not values:
        return None

    # Sử dụng abs() cho tất cả giá trị trước khi tính tổng
    return float(sum(abs(v) for v in values))
