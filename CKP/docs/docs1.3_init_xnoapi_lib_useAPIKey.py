from xnoapi.vn.data import *

from xnoapi import client

from xnoapi.vn.data.utils import client
from xnoapi.vn.data import stocks, derivatives

# Khởi tạo client
client(apikey="your_api_key")

# Danh sách cổ phiếu có tính thanh khoản cao
liquid_stocks = stocks.list_liquid_asset()
print("Cổ phiếu thanh khoản cao:", liquid_stocks)

# Dữ liệu lịch sử cổ phiếu VIC (Vingroup)
from xnoapi.vn.data import get_stock_hist
vic_data = get_stock_hist("VIC", resolution='h')
print("Dữ liệu VIC:")
print(vic_data.head())

# Dữ liệu phái sinh VN30F1M theo khung thời gian 1 phút
from xnoapi.vn.data import get_derivatives_hist
vn30f1m_data = get_derivatives_hist("VN30F1M", "1m")
print("Dữ liệu VN30F1M:")
print(vn30f1m_data.head())