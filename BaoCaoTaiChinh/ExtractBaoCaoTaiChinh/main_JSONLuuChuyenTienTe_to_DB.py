"""
Utility script: upload existing cash flow statement JSON files into PostgreSQL.

Usage:
    python main_JSONLuuChuyenTienTe_to_DB.py <json_file_or_folder> [--overwrite] [--no-recursive]

Responsibilities:
- Scan a single file or a directory (recursive by default)
- Parse stock symbol + year + quarter from file name
- Delegate upload to utils_database_manager.upload_json_to_db

Filename patterns:
    STOCK_YYYY_1_QUARTER_*.json  → Extracts stock, year, and quarter
    STOCK_YYYY_*.json            → Extracts stock and year (quarter = None)

Examples:
    BIC_2024_1_5_1_LuuChuyenTienTe.json → stock=BIC, year=2024, quarter=5
    PGI_2024_1_3_LuuChuyenTienTe.json   → stock=PGI, year=2024, quarter=3

The script intentionally skips any conversion from markdown/xlsx.
"""

import sys
import re
from pathlib import Path
from typing import Optional, Tuple, List

from utils_database_manager import (
    upload_json_to_db,
    DB_CONFIG,
)

# Table name for cash flow statements
TABLE_NAME = 'cash_flow_statement_raw'


def parse_stock_year_quarter_from_filename(filename: str) -> Tuple[Optional[str], Optional[int], Optional[int]]:
    """
    Parse stock code, year, and quarter from filename.
    
    Naming convention examples:
        STOCK_YYYY_1_QUARTER_*.json  → (STOCK, YYYY, QUARTER)
        STOCK_YYYY_*.json            → (STOCK, YYYY, None)
        STOCK_YYYY_1_5_1_*.json      → quarter = 5 (the number after YYYY_1_)
        STOCK_YYYY_1_3_*.json        → quarter = 3
    
    Args:
        filename: Filename to parse
        
    Returns:
        Tuple of (stock, year, quarter). quarter is None if not found.
    """
    stem = Path(filename).stem

    # Pattern 1: STOCK_YYYY_1_QUARTER_* (e.g., BIC_2024_1_5_1_LuuChuyenTienTe)
    # Extract quarter as the number after YYYY_1_
    pattern_with_quarter = r"^([A-Z]+)_(\d{4})_1_(\d+)_"
    match = re.match(pattern_with_quarter, stem)
    if match:
        stock = match.group(1)
        year = int(match.group(2))
        quarter = int(match.group(3))
        return stock, year, quarter

    # Pattern 2: STOCK_YYYY_* (fallback, no quarter)
    pattern_basic = r"^([A-Z]+)_(\d{4})_"
    match_basic = re.match(pattern_basic, stem)
    if match_basic:
        return match_basic.group(1), int(match_basic.group(2)), None

    # Pattern 3: STOCK_YYYY (with dash or underscore, no quarter)
    pattern_fallback = r"^([A-Z]+)[_-](\d{4})"
    match_fallback = re.match(pattern_fallback, stem)
    if match_fallback:
        return match_fallback.group(1), int(match_fallback.group(2)), None

    return None, None, None


def collect_json_files(target: Path, recursive: bool = True) -> List[Path]:
    """
    Collect JSON files from target path.
    
    Args:
        target: File or directory path
        recursive: If True, recursively search subdirectories. Default: True.
        
    Returns:
        List of JSON file paths
    """
    if target.is_file():
        return [target] if target.suffix.lower() == ".json" else []
    if target.is_dir():
        if recursive:
            # Recursive search: rglob searches all subdirectories
            return sorted(p for p in target.rglob("*.json") if p.is_file())
        else:
            # Non-recursive: only current directory level
            return sorted(p for p in target.glob("*.json") if p.is_file())
    return []


def process_json_files(json_files: List[Path], overwrite: bool) -> Tuple[int, int]:
    success = 0
    failed = 0

    total = len(json_files)
    for idx, json_file in enumerate(json_files, start=1):
        print("\n" + "=" * 80)
        print(f"Processing {idx}/{total}: {json_file.name}")
        print("=" * 80)

        stock, year, quarter = parse_stock_year_quarter_from_filename(json_file.name)
        if stock is None or year is None:
            print(f"  ✗ Cannot parse stock/year from filename: {json_file.name}")
            failed += 1
            continue

        # Display parsed information
        quarter_info = f", quarter={quarter}" if quarter is not None else ", quarter=None"
        print(f"  Parsed: stock={stock}, year={year}{quarter_info}")

        upload_ok = upload_json_to_db(
            json_file=str(json_file),
            stock=stock,
            year=year,
            quarter=quarter,
            overwrite=overwrite,
            table_name=TABLE_NAME,
            source_filename=json_file.name,
        )
        if upload_ok:
            success += 1
        else:
            failed += 1

    return success, failed


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python main_JSONLuuChuyenTienTe_to_DB.py <json_file_or_folder> [--overwrite] [--no-recursive]")
        print("\nOptions:")
        print("  --overwrite      Overwrite existing records in database")
        print("  --no-recursive   Only search current directory (disable recursive search)")
        sys.exit(1)

    overwrite = "--overwrite" in sys.argv[2:]
    # Check for --no-recursive flag
    recursive = "--no-recursive" not in sys.argv[2:]
    target_path = Path(sys.argv[1])

    json_files = collect_json_files(target_path, recursive=recursive)
    if not json_files:
        print(f"No JSON files found at: {target_path}")
        sys.exit(1)

    print("=" * 80)
    print("DATABASE CONFIGURATION")
    print("=" * 80)
    print(f"Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"Database: {DB_CONFIG['database']}")
    print(f"Table: {TABLE_NAME}")
    print(f"Overwrite mode: {overwrite}")
    print(f"Recursive search: {recursive}")
    print("=" * 80)

    success, failed = process_json_files(json_files, overwrite)

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total JSON files: {len(json_files)}")
    print(f"Successful uploads: {success}")
    print(f"Failed uploads: {failed}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()

