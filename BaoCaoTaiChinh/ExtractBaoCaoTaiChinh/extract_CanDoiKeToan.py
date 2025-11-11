"""
Code extract các bảng cân đối kế toán từ file markdown báo cáo tài chính. 

Input: 1 file markdown báo cáo tài chính. 
Output: 1 file .csv gồm 4 bảng của cân đối kế toán: 
- A. Tài sản ngắn hạn
- B. Tài sản dài hạn
- C. Nợ phải trả
- D. Vốn chủ sở hữu

"""

import re
import csv
import sys
from pathlib import Path
from typing import Optional


def find_balance_sheet_section(content: str) -> Optional[str]:
    """
    Tìm phần bảng cân đối kế toán trong file markdown.
    
    Args:
        content: Nội dung file markdown
        
    Returns:
        Phần nội dung chứa bảng cân đối kế toán hoặc None
    """
    # Tìm vị trí bắt đầu
    start_patterns = [
        r'BẢNG CÂN ĐỐI KẾ TOÁN',
        r'Bảng cân đối kế toán',
    ]
    
    start_pos = None
    for pattern in start_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            start_pos = match.start()
            break
    
    if start_pos is None:
        return None
    
    # Tìm dòng bắt đầu thực sự (từ dòng có "BẢNG CÂN ĐỐI KẾ TOÁN")
    # Có thể có text trước đó, nên tìm dòng chứa pattern này
    lines_before = content[:start_pos].split('\n')
    lines_after = content[start_pos:].split('\n')
    
    # Tìm dòng đầu tiên sau start_pos chứa "BẢNG CÂN ĐỐI KẾ TOÁN"
    actual_start_idx = 0
    for i, line in enumerate(lines_after):
        if 'BẢNG CÂN ĐỐI KẾ TOÁN' in line.upper() or 'Bảng cân đối kế toán' in line:
            actual_start_idx = i
            break
    
    # Lấy từ dòng đó trở đi
    lines = lines_after[actual_start_idx:]
    end_line_idx = len(lines)
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        
        # Kiểm tra nếu là phần báo cáo mới (không phải tiếp theo của bảng cân đối)
        if any(pattern in line_lower for pattern in ['báo cáo kết quả hoạt động', 'báo cáo lưu chuyển tiền tệ']):
            # Kiểm tra context xung quanh
            look_back = max(0, i - 5)
            context = '\n'.join(lines[look_back:i]).lower()
            
            # Nếu không có "tiếp theo" hoặc "bảng cân đối" trong context gần đó
            if 'tiếp theo' not in context and 'bảng cân đối' not in context[-100:]:
                # Tìm dòng "---" gần nhất trước đó
                for j in range(i - 1, max(0, i - 10), -1):
                    if lines[j].strip() == '---':
                        end_line_idx = j
                        break
                else:
                    end_line_idx = i
                break
    
    # Nếu không tìm thấy, tìm "TỔNG CỘNG NGUỒN VỐN" và lấy thêm một vài dòng sau đó
    if end_line_idx == len(lines):
        for i, line in enumerate(lines):
            if 'TỔNG CỘNG NGUỒN VỐN' in line.upper():
                # Tìm dòng "---" tiếp theo
                for j in range(i + 1, min(len(lines), i + 20)):
                    if lines[j].strip() == '---':
                        end_line_idx = j + 1
                        break
                break
    
    return '\n'.join(lines[:end_line_idx])


