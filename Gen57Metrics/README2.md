[2 tools called]

## Kết quả chạy hiện tại

- Đã chạy `python Gen57Metrics\calculate_all_indicators.py MIG 2024 --indicator CFO --pretty`.
- Registry load OK nhưng DB không có bản ghi `cash_flow_statement_raw` cho `stock=MIG, year=2024`, nên CFO trả về `null`. Bạn cần nạp dữ liệu BCTC trước khi chạy lại.

```json
{
  "stock": "MIG",
  "year": 2024,
  "quarter": null,
  "indicators_with_id": [
    {"id": 1, "name": "CFO", "value": null}
  ],
  "metadata": {
    "requested": 1,
    "successful": 0,
    "failed": 1,
    "failed_list": ["CFO"]
  }
}
```

## Luồng cấu trúc file chính

```
calculate_all_indicators.py  (CLI + argparse, xử lý --indicator, --save-to-db)
        │
        ▼
IndicatorCalculator (indicator_calculator.py)
        │
        ├─ IndicatorRegistry (indicator_registry.py) → load 57 định nghĩa + meta
        │
        ├─ IndicatorMapper (indicator_mapper.py) → map tên ↔ hàm/ma_so
        │
        └─ Direct/Calculated Indicators (ví dụ M1/CFO.py, base_indicator.py, direct_indicator.py)
                │
                ▼
        utils_database_manager.get_value_by_ma_so() → PostgreSQL bảng nguồn (balance_sheet_raw, cash_flow_statement_raw,...)

Khi cần lưu:
IndicatorCalculator result
        │
        ▼
save_indicator_result_payload() (indicator_result_repository.py)
        │
        ▼
Table `indicator_57` (tự tạo nếu chưa có, upsert từng indicator)
```

Gợi ý: sau khi bạn import dữ liệu cash-flow vào `cash_flow_statement_raw`, chạy lại câu lệnh CFO và nếu muốn lưu DB thì thêm `--save-to-db` (mặc định bảng `indicator_57`).
