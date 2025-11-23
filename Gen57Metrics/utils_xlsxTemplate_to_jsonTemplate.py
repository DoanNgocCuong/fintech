"""
Utility script to convert Excel template to JSON template.

Reads Excel file with multiple sheets and converts to JSON structure,
adding "value" key to each object.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    import pandas as pd
except ImportError:
    pd = None
    print("Error: pandas is required. Install with: pip install pandas openpyxl")
    sys.exit(1)


def get_excel_columns_info(
    excel_file_path: str
) -> Dict[str, Dict[str, Any]]:
    """
    Lấy thông tin về các cột trong file Excel (không đọc toàn bộ dữ liệu).
    
    Args:
        excel_file_path (str): Đường dẫn đến file Excel
    
    Returns:
        Dict[str, Dict[str, Any]]: Dictionary với keys là tên các sheets,
                                   values là dict chứa thông tin về columns
    
    Raises:
        FileNotFoundError: Nếu file Excel không tồn tại
        ImportError: Nếu pandas chưa được cài đặt
    """
    excel_path = Path(excel_file_path)
    
    if not excel_path.exists():
        raise FileNotFoundError(f"Excel file not found: {excel_file_path}")
    
    if pd is None:
        raise ImportError("pandas is required. Install with: pip install pandas openpyxl")
    
    excel_file_obj = pd.ExcelFile(str(excel_path))
    sheet_names = excel_file_obj.sheet_names
    
    result = {}
    
    for sheet_name in sheet_names:
        # Chỉ đọc một vài dòng đầu để lấy thông tin về cột
        df = pd.read_excel(excel_file_obj, sheet_name=sheet_name, nrows=0)
        columns = df.columns.tolist()
        
        result[sheet_name] = {
            "columns": columns,
            "column_count": len(columns),
            "row_count": None  # Sẽ được cập nhật khi đọc toàn bộ
        }
    
    return result


def read_excel_to_json(
    excel_file_path: str,
    output_json_path: Optional[str] = None,
    add_value_key: bool = True,
    show_columns_info: bool = True
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Đọc file Excel và chuyển đổi sang JSON, thêm key "value" vào mỗi object.
    
    Args:
        excel_file_path (str): Đường dẫn đến file Excel
        output_json_path (Optional[str]): Đường dẫn file JSON output. 
                                         Nếu None, tạo tên tự động từ excel_file_path
        add_value_key (bool): Nếu True, thêm key "value": null vào cuối mỗi object
        show_columns_info (bool): Nếu True, hiển thị thông tin chi tiết về các cột
    
    Returns:
        Dict[str, List[Dict[str, Any]]]: Dictionary với keys là tên các sheets,
                                        values là list các dictionaries (rows)
    
    Raises:
        FileNotFoundError: Nếu file Excel không tồn tại
        ImportError: Nếu pandas chưa được cài đặt
    """
    excel_path = Path(excel_file_path)
    
    if not excel_path.exists():
        raise FileNotFoundError(f"Excel file not found: {excel_file_path}")
    
    if pd is None:
        raise ImportError("pandas is required. Install with: pip install pandas openpyxl")
    
    print(f"Reading Excel file: {excel_file_path}")
    
    # Đọc tất cả sheets
    excel_file_obj = pd.ExcelFile(str(excel_path))
    sheet_names = excel_file_obj.sheet_names
    
    print(f"Found {len(sheet_names)} sheet(s): {', '.join(sheet_names)}")
    
    # Dictionary để lưu kết quả
    result = {}
    
    # Đọc từng sheet
    for sheet_name in sheet_names:
        print(f"\nProcessing sheet: {sheet_name}")
        df = pd.read_excel(excel_file_obj, sheet_name=sheet_name)
        
        if df.empty:
            print(f"  Warning: Sheet {sheet_name} is empty, skipping...")
            result[sheet_name] = []
            continue
        
        # Tự động kiểm tra và hiển thị các cột
        columns = df.columns.tolist()
        if show_columns_info:
            print(f"  Found {len(columns)} column(s):")
            for idx, col in enumerate(columns, 1):
                # Đếm số giá trị không null
                non_null_count = df[col].notna().sum()
                null_count = df[col].isna().sum()
                # Lấy kiểu dữ liệu
                dtype = str(df[col].dtype)
                # Tính phần trăm non-null
                total_rows = len(df)
                non_null_pct = (non_null_count / total_rows * 100) if total_rows > 0 else 0
                print(f"    {idx}. {col}")
                print(f"       Type: {dtype}, Non-null: {non_null_count}/{total_rows} ({non_null_pct:.1f}%), Null: {null_count}")
        else:
            print(f"  Found {len(columns)} column(s): {', '.join(columns)}")
        
        # Chuyển DataFrame thành list of dictionaries
        # Sử dụng orient='records' để mỗi row thành một dict
        sheet_data = df.to_dict(orient='records')
        
        # Replace tất cả NaN values thành None (sẽ serialize thành null trong JSON)
        for record in sheet_data:
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None
        
        # Thêm key "value" vào cuối mỗi object nếu được yêu cầu
        if add_value_key:
            for record in sheet_data:
                # Đảm bảo "value" được thêm vào cuối (không overwrite nếu đã có)
                if "value" not in record:
                    record["value"] = None
                else:
                    # Nếu đã có, di chuyển nó xuống cuối
                    temp_value = record.pop("value")
                    record["value"] = temp_value
        
        result[sheet_name] = sheet_data
        print(f"  Converted {len(sheet_data)} rows")
        
        # Hiển thị thống kê về các keys trong JSON
        if sheet_data and show_columns_info:
            all_keys = set()
            for record in sheet_data:
                all_keys.update(record.keys())
            print(f"  JSON keys in output: {', '.join(sorted(all_keys))}")
    
    # Tạo tên file output nếu chưa có
    if output_json_path is None:
        output_json_path = excel_path.with_suffix('.json')
    
    # Ghi ra file JSON
    output_path = Path(output_json_path)
    print(f"\nWriting JSON to: {output_path}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"Successfully saved to: {output_path}")
    
    return result


def main():
    """Main function để chạy script."""
    # Đường dẫn file Excel
    excel_file = r"D:\GIT\Fintech\fintech\Gen57Metrics\57_Base_Indicators_FinAI_TT199_T112025.xlsx"
    
    # Tạo tên file JSON output (cùng thư mục, đổi extension)
    excel_path = Path(excel_file)
    json_file = excel_path.with_suffix('.json')
    
    try:
        result = read_excel_to_json(
            excel_file_path=excel_file,
            output_json_path=str(json_file),
            add_value_key=True
        )
        
        print("\n" + "="*60)
        print("Conversion completed successfully!")
        print("="*60)
        for sheet_name, data in result.items():
            print(f"  {sheet_name}: {len(data)} records")
        
        # Hiển thị tổng kết về cấu trúc
        print("\n" + "="*60)
        print("Excel Structure Summary:")
        print("="*60)
        columns_info = get_excel_columns_info(excel_file)
        for sheet_name, info in columns_info.items():
            print(f"\nSheet: {sheet_name}")
            print(f"  Total columns: {info['column_count']}")
            print(f"  Total rows: {len(result.get(sheet_name, []))}")
            print(f"  Columns: {', '.join(info['columns'])}")
        
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

