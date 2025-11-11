# -*- coding: utf-8 -*-
"""Regenerate JSON file from Excel"""
from utils_xlsx_to_json import create_json_result

excel_file = 'MIG_2024_1_5_1_CanDoiKeToan.xlsx'
json_file = 'MIG_2024_1_5_1_CanDoiKeToan.json'

print(f"Regenerating JSON from Excel: {excel_file}")
print(f"Output JSON: {json_file}")
print("="*80)

try:
    result = create_json_result(
        excel_file=excel_file,
        output_json_file=json_file,
        replace_null_with=None
    )
    print("\n" + "="*80)
    print("SUCCESS: JSON file regenerated successfully!")
    print("="*80)
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()



