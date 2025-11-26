"""
Main Batch Runner - Calculate indicators for multiple stocks.

This script runs calculate_all_indicators.py for a batch of stocks.
Supports reading stocks from file, command line, or database.
"""

import sys
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
import argparse
import json
from datetime import datetime

# Add parent directory to Python path
script_dir = Path(__file__).parent.absolute()
parent_dir = script_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from Gen57Metrics.indicator_calculator import calculate_all_indicators
from Gen57Metrics.utils_database_manager import connect
from Gen57Metrics.indicator_result_repository import save_indicator_result_payload


def get_stocks_from_database() -> List[str]:
    """
    Lấy danh sách tất cả mã cổ phiếu từ bảng 'company' trong database.
    
    Returns:
        List[str]: Danh sách mã cổ phiếu (uppercase)
    """
    try:
        import psycopg2
        from Gen57Metrics.utils_database_manager import connect
    except ImportError:
        print("Warning: psycopg2 not available. Cannot fetch stocks from database.")
        return []
    
    conn = None
    cursor = None
    try:
        conn = connect()
        cursor = conn.cursor()
        
        query = """
        SELECT DISTINCT company_name
        FROM company
        WHERE company_name IS NOT NULL
        ORDER BY company_name
        """
        cursor.execute(query)
        results = cursor.fetchall()
        
        stocks = [row[0].upper() for row in results if row[0]]
        return stocks
    except Exception as e:
        print(f"Error fetching stocks from database: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_years_from_database(stock: str, table_name: str = "balance_sheet_raw") -> List[int]:
    """
    Lấy danh sách tất cả các năm có dữ liệu cho một mã cổ phiếu từ database.
    
    Args:
        stock: Mã cổ phiếu
        table_name: Tên bảng để query (mặc định: balance_sheet_raw)
                   Có thể thử các bảng: balance_sheet_raw, income_statement_p2_raw, cash_flow_statement_raw
    
    Returns:
        List[int]: Danh sách các năm (sắp xếp tăng dần)
    """
    try:
        import psycopg2
        from Gen57Metrics.utils_database_manager import connect
    except ImportError:
        print("Warning: psycopg2 not available. Cannot fetch years from database.")
        return []
    
    conn = None
    cursor = None
    try:
        conn = connect()
        cursor = conn.cursor()
        
        # Thử query từ nhiều bảng để lấy tất cả các năm có dữ liệu
        tables_to_check = [
            "balance_sheet_raw",
            "income_statement_p2_raw", 
            "cash_flow_statement_raw"
        ]
        
        all_years = set()
        
        for table in tables_to_check:
            try:
                query = f"""
                SELECT DISTINCT year
                FROM "{table}"
                WHERE UPPER(stock) = UPPER(%s)
                AND year IS NOT NULL
                ORDER BY year
                """
                cursor.execute(query, (str(stock).upper(),))
                results = cursor.fetchall()
                
                for row in results:
                    if row[0]:
                        all_years.add(int(row[0]))
            except Exception as e:
                # Bỏ qua nếu bảng không tồn tại
                continue
        
        years = sorted(list(all_years))
        return years
    except Exception as e:
        print(f"Error fetching years from database for {stock}: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_stocks_from_file(file_path: Path) -> List[str]:
    """
    Đọc danh sách mã cổ phiếu từ file (mỗi dòng một mã).
    
    Args:
        file_path: Đường dẫn đến file chứa danh sách mã
        
    Returns:
        List[str]: Danh sách mã cổ phiếu (uppercase, đã loại bỏ khoảng trắng)
    """
    stocks = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                stock = line.strip().upper()
                if stock and not stock.startswith('#'):  # Bỏ qua dòng trống và comment
                    stocks.append(stock)
        return stocks
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Error reading file {file_path}: {e}", file=sys.stderr)
        return []


def calculate_for_stock(
    stock: str,
    year: int,
    quarter: Optional[int] = 5,
    skip_on_error: bool = True
) -> Dict[str, Any]:
    """
    Tính toán indicators cho một mã cổ phiếu.
    
    Args:
        stock: Mã cổ phiếu
        year: Năm
        quarter: Quý (1-4) hoặc 5 cho báo cáo năm
        skip_on_error: Nếu True, bỏ qua lỗi và tiếp tục với mã tiếp theo
        
    Returns:
        Dict với keys: 'stock', 'success', 'result', 'error'
    """
    print(f"\n{'='*60}")
    print(f"Processing: {stock} - Year {year} Q{quarter}")
    print(f"{'='*60}")
    
    try:
        result = calculate_all_indicators(
            stock=stock,
            year=year,
            quarter=quarter,
            include_metadata=True
        )
        
        metadata = result.get("metadata", {})
        successful = metadata.get("successful", 0)
        failed = metadata.get("failed", 0)
        total = metadata.get("total_indicators", 0)
        
        print(f"✓ {stock}: {successful}/{total} indicators calculated successfully")
        if failed > 0:
            print(f"  ⚠ {failed} indicators failed")

        # Log chi tiết từng indicator (ID, tên, value) để debug / kiểm tra kết quả
        indicators_with_id = result.get("indicators_with_id", [])
        if indicators_with_id:
            print("\n  Indicator values:")
            for item in indicators_with_id:
                ind_id = item.get("id")
                name = item.get("name")
                value = item.get("value")
                id_str = f"{ind_id:02d}" if isinstance(ind_id, int) else "--"
                print(f"    - [{id_str}] {name}: {value}")
            print()

        # Persist kết quả vào bảng indicator_57 để API/web chỉ đọc từ DB
        try:
            json_payload = dict(result)
            json_payload.pop("metadata", None)

            row_payload = {
                "stock": result.get("stock", stock).upper(),
                "year": int(result.get("year", year)),
                "quarter": int(
                    result.get("quarter")
                    if result.get("quarter") is not None
                    else (quarter if quarter is not None else 5)
                ),
                "json_raw": json_payload,
            }

            rows_written = save_indicator_result_payload(row_payload)
            try:
                print(f"  ✓ Persisted {rows_written} row to table 'indicator_57'")
            except UnicodeEncodeError:
                print(f"  Persisted {rows_written} row to table 'indicator_57'")
        except Exception as persist_exc:
            try:
                print(f"  ⚠ Warning: could not persist indicator results to DB: {persist_exc}")
            except UnicodeEncodeError:
                print(f"  Warning: could not persist indicator results to DB: {persist_exc}")

        return {
            "stock": stock,
            "success": True,
            "result": result,
            "successful": successful,
            "failed": failed,
            "total": total
        }
    except Exception as e:
        error_msg = str(e)
        print(f"✗ {stock}: Error - {error_msg}")
        
        if not skip_on_error:
            raise
        
        return {
            "stock": stock,
            "success": False,
            "result": None,
            "error": error_msg,
            "successful": 0,
            "failed": 0,
            "total": 0
        }


def main():
    """
    Main entry point for batch processing.
    
    Examples:
        # Chạy cho danh sách mã từ file
        python main_run_batch.py --stocks-file stocks.txt --year 2024 --quarter 5
        
        # Chạy cho danh sách mã từ command line
        python main_run_batch.py --stocks MIG PGI BIC --year 2024
        
        # Chạy cho tất cả mã trong database
        python main_run_batch.py --all-stocks --year 2024 --quarter 5
        
        # Chạy cho nhiều năm
        python main_run_batch.py --stocks MIG --years 2022 2023 2024
    """
    parser = argparse.ArgumentParser(
        description="Calculate indicators for multiple stocks (batch processing)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run for stocks from file
  python main_run_batch.py --stocks-file stocks.txt --year 2024 --quarter 5
  
  # Run for specific stocks
  python main_run_batch.py --stocks MIG PGI BIC --year 2024
  
  # Run for all stocks in database
  python main_run_batch.py --all-stocks --year 2024
  
  # Run for multiple years
  python main_run_batch.py --stocks MIG --years 2022 2023 2024
  
  # Run for multiple quarters
  python main_run_batch.py --stocks MIG --year 2024 --quarters 1 2 3 4 5
  
  # Run for 1 stock with ALL years from database
  python main_run_batch.py --stocks MIG --all-years --quarter 5
        """
    )
    
    # Stock selection options (mutually exclusive)
    stock_group = parser.add_mutually_exclusive_group(required=True)
    stock_group.add_argument(
        "--stocks", "-s",
        nargs="+",
        help="List of stock symbols (e.g., MIG PGI BIC)"
    )
    stock_group.add_argument(
        "--stocks-file", "-f",
        type=str,
        help="Path to file containing stock symbols (one per line)"
    )
    stock_group.add_argument(
        "--all-stocks", "-a",
        action="store_true",
        help="Process all stocks from database"
    )
    
    # Year/Quarter options
    parser.add_argument(
        "--year", "-y",
        type=int,
        help="Year (e.g., 2024). Use --years for multiple years."
    )
    
    parser.add_argument(
        "--years",
        nargs="+",
        type=int,
        help="Multiple years (e.g., 2022 2023 2024)"
    )
    
    parser.add_argument(
        "--all-years",
        action="store_true",
        help="Use all years available in database for the stock(s)"
    )
    
    parser.add_argument(
        "--quarter", "-q",
        type=int,
        default=5,
        help="Quarter (1-4) or 5 for annual report (default: 5)"
    )
    
    parser.add_argument(
        "--quarters",
        nargs="+",
        type=int,
        help="Multiple quarters (e.g., 1 2 3 4 5)"
    )
    
    # Output options
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output JSON file path for batch summary"
    )
    
    parser.add_argument(
        "--skip-on-error",
        action="store_true",
        default=True,
        help="Skip stocks with errors and continue (default: True)"
    )
    
    parser.add_argument(
        "--no-skip-on-error",
        dest="skip_on_error",
        action="store_false",
        help="Stop on first error"
    )
    
    args = parser.parse_args()
    
    # Validate quarter
    if args.quarter and (args.quarter < 1 or args.quarter > 5):
        print(f"Error: Quarter must be between 1 and 5, got {args.quarter}", file=sys.stderr)
        return 1
    
    if args.quarters:
        for q in args.quarters:
            if q < 1 or q > 5:
                print(f"Error: Quarter must be between 1 and 5, got {q}", file=sys.stderr)
                return 1
    
    # Get stocks list
    stocks: List[str] = []
    
    if args.stocks:
        stocks = [s.upper() for s in args.stocks]
    elif args.stocks_file:
        file_path = Path(args.stocks_file)
        stocks = get_stocks_from_file(file_path)
        if not stocks:
            print("Error: No stocks found in file or file is empty", file=sys.stderr)
            return 1
    elif args.all_stocks:
        stocks = get_stocks_from_database()
        if not stocks:
            print("Error: No stocks found in database", file=sys.stderr)
            return 1
        print(f"Found {len(stocks)} stocks in database")
    
    if not stocks:
        print("Error: No stocks to process", file=sys.stderr)
        return 1
    
    # Prepare years list
    years: List[int] = []
    if args.all_years:
        # Lấy tất cả các năm từ database cho từng mã
        # Nếu chỉ có 1 mã, lấy năm cho mã đó
        # Nếu nhiều mã, lấy union của tất cả các năm
        if len(stocks) == 1:
            years = get_years_from_database(stocks[0])
            if not years:
                print(f"Error: No years found in database for stock {stocks[0]}", file=sys.stderr)
                return 1
            print(f"Found {len(years)} years in database for {stocks[0]}: {min(years)}-{max(years)}")
        else:
            # Lấy union của tất cả các năm từ tất cả các mã
            all_years_set = set()
            for stock in stocks:
                stock_years = get_years_from_database(stock)
                all_years_set.update(stock_years)
            years = sorted(list(all_years_set))
            if not years:
                print("Error: No years found in database for any of the stocks", file=sys.stderr)
                return 1
            print(f"Found {len(years)} unique years across all stocks: {min(years)}-{max(years)}")
    elif args.years:
        years = args.years
    elif args.year:
        years = [args.year]
    else:
        print("Error: Must specify --year, --years, or --all-years", file=sys.stderr)
        return 1
    
    # Prepare quarters list
    quarters: List[int] = []
    if args.quarters:
        quarters = args.quarters
    elif args.quarter:
        quarters = [args.quarter]
    else:
        quarters = [5]  # Default to annual
    
    # Print batch info
    print(f"\n{'='*60}")
    print(f"BATCH PROCESSING")
    print(f"{'='*60}")
    print(f"Stocks: {len(stocks)} ({', '.join(stocks[:5])}{'...' if len(stocks) > 5 else ''})")
    print(f"Years: {', '.join(map(str, years))}")
    print(f"Quarters: {', '.join(map(str, quarters))}")
    print(f"Total tasks: {len(stocks) * len(years) * len(quarters)}")
    print(f"{'='*60}\n")
    
    # Process all combinations
    results: List[Dict[str, Any]] = []
    start_time = datetime.now()
    
    total_tasks = len(stocks) * len(years) * len(quarters)
    current_task = 0
    
    for stock in stocks:
        for year in years:
            for quarter in quarters:
                current_task += 1
                print(f"\n[{current_task}/{total_tasks}] ", end="")
                
                result = calculate_for_stock(
                    stock=stock,
                    year=year,
                    quarter=quarter,
                    skip_on_error=args.skip_on_error
                )
                results.append(result)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Summary
    print(f"\n{'='*60}")
    print(f"BATCH PROCESSING COMPLETED")
    print(f"{'='*60}")
    print(f"Total tasks: {total_tasks}")
    print(f"Successful: {sum(1 for r in results if r['success'])}")
    print(f"Failed: {sum(1 for r in results if not r['success'])}")
    print(f"Total indicators calculated: {sum(r.get('successful', 0) for r in results)}")
    print(f"Total indicators failed: {sum(r.get('failed', 0) for r in results)}")
    print(f"Duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")
    print(f"{'='*60}\n")
    
    # Save summary to file if requested
    if args.output:
        summary = {
            "batch_info": {
                "stocks": stocks,
                "years": years,
                "quarters": quarters,
                "total_tasks": total_tasks,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration
            },
            "summary": {
                "successful_tasks": sum(1 for r in results if r['success']),
                "failed_tasks": sum(1 for r in results if not r['success']),
                "total_indicators_calculated": sum(r.get('successful', 0) for r in results),
                "total_indicators_failed": sum(r.get('failed', 0) for r in results)
            },
            "results": results
        }
        
        output_path = Path(args.output)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"Summary saved to: {output_path}")
    
    # Print failed stocks if any
    failed_results = [r for r in results if not r['success']]
    if failed_results:
        print(f"\nFailed stocks ({len(failed_results)}):")
        for r in failed_results:
            print(f"  - {r['stock']}: {r.get('error', 'Unknown error')}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

