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

from Gen57Metrics.indicator_calculator import IndicatorCalculator, calculate_all_indicators
from Gen57Metrics.indicator_registry import get_registry


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
        "stock",
        type=str,
        help="Stock symbol (e.g., MIG, PGI, BIC)"
    )
    
    parser.add_argument(
        "year",
        type=int,
        help="Year (e.g., 2024)"
    )
    
    parser.add_argument(
        "--quarter", "-q",
        type=int,
        default=None,
        help="Quarter (1-4) or omit for annual report"
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
    
    args = parser.parse_args()
    
    # Validate quarter
    if args.quarter is not None:
        if args.quarter < 1 or args.quarter > 4:
            print(f"Error: Quarter must be between 1 and 4, got {args.quarter}", file=sys.stderr)
            return 1
    
    # Calculate all indicators
    print(f"Calculating 57 indicators for {args.stock} - Year {args.year}", end="")
    if args.quarter:
        print(f" Q{args.quarter}")
    else:
        print(" (Annual)")
    
    try:
        result = calculate_all_indicators(
            stock=args.stock,
            year=args.year,
            quarter=args.quarter,
            include_metadata=not args.no_metadata
        )
        
        # Print summary
        if args.no_metadata:
            metadata = {}
        else:
            metadata = result.get("metadata", {})
        
        if metadata:
            try:
                print(f"\n✓ Calculation completed:")
            except UnicodeEncodeError:
                print(f"\n[OK] Calculation completed:")
            print(f"  Total indicators: {metadata.get('total_indicators', 0)}")
            print(f"  Successful: {metadata.get('successful', 0)}")
            print(f"  Failed: {metadata.get('failed', 0)}")
            
            if metadata.get('failed_list'):
                print(f"\n  Failed indicators: {', '.join(metadata['failed_list'][:5])}")
                if len(metadata['failed_list']) > 5:
                    print(f"  ... and {len(metadata['failed_list']) - 5} more")
        
        # Output results
        output_json = json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False)
        
        if args.output:
            # Save to file
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output_json)
            try:
                print(f"\n✓ Results saved to {args.output}")
            except UnicodeEncodeError:
                print(f"\n[OK] Results saved to {args.output}")
        else:
            # Print to stdout
            print(f"\n{output_json}")
        
        # Return success
        return 0
        
    except Exception as e:
        try:
            print(f"\n✗ Error: {e}", file=sys.stderr)
        except UnicodeEncodeError:
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

