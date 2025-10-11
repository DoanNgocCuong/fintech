# ===========================================
# 📊 VNSTOCK - VALUATION METRICS CRAWLER
# ===========================================
from vnstock import Financial, Fundamental, Company
import math

TICKER = "FPT"  # Thay bằng mã cổ phiếu bạn muốn crawl


def valuation_metrics_vnstock(ticker=TICKER):
    data = {}

    # --- 1. P/E ---
    try:
        data["PE"] = Fundamental(ticker).pe()
    except Exception:
        data["PE"] = None

    # --- 2. PEG ---
    try:
        eps_growth = Fundamental(ticker).eps_growth()  # %
        if data["PE"] and eps_growth:
            data["PEG"] = round(data["PE"] / eps_growth, 2)
        else:
            data["PEG"] = None
    except Exception:
        data["PEG"] = None

    # --- 3. EV/EBITDA ---
    try:
        fin = Financial(ticker)
        ev = fin.enterprise_value()  # EV = Market Cap + Debt - Cash
        ebitda = fin.ebitda()
        data["EV_EBITDA"] = round(ev / ebitda, 2) if ev and ebitda else None
    except Exception:
        data["EV_EBITDA"] = None

    # --- 4. P/B ---
    try:
        data["PB"] = Fundamental(ticker).pb()
    except Exception:
        data["PB"] = None

    # --- 5. Dividend Yield ---
    try:
        dy = Fundamental(ticker).dividend_yield()  # %
        data["Dividend_Yield"] = dy
    except Exception:
        data["Dividend_Yield"] = None

    # --- 6. Earnings Yield ---
    try:
        pe = data.get("PE")
        data["Earnings_Yield"] = round(1 / pe, 4) if pe and pe != 0 else None
    except Exception:
        data["Earnings_Yield"] = None

    # --- 7. FCF Yield ---
    try:
        cf = Financial(ticker).cashflow_statement()
        free_cf = float(cf.loc[cf['item'] == 'Lưu chuyển tiền thuần từ hoạt động kinh doanh', 'value'].values[0])
        mcap = Fundamental(ticker).market_cap()
        data["FCF_Yield"] = round(free_cf / mcap, 4) if mcap else None
    except Exception:
        data["FCF_Yield"] = None

    # --- 8. EV/FCF ---
    try:
        fin = Financial(ticker)
        ev = fin.enterprise_value()
        cf = fin.cashflow_statement()
        free_cf = float(cf.loc[cf['item'] == 'Lưu chuyển tiền thuần từ hoạt động kinh doanh', 'value'].values[0])
        data["EV_FCF"] = round(ev / free_cf, 2) if ev and free_cf else None
    except Exception:
        data["EV_FCF"] = None

    # --- 9. P/OCF ---
    try:
        ocf = float(cf.loc[cf['item'] == 'Lưu chuyển tiền thuần từ hoạt động kinh doanh', 'value'].values[0])
        shares = Company(ticker).outstanding_shares()
        ocf_per_share = ocf / shares if shares else None
        price = Fundamental(ticker).price()
        data["P_OCF"] = round(price / ocf_per_share, 2) if price and ocf_per_share else None
    except Exception:
        data["P_OCF"] = None

    # --- 10. DCF (Discounted Cash Flow) ---
    try:
        # Lấy dòng tiền 5 năm gần nhất
        cf_hist = Financial(ticker).cashflow_statement().head(5)
        cfs = cf_hist['value'].astype(float).tolist()
        discount_rate = 0.1
        pv = sum([cfs[i] / ((1 + discount_rate) ** (i + 1)) for i in range(len(cfs))])
        data["DCF_Value"] = round(pv, 2)
    except Exception:
        data["DCF_Value"] = None

    # --- 11. Intrinsic Gap (% chênh lệch giá trị nội tại) ---
    try:
        price = Fundamental(ticker).price()
        intrinsic = data.get("DCF_Value")
        if price and intrinsic and intrinsic != 0:
            data["Intrinsic_Gap_%"] = round((price - intrinsic) / intrinsic * 100, 2)
        else:
            data["Intrinsic_Gap_%"] = None
    except Exception:
        data["Intrinsic_Gap_%"] = None

    # --- 12. EV/Sales ---
    try:
        fin = Financial(ticker)
        ev = fin.enterprise_value()
        revenue = fin.income_statement().loc[0, 'value']
        data["EV_Sales"] = round(ev / revenue, 2) if ev and revenue else None
    except Exception:
        data["EV_Sales"] = None

    return data


if __name__ == "__main__":
    result = valuation_metrics_vnstock()
    print(f"📘 Valuation Metrics for: {TICKER}")
    for k, v in result.items():
        print(f"{k:20}: {v}")
