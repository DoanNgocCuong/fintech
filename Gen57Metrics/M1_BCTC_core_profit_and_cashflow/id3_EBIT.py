from Gen57Metrics.utils_database_manager import get_value_by_ma_so
from typing import Optional

def get_EBIT_value(stock: str, year: int, quarter: int = None) -> Optional[float]:
    """
    Tính giá trị EBIT (Lợi nhuận trước lãi vay và thuế) cho công ty bảo hiểm.

    Definition (Định nghĩa):
        EBIT ≈ Lợi nhuận kế toán trước thuế (BCKQ HĐKD bảo hiểm – Mã 50)
               + Chi phí lãi vay (thành phần trong Chi phí hoạt động tài chính – Mã 22, cần tách từ thuyết minh).

        EBIT ≈ Profit before tax (Insurance business income statement – Code 50)
               + Interest expense (component of Finance costs – Code 22, should be split from financial statement notes).

    Args (Tham số):
        stock (str): Stock ticker (e.g. "MIG", "PGI") / Mã cổ phiếu
        year (int): Reporting year (e.g. 2024) / Năm báo cáo
        quarter (int, optional): Quarter (1, 2, 3, 4) or None for full year / Quý hoặc None cho cả năm

    Returns (Kết quả trả về):
        Optional[float]: EBIT value or None if not enough data / Giá trị EBIT hoặc None nếu thiếu dữ liệu

    Ghi chú (Notes):
        - Lợi nhuận kế toán trước thuế lấy từ báo cáo kết quả hoạt động kinh doanh bảo hiểm (Mã 50)
          Profit before tax is taken from insurance business income statement (code 50)
        - Chi phí lãi vay hiện nằm trong chi phí hoạt động tài chính (Mã 22), cần tách riêng từ thuyết minh.
          Hiện tại hàm get_value_by_ma_so trả về tổng chi phí hoạt động tài chính, 
          chỉ trả về đúng nếu toàn bộ chi phí tài chính là chi phí lãi vay.
          Interest expense is currently included in finance costs (code 22) and should ideally be split
          using notes in the financial statements. Currently we return total finance costs, which may 
          only be correct if all finance costs are interest expense.
    """
    # Mã 50: Lợi nhuận kế toán trước thuế / Profit before tax (code 50)
    profit_before_tax = get_value_by_ma_so(stock, year, 50, quarter)
    
    # Mã 22: Chi phí hoạt động tài chính / Finance costs (code 22)
    interest_expense = get_value_by_ma_so(stock, year, 22, quarter)
    
    # Nếu thiếu bất cứ thành phần nào thì trả về None / Return None if any component missing
    if profit_before_tax is None or interest_expense is None:
        return None
    
    # EBIT ≈ Lợi nhuận trước lãi vay và thuế / EBIT ≈ Earnings before interest and tax
    return profit_before_tax + interest_expense

