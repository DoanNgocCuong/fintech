# 🔧 HƯỚNG DẪN SỬA LỖI VNSTOCK IMPORT - VERSION 3.2.6

## 📋 Tóm tắt vấn đề

**Lỗi gốc:**
```python
ImportError: cannot import name 'Fundamental' from 'vnstock'
```

**Nguyên nhân:** 
- Code cũ sử dụng API của vnstock version cũ
- Vnstock version 3.2.6 có API hoàn toàn mới
- Các class `Fundamental`, `Financial` không còn tồn tại

## 🚀 Giải pháp

### 1. Cài đặt vnstock (nếu chưa có)
```bash
pip install vnstock
```

### 2. Thay đổi Import Statements

**❌ Code cũ (không hoạt động):**
```python
from vnstock import Fundamental, Financial, stock_historical_data
```

**✅ Code mới (hoạt động):**
```python
from vnstock import Finance, Quote  # API mới của vnstock 3.2.6
```

### 3. Thay đổi cách khởi tạo đối tượng

**❌ Code cũ:**
```python
fundamental_obj = Fundamental(ticker)
financial_obj = Financial(ticker)
```

**✅ Code mới:**
```python
finance_obj = Finance(source='tcbs', symbol=ticker)  # Cần cả source và symbol
quote_obj = Quote(symbol=ticker, source='tcbs')      # Cần cả symbol và source
```

### 4. Thay đổi cách lấy dữ liệu

**❌ Code cũ:**
```python
data["PE"] = fundamental_obj.pe()
data["PB"] = fundamental_obj.pb()
data["ROE"] = fundamental_obj.roe()
```

**✅ Code mới:**
```python
# Lấy tất cả dữ liệu tỷ số tài chính một lần
ratio_data = finance_obj.ratio()

# Lấy dữ liệu gần nhất
latest_data = ratio_data.iloc[0]

# Truy cập các chỉ số từ DataFrame
data["PE"] = latest_data['price_to_earning']
data["PB"] = latest_data['price_to_book']
data["ROE"] = latest_data['roe'] * 100  # Chuyển thành phần trăm
```

### 5. Thay đổi cách lấy dữ liệu giá

**❌ Code cũ:**
```python
price_data = stock_historical_data(symbol=ticker, start_date='2024-01-01', end_date='2024-12-31')
```

**✅ Code mới:**
```python
price_data = quote_obj.history(start='2024-01-01', end='2024-12-31')
```

## 📊 Các chỉ số có sẵn trong vnstock 3.2.6

Khi gọi `finance_obj.ratio()`, bạn sẽ nhận được DataFrame với các cột sau:

```python
[
    'quarter', 'year', 'price_to_earning', 'price_to_book', 'value_before_ebitda',
    'roe', 'roa', 'days_receivable', 'days_inventory', 'days_payable',
    'ebit_on_interest', 'earning_per_share', 'book_value_per_share',
    'equity_on_total_asset', 'equity_on_liability', 'current_payment',
    'quick_payment', 'eps_change', 'ebitda_on_stock', 'gross_profit_margin',
    'operating_profit_margin', 'post_tax_margin', 'debt_on_equity',
    'debt_on_asset', 'debt_on_ebitda', 'short_on_long_debt', 'asset_on_equity',
    'capital_balance', 'cash_on_equity', 'cash_on_capitalize', 'cash_circulation',
    'revenue_on_work_capital', 'capex_on_fixed_asset', 'revenue_on_asset',
    'post_tax_on_pre_tax', 'ebit_on_revenue', 'pre_tax_on_ebit',
    'payable_on_equity', 'ebitda_on_stock_change', 'book_value_per_share_change'
]
```

## 🎯 Ví dụ code hoàn chỉnh

```python
from vnstock import Finance, Quote
import pandas as pd

def get_valuation_metrics(ticker):
    """Lấy các chỉ số định giá cho mã cổ phiếu"""
    
    # Khởi tạo đối tượng
    finance_obj = Finance(source='tcbs', symbol=ticker)
    quote_obj = Quote(symbol=ticker, source='tcbs')
    
    # Lấy dữ liệu tỷ số tài chính
    ratio_data = finance_obj.ratio()
    latest_data = ratio_data.iloc[0]
    
    # Lấy dữ liệu giá
    price_data = quote_obj.history(start='2024-01-01', end='2024-12-31')
    
    # Trích xuất các chỉ số
    metrics = {
        'PE': latest_data['price_to_earning'],
        'PB': latest_data['price_to_book'],
        'ROE': latest_data['roe'] * 100,
        'Current_Price': price_data['close'].iloc[-1]
    }
    
    return metrics

# Sử dụng
result = get_valuation_metrics('FPT')
print(result)
```

## ⚠️ Lưu ý quan trọng

1. **Source Parameter:** Cả `Finance` và `Quote` đều cần parameter `source`. Các giá trị hợp lệ: `'tcbs'`, `'vci'`, `'msn'`

2. **DataFrame Structure:** API mới trả về DataFrame thay vì giá trị trực tiếp

3. **Encoding Issues:** Tránh sử dụng emoji trong code để tránh lỗi encoding trên Windows

4. **Error Handling:** Luôn kiểm tra `pd.notna()` trước khi sử dụng dữ liệu

## 📁 Files đã tạo

1. **`fintech_vnstock_final.py`** - Version đã sửa lỗi hoàn chỉnh
2. **`test_vnstock_simple.py`** - File test đơn giản để kiểm tra API
3. **`docs/vnstock_bug_fix_documentation.md`** - Tài liệu này

## 🧪 Kết quả test

Code đã được test thành công với mã FPT:
```
OK P/E Ratio: 19.0
OK P/B Ratio: 4.9
OK ROE: 28.3%
OK Debt/Equity: 0.6
OK Current Ratio: 1.4
OK Earnings Yield: 5.26%
OK EPS Growth: 4.6%
OK PEG Ratio: 4.13
OK EPS: 5,057 VND
OK Book Value Per Share: 19,549 VND
OK Current Price: 131.49 VND
```

## 💡 Tips cho người mới học Python

1. **Luôn đọc documentation** trước khi sử dụng thư viện mới
2. **Kiểm tra version** của thư viện khi gặp lỗi import
3. **Test từng phần nhỏ** trước khi viết code phức tạp
4. **Sử dụng try-except** để xử lý lỗi gracefully
5. **Kiểm tra dữ liệu** trước khi sử dụng (pd.notna(), .empty, etc.)

---

**Tác giả:** AI Assistant  
**Ngày tạo:** 2024  
**Mục đích:** Hướng dẫn sửa lỗi vnstock cho người mới học Python



