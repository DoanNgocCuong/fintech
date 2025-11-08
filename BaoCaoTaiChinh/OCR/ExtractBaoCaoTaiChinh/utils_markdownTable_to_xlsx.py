"""
Markdown table example: 
| Mã số | CHỈ TIÊU | Thuyết minh | Năm nay | Năm trước (trình bày lại) |
| --- | --- | --- | --- | --- |
| 01 | 1. Doanh thu phí bảo hiểm (01 = 01.1 + 01.2 + 01.3) Trong đó: | 22 | 5.524.525.927.458 | 4.744.822.893.543 |
| 01.1 | - Phí bảo hiểm gốc |  | 5.437.581.358.498 | 4.929.987.887.081 |
| 01.2 | - Phí nhận tái bảo hiểm |  | 131.908.616.270 | 155.604.010.559 |
| 01.3 | - Tăng dự phòng phí bảo hiểm gốc và nhận tái bảo hiểm |  | (44.964.047.310) | (340.769.004.097) |
| 02 | 2. Phí nhượng tái bảo hiểm (02 = 02.1 + 02.2) Trong đó: | 23 | (1.535.954.562.964) | (1.390.619.914.418) |
| 02.1 | - Tổng phí nhượng tái bảo hiểm |  | (1.553.762.769.096) | (1.412.773.050.817) |
| 02.2 | - Tăng dự phòng phí nhượng tái bảo hiểm |  | 17.808.206.132 | 22.153.136.399 |
| 03 | 3. Doanh thu phí bảo hiểm thuần (03 = 01 + 02) |  | 3.988.571.364.494 | 3.354.202.979.125 |
| 04 | 4. Hoa hồng nhượng tái bảo hiểm và doanh thu khác hoạt động kinh doanh bảo hiểm (04 = 04.1 + 04.2) Trong đó: |  | 275.673.547.268 | 275.857.414.615 |
| 04.1 | - Hoa hồng nhượng tái bảo hiểm | 24 | 233.236.305.303 | 232.012.916.044 |
| 04.2 | - Doanh thu khác hoạt động kinh doanh bảo hiểm | 25 | 42.437.241.965 | 43.844.498.571 |
| 10 | 5. Doanh thu thuần hoạt động kinh doanh bảo hiểm (10 = 03 + 04) |  | 4.264.244.911.762 | 3.630.060.393.740 |
| 11 | 6. Chi bồi thường (11 = 11.1 + 11.2) Trong đó: |  | (1.298.314.539.639) | (1.067.078.808.068) |
| 11.1 | - Tổng chi bồi thường |  | (1.320.603.226.801) | (1.085.055.560.353) |
| 11.2 | - Các khoản giảm trừ |  | 22.288.687.162 | 17.976.752.285 |
| 12 | 7. Thu bồi thường nhượng tái bảo hiểm |  | 411.316.467.133 | 250.395.047.934 |
| 13 | 8. Tăng dự phòng bồi thường bảo hiểm gốc và nhận tái bảo hiểm |  | (237.722.275.126) | (132.964.379.369) |
| 14 | 9. Tăng dự phòng bồi thường nhượng tái bảo hiểm |  | 190.773.654.293 | 69.430.692.093 |
| 15 | 10. Tổng chi bồi thường bảo hiểm (15 = 11 + 12 + 13 + 14) | 26 | (933.946.693.339) | (880.217.447.410) |
| 16 | 11. Tăng dự phòng dao động lớn | 20.2 | (40.157.289.882) | (36.728.625.484) |
"""

import os
import re
import tempfile
from pathlib import Path
from typing import List, Optional

try:
    import pandas as pd
except ImportError:
    pd = None


def _is_separator_line(line: str) -> bool:
    """
    Check if a line is a markdown table separator line.
    
    Args:
        line: Line to check
        
    Returns:
        True if the line is a separator line (e.g., | --- | --- |)
    """
    if not line.startswith('|'):
        return False
    
    # Remove leading and trailing pipes, then split by pipe
    cells = [cell.strip() for cell in line.strip('|').split('|')]
    
    # Check if all cells contain only dashes, spaces, and colons
    # This is the markdown table separator pattern
    for cell in cells:
        # Remove all dashes, spaces, and colons
        remaining = re.sub(r'[\s\-:]+', '', cell)
        # If there's anything left, it's not a separator
        if remaining:
            return False
    
    # If all cells are empty or only contain dashes/spaces/colons, it's a separator
    return True