def extract_markdown_tables(content: str) -> list:
    """
    Extract tất cả các markdown tables từ content.
    Chỉ lấy các bảng có header chứa "Mã số" (bảng cân đối kế toán).
    
    Args:
        content: Nội dung chứa markdown tables
        
    Returns:
        List các tables (mỗi table là list các dòng)
    """
    tables = []
    lines = content.split('\n')
    
    current_table = []
    in_table = False
    has_valid_header = False
    
    for line in lines:
        stripped = line.strip()
        
        # Bắt đầu table
        if stripped.startswith('|') and '---' not in stripped:
            if not in_table:
                in_table = True
                current_table = []
                has_valid_header = False
            
            current_table.append(line)
            
            # Kiểm tra nếu là header row có chứa "Mã số"
            # Parse cells
            parts = stripped.split('|')
            cells = [cell.strip() for cell in parts[1:]]
            if cells and not cells[-1].strip():
                cells = cells[:-1]
            
            if cells:
                row_text = ' '.join(cells).lower()
                if 'mã số' in row_text or ('mã' in row_text and 'số' in row_text):
                    has_valid_header = True
        
        # Dòng separator
        elif stripped.startswith('|---'):
            if in_table:
                current_table.append(line)
        
        # Kết thúc table
        else:
            if in_table and current_table and has_valid_header:
                # Chỉ lấy table có header hợp lệ và có ít nhất header + separator + 1 data row
                if len(current_table) > 2:
                    tables.append(current_table)
            in_table = False
            current_table = []
            has_valid_header = False
    
    # Xử lý table cuối cùng
    if in_table and current_table and has_valid_header and len(current_table) > 2:
        tables.append(current_table)
    
    return tables


def parse_table_to_csv_rows(table_lines: list) -> list:
    """
    Parse markdown table thành list các rows cho CSV.
    
    Args:
        table_lines: List các dòng của markdown table
        
    Returns:
        List các rows (mỗi row là list các cells)
    """
    rows = []
    
    for line in table_lines:
        stripped = line.strip()
        # Bỏ qua separator
        if stripped.startswith('|---'):
            continue
        
        if stripped.startswith('|'):
            # Parse cells
            cells = [cell.strip() for cell in stripped.split('|')[1:-1]]
            if cells:
                rows.append(cells)
    
    return rows


def write_tables_to_csv(tables: list, output_path: Path):
    """
    Ghi các tables ra file CSV.
    
    Args:
        tables: List các tables
        output_path: Đường dẫn file output CSV
    """
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        
        for table_idx, table_lines in enumerate(tables):
            # Parse table thành rows
            rows = parse_table_to_csv_rows(table_lines)
            
            if not rows:
                continue
            
            # Ghi header nếu là table đầu tiên
            if table_idx == 0 and rows:
                # Sử dụng row đầu tiên làm header
                writer.writerow(rows[0])
            
            # Ghi các data rows (bỏ qua header nếu đã ghi)
            start_row = 0 if table_idx == 0 else 1
            for row in rows[start_row:]:
                writer.writerow(row)
            
            # Thêm dòng trống giữa các tables
            if table_idx < len(tables) - 1:
                writer.writerow([])


def main(input_file: str, output_file: Optional[str] = None):
    """
    Main function để extract bảng cân đối kế toán.
    
    Args:
        input_file: Đường dẫn file markdown input
        output_file: Đường dẫn file CSV output (nếu None thì tự generate)
    """
    input_path = Path(input_file)
    
    if not input_path.exists():
        print(f"Error: File not found: {input_file}")
        return
    
    # Đọc file
    print(f"Reading file: {input_file}")
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Tìm phần bảng cân đối kế toán
    print("Finding balance sheet section...")
    balance_sheet_content = find_balance_sheet_section(content)
    
    if not balance_sheet_content:
        print("Error: Could not find balance sheet section")
        return
    
    print(f"Found balance sheet section ({len(balance_sheet_content)} characters)")
    
    # Extract các markdown tables
    print("Extracting markdown tables...")
    tables = extract_markdown_tables(balance_sheet_content)
    print(f"Found {len(tables)} table(s)")
    
    if not tables:
        print("Warning: No tables found in balance sheet section")
        return
    
    # Generate output file name nếu chưa có
    if output_file is None:
        output_path = input_path.parent / f"{input_path.stem}_CanDoiKeToan.csv"
    else:
        output_path = Path(output_file)
    
    # Ghi ra CSV
    print(f"Writing to CSV: {output_path}")
    write_tables_to_csv(tables, output_path)
    
    print("Done!")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python extract_CanDoiKeToan.py <input_markdown_file> [output_csv_file]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    main(input_file, output_file)
