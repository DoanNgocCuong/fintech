# ===========================================
# 📊 XNO / VNSTOCK - VALUATION METRICS CRAWLER
# ===========================================
from xno import stock, financials, metrics, valuation
from vnstock import Fundamental, Financial

TICKER = "FPT"  # Thay bằng mã cổ phiếu bạn muốn crawl

def valuation_metrics(ticker=TICKER):
    data = {}

    # --- 1. P/E ---
    try:
        data["PE"] = stock(ticker).pe_ttm()
    except Exception:
        data["PE"] = Fundamental(ticker).pe()

    # --- 2. PEG ---
    try:
        data["PEG"] = stock(ticker).peg_ratio()
    except Exception:
        data["PEG"] = None  # Cần tính thủ công nếu không có

    # --- 3. EV/EBITDA ---
    try:
        data["EV_EBITDA"] = financials(ticker).ev_ebitda()
    except Exception:
        data["EV_EBITDA"] = None

    # --- 4. P/B ---
    try:
        data["PB"] = Fundamental(ticker).pb()
    except Exception:
        data["PB"] = None

    # --- 5. Dividend Yield ---
    try:
        data["Dividend_Yield"] = stock(ticker).dividend_yield()
    except Exception:
        data["Dividend_Yield"] = None

    # --- 6. Earnings Yield ---
    try:
        pe = data.get("PE")
        data["Earnings_Yield"] = 1 / pe if pe else None
    except Exception:
        data["Earnings_Yield"] = None

    # --- 7. FCF Yield ---
    try:
        data["FCF_Yield"] = financials(ticker).fcf_yield()
    except Exception:
        data["FCF_Yield"] = None

    # --- 8. EV/FCF ---
    try:
        data["EV_FCF"] = metrics(ticker).ev_fcf()
    except Exception:
        data["EV_FCF"] = None

    # --- 9. P/OCF ---
    try:
        data["P_OCF"] = financials(ticker).p_ocf()
    except Exception:
        data["P_OCF"] = None

    # --- 10. DCF ---
    try:
        data["DCF_Value"] = valuation(ticker).dcf()
    except Exception:
        # fallback: tự tính từ dòng tiền
        cf = financials(ticker).cashflow(5)  # 5 năm
        discount_rate = 0.1
        data["DCF_Value"] = sum([cf[i] / ((1 + discount_rate) ** (i + 1)) for i in range(len(cf))])

    # --- 11. Intrinsic Gap ---
    try:
        price = stock(ticker).price()
        intrinsic = data.get("DCF_Value")
        if price and intrinsic:
            data["Intrinsic_Gap_%"] = round((price - intrinsic) / intrinsic * 100, 2)
    except Exception:
        data["Intrinsic_Gap_%"] = None

    # --- 12. EV/Sales ---
    try:
        data["EV_Sales"] = financials(ticker).ev_sales()
    except Exception:
        data["EV_Sales"] = None

    return data


if __name__ == "__main__":
    result = valuation_metrics()
    print("📘 Valuation Metrics for:", TICKER)
    for k, v in result.items():
        print(f"{k:20}: {v}")
