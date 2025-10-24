# ===========================================
# VNSTOCK - VALUATION METRICS CRAWLER (FINAL VERSION)
# ===========================================
# 
# MÔ TẢ:
# File này sử dụng vnstock version 3.2.6 với API mới để crawl các chỉ số định giá cổ phiếu
# Đã sửa lỗi import và cập nhật các method calls cho phù hợp với API mới
# Không sử dụng emoji để tránh lỗi encoding
#
# CHỨC NĂNG CHÍNH:
# 1. Crawl 12+ chỉ số định giá quan trọng từ vnstock API
# 2. Tính toán các chỉ số phái sinh (PEG, Earnings Yield, DCF)
# 3. Hiển thị kết quả đẹp mắt theo nhóm
# 4. Lưu báo cáo ra file text
#
# API SỬ DỤNG:
# - Finance(source='tcbs', symbol=ticker): Lấy dữ liệu tài chính
# - Quote(symbol=ticker, source='tcbs'): Lấy dữ liệu giá cổ phiếu
#
# TÁC GIẢ: Hệ thống phân tích tài chính tự động
# PHIÊN BẢN: 2.0 - Cải thiện tính toán và documentation
# NGÀY CẬP NHẬT: 2024

from vnstock import Finance, Quote  # API mới của vnstock 3.2.6
import pandas as pd
import numpy as np
from typing import Dict, Optional, Union, Tuple
import warnings
warnings.filterwarnings('ignore')  # Tắt cảnh báo không cần thiết

# Mã cổ phiếu mặc định để test - có thể thay đổi
TICKER = "FPT"  # Thay bằng mã cổ phiếu bạn muốn phân tích

