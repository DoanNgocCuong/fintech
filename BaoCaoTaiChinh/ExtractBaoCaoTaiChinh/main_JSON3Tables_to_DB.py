"""
Utility script: upload existing financial statement JSON files (3 types) into PostgreSQL.

Usage:
    python main_JSON3Tables_to_DB.py <json_file_or_folder> [--overwrite] [--no-recursive]

Responsibilities:
- Scan a single file or a directory (recursive by default)
- Parse stock symbol + year + quarter from file name
- Upload to appropriate database tables:
  - CanDoiKeToan → balance_sheet_raw
  - KetQuaHoatDongKinhDoanh → income_statement_raw
  - LuuChuyenTienTe → cash_flow_statement_raw

Filename patterns:
    STOCK_YYYY_1_QUARTER_*.json  → Extracts stock, year, and quarter
    STOCK_YYYY_*.json            → Extracts stock and year (quarter = None)

Examples:
    BIC_2024_1_5_1_CanDoiKeToan.json → stock=BIC, year=2024, quarter=5, table=balance_sheet_raw
    PGI_2024_1_3_KetQuaHoatDongKinhDoanh.json → stock=PGI, year=2024, quarter=3, table=income_statement_raw
    BIC_2024_1_5_1_LuuChuyenTienTe.json → stock=BIC, year=2024, quarter=5, table=cash_flow_statement_raw

The script intentionally skips any conversion from markdown/xlsx.
"""

import sys
import re
from pathlib import Path
from typing import Optional, Tuple, List
from dataclasses import dataclass
from datetime import datetime

from utils_database_manager import (
    upload_json_to_db,
    DB_CONFIG,
    TABLE_NAME as BALANCE_SHEET_TABLE,
)

# Table names for different financial statements
INCOME_STATEMENT_TABLE = 'income_statement_raw'
CASH_FLOW_STATEMENT_TABLE = 'cash_flow_statement_raw'

# Dedicated tables for income statement sections
INCOME_SECTION_TABLES = {
    "P1": "income_statement_p1_raw",
    "P2": "income_statement_p2_raw",
}
DEFAULT_INCOME_SECTION = "P2"


@dataclass
class FailedFile:
    """Information about a failed file."""
    filepath: str
    reason: str
    statement_type: str  # 'CanDoiKeToan', 'KetQuaHoatDongKinhDoanh', or 'LuuChuyenTienTe'


def parse_stock_year_quarter_from_filename(filename: str) -> Tuple[Optional[str], Optional[int], Optional[int]]:
    """
    Parse stock code, year, and quarter from filename.
    
    Naming convention examples (strict):
        STOCK_YYYY_1_QUARTER_*.json  → (STOCK, YYYY, QUARTER)
        STOCK_YYYY_1_5_1_*.json      → quarter = 5 (the number after YYYY_1_)
        STOCK_YYYY_1_3_*.json        → quarter = 3
    
    Args:
        filename: Filename to parse
        
    Returns:
        Tuple of (stock, year, quarter). quarter is None if not found.
    """
    stem = Path(filename).stem

    # Pattern 1: STOCK_YYYY_1_QUARTER_* (e.g., BIC_2024_1_5_1_CanDoiKeToan)
    # Extract quarter as the number after YYYY_1_
    pattern_with_quarter = r"^([A-Z]+)_(\d{4})_1_([1-5])_"
    match = re.match(pattern_with_quarter, stem)
    if match:
        stock = match.group(1)
        year = int(match.group(2))
        quarter = int(match.group(3))
        return stock, year, quarter

    return None, None, None


