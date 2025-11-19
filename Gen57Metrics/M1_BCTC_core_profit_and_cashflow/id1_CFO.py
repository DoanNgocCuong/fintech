"""
CFO (Cash Flow from Operations) Indicator.

This is a DirectIndicator that retrieves CFO value directly from database.
According to 57BaseIndicators.json:
- ID: 1
- Indicator_Name: "CFO"
- Definition: "Dòng tiền thuần từ hoạt động kinh doanh"
- Get_Direct_From_DB: "yes"
- TT200_Formula: "LCTT (TT200) – Mã 20 (gián tiếp) hoặc Mã 21 (trực tiếp)"

Note: CFO is from cash flow statement (LCTT), using ma_so 20 (indirect) or 21 (direct)
"""

from typing import Optional
from Gen57Metrics.utils_database_manager import get_value_by_ma_so


def get_CFO_value(stock: str, year: int, quarter: Optional[int] = None) -> Optional[float]:
    """
    Lấy giá trị CFO (Dòng tiền thuần từ hoạt động kinh doanh) cho cổ phiếu và kỳ báo cáo chỉ định.

    - CFO lấy từ Báo cáo lưu chuyển tiền tệ (LCTT), sử dụng mã số 20 (phương pháp gián tiếp) hoặc 21 (phương pháp trực tiếp).
    - Thử truy vấn mã số 20 trước (gián tiếp). Nếu không có dữ liệu thì thử tiếp mã số 21 (trực tiếp).

    Tham số:
        stock: Mã cổ phiếu, ví dụ: "MIG", "PGI", "BIC".
        year: Năm tài chính, ví dụ: 2024.
        quarter: Quý (1-4), hoặc None cho báo cáo năm.

    Kết quả trả về:
        Optional[float]: Giá trị CFO lấy từ database, hoặc None nếu không tìm thấy.

    Ví dụ:
        >>> # Lấy CFO năm của MIG năm 2024
        >>> cfo = get_CFO_value("MIG", 2024)
        >>> print(cfo)
        1234567890.0

        >>> # Lấy CFO quý 2 của MIG năm 2024
        >>> cfo_q2 = get_CFO_value("MIG", 2024, quarter=2)
        >>> print(cfo_q2)
        9876543210.0
    """
    # CFO is from cash flow statement (LCTT)
    # Try ma_so 20 (indirect method) first
    value = get_value_by_ma_so(
        stock=stock,
        year=year,
        ma_so=20,
        quarter=quarter,
        table_name="cash_flow_statement_raw"  # Cash flow statement table
    )
    
    # If ma_so 20 not found, try ma_so 21 (direct method)
    if value is None:
        value = get_value_by_ma_so(
            stock=stock,
            year=year,
            ma_so=21,
            quarter=quarter,
            table_name="cash_flow_statement_raw"
        )
    
    return value