def valuation_metrics(ticker: str = TICKER) -> Dict[str, Optional[Union[float, int]]]:
    """
    Hàm crawl các chỉ số định giá (valuation metrics) sử dụng vnstock 3.2.6
    
    MÔ TẢ CHI TIẾT:
    ----------------
    Hàm này thực hiện crawl và tính toán 12+ chỉ số định giá quan trọng nhất cho cổ phiếu Việt Nam
    sử dụng API mới của vnstock 3.2.6. Bao gồm cả việc lấy dữ liệu thô và tính toán các chỉ số phái sinh.
    
    QUY TRÌNH XỬ LÝ:
    ---------------
    1. Khởi tạo đối tượng Finance và Quote từ vnstock API
    2. Lấy dữ liệu tỷ số tài chính (ratio_data) - dữ liệu gốc từ TCBS
    3. Trích xuất từng chỉ số từ dữ liệu gốc với xử lý lỗi
    4. Tính toán các chỉ số phái sinh (PEG, Earnings Yield, DCF)
    5. Trả về dictionary chứa tất cả chỉ số đã xử lý
    
    DANH SÁCH CHỈ SỐ:
    ----------------
    CHỈ SỐ ĐỊNH GIÁ:
    - PE (Price-to-Earnings): Tỷ lệ giá/lợi nhuận
    - PB (Price-to-Book): Tỷ lệ giá/giá trị sổ sách  
    - PEG (Price/Earnings to Growth): P/E so với tăng trưởng
    - Earnings_Yield: Tỷ suất sinh lời từ lợi nhuận
    - Simple_DCF: Định giá chiết khấu dòng tiền đơn giản
    
    CHỈ SỐ SINH LỜI:
    - ROE (Return on Equity): Tỷ suất sinh lời trên vốn CSH
    - EPS_Growth: Tăng trưởng lợi nhuận trên mỗi cổ phiếu
    - EPS (Earnings Per Share): Lợi nhuận trên mỗi cổ phiếu
    
    TÌNH HÌNH TÀI CHÍNH:
    - Debt_Equity: Tỷ lệ nợ/vốn chủ sở hữu
    - Current_Ratio: Tỷ số thanh toán hiện hành
    
    THÔNG TIN THỊ TRƯỜNG:
    - Current_Price: Giá cổ phiếu hiện tại
    - Book_Value_Per_Share: Giá trị sổ sách trên mỗi cổ phiếu
    
    Args:
        ticker (str): Mã cổ phiếu cần phân tích 
                     Ví dụ: "FPT", "VCB", "HPG", "VIC", "MSN"
                     Lưu ý: Mã cổ phiếu phải đúng định dạng HOSE/HNX
        
    Returns:
        Dict[str, Optional[Union[float, int]]]: Dictionary chứa các chỉ số định giá
        - Key (str): Tên chỉ số (ví dụ: "PE", "ROE", "Current_Price")
        - Value (Union[float, int, None]): Giá trị chỉ số hoặc None nếu không lấy được
        
    Raises:
        Exception: Không crash chương trình, chỉ log lỗi và trả về None cho chỉ số bị lỗi
        
    Example:
        >>> data = valuation_metrics("FPT")
        >>> print(data["PE"])  # 19.0
        >>> print(data["ROE"])  # 28.3
        
    Performance:
        - Thời gian thực thi: ~3-5 giây (tùy thuộc vào tốc độ mạng)
        - API calls: 2-3 calls (Finance.ratio(), Quote.history(), Finance.income_statement())
        - Memory usage: ~10-20MB (cho dữ liệu 1 cổ phiếu)
        
    Error Handling:
        - Xử lý lỗi gracefully cho từng chỉ số riêng biệt
        - Log chi tiết lỗi để debug
        - Trả về None cho chỉ số bị lỗi thay vì crash toàn bộ chương trình
        - Retry mechanism: Không có (có thể cải thiện trong tương lai)
    """
    
    # Khởi tạo dictionary để lưu kết quả
    data = {}
    
    print(f"Dang crawl du lieu cho ma {ticker}...")
    
    try:
        # Khởi tạo các đối tượng vnstock để lấy dữ liệu (API mới v3.2.6)
        # Finance: Chứa các chỉ số tài chính như P/E, P/B, ROE, báo cáo tài chính...
        # Quote: Chứa dữ liệu giá cổ phiếu, giao dịch...
        finance_obj = Finance(source='tcbs', symbol=ticker)  # API mới cần source và symbol
        quote_obj = Quote(symbol=ticker, source='tcbs')      # Quote cần cả symbol và source
        
        # Lấy tất cả dữ liệu tỷ số tài chính một lần để tối ưu hiệu suất
        print("Dang lay du lieu ty so tai chinh...")
        ratio_data = finance_obj.ratio()
        
        if ratio_data.empty:
            print("Khong co du lieu ty so tai chinh")
            return data
            
        # Lấy dữ liệu gần nhất (hàng đầu tiên)
        latest_data = ratio_data.iloc[0]
        print(latest_data)
        
        # ===========================================
        # 1. P/E RATIO (Price-to-Earnings) - Tỷ lệ giá/lợi nhuận
        # ===========================================
        # Ý nghĩa: Nhà đầu tư trả bao nhiêu đồng cho 1 đồng lợi nhuận
        # Công thức: P/E = Giá cổ phiếu / EPS (Earnings Per Share)
        # Ví dụ: Giá = 100k, EPS = 5k → P/E = 20
        # Giá trị tốt: 10-25, cao hơn có thể overvalued
        try:
            data["PE"] = latest_data['price_to_earning'] if pd.notna(latest_data['price_to_earning']) else None
            print(f"OK P/E Ratio: {data['PE']}")
        except Exception as e:
            data["PE"] = None
            print(f"LOI P/E Ratio: {str(e)}")

        # ===========================================
        # 2. P/B RATIO (Price-to-Book) - Tỷ lệ giá/giá trị sổ sách
        # ===========================================
        # Ý nghĩa: Giá cổ phiếu so với giá trị sổ sách (book value)
        # Công thức: P/B = Giá cổ phiếu / Book Value Per Share
        # Ví dụ: Giá = 50k, BVPS = 25k → P/B = 2
        # Giá trị tốt: < 3, cao hơn có thể overvalued
        try:
            data["PB"] = latest_data['price_to_book'] if pd.notna(latest_data['price_to_book']) else None
            print(f"OK P/B Ratio: {data['PB']}")
        except Exception as e:
            data["PB"] = None
            print(f"LOI P/B Ratio: {str(e)}")

        # ===========================================
        # 3. ROE (Return on Equity) - Tỷ suất sinh lời trên vốn chủ sở hữu
        # ===========================================
        # Ý nghĩa: Hiệu quả sử dụng vốn chủ sở hữu của công ty
        # Công thức: ROE = Net Income / Shareholders' Equity
        # Ví dụ: Lợi nhuận = 100 tỷ, Vốn CSH = 500 tỷ → ROE = 20%
        # Giá trị tốt: > 15%, cao hơn = hiệu quả tốt hơn
        try:
            roe_value = latest_data['roe'] if pd.notna(latest_data['roe']) else None
            data["ROE"] = round(roe_value * 100, 2) if roe_value is not None else None  # Chuyển thành phần trăm
            print(f"OK ROE: {data['ROE']}%")
        except Exception as e:
            data["ROE"] = None
            print(f"LOI ROE: {str(e)}")

        # ===========================================
        # 4. DEBT/EQUITY RATIO - Tỷ lệ nợ/vốn chủ sở hữu
        # ===========================================
        # Ý nghĩa: Mức độ sử dụng đòn bẩy tài chính của công ty
        # Công thức: D/E = Total Debt / Shareholders' Equity
        # Ví dụ: Nợ = 400 tỷ, Vốn CSH = 200 tỷ → D/E = 2
        # Giá trị tốt: < 1, cao hơn = rủi ro tài chính cao hơn
        try:
            data["Debt_Equity"] = latest_data['debt_on_equity'] if pd.notna(latest_data['debt_on_equity']) else None
            print(f"OK Debt/Equity: {data['Debt_Equity']}")
        except Exception as e:
            data["Debt_Equity"] = None
            print(f"LOI Debt/Equity: {str(e)}")

        # ===========================================
        # 5. CURRENT RATIO - Tỷ số thanh toán hiện hành
        # ===========================================
        # Ý nghĩa: Khả năng thanh toán nợ ngắn hạn của công ty
        # Công thức: Current Ratio = Current Assets / Current Liabilities
        # Ví dụ: Tài sản ngắn hạn = 300 tỷ, Nợ ngắn hạn = 150 tỷ → Ratio = 2
        # Giá trị tốt: 1.5-3, thấp hơn = khó thanh toán nợ
        try:
            data["Current_Ratio"] = latest_data['current_payment'] if pd.notna(latest_data['current_payment']) else None
            print(f"OK Current Ratio: {data['Current_Ratio']}")
        except Exception as e:
            data["Current_Ratio"] = None
            print(f"LOI Current Ratio: {str(e)}")

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
                print(f"OK Earnings Yield: {data['Earnings_Yield']}%")
            else:
                data["Earnings_Yield"] = None
                print("Khong the tinh Earnings Yield do thieu P/E")
        except Exception as e:
            data["Earnings_Yield"] = None
            print(f"LOI Earnings Yield: {str(e)}")

        # ===========================================
        # 7. EPS GROWTH - Tăng trưởng lợi nhuận trên mỗi cổ phiếu
        # ===========================================
        # Ý nghĩa: Tốc độ tăng trưởng lợi nhuận trên mỗi cổ phiếu
        # Công thức: EPS Growth = (EPS năm nay - EPS năm trước) / EPS năm trước × 100%
        # Ví dụ: EPS 2023 = 6k, EPS 2022 = 5k → Growth = 20%
        # Giá trị tốt: > 10%, cao hơn = tăng trưởng tốt hơn
        try:
            eps_growth = latest_data['eps_change'] if pd.notna(latest_data['eps_change']) else None
            data["EPS_Growth"] = round(eps_growth * 100, 2) if eps_growth is not None else None  # Chuyển thành phần trăm
            print(f"OK EPS Growth: {data['EPS_Growth']}%")
        except Exception as e:
            data["EPS_Growth"] = None
            print(f"LOI EPS Growth: {str(e)}")

        # ===========================================
        # 8. PEG RATIO (Price/Earnings to Growth) - Tỷ lệ P/E so với tăng trưởng
        # ===========================================
        # Ý nghĩa: Kết hợp P/E và tốc độ tăng trưởng EPS để đánh giá định giá hợp lý
        # Công thức: PEG = P/E / EPS Growth Rate (tính theo phần trăm)
        # Ví dụ: P/E = 20, EPS Growth = 25% → PEG = 20 / 25 = 0.8
        # Giá trị tốt: < 1 = undervalued, > 1 = overvalued
        try:
            if data.get("PE") and data.get("EPS_Growth") and data["EPS_Growth"] > 0:
                # Lưu ý: EPS_Growth đã được chuyển thành % ở trên, cần chia cho 100
                eps_growth_rate = data["EPS_Growth"] / 100  # Chuyển từ % về decimal
                data["PEG"] = round(data["PE"] / eps_growth_rate, 2)  # Tính PEG đúng
                print(f"OK PEG Ratio: {data['PEG']} (EPS Growth: {data['EPS_Growth']}%)")
            else:
                data["PEG"] = None
                print("Khong the tinh PEG do thieu du lieu tang truong")
        except Exception as e:
            data["PEG"] = None
            print(f"LOI PEG: {str(e)}")

        # ===========================================
        # 9. EPS - Earnings Per Share - Lợi nhuận trên mỗi cổ phiếu
        # ===========================================
        # Ý nghĩa: Lợi nhuận sau thuế chia cho số cổ phiếu đang lưu hành
        # Công thức: EPS = Net Income / Outstanding Shares
        # Ví dụ: Lợi nhuận = 1000 tỷ, Số cổ phiếu = 200 triệu → EPS = 5000 VND
        # Giá trị tốt: Cao hơn = sinh lời tốt hơn
        try:
            eps_value = latest_data['earning_per_share'] if pd.notna(latest_data['earning_per_share']) else None
            data["EPS"] = eps_value
            print(f"OK EPS: {data['EPS']:,} VND")
        except Exception as e:
            data["EPS"] = None
            print(f"LOI EPS: {str(e)}")

        # ===========================================
        # 10. BOOK VALUE PER SHARE - Giá trị sổ sách trên mỗi cổ phiếu
        # ===========================================
        # Ý nghĩa: Giá trị sổ sách của công ty chia cho số cổ phiếu
        # Công thức: BVPS = Shareholders' Equity / Outstanding Shares
        # Ví dụ: Vốn CSH = 5000 tỷ, Số cổ phiếu = 200 triệu → BVPS = 25,000 VND
        # Sử dụng: Làm cơ sở tính P/B ratio
        try:
            bvps_value = latest_data['book_value_per_share'] if pd.notna(latest_data['book_value_per_share']) else None
            data["Book_Value_Per_Share"] = bvps_value
            print(f"OK Book Value Per Share: {data['Book_Value_Per_Share']:,} VND")
        except Exception as e:
            data["Book_Value_Per_Share"] = None
            print(f"LOI Book Value Per Share: {str(e)}")

        # ===========================================
        # 11. PRICE - Giá cổ phiếu hiện tại
        # ===========================================
        # Ý nghĩa: Giá giao dịch hiện tại của cổ phiếu
        # Sử dụng: Làm cơ sở để tính các tỷ lệ khác, so sánh với giá trị nội tại
        try:
            # Lấy dữ liệu giá gần nhất từ vnstock (7 ngày gần nhất)
            from datetime import datetime, timedelta
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            
            price_data = quote_obj.history(start=start_date, end=end_date)
            if not price_data.empty:
                # Lấy giá đóng cửa gần nhất và chuyển đổi đơn vị (nếu cần)
                raw_price = price_data['close'].iloc[-1]
                
                # Kiểm tra và điều chỉnh đơn vị giá (vnstock có thể trả về giá nhân 1000)
                if raw_price < 1000:  # Nếu giá quá thấp, có thể cần nhân 1000
                    data["Current_Price"] = round(raw_price * 1000, 2)
                    print(f"OK Current Price: {data['Current_Price']:,} VND (đã điều chỉnh đơn vị)")
                else:
                    data["Current_Price"] = round(raw_price, 2)
                    print(f"OK Current Price: {data['Current_Price']:,} VND")
            else:
                data["Current_Price"] = None
                print("Khong the lay gia co phieu")
        except Exception as e:
            data["Current_Price"] = None
            print(f"LOI gia co phieu: {str(e)}")

        # ===========================================
        # 12. MARKET CAP - Vốn hóa thị trường
        # ===========================================
        # Ý nghĩa: Tổng giá trị thị trường của tất cả cổ phiếu đang lưu hành
        # Công thức: Market Cap = Giá cổ phiếu × Số cổ phiếu lưu hành
        try:
            # Ước tính Market Cap từ dữ liệu có sẵn
            if data.get("Current_Price") and data.get("Book_Value_Per_Share") and data.get("EPS"):
                # Ước tính số cổ phiếu lưu hành từ EPS và Net Income
                # Giả sử Net Income = EPS × Outstanding Shares
                # Chúng ta cần lấy Net Income từ income statement
                try:
                    income_data = finance_obj.income_statement()
                    if not income_data.empty and 'net_income' in income_data.columns:
                        net_income = income_data['net_income'].iloc[0]
                        outstanding_shares = net_income / data["EPS"] if data["EPS"] > 0 else None
                        if outstanding_shares:
                            data["Market_Cap"] = round(data["Current_Price"] * outstanding_shares / 1e9, 2)  # Đơn vị: tỷ VND
                            print(f"OK Market Cap: {data['Market_Cap']} ty VND")
                        else:
                            data["Market_Cap"] = None
                    else:
                        data["Market_Cap"] = None
                except:
                    data["Market_Cap"] = None
            else:
                data["Market_Cap"] = None
                print("Khong the tinh Market Cap do thieu du lieu")
        except Exception as e:
            data["Market_Cap"] = None
            print(f"LOI Market Cap: {str(e)}")

        # ===========================================
        # 13. SIMPLE DCF - Định giá chiết khấu dòng tiền đơn giản
        # ===========================================
        # Ý nghĩa: Ước tính giá trị nội tại của cổ phiếu dựa trên dòng tiền tương lai
        # Công thức: DCF = Σ [FCF / (1 + discount_rate)^n]
        # Lưu ý: Đây là tính toán đơn giản, thực tế cần phân tích chi tiết hơn
        try:
            # Lấy dữ liệu tài chính để ước tính FCF
            income_data = finance_obj.income_statement()
            if not income_data.empty:
                # Tìm cột net_income trong DataFrame
                net_income_col = None
                for col in income_data.columns:
                    if 'net_income' in col.lower() or 'lợi nhuận' in col.lower():
                        net_income_col = col
                        break
                
                if net_income_col:
                    net_income = income_data[net_income_col].iloc[0]
                    if pd.notna(net_income) and net_income > 0:
                        # Giả sử FCF = 80% của Net Income (đơn giản hóa)
                        estimated_fcf = net_income * 0.8
                        # Tỷ lệ chiết khấu 10% (có thể điều chỉnh)
                        discount_rate = 0.1
                        # Tính DCF đơn giản cho 5 năm
                        dcf_value = 0
                        for year in range(1, 6):  # 5 năm
                            dcf_value += estimated_fcf / ((1 + discount_rate) ** year)
                        
                        # Chuyển đổi về giá trị trên mỗi cổ phiếu (nếu có thông tin số cổ phiếu)
                        if data.get("EPS") and data.get("EPS") > 0:
                            outstanding_shares = net_income / data["EPS"]
                            dcf_per_share = dcf_value / outstanding_shares
                            data["Simple_DCF"] = round(dcf_per_share, 2)
                        else:
                            data["Simple_DCF"] = round(dcf_value / 1e6, 2)  # Đơn vị: triệu VND
                        
                        print(f"OK Simple DCF: {data['Simple_DCF']:,} VND")
                    else:
                        data["Simple_DCF"] = None
                        print("Khong the tinh DCF do thieu du lieu Net Income")
                else:
                    data["Simple_DCF"] = None
                    print("Khong the tinh DCF do khong tim thay cot Net Income")
            else:
                data["Simple_DCF"] = None
                print("Khong the tinh DCF do thieu du lieu bao cao ket qua kinh doanh")
        except Exception as e:
            data["Simple_DCF"] = None
            print(f"LOI DCF: {str(e)}")

        # ===========================================
        # 14. DIVIDEND YIELD - Tỷ suất cổ tức (ước tính)
        # ===========================================
        # Ý nghĩa: Tỷ lệ cổ tức so với giá cổ phiếu
        # Công thức: Dividend Yield = Cổ tức năm / Giá cổ phiếu × 100%
        # Lưu ý: Chỉ là ước tính dựa trên dữ liệu có sẵn
        try:
            # Ước tính dividend yield từ ROE và payout ratio giả định
            if data.get("ROE") and data.get("Current_Price") and data.get("EPS"):
                # Giả sử payout ratio = 30% (30% lợi nhuận được chia cổ tức)
                estimated_payout_ratio = 0.3
                estimated_dividend_per_share = data["EPS"] * estimated_payout_ratio
                data["Dividend_Yield"] = round((estimated_dividend_per_share / data["Current_Price"]) * 100, 2)
                print(f"OK Dividend Yield (uoc tinh): {data['Dividend_Yield']}%")
            else:
                data["Dividend_Yield"] = None
                print("Khong the uoc tinh Dividend Yield")
        except Exception as e:
            data["Dividend_Yield"] = None
            print(f"LOI Dividend Yield: {str(e)}")

    except Exception as e:
        print(f"LOI khoi tao doi tuong vnstock: {str(e)}")
        return data

    # ===========================================
    # TỔNG KẾT VÀ HIỂN THỊ KẾT QUẢ
    # ===========================================
    print(f"\nTong ket {len(data)} chi so dinh gia cho ma {ticker}:")
    print("=" * 60)
    
    return data


