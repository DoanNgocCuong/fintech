#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for utils_xlsx_to_json.py
"""
import json
from pathlib import Path
from utils_xlsx_to_json import create_json_result

def test_create_json_result():
    """Test create_json_result function"""
    excel_file = "BMI_2024_1_5_1_CanDoiKeToan.xlsx"
    output_json = "BMI_2024_1_5_1_CanDoiKeToan_test.json"
    
    print("=" * 80)
    print("Testing create_json_result function")
    print("=" * 80)
    
    # Check if Excel file exists
    if not Path(excel_file).exists():
        print(f"ERROR: Excel file not found: {excel_file}")
        return False
    
    try:
        # Run the function
        result = create_json_result(excel_file, output_json)
        
        # Verify result
        print("\n" + "=" * 80)
        print("Verification:")
        print("=" * 80)
        print(f"Total keys in result: {len(result)}")
        print(f"Keys: {list(result.keys())}")
        
        # Check if JSON file was created
        if Path(output_json).exists():
            print(f"\n[OK] JSON file created: {output_json}")
            
            # Load and verify JSON structure
            with open(output_json, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # Sample verification
            if 'can_doi_ke_toan' in json_data:
                tai_san = json_data['can_doi_ke_toan'].get('tai_san', {})
                if 'A_tai_san_ngan_han_100' in tai_san:
                    tai_san_ngan_han = tai_san['A_tai_san_ngan_han_100']
                    print(f"\n[OK] Sample value - Tai san ngan han (100): {tai_san_ngan_han.get('so_cuoi_nam')}")
                    
                    if 'I_tien_va_cac_khoan_tuong_duong_tien_110' in tai_san_ngan_han:
                        tien = tai_san_ngan_han['I_tien_va_cac_khoan_tuong_duong_tien_110']
                        if '1_tien_111' in tien:
                            tien_111 = tien['1_tien_111']
                            print(f"[OK] Sample value - Tien (111): {tien_111.get('so_cuoi_nam')}")
            
            print("\n" + "=" * 80)
            print("[OK] Test completed successfully!")
            print("=" * 80)
            return True
        else:
            print(f"\n[ERROR] JSON file not created: {output_json}")
            return False
            
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_create_json_result()
    exit(0 if success else 1)

