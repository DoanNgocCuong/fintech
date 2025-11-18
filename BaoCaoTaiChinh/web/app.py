"""
FastAPI backend API để serve data từ database cho dashboard visualization.
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import sys
from pathlib import Path

# Add parent directory to path to import utils
sys.path.insert(0, str(Path(__file__).parent.parent / "ExtractBaoCaoTaiChinh"))
sys.path.insert(0, str(Path(__file__).parent))

from utils_database_manager import connect, DB_CONFIG
from utils_data_extractor import get_indicators_for_report_type, extract_value_from_json
import json
from typing import Dict, List, Any, Optional

app = FastAPI(
    title="Financial Reports Dashboard API",
    description="API để visualize và analyze financial data",
    version="1.0.0"
)

# Income statement sections mapping
INCOME_SECTION_TABLES = {
    "P1": "income_statement_p1_raw",
    "P2": "income_statement_p2_raw",
}
DEFAULT_INCOME_SECTION = "P2"

VALID_REPORT_TABLES = [
    *INCOME_SECTION_TABLES.values(),
    "balance_sheet_raw",
    "cash_flow_statement_raw",
]

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all headers
)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "API is running"}


@app.get("/api/stats")
async def get_stats():
    """Get statistics về số lượng records trong mỗi bảng."""
    try:
        conn = connect()
        cursor = conn.cursor()
        
        stats = {}
        
        tables = [
            *INCOME_SECTION_TABLES.values(),
            'balance_sheet_raw',
            'cash_flow_statement_raw'
        ]
        for table in tables:
            try:
                cursor.execute(f'SELECT COUNT(*) FROM "{table}";')
                count = cursor.fetchone()[0]
                stats[table] = count
            except Exception as e:
                stats[table] = {'error': str(e)}
        
        # Backward compatibility aggregate for legacy key
        income_total = 0
        for table_name in INCOME_SECTION_TABLES.values():
            value = stats.get(table_name)
            if isinstance(value, int):
                income_total += value
        stats['income_statement_raw'] = income_total
        
        cursor.close()
        conn.close()
        
        return {"success": True, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/income-statement")
async def get_income_statements(
    stock: Optional[str] = Query(None, description="Stock symbol"),
    year: Optional[int] = Query(None, description="Year"),
    quarter: Optional[int] = Query(None, description="Quarter"),
    limit: int = Query(100, description="Limit results"),
    section: Optional[str] = Query(
        DEFAULT_INCOME_SECTION,
        description="Income statement section (P1/P2)"
    )
):
    """Get income statement data."""
    try:
        section_key = normalize_income_section(section)
        table_name = INCOME_SECTION_TABLES[section_key]
        conn = connect()
        cursor = conn.cursor()
        
        query = f'SELECT stock, year, quarter, source_filename, json_raw, created_at FROM "{table_name}" WHERE 1=1'
        params = []
        
        if stock:
            query += ' AND stock = %s'
            params.append(stock)
        if year:
            query += ' AND year = %s'
            params.append(year)
        if quarter is not None:
            query += ' AND quarter = %s'
            params.append(quarter)
        
        query += ' ORDER BY year DESC, quarter DESC, stock LIMIT %s'
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            results.append({
                'stock': row[0],
                'year': row[1],
                'quarter': row[2],
                'source_filename': row[3],
                'json_raw': row[4],
                'created_at': row[5].isoformat() if row[5] else None
            })
        
        cursor.close()
        conn.close()
        
        return {"success": True, "count": len(results), "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/balance-sheet")
async def get_balance_sheets(
    stock: Optional[str] = Query(None, description="Stock symbol"),
    year: Optional[int] = Query(None, description="Year"),
    quarter: Optional[int] = Query(None, description="Quarter"),
    limit: int = Query(100, description="Limit results")
):
    """Get balance sheet data."""
    try:
        conn = connect()
        cursor = conn.cursor()
        
        query = 'SELECT stock, year, quarter, source_filename, json_raw, created_at FROM "balance_sheet_raw" WHERE 1=1'
        params = []
        
        if stock:
            query += ' AND stock = %s'
            params.append(stock)
        if year:
            query += ' AND year = %s'
            params.append(year)
        if quarter is not None:
            query += ' AND quarter = %s'
            params.append(quarter)
        
        query += ' ORDER BY year DESC, quarter DESC, stock LIMIT %s'
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            results.append({
                'stock': row[0],
                'year': row[1],
                'quarter': row[2],
                'source_filename': row[3],
                'json_raw': row[4],
                'created_at': row[5].isoformat() if row[5] else None
            })
        
        cursor.close()
        conn.close()
        
        return {"success": True, "count": len(results), "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cash-flow")
async def get_cash_flows(
    stock: Optional[str] = Query(None, description="Stock symbol"),
    year: Optional[int] = Query(None, description="Year"),
    quarter: Optional[int] = Query(None, description="Quarter"),
    limit: int = Query(100, description="Limit results")
):
    """Get cash flow statement data."""
    try:
        conn = connect()
        cursor = conn.cursor()
        
        query = 'SELECT stock, year, quarter, source_filename, json_raw, created_at FROM "cash_flow_statement_raw" WHERE 1=1'
        params = []
        
        if stock:
            query += ' AND stock = %s'
            params.append(stock)
        if year:
            query += ' AND year = %s'
            params.append(year)
        if quarter is not None:
            query += ' AND quarter = %s'
            params.append(quarter)
        
        query += ' ORDER BY year DESC, quarter DESC, stock LIMIT %s'
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            results.append({
                'stock': row[0],
                'year': row[1],
                'quarter': row[2],
                'source_filename': row[3],
                'json_raw': row[4],
                'created_at': row[5].isoformat() if row[5] else None
            })
        
        cursor.close()
        conn.close()
        
        return {"success": True, "count": len(results), "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stocks")
async def get_stocks(
    table: str = Query('income_statement_p2_raw', description="Table name")
):
    """Get list of unique stocks."""
    try:
        # Validate table name
        if table not in VALID_REPORT_TABLES:
            table = INCOME_SECTION_TABLES[DEFAULT_INCOME_SECTION]
        
        conn = connect()
        cursor = conn.cursor()
        
        try:
            # Query distinct stocks
            cursor.execute(f'SELECT DISTINCT stock FROM "{table}" ORDER BY stock;')
            stocks = [row[0] for row in cursor.fetchall()] if cursor.rowcount > 0 else []
            
            return {
                "success": True,
                "stocks": stocks,
                "table": table,
                "count": len(stocks)
            }
        except Exception as db_error:
            # Database error
            print(f"Database error in /api/stocks for table {table}: {db_error}")
            raise HTTPException(
                status_code=500,
                detail=f"Database error: {str(db_error)}"
            )
        finally:
            cursor.close()
            conn.close()
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in /api/stocks: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/years")
async def get_years(
    table: str = Query('income_statement_p2_raw', description="Table name")
):
    """Get list of unique years."""
    try:
        if table not in VALID_REPORT_TABLES:
            table = INCOME_SECTION_TABLES[DEFAULT_INCOME_SECTION]
        
        conn = connect()
        cursor = conn.cursor()
        
        cursor.execute(f'SELECT DISTINCT year FROM "{table}" ORDER BY year DESC;')
        years = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return {"success": True, "years": years}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Helper function to get table data for a stock
async def get_table_data_for_stock(stock: str, table_name: str, report_type: str) -> dict:
    """
    Helper function to get table data for a stock from any table.
    
    Args:
        stock: Stock symbol
        table_name: Database table name
        report_type: Report type string (e.g., "balance-sheet", "income-statement", "cash-flow")
        
    Returns:
        Dictionary with periods, indicators, and metadata
    """
    conn = connect()
    cursor = conn.cursor()
    
    try:
        # Query all records for this stock
        query = f'SELECT year, quarter, json_raw, created_at FROM "{table_name}" WHERE stock = %s ORDER BY year DESC, quarter DESC NULLS LAST'
        cursor.execute(query, (stock,))
        rows = cursor.fetchall()
        
        if not rows:
            cursor.close()
            conn.close()
            return {
                "success": True,
                "stock": stock,
                "report_type": report_type,
                "periods": [],
                "indicators": []
            }
        
        # Extract periods and data
        periods = []
        data_by_period = {}
        last_update = None
        
        for year, quarter, json_raw, created_at in rows:
            # Handle quarter (None means year-end, use 5)
            if quarter is None:
                quarter = 5
            period_label = f"Q{quarter}-{year}"
            
            periods.append({
                "year": year,
                "quarter": quarter,
                "label": period_label
            })
            
            # Parse json_raw from PostgreSQL JSONB
            if isinstance(json_raw, str):
                data_by_period[period_label] = json.loads(json_raw)
            elif isinstance(json_raw, dict):
                data_by_period[period_label] = json_raw
            else:
                # Fallback: try to convert to dict
                data_by_period[period_label] = dict(json_raw) if hasattr(json_raw, '__iter__') else {}
            
            # Get last update time
            if created_at and (last_update is None or created_at > last_update):
                last_update = created_at
        
        # Remove duplicate periods (keep first occurrence)
        seen_periods = set()
        unique_periods = []
        for period in periods:
            period_key = (period["year"], period["quarter"])
            if period_key not in seen_periods:
                seen_periods.add(period_key)
                unique_periods.append(period)
        
        # Sort periods by year DESC, then quarter DESC (Q5-2025, Q4-2025, Q3-2025, ...)
        periods = sorted(unique_periods, key=lambda p: (p["year"], p["quarter"]), reverse=True)
        
        # Get indicators from first record (all records should have same structure)
        indicator_data = []
        if rows:
            first_json = rows[0][2]
            # Parse first_json if needed
            if isinstance(first_json, str):
                first_json = json.loads(first_json)
            elif not isinstance(first_json, dict):
                first_json = dict(first_json) if hasattr(first_json, '__iter__') else {}
            
            # Debug: Print JSON structure
            print(f"[DEBUG] JSON keys for {report_type}, stock: {stock}: {list(first_json.keys()) if isinstance(first_json, dict) else 'NOT A DICT'}")
            if isinstance(first_json, dict) and len(first_json) > 0:
                first_key = list(first_json.keys())[0]
                print(f"[DEBUG] First key: {first_key}, type: {type(first_json.get(first_key))}")
                if isinstance(first_json.get(first_key), dict):
                    print(f"[DEBUG] First key's keys: {list(first_json[first_key].keys())[:5]}...")  # First 5 keys
            
            indicators_config = get_indicators_for_report_type(first_json, report_type)
            
            print(f"[DEBUG] Found {len(indicators_config)} indicators for {report_type}, stock: {stock}")
            if len(indicators_config) > 0:
                print(f"[DEBUG] First 3 indicators: {[ind.get('key') for ind in indicators_config[:3]]}")
            
            # Build tree structure from flat indicators list
            indicator_tree = build_indicator_tree(indicators_config)
            
            print(f"[DEBUG] Built tree with {len(indicator_tree)} root nodes")
            if indicator_tree:
                first_root = indicator_tree[0]
                print(f"[DEBUG] First root: {first_root.get('key')}, has_children: {first_root.get('has_children')}, children count: {len(first_root.get('children', []))}")
            
            # Build indicator data with values for each period
            # Process in tree order to maintain hierarchy
            def process_tree_node(node):
                values = {}
                for period in periods:
                    period_label = period["label"]
                    json_data = data_by_period.get(period_label)
                    if json_data:
                        value = extract_value_from_json(json_data, node["path"])
                        values[period_label] = value
                    else:
                        values[period_label] = None
                
                indicator_entry = {
                    "key": node["key"],
                    "label": node["label"],
                    "label_vn": node["label_vn"],
                    "ma_so": node["ma_so"],
                    "values": values,
                    "level": node.get("level", 0),
                    "parent_path": node.get("parent_path"),
                    "full_path": node.get("full_path"),
                    "has_children": node.get("has_children", False)
                }
                
                # Process children if exists
                if "children" in node and node["children"]:
                    indicator_entry["children"] = [process_tree_node(child) for child in node["children"]]
                    indicator_entry["has_children"] = True
                else:
                    indicator_entry["has_children"] = False
                
                return indicator_entry
            
            # Process tree and create flat list with hierarchy info
            for root_node in indicator_tree:
                indicator_data.append(process_tree_node(root_node))
        
        return {
            "success": True,
            "stock": stock,
            "report_type": report_type,
            "periods": periods,
            "indicators": indicator_data,
            "last_update": last_update.isoformat() if last_update else None
        }
    finally:
        cursor.close()
        conn.close()


@app.get("/api/balance-sheet/table-data")
async def get_balance_sheet_table_data(
    stock: str = Query(..., description="Stock symbol")
):
    """Get balance sheet table data for a stock."""
    try:
        return await get_table_data_for_stock(stock, "balance_sheet_raw", "balance-sheet")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/income-statement/table-data")
async def get_income_statement_table_data(
    stock: str = Query(..., description="Stock symbol"),
    section: Optional[str] = Query(
        DEFAULT_INCOME_SECTION,
        description="Income statement section (P1/P2)"
    )
):
    """Get income statement table data for a stock."""
    try:
        section_key = normalize_income_section(section)
        table_name = INCOME_SECTION_TABLES[section_key]
        return await get_table_data_for_stock(stock, table_name, "income-statement")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cash-flow/table-data")
async def get_cash_flow_table_data(
    stock: str = Query(..., description="Stock symbol")
):
    """Get cash flow table data for a stock."""
    try:
        return await get_table_data_for_stock(stock, "cash_flow_statement_raw", "cash-flow")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def build_indicator_tree(indicators: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Build tree structure from flat indicators list.
    Groups indicators by parent-child relationship.
    
    Args:
        indicators: Flat list of indicators with level and parent_path
        
    Returns:
        Tree structure with children arrays
    """
    if not indicators:
        return []
    
    # Create a map of indicators by full_path (use copies to avoid modifying original)
    indicator_map = {}
    for ind in indicators:
        full_path = ind.get("full_path")
        if full_path:
            indicator_map[full_path] = ind.copy()
    
    # Mark indicators that have children
    for ind in indicators:
        parent_path = ind.get("parent_path")
        if parent_path and parent_path in indicator_map:
            indicator_map[parent_path]["has_children"] = True
    
    # Build tree structure - need to use copies from map
    tree = []
    processed = set()
    
    for ind in indicators:
        full_path = ind.get("full_path")
        if not full_path or full_path in processed:
            continue
            
        parent_path = ind.get("parent_path")
        if parent_path and parent_path in indicator_map:
            parent = indicator_map[parent_path]
            if "children" not in parent:
                parent["children"] = []
            # Use copy from map
            parent["children"].append(indicator_map[full_path])
            processed.add(full_path)
        else:
            # Root level indicator - use copy from map
            tree.append(indicator_map[full_path])
            processed.add(full_path)
    
    # Sort tree and children by ma_so
    def sort_by_ma_so(items):
        if not items:
            return
        def sort_key(x):
            ma_so = x.get("ma_so")
            if isinstance(ma_so, (int, float)):
                return ma_so
            elif isinstance(ma_so, str):
                try:
                    return float(ma_so)
                except ValueError:
                    return 999999
            return 999999
        
        items.sort(key=sort_key)
        for item in items:
            if "children" in item and item["children"]:
                sort_by_ma_so(item["children"])
    
    sort_by_ma_so(tree)
    
    return tree


