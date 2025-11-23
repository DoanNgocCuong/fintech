"""
Total Assets Indicator.

This is a DirectIndicator that retrieves Total Assets value directly from database.
According to 57BaseIndicators.json:
- ID: 15
- Indicator_Name: "Total Assets"
- Definition: "Tổng tài sản"
- Get_Direct_From_DB: "yes"
- TT200_Formula: "Bảng CĐKT – Mẫu B01-DNNT – Mã 270 (công thức: CDKT_270)"
- Formula: "CDKT_270"
- Alternative_Formula: "Total Assets = Sum of all assets"

Note: Total Assets is from balance sheet (CDKT), using ma_so 270.
"""

from typing import Optional
from Gen57Metrics.utils_database_manager import get_value_by_ma_so, get_legal_framework

BALANCE_SHEET_TABLE = "balance_sheet_raw"
TOTAL_ASSETS_CODE = 270


def get_total_assets_value(
    stock: str, 
    year: int, 
    quarter: Optional[int] = 5,
    legal_framework: Optional[str] = None
) -> Optional[float]:
    """
    Lấy giá trị Total Assets (Tổng tài sản) cho cổ phiếu và kỳ báo cáo chỉ định.

    - Total Assets lấy từ Bảng Cân Đối Kế Toán (Bảng CĐKT), Mẫu B01-DNNT, sử dụng mã số 270.
    - Lấy từ bảng balance_sheet_raw.
    - Công thức: CDKT_270
    - Công thức thay thế: Total Assets = Sum of all assets

    Tham số:
        stock: Mã cổ phiếu, ví dụ: "MIG", "PGI", "BIC".
        year: Năm tài chính, ví dụ: 2024.
        quarter: Quý (1-4) cho báo cáo quý, hoặc 5 cho báo cáo năm (mặc định: 5).
        legal_framework: Tên bộ luật (ví dụ: "TT199_2014", "TT232_2012"). 
                        Nếu None, sẽ tự động lấy từ database dựa trên stock.

    Kết quả trả về:
        Optional[float]: Giá trị Total Assets lấy từ database, hoặc None nếu không tìm thấy.

    Ví dụ:
        >>> # Lấy Total Assets năm của MIG năm 2024 (quarter=5)
        >>> total_assets = get_total_assets_value("MIG", 2024)
        >>> print(total_assets)
        50000000000.0

        >>> # Lấy Total Assets quý 2 của MIG năm 2024
        >>> total_assets_q2 = get_total_assets_value("MIG", 2024, quarter=2)
        >>> print(total_assets_q2)
        48000000000.0
    """
    # Get legal framework if not provided
    if legal_framework is None:
        legal_framework = get_legal_framework(stock)
    
    # Map ma_so based on legal framework (currently same for all frameworks)
    ma_so = TOTAL_ASSETS_CODE
    
    return get_value_by_ma_so(
        stock=stock,
        year=year,
        ma_so=ma_so,
        quarter=quarter,
        table_name=BALANCE_SHEET_TABLE,
    )

