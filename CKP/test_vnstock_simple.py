# Test đơn giản vnstock API mới
from vnstock import Finance, Quote
import pandas as pd

def test_vnstock():
    ticker = "FPT"
    print(f"Testing vnstock API for {ticker}")
    
    try:
        # Test Finance object
        finance_obj = Finance(source='tcbs', symbol=ticker)
        print("Finance object created successfully")
        
        # Test ratio data
        ratio_data = finance_obj.ratio()
        print(f"Ratio data shape: {ratio_data.shape}")
        print(f"Ratio data columns: {list(ratio_data.columns)}")
        
        if not ratio_data.empty:
            latest_data = ratio_data.iloc[0]
            print(f"Latest PE ratio: {latest_data['price_to_earning']}")
            print(f"Latest PB ratio: {latest_data['price_to_book']}")
            print(f"Latest ROE: {latest_data['roe']}")
        
        # Test Quote object
        quote_obj = Quote(symbol=ticker)
        print("Quote object created successfully")
        
        # Test price data
        price_data = quote_obj.history(start_date='2024-01-01', end_date='2024-12-31')
        print(f"Price data shape: {price_data.shape}")
        
        if not price_data.empty:
            print(f"Latest close price: {price_data['close'].iloc[-1]}")
        
        print("All tests passed!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_vnstock()



