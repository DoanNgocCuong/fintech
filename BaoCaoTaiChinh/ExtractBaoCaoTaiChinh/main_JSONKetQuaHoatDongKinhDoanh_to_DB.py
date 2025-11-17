"""
Utility script: upload existing income statement JSON files into PostgreSQL.

Usage:
    python main_JSONKetQuaHoatDongKinhDoanh_to_DB.py <json_file_or_folder> [--no-overwrite] [--no-recursive]

Responsibilities:
- Scan a single file or a directory (recursive by default)
- Parse stock symbol + year + quarter from file name
- Delegate upload to utils_database_manager.upload_json_to_db

Filename patterns:
    STOCK_YYYY_1_QUARTER_*.json  → Extracts stock, year, and quarter
    STOCK_YYYY_*.json            → Extracts stock and year (quarter = None)

Examples:
    BIC_2024_1_5_1_KetQuaHoatDongKinhDoanh.json → stock=BIC, year=2024, quarter=5
    PGI_2024_1_3_KetQuaHoatDongKinhDoanh.json   → stock=PGI, year=2024, quarter=3

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
)

# Table name for income statements
TABLE_NAME = 'income_statement_raw'


@dataclass
class FailedFile:
    """Information about a failed file."""
    filepath: str
    reason: str


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

    # Pattern 1: STOCK_YYYY_1_QUARTER_* (e.g., BIC_2024_1_5_1_KetQuaHoatDongKinhDoanh)
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


def collect_json_files(target: Path, recursive: bool = True) -> List[Path]:
    """
    Collect JSON files from target path (only income statement files).
    
    Args:
        target: File or directory path
        recursive: If True, recursively search subdirectories. Default: True.
        
    Returns:
        List of JSON file paths (only income statement files)
    """
    if target.is_file():
        # Only return if it's an income statement JSON file
        if target.suffix.lower() == ".json" and "KetQuaHoatDongKinhDoanh" in target.name:
            return [target]
        return []
    if target.is_dir():
        if recursive:
            # Recursive search: rglob searches all subdirectories
            # Filter: only income statement files
            return sorted(p for p in target.rglob("*.json") 
                         if p.is_file() and "KetQuaHoatDongKinhDoanh" in p.name)
        else:
            # Non-recursive: only current directory level
            # Filter: only income statement files
            return sorted(p for p in target.glob("*.json") 
                         if p.is_file() and "KetQuaHoatDongKinhDoanh" in p.name)
    return []


def process_json_files(json_files: List[Path], overwrite: bool) -> Tuple[int, int, List[FailedFile]]:
    """
    Process JSON files and upload to database.
    
    Returns:
        Tuple of (success_count, failed_count, failed_files_list)
    """
    success = 0
    failed = 0
    failed_files: List[FailedFile] = []

    total = len(json_files)
    for idx, json_file in enumerate(json_files, start=1):
        print("\n" + "=" * 80)
        print(f"Processing {idx}/{total}: {json_file.name}")
        print("=" * 80)

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
            failed_files.append(FailedFile(
                filepath=str(json_file),
                reason=reason
            ))
            continue

        # Display parsed information
        quarter_info = f", quarter={quarter}" if quarter is not None else ", quarter=None"
        print(f"  Parsed from {parse_source}: stock={stock}, year={year}{quarter_info}")

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
            failed_files.append(FailedFile(
                filepath=str(json_file),
                reason=f"Upload failed: stock={stock}, year={year}, quarter={quarter}"
            ))

    return success, failed, failed_files


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python main_JSONKetQuaHoatDongKinhDoanh_to_DB.py <json_file_or_folder> [--no-overwrite] [--no-recursive]")
        print("\nOptions:")
        print("  --no-overwrite   Do NOT overwrite existing records (default: overwrite)")
        print("  --no-recursive   Only search current directory (disable recursive search)")
        sys.exit(1)

    extra_args = sys.argv[2:]
    overwrite = True
    if "--no-overwrite" in extra_args:
        overwrite = False
    elif "--overwrite" in extra_args:
        overwrite = True
    # Check for --no-recursive flag
    recursive = "--no-recursive" not in extra_args
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

    success, failed, failed_files = process_json_files(json_files, overwrite)

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total JSON files: {len(json_files)}")
    print(f"Successful uploads: {success}")
    print(f"Failed uploads: {failed}")
    
    # Write failed files to fail_KetQuaHoatDongKinhDoanh.txt
    if failed_files:
        fail_log_path = Path("fail_KetQuaHoatDongKinhDoanh.txt")
        try:
            with open(fail_log_path, "w", encoding="utf-8") as f:
                f.write("=" * 80 + "\n")
                f.write("FAILED FILES LOG - KET QUA HOAT DONG KINH DOANH\n")
                f.write("=" * 80 + "\n")
                f.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total failed files: {len(failed_files)}\n")
                f.write("=" * 80 + "\n\n")
                
                for idx, failed_file in enumerate(failed_files, start=1):
                    f.write(f"{idx}. {failed_file.filepath}\n")
                    f.write(f"   Reason: {failed_file.reason}\n\n")
            
            try:
                print(f"\n✓ Failed files logged to: {fail_log_path.absolute()}")
            except UnicodeEncodeError:
                print(f"\n[OK] Failed files logged to: {fail_log_path.absolute()}")
        except Exception as e:
            try:
                print(f"\n✗ Error writing to fail_KetQuaHoatDongKinhDoanh.txt: {e}")
            except UnicodeEncodeError:
                print(f"\n[ERROR] Error writing to fail_KetQuaHoatDongKinhDoanh.txt: {e}")
    
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
