# ===========================================
# 📊 VNSTOCK - VALUATION METRICS CRAWLER
# ===========================================
# File này chỉ sử dụng thư viện vnstock để crawl các chỉ số định giá
# Không sử dụng xno API, chỉ dùng vnstock để lấy dữ liệu chứng khoán Việt Nam

from vnstock import Fundamental, Financial, stock_historical_data
import pandas as pd
import numpy as np
from typing import Dict, Optional, Union

# Mã cổ phiếu mặc định để test - có thể thay đổi
TICKER = "FPT"  # Thay bằng mã cổ phiếu bạn muốn phân tích

def valuation_metrics(ticker: str = TICKER) -> Dict[str, Optional[Union[float, int]]]:
    """
    Hàm crawl các chỉ số định giá (valuation metrics) chỉ sử dụng vnstock
    
    Args:
        ticker (str): Mã cổ phiếu cần phân tích (ví dụ: "FPT", "VCB", "HPG")
        
    Returns:
        Dict[str, Optional[Union[float, int]]]: Dictionary chứa các chỉ số định giá
        - Key: Tên chỉ số (string)
        - Value: Giá trị chỉ số (float/int hoặc None nếu không lấy được)
        
    Chức năng:
        - Crawl 12 chỉ số định giá quan trọng nhất
        - Xử lý lỗi gracefully - trả về None thay vì crash
        - Tính toán một số chỉ số từ các dữ liệu có sẵn
    """
    
    # Khởi tạo dictionary để lưu kết quả
    data = {}
    
    # Khởi tạo các đối tượng vnstock để lấy dữ liệu
    # Fundamental: Chứa các chỉ số cơ bản như P/E, P/B, ROE...
    # Financial: Chứa dữ liệu tài chính như doanh thu, lợi nhuận...
    fundamental_obj = Fundamental(ticker)
    financial_obj = Financial(ticker)
    
    print(f"🔍 Đang crawl dữ liệu cho mã {ticker}...")
    
    # ===========================================
    # 1. P/E RATIO (Price-to-Earnings) - Tỷ lệ giá/lợi nhuận
    # ===========================================
    # Ý nghĩa: Nhà đầu tư trả bao nhiêu đồng cho 1 đồng lợi nhuận
    # Công thức: P/E = Giá cổ phiếu / EPS (Earnings Per Share)
    # Ví dụ: Giá = 100k, EPS = 5k → P/E = 20
    # Giá trị tốt: 10-25, cao hơn có thể overvalued
    try:
        data["PE"] = fundamental_obj.pe()  # Lấy P/E ratio từ vnstock
        print(f"✅ P/E Ratio: {data['PE']}")
    except Exception as e:
        data["PE"] = None
        print(f"❌ Không thể lấy P/E Ratio: {str(e)}")

    # ===========================================
    # 2. P/B RATIO (Price-to-Book) - Tỷ lệ giá/giá trị sổ sách
    # ===========================================
    # Ý nghĩa: Giá cổ phiếu so với giá trị sổ sách (book value)
    # Công thức: P/B = Giá cổ phiếu / Book Value Per Share
    # Ví dụ: Giá = 50k, BVPS = 25k → P/B = 2
    # Giá trị tốt: < 3, cao hơn có thể overvalued
    try:
        data["PB"] = fundamental_obj.pb()  # Lấy P/B ratio từ vnstock
        print(f"✅ P/B Ratio: {data['PB']}")
    except Exception as e:
        data["PB"] = None
        print(f"❌ Không thể lấy P/B Ratio: {str(e)}")

    # ===========================================
    # 3. ROE (Return on Equity) - Tỷ suất sinh lời trên vốn chủ sở hữu
    # ===========================================
    # Ý nghĩa: Hiệu quả sử dụng vốn chủ sở hữu của công ty
    # Công thức: ROE = Net Income / Shareholders' Equity
    # Ví dụ: Lợi nhuận = 100 tỷ, Vốn CSH = 500 tỷ → ROE = 20%
    # Giá trị tốt: > 15%, cao hơn = hiệu quả tốt hơn
    try:
        data["ROE"] = fundamental_obj.roe()  # Lấy ROE từ vnstock
        print(f"✅ ROE: {data['ROE']}%")
    except Exception as e:
        data["ROE"] = None
        print(f"❌ Không thể lấy ROE: {str(e)}")

    # ===========================================
    # 4. DEBT/EQUITY RATIO - Tỷ lệ nợ/vốn chủ sở hữu
    # ===========================================
    # Ý nghĩa: Mức độ sử dụng đòn bẩy tài chính của công ty
    # Công thức: D/E = Total Debt / Shareholders' Equity
    # Ví dụ: Nợ = 400 tỷ, Vốn CSH = 200 tỷ → D/E = 2
    # Giá trị tốt: < 1, cao hơn = rủi ro tài chính cao hơn
    try:
        data["Debt_Equity"] = fundamental_obj.debt_equity()  # Lấy D/E từ vnstock
        print(f"✅ Debt/Equity: {data['Debt_Equity']}")
    except Exception as e:
        data["Debt_Equity"] = None
        print(f"❌ Không thể lấy Debt/Equity: {str(e)}")

    # ===========================================
    # 5. CURRENT RATIO - Tỷ số thanh toán hiện hành
    # ===========================================
    # Ý nghĩa: Khả năng thanh toán nợ ngắn hạn của công ty
    # Công thức: Current Ratio = Current Assets / Current Liabilities
    # Ví dụ: Tài sản ngắn hạn = 300 tỷ, Nợ ngắn hạn = 150 tỷ → Ratio = 2
    # Giá trị tốt: 1.5-3, thấp hơn = khó thanh toán nợ
    try:
        data["Current_Ratio"] = financial_obj.current_ratio()  # Lấy Current Ratio từ vnstock
        print(f"✅ Current Ratio: {data['Current_Ratio']}")
    except Exception as e:
        data["Current_Ratio"] = None
        print(f"❌ Không thể lấy Current Ratio: {str(e)}")

    # ===========================================
    # 6. EARNINGS YIELD - Tỷ suất sinh lời từ lợi nhuận
    # ===========================================
    # Ý nghĩa: Ngược của P/E - tỷ lệ sinh lời trên giá cổ phiếu
    # Công thức: Earnings Yield = EPS / Giá cổ phiếu = 1 / P/E
    # Ví dụ: EPS = 5k, Giá = 100k → Earnings Yield = 5%
    # Giá trị tốt: > 5%, cao hơn = sinh lời tốt hơn
    try:
        if data.get("PE") and data["PE"] > 0:  # Kiểm tra P/E có hợp lệ không
            data["Earnings_Yield"] = round((1 / data["PE"]) * 100, 2)  # Tính từ P/E
            print(f"✅ Earnings Yield: {data['Earnings_Yield']}%")
        else:
            data["Earnings_Yield"] = None
            print("❌ Không thể tính Earnings Yield do thiếu P/E")
    except Exception as e:
        data["Earnings_Yield"] = None
        print(f"❌ Không thể tính Earnings Yield: {str(e)}")

    # ===========================================
    # 7. PEG RATIO (Price/Earnings to Growth) - Tỷ lệ P/E so với tăng trưởng
    # ===========================================
    # Ý nghĩa: Kết hợp P/E và tốc độ tăng trưởng EPS để đánh giá định giá hợp lý
    # Công thức: PEG = P/E / EPS Growth Rate
    # Ví dụ: P/E = 20, EPS Growth = 25% → PEG = 0.8
    # Giá trị tốt: < 1 = undervalued, > 1 = overvalued
    try:
        # Lấy EPS growth từ vnstock
        eps_growth = fundamental_obj.eps_growth()
        if eps_growth and eps_growth > 0 and data.get("PE"):
            data["PEG"] = round(data["PE"] / eps_growth, 2)  # Tính PEG
            print(f"✅ PEG Ratio: {data['PEG']}")
        else:
            data["PEG"] = None
            print("❌ Không thể tính PEG do thiếu dữ liệu tăng trưởng")
    except Exception as e:
        data["PEG"] = None
        print(f"❌ Không thể tính PEG: {str(e)}")

    # ===========================================
    # 8. MARKET CAP - Vốn hóa thị trường
    # ===========================================
    # Ý nghĩa: Tổng giá trị thị trường của tất cả cổ phiếu đang lưu hành
    # Công thức: Market Cap = Giá cổ phiếu × Số cổ phiếu lưu hành
    # Ví dụ: Giá = 100k, Số cổ phiếu = 1 tỷ → Market Cap = 100,000 tỷ VND
    # Sử dụng: So sánh quy mô công ty, tính các tỷ lệ khác
    try:
        data["Market_Cap"] = fundamental_obj.market_cap()  # Lấy Market Cap từ vnstock
        print(f"✅ Market Cap: {data['Market_Cap']:,} VND")
    except Exception as e:
        data["Market_Cap"] = None
        print(f"❌ Không thể lấy Market Cap: {str(e)}")

    # ===========================================
    # 9. DIVIDEND YIELD - Tỷ suất cổ tức
    # ===========================================
    # Ý nghĩa: Tỷ lệ cổ tức so với giá cổ phiếu
    # Công thức: Dividend Yield = Cổ tức năm / Giá cổ phiếu
    # Ví dụ: Cổ tức = 2k, Giá = 50k → Dividend Yield = 4%
    # Giá trị tốt: > 3%, cao hơn = thu nhập từ cổ tức tốt hơn
    try:
        data["Dividend_Yield"] = fundamental_obj.dividend_yield()  # Lấy Dividend Yield từ vnstock
        print(f"✅ Dividend Yield: {data['Dividend_Yield']}%")
    except Exception as e:
        data["Dividend_Yield"] = None
        print(f"❌ Không thể lấy Dividend Yield: {str(e)}")

    # ===========================================
    # 10. EPS GROWTH - Tăng trưởng lợi nhuận trên mỗi cổ phiếu
    # ===========================================
    # Ý nghĩa: Tốc độ tăng trưởng lợi nhuận trên mỗi cổ phiếu
    # Công thức: EPS Growth = (EPS năm nay - EPS năm trước) / EPS năm trước × 100%
    # Ví dụ: EPS 2023 = 6k, EPS 2022 = 5k → Growth = 20%
    # Giá trị tốt: > 10%, cao hơn = tăng trưởng tốt hơn
    try:
        data["EPS_Growth"] = fundamental_obj.eps_growth()  # Lấy EPS Growth từ vnstock
        print(f"✅ EPS Growth: {data['EPS_Growth']}%")
    except Exception as e:
        data["EPS_Growth"] = None
        print(f"❌ Không thể lấy EPS Growth: {str(e)}")

    # ===========================================
    # 11. PRICE - Giá cổ phiếu hiện tại
    # ===========================================
    # Ý nghĩa: Giá giao dịch hiện tại của cổ phiếu
    # Sử dụng: Làm cơ sở để tính các tỷ lệ khác, so sánh với giá trị nội tại
    try:
        # Lấy dữ liệu giá gần nhất từ vnstock
        price_data = stock_historical_data(symbol=ticker, start_date='2024-01-01', end_date='2024-12-31')
        if not price_data.empty:
            data["Current_Price"] = price_data['close'].iloc[-1]  # Lấy giá đóng cửa gần nhất
            print(f"✅ Current Price: {data['Current_Price']:,} VND")
        else:
            data["Current_Price"] = None
            print("❌ Không thể lấy giá cổ phiếu")
    except Exception as e:
        data["Current_Price"] = None
        print(f"❌ Không thể lấy giá cổ phiếu: {str(e)}")

    # ===========================================
    # 12. SIMPLE DCF - Định giá chiết khấu dòng tiền đơn giản
    # ===========================================
    # Ý nghĩa: Ước tính giá trị nội tại của cổ phiếu dựa trên dòng tiền tương lai
    # Công thức: DCF = Σ [FCF / (1 + discount_rate)^n]
    # Lưu ý: Đây là tính toán đơn giản, thực tế cần phân tích chi tiết hơn
    try:
        # Lấy dữ liệu tài chính để ước tính FCF
        # Giả sử FCF = Net Income (đơn giản hóa)
        net_income = financial_obj.net_income()
        if net_income and net_income > 0:
            # Ước tính FCF = 80% của Net Income (giả định)
            estimated_fcf = net_income * 0.8
            # Tỷ lệ chiết khấu 10% (có thể điều chỉnh)
            discount_rate = 0.1
            # Tính DCF đơn giản cho 5 năm
            dcf_value = 0
            for year in range(1, 6):  # 5 năm
                dcf_value += estimated_fcf / ((1 + discount_rate) ** year)
            
            data["Simple_DCF"] = round(dcf_value, 2)
            print(f"✅ Simple DCF: {data['Simple_DCF']:,} VND")
        else:
            data["Simple_DCF"] = None
            print("❌ Không thể tính DCF do thiếu dữ liệu Net Income")
    except Exception as e:
        data["Simple_DCF"] = None
        print(f"❌ Không thể tính DCF: {str(e)}")

    # ===========================================
    # TỔNG KẾT VÀ HIỂN THỊ KẾT QUẢ
    # ===========================================
    print(f"\n📊 Tổng kết {len(data)} chỉ số định giá cho mã {ticker}:")
    print("=" * 60)
    
    return data


