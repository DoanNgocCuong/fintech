# VNStock Full Report (MECE)

Tạo FULL báo cáo phân tích cho cổ phiếu VN: FA, Định giá, TA, giao dịch nội bộ/cổ đông lớn, tin tức, cấu trúc DN…
Xuất **Excel nhiều sheet** + **JSON**. Có sẵn **API** để tích hợp agent.

## Cài đặt
```bash
python -m venv .venv && source .venv/bin/activate   # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
```

## Chạy CLI
```bash
python vnstock_full_report.py --symbols TCB,HPG,CTD --start 2024-01-01 --end 2025-10-10 --out ./reports
# hoặc nhanh
python vnstock_full_report.py -s TCB -o ./reports
```

Kết quả:
- `./reports/report_TCB_YYYY-MM-DD.xlsx`
- `./reports/report_TCB_YYYY-MM-DD.json`

## Chạy API
```bash
# Dev
uvicorn api:app --reload --host 0.0.0.0 --port 8000

# Prod đơn giản
python api.py --host 0.0.0.0 --port 8000
# hoặc
nohup python api.py --host 0.0.0.0 --port 8000 > server.log 2>&1 &
```

Endpoints:
- `GET /health`
- `GET /report/{symbol}?start=YYYY-MM-DD&end=YYYY-MM-DD&source=VCI`

> Gợi ý: Dùng API để kiểm tra nhanh kích thước dữ liệu; dùng CLI để xuất Excel/JSON đầy đủ.

## Notes
- Mã nguồn dùng `safe_call` nên tương thích với nhiều phiên bản `vnstock` khác nhau (nếu một số hàm chưa có sẽ trả về sheet rỗng thay vì lỗi).
- Bộ chỉ báo TA cơ bản (MA20, EMA20, RSI14, MACD, Bollinger) được tính trực tiếp bằng pandas từ `price_history`.
- Có thể mở rộng thêm indicator hoặc sheet mới rất dễ (xem file `vnstock_full_report.py`).

---

Made with ♥