def parse_stock_year_quarter_from_foldername(foldername: str) -> Tuple[Optional[str], Optional[int], Optional[int]]:
    """
    Parse stock code, year, and quarter from folder name.
    
    Naming convention examples:
        PGI_2025_1_2_1_zip  → (PGI, 2025, 2)
        PGI_2025_1_2_1_rar  → (PGI, 2025, 2)
        BIC_2024_1_5_1_zip  → (BIC, 2024, 5)
        STOCK_YYYY_1_QUARTER_1_* → (STOCK, YYYY, QUARTER)
    
    Args:
        foldername: Folder name to parse
        
    Returns:
        Tuple of (stock, year, quarter). quarter is None if not found.
    """
    # Pattern 1: STOCK_YYYY_1_QUARTER_1_* (e.g., PGI_2025_1_2_1_zip, PGI_2025_1_2_1_rar)
    # Extract quarter as the number after YYYY_1_
    pattern_with_quarter = r"^([A-Z]+)_(\d{4})_1_([1-5])_1_"
    match = re.match(pattern_with_quarter, foldername)
    if match:
        stock = match.group(1)
        year = int(match.group(2))
        quarter = int(match.group(3))
        return stock, year, quarter

    # Pattern 2: STOCK_YYYY_1_QUARTER_* (fallback, without the trailing _1_)
    pattern_with_quarter_alt = r"^([A-Z]+)_(\d{4})_1_([1-5])_"
    match_alt = re.match(pattern_with_quarter_alt, foldername)
    if match_alt:
        stock = match_alt.group(1)
        year = int(match_alt.group(2))
        quarter = int(match_alt.group(3))
        return stock, year, quarter

    return None, None, None


def detect_statement_type(filename: str) -> Optional[str]:
    """
    Detect financial statement type from filename.
    
    Args:
        filename: Filename to check
        
    Returns:
        'CanDoiKeToan', 'KetQuaHoatDongKinhDoanh', 'LuuChuyenTienTe', or None
    """
    if "CanDoiKeToan" in filename:
        return "CanDoiKeToan"
    elif "KetQuaHoatDongKinhDoanh" in filename:
        return "KetQuaHoatDongKinhDoanh"
    elif "LuuChuyenTienTe" in filename:
        return "LuuChuyenTienTe"
    return None


def get_table_name(statement_type: str) -> str:
    """
    Get database table name for statement type.
    
    Args:
        statement_type: 'CanDoiKeToan', 'KetQuaHoatDongKinhDoanh', or 'LuuChuyenTienTe'
        
    Returns:
        Database table name
    """
    if statement_type == "CanDoiKeToan":
        return BALANCE_SHEET_TABLE
    elif statement_type == "KetQuaHoatDongKinhDoanh":
        return INCOME_STATEMENT_TABLE
    elif statement_type == "LuuChuyenTienTe":
        return CASH_FLOW_STATEMENT_TABLE
    else:
        raise ValueError(f"Unknown statement type: {statement_type}")


def detect_income_section_from_name(name: str) -> Optional[str]:
    """
    Detect income statement section (P1/P2) from a string.
    Returns None if no marker is found.
    """
    if not name:
        return None

    upper_name = name.upper()
    compact_name = upper_name.replace(" ", "").replace("-", "")

    p1_markers = ["_P1", "PHAN I", "PHAN 1", "PHAN-I", "PHAN-1"]
    p2_markers = ["_P2", "PHAN II", "PHAN 2", "PHAN-II", "PHAN-2"]

    if any(marker in upper_name for marker in p1_markers) or any(marker.replace(" ", "") in compact_name for marker in ["PHANI", "PHAN1"]):
        return "P1"
    if any(marker in upper_name for marker in p2_markers) or any(marker.replace(" ", "") in compact_name for marker in ["PHANII", "PHAN2"]):
        return "P2"
    return None


def resolve_income_section(json_path: Path) -> str:
    """
    Resolve section by inspecting file name and ancestor folders.
    Defaults to DEFAULT_INCOME_SECTION if no marker found.
    """
    candidates = [
        json_path.stem,
        json_path.name,
        json_path.parent.name if json_path.parent else "",
        json_path.parent.parent.name if json_path.parent and json_path.parent.parent else "",
    ]
    for candidate in candidates:
        section = detect_income_section_from_name(candidate)
        if section:
            return section
    return DEFAULT_INCOME_SECTION