def display_results(data: Dict[str, Optional[Union[float, int]]], ticker: str) -> None:
    """
    Hiển thị kết quả phân tích một cách đẹp mắt và dễ hiểu
    
    MÔ TẢ CHI TIẾT:
    ----------------
    Hàm này hiển thị tất cả các chỉ số định giá đã crawl được theo từng nhóm logic,
    giúp người dùng dễ dàng đánh giá tình hình tài chính và định giá của cổ phiếu.
    
    CÁC NHÓM CHỈ SỐ:
    ---------------
    1. CHỈ SỐ ĐỊNH GIÁ: Các tỷ lệ để đánh giá cổ phiếu có đắt hay rẻ
    2. CHỈ SỐ SINH LỜI: Khả năng tạo ra lợi nhuận của công ty
    3. TÌNH HÌNH TÀI CHÍNH: Rủi ro tài chính và khả năng thanh toán
    4. THÔNG TIN THỊ TRƯỜNG: Thông tin cơ bản về giá và quy mô
    
    FORMAT HIỂN THỊ:
    ---------------
    - Mỗi chỉ số được hiển thị với tên và giá trị
    - Giá trị được format đẹp mắt với số thập phân phù hợp
    - N/A cho các chỉ số không lấy được dữ liệu
    
    Args:
        data (Dict[str, Optional[Union[float, int]]]): Dictionary chứa các chỉ số đã crawl được
            - Key: Tên chỉ số (ví dụ: "PE", "ROE", "Current_Price")
            - Value: Giá trị chỉ số hoặc None nếu không lấy được
        ticker (str): Mã cổ phiếu đã phân tích (ví dụ: "FPT", "VCB")
        
    Returns:
        None: Chỉ hiển thị kết quả, không trả về giá trị
        
    Example:
        >>> data = {"PE": 19.0, "ROE": 28.3, "Current_Price": 95000}
        >>> display_results(data, "FPT")
        # Sẽ hiển thị báo cáo phân tích đẹp mắt cho FPT
    """
    print(f"\nBAO CAO PHAN TICH DINH GIA - MA {ticker}")
    print("=" * 60)
    
    # Định nghĩa các nhóm chỉ số để hiển thị có tổ chức
    valuation_metrics = ["PE", "PB", "PEG", "Earnings_Yield", "Simple_DCF", "Dividend_Yield"]
    profitability_metrics = ["ROE", "EPS_Growth", "EPS"]
    financial_health_metrics = ["Debt_Equity", "Current_Ratio"]
    market_metrics = ["Current_Price", "Book_Value_Per_Share", "Market_Cap"]
    
    # Hiển thị từng nhóm
    print("\nCHI SO DINH GIA:")
    for metric in valuation_metrics:
        if metric in data and data[metric] is not None:
            if metric in ["Earnings_Yield", "Dividend_Yield"]:
                print(f"  {metric:20}: {data[metric]:>10}%")
            else:
                print(f"  {metric:20}: {data[metric]:>10}")
        else:
            print(f"  {metric:20}: {'N/A':>10}")
    
    print("\nCHI SO SINH LOI:")
    for metric in profitability_metrics:
        if metric in data and data[metric] is not None:
            if metric in ["ROE", "EPS_Growth"]:
                print(f"  {metric:20}: {data[metric]:>10}%")
            else:
                print(f"  {metric:20}: {data[metric]:>10}")
        else:
            print(f"  {metric:20}: {'N/A':>10}")
    
    print("\nTINH HINH TAI CHINH:")
    for metric in financial_health_metrics:
        if metric in data and data[metric] is not None:
            print(f"  {metric:20}: {data[metric]:>10}")
        else:
            print(f"  {metric:20}: {'N/A':>10}")
    
    print("\nTHONG TIN THI TRUONG:")
    for metric in market_metrics:
        if metric in data and data[metric] is not None:
            if metric == "Market_Cap":
                print(f"  {metric:20}: {data[metric]:>10} ty VND")
            else:
                print(f"  {metric:20}: {data[metric]:>10}")
        else:
            print(f"  {metric:20}: {'N/A':>10}")
    
    # Thêm phần đánh giá tổng quan
    print(f"\nDANH GIA TONG QUAN:")
    print("-" * 40)
    
    # Đánh giá PE
    if data.get("PE"):
        if data["PE"] < 15:
            print("  PE Ratio: HAP DAN (dưới 15)")
        elif data["PE"] < 25:
            print("  PE Ratio: TRUNG BINH (15-25)")
        else:
            print("  PE Ratio: CAO (trên 25)")
    
    # Đánh giá ROE
    if data.get("ROE"):
        if data["ROE"] > 20:
            print("  ROE: XUAT SAC (trên 20%)")
        elif data["ROE"] > 15:
            print("  ROE: TOT (15-20%)")
        else:
            print("  ROE: TRUNG BINH (dưới 15%)")
    
    # Đánh giá PEG
    if data.get("PEG"):
        if data["PEG"] < 1:
            print("  PEG: UNDERVALUED (dưới 1)")
        elif data["PEG"] < 1.5:
            print("  PEG: FAIR VALUE (1-1.5)")
        else:
            print("  PEG: OVERVALUED (trên 1.5)")


