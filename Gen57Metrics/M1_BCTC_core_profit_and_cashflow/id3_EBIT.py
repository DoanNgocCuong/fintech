from typing import Optional
from Gen57Metrics.utils_database_manager import get_value_by_ma_so

def get_EBIT_value(stock: str, year: int, quarter: Optional[int] = None) -> Optional[float]:
    """
    EBIT (Lợi nhuận trước lãi vay và thuế) cho doanh nghiệp bảo hiểm.

    Theo TT232/TT200: EBIT ≈ Lợi nhuận kế toán trước thuế (KQKD – Mã 50).
    Đặc thù ngành bảo hiểm xem chi phí vốn là hoạt động tài chính lõi nên
    không cộng lại chi phí lãi vay.

    Chỉ lấy từ bảng income_statement_p2_raw (P2), không check P1.

    Args:
        stock: Mã cổ phiếu (ví dụ "MIG").
        year: Năm báo cáo.
        quarter: Quý (1-4) hoặc None cho báo cáo năm.

    Returns:
        Giá trị EBIT hoặc None nếu không tìm thấy Mã 50.
    """
    return get_value_by_ma_so(
        stock=stock,
        year=year,
        ma_so=50,
        quarter=quarter,
        table_name="income_statement_p2_raw"
    )
