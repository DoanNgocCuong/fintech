"""
Accounts Receivable Indicator.

This is a DirectIndicator that retrieves Accounts Receivable value directly from database.
According to 57BaseIndicators.json:
- ID: 23
- Indicator_Name: "Accounts Receivable"
- Definition: "Phải thu khách hàng"
- Get_Direct_From_DB: "yes"
- TT200_Formula: "Bảng CĐKT – Mẫu B01-DNNT – Mã 131 (công thức: CDKT_131)"
- Formula: "CDKT_131"
- Alternative_Formula: "A/R = Trade receivables"

Note: Accounts Receivable is from balance sheet (CDKT), using ma_so 131.
"""

from typing import Optional
from Gen57Metrics.utils_database_manager import get_value_by_ma_so, get_legal_framework

BALANCE_SHEET_TABLE = "balance_sheet_raw"
ACCOUNTS_RECEIVABLE_CODE = 131


def get_accounts_receivable_value(
    stock: str, 
    year: int, 
    quarter: Optional[int] = 5,
    legal_framework: Optional[str] = None
) -> Optional[float]:
    """
    Lấy giá trị Accounts Receivable (Phải thu khách hàng) cho cổ phiếu và kỳ báo cáo chỉ định.

    - Accounts Receivable lấy từ Bảng Cân Đối Kế Toán (Bảng CĐKT), Mẫu B01-DNNT, sử dụng mã số 131.
    - Lấy từ bảng balance_sheet_raw.
    - Công thức: CDKT_131
    - Công thức thay thế: A/R = Trade receivables

    Tham số:
        stock: Mã cổ phiếu, ví dụ: "MIG", "PGI", "BIC".
        year: Năm tài chính, ví dụ: 2024.
        quarter: Quý (1-4) cho báo cáo quý, hoặc 5 cho báo cáo năm (mặc định: 5).
        legal_framework: Tên bộ luật (ví dụ: "TT199_2014", "TT232_2012"). 
                        Nếu None, sẽ tự động lấy từ database dựa trên stock.

    Kết quả trả về:
        Optional[float]: Giá trị Accounts Receivable lấy từ database, hoặc None nếu không tìm thấy.

    Ví dụ:
        >>> # Lấy Accounts Receivable năm của MIG năm 2024 (quarter=5)
        >>> ar = get_accounts_receivable_value("MIG", 2024)
        >>> print(ar)
        3000000000.0

        >>> # Lấy Accounts Receivable quý 2 của MIG năm 2024
        >>> ar_q2 = get_accounts_receivable_value("MIG", 2024, quarter=2)
        >>> print(ar_q2)
        2800000000.0
    """
    # Get legal framework if not provided
    if legal_framework is None:
        legal_framework = get_legal_framework(stock)
    
    # Map ma_so based on legal framework (currently same for all frameworks)
    ma_so = ACCOUNTS_RECEIVABLE_CODE
    
    return get_value_by_ma_so(
        stock=stock,
        year=year,
        ma_so=ma_so,
        quarter=quarter,
        table_name=BALANCE_SHEET_TABLE,
    )