def collect_json_files(target: Path, recursive: bool = True) -> List[Path]:
    """
    Collect JSON files from target path (all 3 types of financial statements).
    
    Args:
        target: File or directory path
        recursive: If True, recursively search subdirectories. Default: True.
        
    Returns:
        List of JSON file paths (all financial statement files)
    """
    if target.is_file():
        # Only return if it's a financial statement JSON file
        if target.suffix.lower() == ".json" and detect_statement_type(target.name):
            return [target]
        return []
    if target.is_dir():
        if recursive:
            # Recursive search: rglob searches all subdirectories
            # Filter: only financial statement files
            return sorted(p for p in target.rglob("*.json") 
                         if p.is_file() and detect_statement_type(p.name))
        else:
            # Non-recursive: only current directory level
            # Filter: only financial statement files
            return sorted(p for p in target.glob("*.json") 
                         if p.is_file() and detect_statement_type(p.name))
    return []


def process_json_files(json_files: List[Path], overwrite: bool) -> Tuple[int, int, List[FailedFile], dict]:
    """
    Process JSON files and upload to database.
    
    Returns:
        Tuple of (success_count, failed_count, failed_files_list, stats_by_table)
    """
    success = 0
    failed = 0
    failed_files: List[FailedFile] = []
    
    # Statistics by statement type
    stats_by_table = {
        BALANCE_SHEET_TABLE: {"label": "CanDoiKeToan", "success": 0, "failed": 0},
        INCOME_SECTION_TABLES["P1"]: {"label": "KetQuaHoatDongKinhDoanh (P1)", "success": 0, "failed": 0},
        INCOME_SECTION_TABLES["P2"]: {"label": "KetQuaHoatDongKinhDoanh (P2)", "success": 0, "failed": 0},
        CASH_FLOW_STATEMENT_TABLE: {"label": "LuuChuyenTienTe", "success": 0, "failed": 0},
    }

    total = len(json_files)
    for idx, json_file in enumerate(json_files, start=1):
        print("\n" + "=" * 80)
        print(f"Processing {idx}/{total}: {json_file.name}")
        print("=" * 80)

        # Detect statement type
        statement_type = detect_statement_type(json_file.name)
        if not statement_type:
            reason = f"Unknown financial statement type in filename: {json_file.name}"
            try:
                print(f"  ✗ {reason}")
            except UnicodeEncodeError:
                print(f"  [ERROR] {reason}")
            failed += 1
            failed_files.append(FailedFile(
                filepath=str(json_file),
                reason=reason,
                statement_type="Unknown"
            ))
            continue

        # Determine destination table (needed even if parsing fails)
        income_section = None
        if statement_type == "KetQuaHoatDongKinhDoanh":
            income_section = resolve_income_section(json_file)
            table_name = INCOME_SECTION_TABLES.get(income_section, INCOME_SECTION_TABLES[DEFAULT_INCOME_SECTION])
        else:
            table_name = get_table_name(statement_type)

        # Try to parse from filename first
        stock, year, quarter = parse_stock_year_quarter_from_filename(json_file.name)
        parse_source = "filename"
        
        # If parsing from filename failed, try parsing from parent folder name
        if stock is None or year is None:
            try:
                parent_folder = json_file.parent.name
                if parent_folder:  # Check if parent folder name is not empty
                    try:
                        print(f"  ⚠ Cannot parse from filename, trying parent folder: {parent_folder}")
                    except UnicodeEncodeError:
                        print(f"  [WARN] Cannot parse from filename, trying parent folder: {parent_folder}")
                    stock, year, quarter = parse_stock_year_quarter_from_foldername(parent_folder)
                    if stock is not None and year is not None:
                        parse_source = "parent folder"
            except Exception as e:
                try:
                    print(f"  ⚠ Error accessing parent folder: {e}")
                except UnicodeEncodeError:
                    print(f"  [WARN] Error accessing parent folder: {e}")
        
        # If still failed, try parsing from grandparent folder name (in case file is nested deeper)
        if stock is None or year is None:
            try:
                grandparent_path = json_file.parent.parent
                if grandparent_path.exists() and grandparent_path.name:  # Check if grandparent exists and has a name
                    grandparent_folder = grandparent_path.name
                    try:
                        print(f"  ⚠ Cannot parse from parent folder, trying grandparent folder: {grandparent_folder}")
                    except UnicodeEncodeError:
                        print(f"  [WARN] Cannot parse from parent folder, trying grandparent folder: {grandparent_folder}")
                    stock, year, quarter = parse_stock_year_quarter_from_foldername(grandparent_folder)
                    if stock is not None and year is not None:
                        parse_source = "grandparent folder"
            except Exception as e:
                try:
                    print(f"  ⚠ Error accessing grandparent folder: {e}")
                except UnicodeEncodeError:
                    print(f"  [WARN] Error accessing grandparent folder: {e}")
        
        # Final check: if still cannot parse, mark as failed
        if stock is None or year is None:
            folder_info = f" (folder: {json_file.parent.name})" if json_file.parent.name else ""
            reason = f"Cannot parse stock/year from filename or folder: {json_file.name}{folder_info}"
            try:
                print(f"  ✗ {reason}")
            except UnicodeEncodeError:
                print(f"  [ERROR] {reason}")
            failed += 1
            stats_bucket = stats_by_table.get(table_name)
            if stats_bucket:
                stats_bucket["failed"] += 1
            failed_files.append(FailedFile(
                filepath=str(json_file),
                reason=reason,
                statement_type=statement_type
            ))
            continue

        # Display parsed information
        quarter_info = f", quarter={quarter}" if quarter is not None else ", quarter=None"
        try:
            print(f"  Statement type: {statement_type}")
            section_info = f", section={income_section}" if income_section else ""
            print(f"  Parsed from {parse_source}: stock={stock}, year={year}{quarter_info}{section_info}")
            print(f"  Target table: {table_name}")
        except UnicodeEncodeError:
            print(f"  Statement type: {statement_type}")
            print(f"  Parsed from {parse_source}: stock={stock}, year={year}{quarter_info}")
            print(f"  Target table: {table_name}")

        upload_ok = upload_json_to_db(
            json_file=str(json_file),
            stock=stock,
            year=year,
            quarter=quarter,
            overwrite=overwrite,
            table_name=table_name,
            source_filename=json_file.name,
        )
        stats_bucket = stats_by_table.get(table_name)
        if upload_ok:
            success += 1
            if stats_bucket:
                stats_bucket["success"] += 1
            try:
                print(f"  ✓ Successfully uploaded to {table_name}")
            except UnicodeEncodeError:
                print(f"  [OK] Successfully uploaded to {table_name}")
        else:
            failed += 1
            if stats_bucket:
                stats_bucket["failed"] += 1
            failed_files.append(FailedFile(
                filepath=str(json_file),
                reason=f"Upload failed: stock={stock}, year={year}, quarter={quarter}",
                statement_type=statement_type
            ))
            try:
                print(f"  ✗ Upload failed")
            except UnicodeEncodeError:
                print(f"  [ERROR] Upload failed")

    return success, failed, failed_files, stats_by_table


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python main_JSON3Tables_to_DB.py <json_file_or_folder> [--no-overwrite] [--no-recursive]")
        print("\nOptions:")
        print("  --no-overwrite   Do NOT overwrite existing records in database (default: overwrite)")
        print("  --no-recursive   Only search current directory (disable recursive search)")
        print("\nSupported file types:")
        print("  - CanDoiKeToan (→ balance_sheet_raw)")
        print("  - KetQuaHoatDongKinhDoanh (→ income_statement_raw)")
        print("  - LuuChuyenTienTe (→ cash_flow_statement_raw)")
        sys.exit(1)

    # Mặc định: overwrite = True (ghi đè)
    # Chỉ tắt overwrite nếu có flag --no-overwrite
    overwrite = "--no-overwrite" not in sys.argv[2:]
    # Check for --no-recursive flag
    recursive = "--no-recursive" not in sys.argv[2:]
    target_path = Path(sys.argv[1])

    json_files = collect_json_files(target_path, recursive=recursive)
    if not json_files:
        print(f"No JSON files found at: {target_path}")
        sys.exit(1)

    # Count files by table destination
    table_file_counts = {
        BALANCE_SHEET_TABLE: 0,
        INCOME_SECTION_TABLES["P1"]: 0,
        INCOME_SECTION_TABLES["P2"]: 0,
        CASH_FLOW_STATEMENT_TABLE: 0,
    }
    for file_path in json_files:
        if "CanDoiKeToan" in file_path.name:
            table_key = BALANCE_SHEET_TABLE
        elif "KetQuaHoatDongKinhDoanh" in file_path.name:
            section = resolve_income_section(file_path)
            table_key = INCOME_SECTION_TABLES.get(section, INCOME_SECTION_TABLES[DEFAULT_INCOME_SECTION])
        elif "LuuChuyenTienTe" in file_path.name:
            table_key = CASH_FLOW_STATEMENT_TABLE
        else:
            continue
        if table_key in table_file_counts:
            table_file_counts[table_key] += 1

    print("=" * 80)
    print("DATABASE CONFIGURATION")
    print("=" * 80)
    print(f"Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"Database: {DB_CONFIG['database']}")
    print(f"Tables:")
    print(f"  - {BALANCE_SHEET_TABLE}: {table_file_counts[BALANCE_SHEET_TABLE]} file(s)")
    print(f"  - {INCOME_SECTION_TABLES['P1']}: {table_file_counts[INCOME_SECTION_TABLES['P1']]} file(s)")
    print(f"  - {INCOME_SECTION_TABLES['P2']}: {table_file_counts[INCOME_SECTION_TABLES['P2']]} file(s)")
    print(f"  - {CASH_FLOW_STATEMENT_TABLE}: {table_file_counts[CASH_FLOW_STATEMENT_TABLE]} file(s)")
    print(f"Overwrite mode: {overwrite}")
    print(f"Recursive search: {recursive}")
    print("=" * 80)

    success, failed, failed_files, stats_by_table = process_json_files(json_files, overwrite)

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total JSON files: {len(json_files)}")
    print(f"Successful uploads: {success}")
    print(f"Failed uploads: {failed}")
    print("\nBreakdown by table:")
    for table_name, stats in stats_by_table.items():
        label = stats.get("label", table_name)
        print(f"  {label} ({table_name}):")
        print(f"    Success: {stats['success']}")
        print(f"    Failed: {stats['failed']}")
    
    # Write failed files to fail_3Tables.txt
    if failed_files:
        fail_log_path = Path("fail_3Tables.txt")
        try:
            with open(fail_log_path, "w", encoding="utf-8") as f:
                f.write("=" * 80 + "\n")
                f.write("FAILED FILES LOG - 3 FINANCIAL STATEMENTS\n")
                f.write("=" * 80 + "\n")
                f.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total failed files: {len(failed_files)}\n")
                f.write("=" * 80 + "\n\n")
                
                # Group by statement type
                by_type = {}
                for failed_file in failed_files:
                    stmt_type = failed_file.statement_type
                    if stmt_type not in by_type:
                        by_type[stmt_type] = []
                    by_type[stmt_type].append(failed_file)
                
                for stmt_type, files in by_type.items():
                    f.write(f"\n{stmt_type} ({len(files)} file(s)):\n")
                    f.write("-" * 80 + "\n")
                    for idx, failed_file in enumerate(files, start=1):
                        f.write(f"{idx}. {failed_file.filepath}\n")
                        f.write(f"   Reason: {failed_file.reason}\n\n")
            
            try:
                print(f"\n✓ Failed files logged to: {fail_log_path.absolute()}")
            except UnicodeEncodeError:
                print(f"\n[OK] Failed files logged to: {fail_log_path.absolute()}")
        except Exception as e:
            try:
                print(f"\n✗ Error writing to fail_3Tables.txt: {e}")
            except UnicodeEncodeError:
                print(f"\n[ERROR] Error writing to fail_3Tables.txt: {e}")
    
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()

