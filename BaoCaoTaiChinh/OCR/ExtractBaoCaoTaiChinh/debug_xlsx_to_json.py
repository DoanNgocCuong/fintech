#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Debug script để kiểm tra vấn đề đọc Excel và tạo JSON
"""
import pandas as pd
import sys
from pathlib import Path

# Set UTF-8 encoding for console output
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

excel_file = "MIG_2024_1_5_1_CanDoiKeToan.xlsx"

print("=" * 80)
print("DEBUG: Checking Excel file structure")
print("=" * 80)

# Đọc file Excel
excel_path = Path(excel_file)
if not excel_path.exists():
    print(f"ERROR: File not found: {excel_file}")
    sys.exit(1)

excel_file_obj = pd.ExcelFile(str(excel_path))
sheet_names = excel_file_obj.sheet_names

print(f"\nFound {len(sheet_names)} sheet(s): {sheet_names}")

# Kiểm tra từng sheet
for sheet_name in sheet_names:
    print(f"\n{'='*80}")
    print(f"Sheet: {sheet_name}")
    print(f"{'='*80}")
    
    df = pd.read_excel(excel_path, sheet_name=sheet_name)
    
    print(f"\nShape: {df.shape}")
    print(f"\nColumns:")
    for i, col in enumerate(df.columns):
        print(f"  {i}: '{col}'")
    
    print(f"\nFirst 10 rows:")
    print(df.head(10).to_string())
    
    # Test find columns
    print(f"\n{'='*80}")
    print("Testing column detection:")
    print(f"{'='*80}")
    
    from utils_prepare_process import find_ma_so_column, find_value_column, parse_ma_so, parse_number
    
    ma_so_col = find_ma_so_column(df)
    value_col = find_value_column(df)
    
    print(f"Ma so column: {ma_so_col}")
    print(f"Value column: {value_col}")
    
    if ma_so_col and value_col:
        print(f"\nTesting first 5 rows:")
        for idx in range(min(5, len(df))):
            row = df.iloc[idx]
            ma_so_str = row.get(ma_so_col)
            value = row.get(value_col)
            
            print(f"\n  Row {idx}:")
            print(f"    Ma so raw: {ma_so_str} (type: {type(ma_so_str)})")
            print(f"    Value raw: {value} (type: {type(value)})")
            
            if pd.notna(ma_so_str):
                ma_so = parse_ma_so(str(ma_so_str))
                print(f"    Parsed ma so: {ma_so}")
            
            if pd.notna(value):
                parsed_value = parse_number(value)
                print(f"    Parsed value: {parsed_value}")
            else:
                print(f"    Value is NaN/None")

print("\n" + "=" * 80)
print("DEBUG: Testing update_json_with_ma_so")
print("=" * 80)

# Test update function
from main_CanDoiKeToan import _get_balance_sheet_json_template
from utils_prepare_process import update_json_with_ma_so

test_json = _get_balance_sheet_json_template()
print("\nTesting với ma so 111:")
result = update_json_with_ma_so(test_json, 111, 123456.0)
print(f"Update result: {result}")

# Check if updated
tien_111 = test_json.get("can_doi_ke_toan", {}).get("tai_san", {}).get("A_tai_san_ngan_han_100", {}).get("I_tien_va_cac_khoan_tuong_duong_tien_110", {}).get("1_tien_111", {})
print(f"Value after update: {tien_111.get('so_cuoi_nam')}")