def _parse_markdown_table(markdown_table: str) -> List[List[str]]:
    """
    Parse markdown table string into a list of rows.
    
    Args:
        markdown_table: String containing markdown table format
        
    Returns:
        List of rows, where each row is a list of cells
    """
    lines = markdown_table.strip().split('\n')
    rows = []
    
    for line in lines:
        line = line.strip()
        # Skip empty lines
        if not line:
            continue
            
        # Skip separator lines (e.g., | --- | --- | or | ------- |)
        if _is_separator_line(line):
            continue
            
        # Skip lines that don't start with |
        if not line.startswith('|'):
            continue
            
        # Remove leading and trailing pipes, then split by pipe
        cells = [cell.strip() for cell in line.strip('|').split('|')]
        
        # Only add non-empty rows
        if cells and any(cell for cell in cells):
            rows.append(cells)
    
    return rows


def _create_dataframe_from_rows(rows: List[List[str]]) -> pd.DataFrame:
    """
    Create pandas DataFrame from parsed rows.
    
    Args:
        rows: List of rows where first row is header
        
    Returns:
        pandas DataFrame
    """
    if not rows:
        raise ValueError("No rows found in markdown table")
    
    # First row is header
    headers = rows[0]
    
    # Remaining rows are data
    data_rows = rows[1:] if len(rows) > 1 else []
    
    # Create DataFrame
    df = pd.DataFrame(data_rows, columns=headers)
    
    return df


def markdownTable_to_xlsx(
    markdown_table: str, 
    output_path: Optional[str] = None,
    sheet_name: str = "Sheet1"
) -> str:
    """
    Convert markdown table to Excel (.xlsx) file.
    
    Args:
        markdown_table: String containing markdown table format
        output_path: Optional output file path. If None, generates a temporary file path
        sheet_name: Name of the Excel sheet (default: "Sheet1")
        
    Returns:
        str: Path to the created Excel file
        
    Raises:
        ValueError: If markdown table is empty or invalid
        ImportError: If pandas or openpyxl is not installed
        
    Example:
        >>> table = "| Col1 | Col2 |\\n| --- | --- |\\n| A | B |"
        >>> path = markdownTable_to_xlsx(table, "output.xlsx")
        >>> print(f"Saved to: {path}")
    """
    # Check if pandas is available
    if pd is None:
        raise ImportError(
            "pandas is required. Install it with: pip install pandas openpyxl"
        )
    
    # Parse markdown table
    rows = _parse_markdown_table(markdown_table)
    
    if not rows:
        raise ValueError("No valid table data found in markdown table")
    
    # Create DataFrame
    df = _create_dataframe_from_rows(rows)
    
    # Generate output path if not provided
    if output_path is None:
        output_path = os.path.join(
            tempfile.gettempdir(), 
            f"markdown_table_{os.getpid()}.xlsx"
        )
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Save to Excel
    df.to_excel(
        output_path, 
        index=False, 
        sheet_name=sheet_name,
        engine='openpyxl'
    )
    
    return output_path

def main():
    """
    Main function to convert markdown table from file to xlsx.
    Reads from markdownTableExample.md and converts to Excel.
    """
    # Get the directory of the current file
    current_dir = Path(__file__).parent
    
    # Path to the markdown file
    markdown_file_path = current_dir / "markdownTableExample.md"
    
    # Check if file exists
    if not markdown_file_path.exists():
        raise FileNotFoundError(
            f"Markdown file not found: {markdown_file_path}"
        )
    
    # Read markdown table from file
    print(f"Reading markdown table from: {markdown_file_path}")
    with open(markdown_file_path, 'r', encoding='utf-8') as f:
        markdown_table = f.read()
    
    # Generate output path (same directory, with .xlsx extension)
    output_path = current_dir / "Example1_MarkdownTable.xlsx"
    
    # Convert to Excel
    print(f"Converting to Excel...")
    result_path = markdownTable_to_xlsx(
        markdown_table, 
        output_path=str(output_path),
        sheet_name="Bảng Cân Đối"
    )
    
    # Count rows for information
    rows = _parse_markdown_table(markdown_table)
    row_count = len(rows) - 1 if len(rows) > 1 else 0  # Exclude header
    
    print(f"Successfully saved to: {result_path}")
    print(f"   Total rows (excluding header): {row_count}")
    print(f"   Total columns: {len(rows[0]) if rows else 0}")

if __name__ == "__main__":
    main()