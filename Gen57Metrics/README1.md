# Gen57Metrics - 57 Indicators Calculator

Hệ thống tính toán 57 chỉ số tài chính cho các mã cổ phiếu, tự động xử lý dependencies và cache results.

## Kiến trúc

### 1. Core Components

#### A. `IndicatorRegistry` class (`indicator_registry.py`)
- Load 57 indicators từ `57BaseIndicators.json`
- Registry/mapping: `Indicator_Name` → function/module
- Phân loại: Direct (từ DB) vs Calculated (tính từ indicators khác)
- Metadata và dependency tracking

#### B. `IndicatorMapper` class (`indicator_mapper.py`)
- Map `Indicator_Name` → Python calculation functions
- Auto-extract `ma_so` từ TT200_Formula cho direct indicators
- Auto-register direct indicators từ JSON definitions

#### C. `IndicatorCalculator` class (`indicator_calculator.py`)
- Tính tất cả 57 indicators cho một stock
- Dependency resolution (topological sort)
- Caching để tránh query DB nhiều lần
- Error handling và progress tracking

#### D. `calculate_all_indicators.py` - Main Entry Point
- Command-line interface (CLI)
- Programmatic API
- JSON output support

### 2. Workflow

```
Stock + Year + Quarter
    ↓
IndicatorRegistry (load 57 indicators from JSON)
    ↓
IndicatorMapper (map Indicator_Name → functions)
    ↓
IndicatorCalculator
    ├── Direct indicators → get_value_by_ma_so()
    ├── Calculated indicators → dependency resolution
    │   ├── EBIT → needs ma_so 50 + 23
    │   ├── EBITDA → needs EBIT + ma_so 02
    │   └── NOPAT → needs EBIT + ma_so 51
    └── Result (JSON with all 57 values sorted by ID)
```

### 3. Cấu trúc Files

```
Gen57Metrics/
├── indicator_registry.py          # Load & manage 57 indicators
├── indicator_mapper.py            # Map Indicator_Name → functions
├── indicator_calculator.py        # Calculate all indicators
├── calculate_all_indicators.py    # Main entry point (CLI & API)
├── base_indicator.py              # Base class for indicators
├── direct_indicator.py            # Direct indicator implementation
├── utils_database_manager.py      # Database utilities
├── 57BaseIndicators.json          # 57 indicators definitions
│
├── M1_BCTC_core_profit_and_cashflow/
│   ├── CFO.py                     # CFO calculation
│   ├── NI.py                      # Net Income calculation
│   ├── EBIT.py                    # EBIT calculation
│   ├── EBITDA.py                  # EBITDA calculation
│   └── NOPAT.py                   # NOPAT calculation
│
├── M2_BCTC_core_revenue_and_margins/
├── M3_BCTC_core_balance_sheet_and_investment/
├── M4_market_and_valuation/
├── M5_cost_of_capital_and_dcf/
└── M6_governance_and_disclosure/
```

## Features

- ✅ **Dependency Resolution**: Tự động xử lý dependencies (EBITDA depends on EBIT)
- ✅ **Topological Sort**: Tính indicators theo thứ tự dependencies
- ✅ **Auto-registration**: Tự động register direct indicators từ JSON
- ✅ **Caching**: Cache values để tránh query DB nhiều lần
- ✅ **Error Tolerance**: Một indicator lỗi không làm dừng toàn bộ
- ✅ **Progress Tracking**: Theo dõi successful/failed indicators
- ✅ **Sorted by ID**: Kết quả được sort theo ID từ 1-57

## Output Format

```json
{
  "stock": "MIG",
  "year": 2024,
  "quarter": 2,
  "indicators_with_id": [
    {
      "id": 1,
      "name": "CFO",
      "value": 174481880282.0
    },
    {
      "id": 2,
      "name": "Net Income (NI)",
      "value": null
    },
    {
      "id": 3,
      "name": "EBIT",
      "value": null
    },
    ...
    {
      "id": 57,
      "name": "Disclosure Count per Year",
      "value": null
    }
  ],
  "metadata": {
    "calculated_at": "2025-11-16T22:52:05.494495",
    "total_indicators": 57,
    "successful": 8,
    "failed": 49,
    "failed_list": [...],
    "calculation_order": [...]
  }
}
```

**Note**: Tất cả indicators được sort theo ID (1-57) trong `indicators_with_id`.

## Cách Sử Dụng

### 1. Command Line Interface (CLI)

```bash
# Calculate annual indicators
python calculate_all_indicators.py MIG 2024

# Calculate quarterly indicators
python calculate_all_indicators.py MIG 2024 --quarter 2

# Save to JSON file
python calculate_all_indicators.py MIG 2024 --quarter 2 --output result.json

# Pretty print JSON
python calculate_all_indicators.py MIG 2024 --pretty

# Exclude metadata
python calculate_all_indicators.py MIG 2024 --no-metadata
```

### 2. Programmatic API

