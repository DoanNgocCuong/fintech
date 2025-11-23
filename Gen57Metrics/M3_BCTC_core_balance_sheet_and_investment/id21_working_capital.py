"""
Working Capital (WC) Indicator.

This is a CalculatedIndicator that calculates Working Capital from balance sheet components.
According to 57BaseIndicators.json:
- ID: 21
- Indicator_Name: "Working Capital (WC)"
- Definition: "Vốn lưu động hoạt động"
- Get_Direct_From_DB: "no"
- TT200_Formula: "Bảng CĐKT – Mẫu B01-DNNT – Mã 130, 140, 312 (công thức: CDKT_130 + CDKT_140 - CDKT_312)"
- Formula: "CDKT_130 + CDKT_140 - CDKT_312"
- Alternative_Formula: "WC = A/R + Inventory – A/P"

Note: Working Capital = Current Assets (130) + Inventory (140) - Accounts Payable (312)
"""

from typing import Optional
from Gen57Metrics.utils_database_manager import get_value_by_ma_so, get_legal_framework

BALANCE_SHEET_TABLE = "balance_sheet_raw"
WORKING_CAPITAL_COMPONENTS = {
    "current_assets": 130,
    "inventory": 140,
    "accounts_payable": 312,
}


def get_working_capital_value(
    stock: str, 
    year: int, 
    quarter: Optional[int] = 5,
    legal_framework: Optional[str] = None
) -> Optional[float]:
    """
    Lấy giá trị Working Capital (Vốn lưu động hoạt động) cho cổ phiếu và kỳ báo cáo chỉ định.

    - Working Capital lấy từ Bảng Cân Đối Kế Toán (Bảng CĐKT), Mẫu B01-DNNT.
    - Công thức: CDKT_130 + CDKT_140 - CDKT_312
    - Lấy từ bảng balance_sheet_raw.
    - Working Capital = Current Assets + Inventory - Accounts Payable
    - Công thức thay thế: WC = A/R + Inventory – A/P

    Tham số:
        stock: Mã cổ phiếu, ví dụ: "MIG", "PGI", "BIC".
        year: Năm tài chính, ví dụ: 2024.
        quarter: Quý (1-4) cho báo cáo quý, hoặc 5 cho báo cáo năm (mặc định: 5).
        legal_framework: Tên bộ luật (ví dụ: "TT199_2014", "TT232_2012"). 
                        Nếu None, sẽ tự động lấy từ database dựa trên stock.

    Kết quả trả về:
        Optional[float]: Giá trị Working Capital, hoặc None nếu thiếu bất kỳ thành phần nào.

    Ví dụ:
        >>> # Lấy Working Capital năm của MIG năm 2024 (quarter=5)
        >>> wc = get_working_capital_value("MIG", 2024)
        >>> print(wc)
        5000000000.0

        >>> # Lấy Working Capital quý 2 của MIG năm 2024
        >>> wc_q2 = get_working_capital_value("MIG", 2024, quarter=2)
        >>> print(wc_q2)
        4800000000.0
    """
    # Get legal framework if not provided
    if legal_framework is None:
        legal_framework = get_legal_framework(stock)
    
    # Map ma_so codes based on legal framework (currently same for all frameworks)
    # Get Current Assets (130)
    current_assets = get_value_by_ma_so(
        stock=stock,
        year=year,
        ma_so=WORKING_CAPITAL_COMPONENTS["current_assets"],
        quarter=quarter,
        table_name=BALANCE_SHEET_TABLE,
    )
    
    # Get Inventory (140)
    inventory = get_value_by_ma_so(
        stock=stock,
        year=year,
        ma_so=WORKING_CAPITAL_COMPONENTS["inventory"],
        quarter=quarter,
        table_name=BALANCE_SHEET_TABLE,
    )
    
    # Get Accounts Payable (312)
    accounts_payable = get_value_by_ma_so(
        stock=stock,
        year=year,
        ma_so=WORKING_CAPITAL_COMPONENTS["accounts_payable"],
        quarter=quarter,
        table_name=BALANCE_SHEET_TABLE,
    )
    
    # If any component is None, return None
    if current_assets is None or inventory is None or accounts_payable is None:
        return None
    
    # Working Capital = Current Assets + Inventory - Accounts Payable
    # Sử dụng abs() cho tất cả giá trị trong phép tính
    return float(abs(current_assets) + abs(inventory) - abs(accounts_payable))

