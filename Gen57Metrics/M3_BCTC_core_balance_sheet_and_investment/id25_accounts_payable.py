"""
Accounts Payable Indicator.

This is a DirectIndicator that retrieves Accounts Payable value directly from database.
According to 57BaseIndicators.json:
- ID: 25
- Indicator_Name: "Accounts Payable"
- Definition: "Phải trả người bán"
- Get_Direct_From_DB: "yes"
- TT200_Formula: "Bảng CĐKT – Mẫu B01-DNNT – Mã 312 (công thức: CDKT_312)"
- Formula: "CDKT_312"
- Alternative_Formula: "A/P = Trade payables"

Note: Accounts Payable is from balance sheet (CDKT), using ma_so 312.
"""

from typing import Optional
from Gen57Metrics.utils_database_manager import get_value_by_ma_so, get_legal_framework

BALANCE_SHEET_TABLE = "balance_sheet_raw"
ACCOUNTS_PAYABLE_CODE = 312


def get_accounts_payable_value(
    stock: str, 
    year: int, 
    quarter: Optional[int] = 5,
    legal_framework: Optional[str] = None
) -> Optional[float]:
    """
    Lấy giá trị Accounts Payable (Phải trả người bán) cho cổ phiếu và kỳ báo cáo chỉ định.

    - Accounts Payable lấy từ Bảng Cân Đối Kế Toán (Bảng CĐKT), Mẫu B01-DNNT, sử dụng mã số 312.
    - Lấy từ bảng balance_sheet_raw.
    - Công thức: CDKT_312
    - Công thức thay thế: A/P = Trade payables

    Tham số:
        stock: Mã cổ phiếu, ví dụ: "MIG", "PGI", "BIC".
        year: Năm tài chính, ví dụ: 2024.
        quarter: Quý (1-4) cho báo cáo quý, hoặc 5 cho báo cáo năm (mặc định: 5).
        legal_framework: Tên bộ luật (ví dụ: "TT199_2014", "TT232_2012"). 
                        Nếu None, sẽ tự động lấy từ database dựa trên stock.

    Kết quả trả về:
        Optional[float]: Giá trị Accounts Payable lấy từ database, hoặc None nếu không tìm thấy.

    Ví dụ:
        >>> # Lấy Accounts Payable năm của MIG năm 2024 (quarter=5)
        >>> ap = get_accounts_payable_value("MIG", 2024)
        >>> print(ap)
        2000000000.0

        >>> # Lấy Accounts Payable quý 2 của MIG năm 2024
        >>> ap_q2 = get_accounts_payable_value("MIG", 2024, quarter=2)
        >>> print(ap_q2)
        1900000000.0
    """
    # Get legal framework if not provided
    if legal_framework is None:
        legal_framework = get_legal_framework(stock)
    
    # Map ma_so based on legal framework (currently same for all frameworks)
    ma_so = ACCOUNTS_PAYABLE_CODE
    
    return get_value_by_ma_so(
        stock=stock,
        year=year,
        ma_so=ma_so,
        quarter=quarter,
        table_name=BALANCE_SHEET_TABLE,
    )

