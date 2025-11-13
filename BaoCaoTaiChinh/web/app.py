"""
FastAPI backend API để serve data từ database cho dashboard visualization.
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import sys
from pathlib import Path

# Add parent directory to path to import utils
sys.path.insert(0, str(Path(__file__).parent.parent / "ExtractBaoCaoTaiChinh"))

from utils_database_manager import connect, DB_CONFIG

app = FastAPI(
    title="Financial Reports Dashboard API",
    description="API để visualize và analyze financial data",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
        
        tables = ['income_statement_raw', 'balance_sheet_raw', 'cash_flow_statement_raw']
        for table in tables:
            try:
                cursor.execute(f'SELECT COUNT(*) FROM "{table}";')
                count = cursor.fetchone()[0]
                stats[table] = count
            except Exception as e:
                stats[table] = {'error': str(e)}
        
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
    limit: int = Query(100, description="Limit results")
):
    """Get income statement data."""
    try:
        conn = connect()
        cursor = conn.cursor()
        
        query = 'SELECT stock, year, quarter, source_filename, json_raw, created_at FROM "income_statement_raw" WHERE 1=1'
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
    table: str = Query('income_statement_raw', description="Table name")
):
    """Get list of unique stocks."""
    try:
        if table not in ['income_statement_raw', 'balance_sheet_raw', 'cash_flow_statement_raw']:
            table = 'income_statement_raw'
        
        conn = connect()
        cursor = conn.cursor()
        
        cursor.execute(f'SELECT DISTINCT stock FROM "{table}" ORDER BY stock;')
        stocks = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return {"success": True, "stocks": stocks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/years")
async def get_years(
    table: str = Query('income_statement_raw', description="Table name")
):
    """Get list of unique years."""
    try:
        if table not in ['income_statement_raw', 'balance_sheet_raw', 'cash_flow_statement_raw']:
            table = 'income_statement_raw'
        
        conn = connect()
        cursor = conn.cursor()
        
        cursor.execute(f'SELECT DISTINCT year FROM "{table}" ORDER BY year DESC;')
        years = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        return {"success": True, "years": years}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == '__main__':
    import uvicorn
    
    print("=" * 80)
    print("Financial Dashboard API Server (FastAPI)")
    print("=" * 80)
    print(f"Database: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"Database: {DB_CONFIG['database']}")
    print("=" * 80)
    print("\nStarting server on http://localhost:8000")
    print("\nAPI Endpoints:")
    print("  - GET /api/health")
    print("  - GET /api/stats")
    print("  - GET /api/income-statement?stock=XXX&year=2024&quarter=5")
    print("  - GET /api/balance-sheet?stock=XXX&year=2024&quarter=5")
    print("  - GET /api/cash-flow?stock=XXX&year=2024&quarter=5")
    print("  - GET /api/stocks?table=income_statement_raw")
    print("  - GET /api/years?table=income_statement_raw")
    print("\nAPI Documentation:")
    print("  - Swagger UI: http://localhost:8000/docs")
    print("  - ReDoc: http://localhost:8000/redoc")
    print("\nOpen index.html in your browser to view the dashboard")
    print("=" * 80)
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