def flatten_tree_with_structure(tree: List[Dict[str, Any]], result: List[Dict[str, Any]] = None, expanded_paths: set = None) -> List[Dict[str, Any]]:
    """
    Flatten tree structure while preserving hierarchy info for rendering.
    
    Args:
        tree: Tree structure
        result: Accumulator list
        expanded_paths: Set of expanded paths (all expanded by default)
        
    Returns:
        Flat list with hierarchy info
    """
    if result is None:
        result = []
    if expanded_paths is None:
        expanded_paths = set()  # Empty means all collapsed, or we can default to all expanded
    
    for node in tree:
        # Add node to result
        result.append(node)
        
        # If node has children and is expanded, add children
        if "children" in node and node["full_path"] in expanded_paths:
            flatten_tree_with_structure(node["children"], result, expanded_paths)
    
    return result


def normalize_income_section(section: Optional[str]) -> str:
    """
    Normalize section string to P1/P2. Defaults to DEFAULT_INCOME_SECTION.
    """
    if not section:
        return DEFAULT_INCOME_SECTION
    section_key = str(section).strip().upper()
    return section_key if section_key in INCOME_SECTION_TABLES else DEFAULT_INCOME_SECTION


if __name__ == '__main__':
    import uvicorn
    import argparse
    
    parser = argparse.ArgumentParser(description='FastAPI Financial Dashboard Server')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload')
    args = parser.parse_args()
    
    print("=" * 80)
    print("Financial Dashboard API Server (FastAPI)")
    print("=" * 80)
    print(f"Database: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"Database: {DB_CONFIG['database']}")
    print("=" * 80)
    print(f"\nStarting server on http://{args.host}:{args.port}")
    print("\nAPI Endpoints:")
    print("  - GET /api/health")
    print("  - GET /api/stats")
    print("  - GET /api/income-statement?stock=XXX&year=2024&quarter=5")
    print("  - GET /api/balance-sheet?stock=XXX&year=2024&quarter=5")
    print("  - GET /api/cash-flow?stock=XXX&year=2024&quarter=5")
    print("  - GET /api/stocks?table=income_statement_p1_raw")
    print("  - GET /api/stocks?table=income_statement_p2_raw")
    print("  - GET /api/years?table=income_statement_p2_raw")
    print("  - GET /api/balance-sheet/table-data?stock=XXX")
    print("  - GET /api/income-statement/table-data?stock=XXX&section=P2")
    print("  - GET /api/cash-flow/table-data?stock=XXX")
    print("\nAPI Documentation:")
    print(f"  - Swagger UI: http://{args.host}:{args.port}/docs")
    print(f"  - ReDoc: http://{args.host}:{args.port}/redoc")
    print("\nOpen index.html in your browser to view the dashboard")
    if args.reload:
        print("\n⚠️  Note: For --reload to work properly, use: uvicorn app:app --host 0.0.0.0 --port 8000 --reload")
    print("=" * 80)
    
    # If reload is requested, warn and run without reload (or use import string method)
    if args.reload:
        print("\n⚠️  WARNING: Running with --reload requires using uvicorn directly.")
        print("   Use this command instead: uvicorn app:app --host 0.0.0.0 --port 8000 --reload\n")
    
    uvicorn.run(app, host=args.host, port=args.port, reload=False)

