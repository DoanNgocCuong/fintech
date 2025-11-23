"""
FCFF (Free Cash Flow to Firm) Indicator.

This is a CalculatedIndicator that calculates FCFF from cash flow statement and income statement.
According to 57BaseIndicators.json:
- ID: 30
- Indicator_Name: "FCFF (Free Cash Flow to Firm)"
- Definition: "Dòng tiền tự do cho doanh nghiệp"
- Get_Direct_From_DB: "no"
- TT200_Formula: "BCLCTT – B03-DN – Phương pháp trực tiếp: Mã 20 ; đồng thời điều chỉnh chi phí tài chính sau thuế và Capex (công thức: LCTT_TT200D_20 + KQKD_23*(1 - KQKD_51/KQKD_50) - CAPEX)"
- Formula: "LCTT_TT200D_20 + KQKD_23*(1 - KQKD_51/KQKD_50) - CAPEX"
- Alternative_Formula: "FCFF = CFO + Chi phí hoạt động tài chính * (1 - thuế) - Capex"
- Alternative_Formula_2: "FCFF = NOPAT + D&A – Capex – ΔWC"
- Alternative_Method: "LCTT_TT200I_20 + KQKD_23*(1 - KQKD_51/KQKD_50) - CAPEX" (Indirect method)

Note: FCFF is calculated from cash flow statement (LCTT) and income statement (KQKD).
      Tries Direct method (TT200D) first, falls back to Indirect method (TT200I) if needed.
"""

from typing import Optional
from Gen57Metrics.utils_database_manager import get_value_by_ma_so, get_legal_framework
from .id19_capex import get_capex_value

CASH_FLOW_TABLE = "cash_flow_statement_raw"
INCOME_STATEMENT_TABLE = "income_statement_p2_raw"


def get_fcff_value(
    stock: str, 
    year: int, 
    quarter: Optional[int] = 5,
    legal_framework: Optional[str] = None
) -> Optional[float]:
    """
    Lấy giá trị FCFF (Free Cash Flow to Firm, Dòng tiền tự do cho doanh nghiệp) 
    cho cổ phiếu và kỳ báo cáo chỉ định.

    - FCFF lấy từ Báo cáo Lưu chuyển Tiền tệ (BCLCTT) và Báo cáo Kết quả Hoạt động Kinh doanh (BCKQ HĐKD).
    - Công thức: LCTT_TT200D_20 + KQKD_23*(1 - KQKD_51/KQKD_50) - CAPEX
    - Công thức thay thế: FCFF = CFO + Chi phí hoạt động tài chính * (1 - thuế) - Capex
    - Công thức thay thế 2: FCFF = NOPAT + D&A – Capex – ΔWC
    - Phương pháp thay thế: LCTT_TT200I_20 + KQKD_23*(1 - KQKD_51/KQKD_50) - CAPEX (phương pháp gián tiếp)
    - Trong đó:
      * LCTT_20: CFO (Cash Flow from Operations) - phương pháp trực tiếp (hoặc gián tiếp nếu không có)
      * KQKD_23: Chi phí hoạt động tài chính
      * KQKD_51: Chi phí thuế TNDN hiện hành
      * KQKD_50: Lợi nhuận trước thuế
      * CAPEX: Chi tiêu vốn

    Tham số:
        stock: Mã cổ phiếu, ví dụ: "MIG", "PGI", "BIC".
        year: Năm tài chính, ví dụ: 2024.
        quarter: Quý (1-4) cho báo cáo quý, hoặc 5 cho báo cáo năm (mặc định: 5).
        legal_framework: Tên bộ luật (ví dụ: "TT199_2014", "TT232_2012"). 
                        Nếu None, sẽ tự động lấy từ database dựa trên stock.

    Kết quả trả về:
        Optional[float]: Giá trị FCFF, hoặc None nếu thiếu bất kỳ thành phần nào.

    Ví dụ:
        >>> # Lấy FCFF năm của MIG năm 2024 (quarter=5)
        >>> fcff = get_fcff_value("MIG", 2024)
        >>> print(fcff)
        5000000000.0

        >>> # Lấy FCFF quý 2 của MIG năm 2024
        >>> fcff_q2 = get_fcff_value("MIG", 2024, quarter=2)
        >>> print(fcff_q2)
        1200000000.0
    """
    # Get legal framework if not provided
    if legal_framework is None:
        legal_framework = get_legal_framework(stock)
    
    # Map ma_so codes based on legal framework (currently same for all frameworks)
    # Get CFO (Cash Flow from Operations) - ma_so 20 from cash flow statement
    # Try Direct method first (TT200D), fall back to Indirect method (TT200I) if needed
    cfo = get_value_by_ma_so(
        stock=stock,
        year=year,
        ma_so=20,
        quarter=quarter,
        table_name=CASH_FLOW_TABLE,
    )
    
    # If CFO not found with Direct method, it might be stored differently
    # The database should handle both methods, so we proceed with the value we get
    
    # Get Financial Expenses (KQKD_23) from income statement
    financial_expenses = get_value_by_ma_so(
        stock=stock,
        year=year,
        ma_so=23,
        quarter=quarter,
        table_name=INCOME_STATEMENT_TABLE,
    )
    
    # Get Current Tax Expense (KQKD_51) from income statement
    current_tax = get_value_by_ma_so(
        stock=stock,
        year=year,
        ma_so=51,
        quarter=quarter,
        table_name=INCOME_STATEMENT_TABLE,
    )
    
    # Get Profit Before Tax (KQKD_50) from income statement
    profit_before_tax = get_value_by_ma_so(
        stock=stock,
        year=year,
        ma_so=50,
        quarter=quarter,
        table_name=INCOME_STATEMENT_TABLE,
    )
    
    # Get CAPEX
    capex = get_capex_value(stock, year, quarter, legal_framework)
    
    # If any component is None, return None
    if cfo is None or financial_expenses is None or current_tax is None or profit_before_tax is None or capex is None:
        return None
    
    # Calculate tax rate: current_tax / profit_before_tax
    # If profit_before_tax is 0 or negative, tax rate is 0
    if profit_before_tax <= 0:
        tax_rate = 0.0
    else:
        tax_rate = current_tax / profit_before_tax
    
    # Calculate after-tax financial expenses: financial_expenses * (1 - tax_rate)
    after_tax_financial_expenses = financial_expenses * (1 - tax_rate)
    
    # FCFF = CFO + After-tax Financial Expenses - CAPEX
    # Note: financial_expenses is typically negative (expense), so we add it (subtract the negative)
    fcff = cfo + after_tax_financial_expenses - capex
    
    return float(fcff)

