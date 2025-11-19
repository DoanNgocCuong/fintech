"""
Main Entry Point - Calculate all 57 indicators for a stock.

This is the main entry point for calculating all indicators.
Provides command-line interface and programmatic API.
"""

import sys
import os
from pathlib import Path

# Add parent directory to Python path to allow imports
# This allows running the script from any directory
script_dir = Path(__file__).parent.absolute()
parent_dir = script_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

import argparse
import json
from typing import Optional, Dict, Any

from Gen57Metrics.indicator_calculator import (
    IndicatorCalculator,
    calculate_all_indicators,
    calculate_selected_indicators,
)
from Gen57Metrics.indicator_result_repository import save_indicator_result_payload


def main():
    """
    Main entry point for command-line usage.
    
    Example:
        python calculate_all_indicators.py MIG 2024
        python calculate_all_indicators.py MIG 2024 --quarter 2
        python calculate_all_indicators.py MIG 2024 --output result.json
    """
    parser = argparse.ArgumentParser(
        description="Calculate all 57 indicators for a stock",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Calculate annual indicators for MIG in 2024
  python calculate_all_indicators.py MIG 2024
  
  # Calculate quarterly indicators for Q2 2024
  python calculate_all_indicators.py MIG 2024 --quarter 2
  
  # Save results to JSON file
  python calculate_all_indicators.py MIG 2024 --output result.json
  
  # Pretty print results
  python calculate_all_indicators.py MIG 2024 --pretty
        """
    )
    
    parser.add_argument(
        "--stock", "-s",
        type=str,
        required=True,
        help="Stock symbol (e.g., MIG, PGI, BIC)"
    )
    
    parser.add_argument(
        "--year", "-y",
        type=int,
        required=True,
        help="Year (e.g., 2024)"
    )
    
    parser.add_argument(
        "--quarter", "-q",
        type=int,
        required=True,
        help="Quarter (1-5, Q5 = annual report)"
    )

    parser.add_argument(
        "--indicator", "-i",
        action="append",
        dest="indicators",
        default=None,
        help="Tên indicator muốn tính (có thể truyền nhiều lần). Ví dụ: --indicator CFO --indicator 'Net Income (NI)'"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output JSON file path (optional)"
    )
    
    parser.add_argument(
        "--pretty", "-p",
        action="store_true",
        help="Pretty print JSON output"
    )
    
    parser.add_argument(
        "--no-metadata",
        action="store_true",
        help="Exclude calculation metadata from output"
    )

    parser.add_argument(
        "--db-table",
        type=str,
        default=None,
        help="Custom table name (default: indicator_57)"
    )

    parser.add_argument(
        "--skip-db",
        action="store_true",
        help="Skip saving results to database"
    )
    
    args = parser.parse_args()
    
    # Validate quarter (1-4 for standard quarters, 5 for annual roll-up)
    if args.quarter < 1 or args.quarter > 5:
        print(f"Error: Quarter must be between 1 and 5 (Q5 = annual), got {args.quarter}", file=sys.stderr)
        return 1
    
    # Calculate all indicators
    if args.indicators:
        indicator_list = ", ".join(args.indicators)
        print(f"Tính các indicator [{indicator_list}] cho {args.stock} - Year {args.year}", end="")
    else:
        print(f"Calculating 57 indicators for {args.stock} - Year {args.year}", end="")
    if args.quarter:
        print(f" Q{args.quarter}")
    else:
        print(" (Annual)")
    
    try:
        if args.indicators:
            result = calculate_selected_indicators(
                indicator_names=args.indicators,
                stock=args.stock,
                year=args.year,
                quarter=args.quarter,
                include_metadata=not args.no_metadata
            )
        else:
            result = calculate_all_indicators(
                stock=args.stock,
                year=args.year,
                quarter=args.quarter,
                include_metadata=not args.no_metadata
            )

        # Clone result and remove metadata before persisting to DB
        json_payload = dict(result)
        json_payload.pop("metadata", None)

        row_payload = {
            "stock": result.get("stock", args.stock).upper(),
            "year": int(result.get("year", args.year)),
            "quarter": int(result.get("quarter") if result.get("quarter") is not None else args.quarter),
            "json_raw": json_payload,
        }
        
        # Print summary
        if args.no_metadata:
            metadata = {}
        else:
            metadata = result.get("metadata", {})
        
        if metadata:
            print("\n[OK] Calculation completed:")
            total_key = "total_indicators" if "total_indicators" in metadata else "requested"
            total_label = "Total indicators" if total_key == "total_indicators" else "Requested indicators"
            print(f"  {total_label}: {metadata.get(total_key, 0)}")
            print(f"  Successful: {metadata.get('successful', 0)}")
            print(f"  Failed: {metadata.get('failed', 0)}")
            
            if metadata.get('failed_list'):
                print(f"\n  Failed indicators: {', '.join(metadata['failed_list'][:5])}")
                if len(metadata['failed_list']) > 5:
                    print(f"  ... and {len(metadata['failed_list']) - 5} more")
        
        # Output results
        output_json = json.dumps(row_payload, indent=2 if args.pretty else None, ensure_ascii=False)
        
        if args.output:
            output_path = Path(args.output)
        else:
            results_dir = script_dir / "results"
            results_dir.mkdir(parents=True, exist_ok=True)
            q_suffix = f"_Q{args.quarter}" if args.quarter else "_Annual"
            mode_suffix = "_subset" if args.indicators else "_all"
            default_name = f"{args.stock.upper()}_{args.year}{q_suffix}{mode_suffix}.json"
            output_path = results_dir / default_name

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output_json)
        print(f"\n[OK] Results saved to {output_path}")

        # Still print JSON for console visibility
        print(f"\n{output_json}")

        if not args.skip_db:
            rows_written = save_indicator_result_payload(row_payload, table_name=args.db_table)
            table_display = args.db_table or "indicator_57"
            print(f"\n[OK] {rows_written} indicator rows persisted to table '{table_display}'")
        
        # Return success
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def calculate_indicators_for_stock(
    stock: str,
    year: int,
    quarter: Optional[int] = None,
    include_metadata: bool = True
) -> Dict[str, Any]:
    """
    Calculate all indicators for a stock (programmatic API).
    
    This is a convenience wrapper around calculate_all_indicators().
    
    Args:
        stock: Stock symbol (e.g., "MIG", "PGI")
        year: Year (e.g., 2024)
        quarter: Quarter (1-4) or None for annual
        include_metadata: Whether to include calculation metadata
        
    Returns:
        Dictionary with all indicators and metadata
        
    Example:
        >>> result = calculate_indicators_for_stock("MIG", 2024)
        >>> cfo = result["indicators"]["CFO"]
        >>> print(f"CFO: {cfo}")
        CFO: 1234567890.0
    """
    return calculate_all_indicators(stock, year, quarter, include_metadata)


if __name__ == "__main__":
    sys.exit(main())