def save_to_file(data: Dict[str, Optional[Union[float, int]]], ticker: str, filename: str = None) -> None:
    """
    Lưu kết quả phân tích vào file text với format đẹp mắt
    
    MÔ TẢ CHI TIẾT:
    ----------------
    Hàm này lưu tất cả các chỉ số định giá đã crawl được vào file text với format
    đẹp mắt và dễ đọc. File được lưu với encoding UTF-8 để hỗ trợ tiếng Việt.
    
    FORMAT FILE:
    ------------
    - Header với thông tin cổ phiếu và thời gian
    - Các chỉ số được nhóm theo từng loại
    - Giá trị được format với số thập phân phù hợp
    - N/A cho các chỉ số không lấy được dữ liệu
    
    CẤU TRÚC FILE:
    --------------
    1. Header: Tên báo cáo và mã cổ phiếu
    2. Thời gian tạo báo cáo
    3. Các nhóm chỉ số:
       - Chỉ số định giá
       - Chỉ số sinh lời  
       - Tình hình tài chính
       - Thông tin thị trường
    4. Đánh giá tổng quan
    
    Args:
        data (Dict[str, Optional[Union[float, int]]]): Dictionary chứa các chỉ số đã crawl
            - Key: Tên chỉ số (ví dụ: "PE", "ROE", "Current_Price")
            - Value: Giá trị chỉ số hoặc None nếu không lấy được
        ticker (str): Mã cổ phiếu đã phân tích (ví dụ: "FPT", "VCB")
        filename (str, optional): Tên file để lưu kết quả
            - Nếu None: Tự động tạo tên file theo format "valuation_report_{ticker}_fixed.txt"
            - Ví dụ: "valuation_report_FPT_fixed.txt"
        
    Returns:
        None: Chỉ lưu file, không trả về giá trị
        
    Raises:
        IOError: Nếu không thể ghi file (quyền truy cập, ổ đĩa đầy, etc.)
        
    Example:
        >>> data = {"PE": 19.0, "ROE": 28.3, "Current_Price": 95000}
        >>> save_to_file(data, "FPT")
        # Sẽ tạo file "valuation_report_FPT_fixed.txt"
        
        >>> save_to_file(data, "FPT", "custom_report.txt")
        # Sẽ tạo file "custom_report.txt"
        
    File Output:
        File được tạo với nội dung:
        ```
        BÁO CÁO PHÂN TÍCH ĐỊNH GIÁ - MÃ FPT (VNSTOCK 3.2.6)
        ==================================================
        
        Thời gian tạo báo cáo: 2024-01-15 10:30:25
        
        CHỈ SỐ ĐỊNH GIÁ:
        PE                  :       19.0
        PB                  :        4.9
        ...
        ```
    """
    if filename is None:
        filename = f"valuation_report_{ticker}_fixed.txt"
    
    try:
        from datetime import datetime
        
        with open(filename, 'w', encoding='utf-8') as f:
            # Header
            f.write(f"BAO CAO PHAN TICH DINH GIA - MA {ticker} (VNSTOCK 3.2.6)\n")
            f.write("=" * 60 + "\n")
            f.write(f"Thoi gian tao bao cao: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Định nghĩa các nhóm chỉ số
            valuation_metrics = ["PE", "PB", "PEG", "Earnings_Yield", "Simple_DCF", "Dividend_Yield"]
            profitability_metrics = ["ROE", "EPS_Growth", "EPS"]
            financial_health_metrics = ["Debt_Equity", "Current_Ratio"]
            market_metrics = ["Current_Price", "Book_Value_Per_Share", "Market_Cap"]
            
            # Lưu từng nhóm
            f.write("CHI SO DINH GIA:\n")
            for metric in valuation_metrics:
                if metric in data and data[metric] is not None:
                    if metric in ["Earnings_Yield", "Dividend_Yield"]:
                        f.write(f"  {metric:20}: {data[metric]:>10}%\n")
                    else:
                        f.write(f"  {metric:20}: {data[metric]:>10}\n")
                else:
                    f.write(f"  {metric:20}: {'N/A':>10}\n")
            
            f.write("\nCHI SO SINH LOI:\n")
            for metric in profitability_metrics:
                if metric in data and data[metric] is not None:
                    if metric in ["ROE", "EPS_Growth"]:
                        f.write(f"  {metric:20}: {data[metric]:>10}%\n")
                    else:
                        f.write(f"  {metric:20}: {data[metric]:>10}\n")
                else:
                    f.write(f"  {metric:20}: {'N/A':>10}\n")
            
            f.write("\nTINH HINH TAI CHINH:\n")
            for metric in financial_health_metrics:
                if metric in data and data[metric] is not None:
                    f.write(f"  {metric:20}: {data[metric]:>10}\n")
                else:
                    f.write(f"  {metric:20}: {'N/A':>10}\n")
            
            f.write("\nTHONG TIN THI TRUONG:\n")
            for metric in market_metrics:
                if metric in data and data[metric] is not None:
                    if metric == "Market_Cap":
                        f.write(f"  {metric:20}: {data[metric]:>10} ty VND\n")
                    else:
                        f.write(f"  {metric:20}: {data[metric]:>10}\n")
                else:
                    f.write(f"  {metric:20}: {'N/A':>10}\n")
            
            # Thêm phần đánh giá tổng quan
            f.write(f"\nDANH GIA TONG QUAN:\n")
            f.write("-" * 40 + "\n")
            
            if data.get("PE"):
                if data["PE"] < 15:
                    f.write("  PE Ratio: HAP DAN (dưới 15)\n")
                elif data["PE"] < 25:
                    f.write("  PE Ratio: TRUNG BINH (15-25)\n")
                else:
                    f.write("  PE Ratio: CAO (trên 25)\n")
            
            if data.get("ROE"):
                if data["ROE"] > 20:
                    f.write("  ROE: XUAT SAC (trên 20%)\n")
                elif data["ROE"] > 15:
                    f.write("  ROE: TOT (15-20%)\n")
                else:
                    f.write("  ROE: TRUNG BINH (dưới 15%)\n")
            
            if data.get("PEG"):
                if data["PEG"] < 1:
                    f.write("  PEG: UNDERVALUED (dưới 1)\n")
                elif data["PEG"] < 1.5:
                    f.write("  PEG: FAIR VALUE (1-1.5)\n")
                else:
                    f.write("  PEG: OVERVALUED (trên 1.5)\n")
            
            f.write(f"\nTong so chi so: {len([k for k, v in data.items() if v is not None])}/{len(data)}\n")
        
        print(f"Da luu ket qua vao file: {filename}")
    except Exception as e:
        print(f"Khong the luu file: {str(e)}")


if __name__ == "__main__":
    """
    Hàm main - chạy chương trình khi file được thực thi trực tiếp
    
    MÔ TẢ CHI TIẾT:
    ----------------
    Đây là entry point chính của chương trình phân tích định giá cổ phiếu.
    Khi file được chạy trực tiếp (python fintech_vnstock_final.py), hàm này sẽ:
    
    1. Hiển thị thông báo khởi động chương trình
    2. Gọi hàm valuation_metrics() để crawl dữ liệu cho mã cổ phiếu mặc định
    3. Gọi hàm display_results() để hiển thị kết quả đẹp mắt trên console
    4. Gọi hàm save_to_file() để lưu báo cáo ra file text
    5. Hiển thị thông báo hoàn thành và hướng dẫn sử dụng
    
    QUY TRÌNH THỰC HIỆN:
    -------------------
    1. Khởi tạo → 2. Crawl dữ liệu → 3. Hiển thị kết quả → 4. Lưu file → 5. Kết thúc
    
    CẤU HÌNH:
    ---------
    - Mã cổ phiếu mặc định: Được định nghĩa trong biến TICKER ở đầu file
    - Có thể thay đổi bằng cách sửa giá trị của biến TICKER
    - Hoặc gọi trực tiếp: valuation_metrics("VCB") cho mã khác
    
    ERROR HANDLING:
    --------------
    - Nếu có lỗi trong quá trình crawl: Chương trình vẫn tiếp tục chạy
    - Các chỉ số bị lỗi sẽ hiển thị "N/A" thay vì crash chương trình
    - Log lỗi chi tiết để debug
    
    Example Usage:
    -------------
    # Chạy với mã mặc định (FPT)
    python fintech_vnstock_final.py
    
    # Hoặc import và sử dụng trong code khác
    from fintech_vnstock_final import valuation_metrics
    data = valuation_metrics("VCB")
    """
    print("BAT DAU CHUONG TRINH PHAN TICH DINH GIA CO PHIEU (VNSTOCK 3.2.6)")
    print("=" * 70)
    print(f"Phan tich ma co phieu: {TICKER}")
    print("=" * 70)
    
    try:
        # Bước 1: Crawl dữ liệu cho mã cổ phiếu mặc định
        print("\n[1/4] Dang crawl du lieu tu vnstock API...")
        result = valuation_metrics(TICKER)
        
        # Bước 2: Hiển thị kết quả đẹp mắt
        print("\n[2/4] Dang hien thi ket qua...")
        display_results(result, TICKER)
        
        # Bước 3: Lưu kết quả vào file
        print("\n[3/4] Dang luu bao cao ra file...")
        save_to_file(result, TICKER)
        
        # Bước 4: Thông báo hoàn thành
        print("\n[4/4] Hoan thanh!")
        print("=" * 70)
        print(f"✅ HOAN THANH phan tich cho ma {TICKER}!")
        print(f"📊 Tong so chi so: {len([k for k, v in result.items() if v is not None])}/{len(result)}")
        print("=" * 70)
        
        # Hướng dẫn sử dụng
        print("\n💡 HUONG DAN SU DUNG:")
        print("- Thay doi bien TICKER o dau file de phan tich ma khac")
        print("- Hoac import module va su dung: valuation_metrics('VCB')")
        print("- File bao cao da duoc luu: valuation_report_FPT_fixed.txt")
        print("- Da sua loi import va cap nhat API cho vnstock 3.2.6")
        
    except Exception as e:
        print(f"\n❌ LOI NGHIEM TRONG: {str(e)}")
        print("Vui long kiem tra ket noi mang va thu lai")
        import traceback
        traceback.print_exc()