def display_results(data: Dict[str, Optional[Union[float, int]]], ticker: str) -> None:
    """
    Hiển thị kết quả phân tích một cách đẹp mắt và dễ hiểu
    
    Args:
        data (Dict): Dictionary chứa các chỉ số đã crawl được
        ticker (str): Mã cổ phiếu đã phân tích
    """
    print(f"\n🎯 BÁO CÁO PHÂN TÍCH ĐỊNH GIÁ - MÃ {ticker}")
    print("=" * 60)
    
    # Định nghĩa các nhóm chỉ số để hiển thị có tổ chức
    valuation_metrics = ["PE", "PB", "PEG", "Earnings_Yield", "Dividend_Yield", "Simple_DCF"]
    profitability_metrics = ["ROE", "EPS_Growth"]
    financial_health_metrics = ["Debt_Equity", "Current_Ratio"]
    market_metrics = ["Market_Cap", "Current_Price"]
    
    # Hiển thị từng nhóm
    print("\n📈 CHỈ SỐ ĐỊNH GIÁ:")
    for metric in valuation_metrics:
        if metric in data and data[metric] is not None:
            print(f"  {metric:20}: {data[metric]:>10}")
        else:
            print(f"  {metric:20}: {'N/A':>10}")
    
    print("\n💰 CHỈ SỐ SINH LỜI:")
    for metric in profitability_metrics:
        if metric in data and data[metric] is not None:
            print(f"  {metric:20}: {data[metric]:>10}")
        else:
            print(f"  {metric:20}: {'N/A':>10}")
    
    print("\n🏥 TÌNH HÌNH TÀI CHÍNH:")
    for metric in financial_health_metrics:
        if metric in data and data[metric] is not None:
            print(f"  {metric:20}: {data[metric]:>10}")
        else:
            print(f"  {metric:20}: {'N/A':>10}")
    
    print("\n📊 THÔNG TIN THỊ TRƯỜNG:")
    for metric in market_metrics:
        if metric in data and data[metric] is not None:
            print(f"  {metric:20}: {data[metric]:>10}")
        else:
            print(f"  {metric:20}: {'N/A':>10}")


