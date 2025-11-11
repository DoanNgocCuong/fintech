"""
Utility script: upload existing balance-sheet JSON files into PostgreSQL.

Usage:
    python main_JSONCanDoiKeToan_to_DB.py <json_file_or_folder> [--overwrite]

Responsibilities:
- Scan a single file or a directory (recursive disabled; only current level)
- Parse stock symbol + year from file name
- Delegate upload to utils_database_manager.upload_json_to_db

The script intentionally skips any conversion from markdown/xlsx.
"""

import sys
import re
from pathlib import Path
from typing import Optional, Tuple, List

from utils_database_manager import (
    upload_json_to_db,
    DB_CONFIG,
    TABLE_NAME,
)


def parse_stock_and_year_from_filename(filename: str) -> Tuple[Optional[str], Optional[int]]:
    """
    Parse stock code and year based on naming convention:
        STOCK_YYYY_*.json
    Accepts both underscore and dash separators before the year.
    """
    stem = Path(filename).stem

    pattern = r"^([A-Z]+)_(\d{4})_"
    match = re.match(pattern, stem)
    if match:
        return match.group(1), int(match.group(2))

    pattern_fallback = r"^([A-Z]+)[_-](\d{4})"
    match_fallback = re.match(pattern_fallback, stem)
    if match_fallback:
        return match_fallback.group(1), int(match_fallback.group(2))

    return None, None


def collect_json_files(target: Path) -> List[Path]:
    if target.is_file():
        return [target] if target.suffix.lower() == ".json" else []
    if target.is_dir():
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

        stock, year = parse_stock_and_year_from_filename(json_file.name)
        if stock is None or year is None:
            print(f"  ✗ Cannot parse stock/year from filename: {json_file.name}")
            failed += 1
            continue

        upload_ok = upload_json_to_db(
            json_file=str(json_file),
            stock=stock,
            year=year,
            overwrite=overwrite,
        )
        if upload_ok:
            success += 1
        else:
            failed += 1

    return success, failed


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python main_JSONCanDoiKeToan_to_DB.py <json_file_or_folder> [--overwrite]")
        sys.exit(1)

    overwrite = "--overwrite" in sys.argv[2:]
    target_path = Path(sys.argv[1])

    json_files = collect_json_files(target_path)
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