```python
from Gen57Metrics.calculate_all_indicators import calculate_indicators_for_stock

# Calculate all 57 indicators
result = calculate_indicators_for_stock("MIG", 2024, quarter=2)

# Access results
for indicator in result["indicators_with_id"]:
    print(f"ID {indicator['id']}: {indicator['name']} = {indicator['value']}")

# Access specific indicator by ID
cfo = next((ind for ind in result["indicators_with_id"] if ind["id"] == 1), None)
if cfo:
    print(f"CFO: {cfo['value']}")
```

### 3. Direct Usage

```python
from Gen57Metrics.indicator_calculator import IndicatorCalculator

calculator = IndicatorCalculator()
result = calculator.calculate_all("MIG", 2024, quarter=2)

# Calculate single indicator
cfo_value = calculator.calculate_single("CFO", "MIG", 2024, quarter=2)
```

## Tính Toán Indicators

### Direct Indicators (Get_Direct_From_DB = "yes")
- Tự động load từ database dựa trên `ma_so` trong TT200_Formula
- Ví dụ: CFO (ma_so 111), NI (ma_so 60), Revenue (ma_so 10)

### Calculated Indicators (Get_Direct_From_DB = null)
- Tính từ các indicators khác
- Ví dụ:
  - **EBIT** = Operating profit (ma_so 50) + Interest expense (ma_so 23)
  - **EBITDA** = EBIT + D&A (ma_so 02)
  - **NOPAT** = EBIT × (1 – Tax rate)

### Tạo Calculation Function Mới

1. Tạo file trong module folder tương ứng (M1, M2, M3, ...)
2. Implement function với signature: `get_[INDICATOR]_value(stock, year, quarter)`
3. Register trong `indicator_mapper.py`:

```python
# In indicator_mapper.py
from Gen57Metrics.M1_BCTC_core_profit_and_cashflow.REVENUE import get_Revenue_value

def _register_builtin_mappings(self):
    self.register("Revenue", get_Revenue_value)
```

## Examples

### Example 1: Calculate all indicators

```python
from Gen57Metrics.calculate_all_indicators import calculate_indicators_for_stock

result = calculate_indicators_for_stock("MIG", 2024, quarter=2)

print(f"Total indicators: {result['metadata']['total_indicators']}")
print(f"Successful: {result['metadata']['successful']}")
print(f"Failed: {result['metadata']['failed']}")

# List all successful indicators
successful = [
    ind for ind in result["indicators_with_id"] 
    if ind["value"] is not None
]
print(f"\nSuccessful indicators ({len(successful)}):")
for ind in successful:
    print(f"  ID {ind['id']}: {ind['name']} = {ind['value']}")
```

### Example 2: Filter by ID range

```python
result = calculate_indicators_for_stock("MIG", 2024)

# Get indicators with ID 1-10 (Profit & Cashflow group)
profit_cashflow = [
    ind for ind in result["indicators_with_id"]
    if 1 <= ind["id"] <= 10
]

for ind in profit_cashflow:
    print(f"ID {ind['id']}: {ind['name']} = {ind['value']}")
```

### Example 3: Export to CSV

```python
import csv
import json

result = calculate_indicators_for_stock("MIG", 2024, quarter=2)

# Export to CSV
with open("indicators.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["ID", "Name", "Value"])
    for ind in result["indicators_with_id"]:
        writer.writerow([ind["id"], ind["name"], ind["value"]])
```

## Current Status

### ✅ Implemented (8 indicators)
- CFO (ID: 1)
- Total Assets (ID: 15)
- Equity (ID: 16)
- Cash & Short-term Investments (ID: 18)
- ΔWorking Capital (ID: 22)
- Accounts Receivable (ID: 23)
- Inventory (ID: 24)
- Accounts Payable (ID: 25)

### 🔄 Partially Implemented (5 indicators - có functions nhưng chưa test)
- NI (ID: 2) - có function nhưng chưa auto-register
- EBIT (ID: 3)
- EBITDA (ID: 4)
- NOPAT (ID: 5)
- Revenue (ID: 6)

### ⏳ TODO (44 indicators)
- Revenue Growth, Earnings Growth
- Gross Profit, Gross Margin
- Core Revenue, Digital Revenue
- Interest-bearing Debt, Capex
- Working Capital, DSO, DIO, DPO, CCC
- FCFF, Shares Outstanding
- Market & Valuation indicators (P/E, P/B, EV/EBITDA, ...)
- Cost of Capital (WACC, CoE, CoD)
- DCF indicators
- Governance indicators (Auditor, Disclosure, ...)

## Notes

- Script có thể chạy từ bất kỳ thư mục nào (tự động add parent dir vào sys.path)
- Quarter validation: chỉ chấp nhận 1-4
- Unicode encoding: tự động fallback sang ASCII trên Windows
- Indicators được sort theo ID trong output

## Future Enhancements

1. Hoàn thiện các calculation functions cho 49 indicators còn lại
2. Cải thiện dependency parsing để tự động phát hiện dependencies tốt hơn
3. Thêm unit tests
4. Performance optimization cho batch calculations
5. Thêm caching layer để cache results theo stock/year/quarter