def save_to_file(data: Dict[str, Optional[Union[float, int]]], ticker: str, filename: str = None) -> None:
    """
    Lưu kết quả phân tích vào file text
    
    Args:
        data (Dict): Dictionary chứa các chỉ số
        ticker (str): Mã cổ phiếu
        filename (str): Tên file (tùy chọn)
    """
    if filename is None:
        filename = f"valuation_report_{ticker}.txt"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"BÁO CÁO PHÂN TÍCH ĐỊNH GIÁ - MÃ {ticker}\n")
            f.write("=" * 50 + "\n\n")
            
            for metric, value in data.items():
                if value is not None:
                    f.write(f"{metric:20}: {value:>10}\n")
                else:
                    f.write(f"{metric:20}: {'N/A':>10}\n")
        
        print(f"💾 Đã lưu kết quả vào file: {filename}")
    except Exception as e:
        print(f"❌ Không thể lưu file: {str(e)}")


if __name__ == "__main__":
    """
    Hàm main - chạy chương trình khi file được thực thi trực tiếp
    """
    print("🚀 BẮT ĐẦU CHƯƠNG TRÌNH PHÂN TÍCH ĐỊNH GIÁ CỔ PHIẾU")
    print("=" * 60)
    
    # Crawl dữ liệu cho mã cổ phiếu mặc định
    result = valuation_metrics(TICKER)
    
    # Hiển thị kết quả đẹp mắt
    display_results(result, TICKER)
    
    # Lưu kết quả vào file
    save_to_file(result, TICKER)
    
    print(f"\n✅ Hoàn thành phân tích cho mã {TICKER}!")
    print("💡 Tip: Thay đổi biến TICKER ở đầu file để phân tích mã khác")
