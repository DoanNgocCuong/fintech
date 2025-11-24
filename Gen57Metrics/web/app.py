"""
FastAPI backend for the Gen57Metrics indicator dashboard.

The service exposes lightweight endpoints so the frontend can:
1. Fetch the 57-indicator metadata straight from `57BaseIndicators.json`.
2. Discover available stock tickers and reporting periods from PostgreSQL.
3. Trigger on-demand calculations via the existing IndicatorCalculator.

Design notes:
- Follows SOLID (single responsibility helpers, explicit abstractions).
- Keeps database access in tiny helpers to simplify testing/mocking.
- Uses cached JSON loading to avoid unnecessary IO on every request.
"""

from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

# Ensure project root is on sys.path so `Gen57Metrics` imports resolve
WEB_DIR = Path(__file__).resolve().parent
PACKAGE_ROOT = WEB_DIR.parent
PROJECT_ROOT = PACKAGE_ROOT.parent
for path in {str(PROJECT_ROOT), str(PACKAGE_ROOT)}:
    if path not in sys.path:
        sys.path.insert(0, path)

from Gen57Metrics.indicator_calculator import calculate_all_indicators
from Gen57Metrics.utils_database_manager import connect, DB_CONFIG

app = FastAPI(
    title="Gen57Metrics Dashboard API",
    description="Serve 57-indicator metadata and calculation results for UI consumption.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

INDICATOR_JSON_PATH = PACKAGE_ROOT / "57BaseIndicators.json"

SOURCE_TABLES: Dict[str, str] = {
    "balance": "balance_sheet_raw",
    "income_p1": "income_statement_p1_raw",
    "income_p2": "income_statement_p2_raw",
    "cashflow": "cash_flow_statement_raw",
}
DEFAULT_SOURCE_KEY = "balance"


# ---------- Helper layer ----------

class IndicatorSerializer:
    """Serialize raw JSON indicator entries into frontend-friendly dicts."""

    @staticmethod
    def serialize(raw: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": raw.get("ID"),
            "group": raw.get("Group"),
            "name": raw.get("Indicator_Name"),
            "definition": raw.get("Definition"),
            "formula": raw.get("Formula"),
            "tt200_formula": raw.get("TT200_Formula"),
            "direct_from_db": raw.get("Get_Direct_From_DB"),
            "used_in_qgv": raw.get("Used_in_QGV"),
            "used_in_4m": raw.get("Used_in_4M"),
            "formula_in_qgv": raw.get("Formula_in_QGV"),
            "formula_in_4m": raw.get("Formula_in_4M"),
            "scoring_metric": raw.get("Scoring_Metric"),
            "weight_in_4m": raw.get("Weight_in_4M"),
            "weight_in_qgv": raw.get("Weight_in_QGV"),
        }


def _resolve_table(source: str) -> str:
    normalized = source.strip().lower()
    if normalized in SOURCE_TABLES:
        return SOURCE_TABLES[normalized]
    # Allow passing actual table names (for flexibility/testing)
    if normalized in SOURCE_TABLES.values():
        return normalized
    raise HTTPException(status_code=400, detail=f"Unknown source '{source}'.")


def _fetch_rows(query: str, params: tuple = ()) -> List[tuple]:
    conn = connect()
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
    finally:
        conn.close()


@lru_cache(maxsize=1)
def _load_indicator_definitions() -> List[Dict[str, Any]]:
    if not INDICATOR_JSON_PATH.exists():
        raise RuntimeError(f"Indicator JSON not found at {INDICATOR_JSON_PATH}")

    with INDICATOR_JSON_PATH.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    indicators = payload.get("Base_Indicators_57", [])
    return [IndicatorSerializer.serialize(item) for item in indicators]


def _filter_indicators(
    indicators: List[Dict[str, Any]],
    group: Optional[str],
    search: Optional[str],
) -> List[Dict[str, Any]]:
    filtered = indicators

    if group:
        group_lower = group.lower()
        filtered = [item for item in filtered if (item.get("group") or "").lower() == group_lower]

    if search:
        term = search.lower()
        filtered = [
            item
            for item in filtered
            if term in (item.get("name") or "").lower()
            or term in (item.get("definition") or "").lower()
            or term in (item.get("formula") or "").lower()
        ]

    return filtered


# ---------- API routes ----------


@app.get("/api/health")
async def health() -> Dict[str, Any]:
    return {"status": "ok", "message": "Gen57Metrics API is running"}


@app.get("/api/indicators")
async def list_indicators(
    group: Optional[str] = Query(None, description="Filter by indicator group"),
    search: Optional[str] = Query(None, description="Free-text search across name/definition/formula"),
) -> Dict[str, Any]:
    indicators = _load_indicator_definitions()
    filtered = _filter_indicators(indicators, group, search)
    groups = sorted({item["group"] for item in indicators if item.get("group")})

    return {
        "success": True,
        "count": len(filtered),
        "groups": groups,
        "indicators": filtered,
    }


@app.get("/api/stocks")
async def list_stocks(
    source: str = Query(DEFAULT_SOURCE_KEY, description="Logical source name or table name"),
) -> Dict[str, Any]:
    table_name = _resolve_table(source)

    try:
        rows = _fetch_rows(f'SELECT DISTINCT stock FROM "{table_name}" ORDER BY stock ASC;')
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

    stocks = [row[0] for row in rows]
    return {
        "success": True,
        "source": table_name,
        "count": len(stocks),
        "stocks": stocks,
    }


@app.get("/api/periods")
async def list_periods(
    stock: str = Query(..., description="Stock ticker"),
    source: str = Query(DEFAULT_SOURCE_KEY, description="Logical source/table for period discovery"),
) -> Dict[str, Any]:
    table_name = _resolve_table(source)
    stock_code = stock.strip().upper()

    if not stock_code:
        raise HTTPException(status_code=400, detail="Stock ticker is required.")

    query = f'''
        SELECT DISTINCT year, COALESCE(quarter, 5) AS quarter_label
        FROM "{table_name}"
        WHERE stock = %s
        ORDER BY year DESC, quarter_label DESC;
    '''

    try:
        rows = _fetch_rows(query, (stock_code,))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

    periods = [
        {"year": year, "quarter": int(quarter), "label": f"Q{int(quarter)}-{year}"}
        for year, quarter in rows
    ]

    return {
        "success": True,
        "stock": stock_code,
        "source": table_name,
        "count": len(periods),
        "periods": periods,
    }


@app.get("/api/indicator-values")
async def indicator_values(
    stock: str = Query(..., description="Stock ticker"),
    year: int = Query(..., ge=2000, le=2100, description="Fiscal year"),
    quarter: Optional[int] = Query(
        None, ge=1, le=5, description="Quarter (1-5). Leave empty to use latest period."
    ),
    include_metadata: bool = Query(True, description="Include calculation metadata"),
) -> Dict[str, Any]:
    stock_code = stock.strip().upper()

    if not stock_code:
        raise HTTPException(status_code=400, detail="Stock ticker is required.")

    try:
        result = calculate_all_indicators(
            stock=stock_code,
            year=year,
            quarter=quarter,
            include_metadata=include_metadata,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to calculate indicators: {exc}") from exc

    return {
        "success": True,
        "stock": stock_code,
        "year": year,
        "quarter": quarter,
        "indicators": result.get("indicators_with_id", []),
        "metadata": result.get("metadata"),
    }


@app.get("/api/dashboard/bootstrap")
async def bootstrap() -> Dict[str, Any]:
    """
    Convenience endpoint for frontend initial load.
    Returns definitions and grouped metadata in one shot.
    """
    indicators = _load_indicator_definitions()
    groups = sorted({item["group"] for item in indicators if item.get("group")})

    return {
        "success": True,
        "indicator_count": len(indicators),
        "groups": groups,
        "indicators": indicators,
    }


__all__ = ["app"]

# Note: from __future__ imports must occur at the very top of the file (Python rule).
# This block should be BELOW all import statements and after the FastAPI code, as here.

if __name__ == "__main__":
    import argparse
    import uvicorn
    try:
        # Try importing DB_CONFIG from the real package module name to avoid relative import error
        from Gen57Metrics.utils_database_manager import DB_CONFIG
    except ImportError:
        # Fallback for local script runs (if package/module layout is different)
        from utils_database_manager import DB_CONFIG

    parser = argparse.ArgumentParser(description="Gen57Metrics FastAPI Server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=30013, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload (dev only)")
    args = parser.parse_args()

    print("=" * 80)
    print("Gen57Metrics API Server (FastAPI)")
    print("=" * 80)
    try:
        print(f"Database: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
        print(f"Database name: {DB_CONFIG['database']}")
    except Exception:
        pass
    print("=" * 80)
    print(f"\nStarting server on http://{args.host}:{args.port}")
    print("\nKey API Endpoints:")

    print("\nAPI Documentation:")
    print(f"  - Swagger UI: http://{args.host}:{args.port}/docs")
    print(f"  - ReDoc:      http://{args.host}:{args.port}/redoc")
    print("=" * 80)

    if args.reload:
        # Note: uvicorn's native reload is recommended via CLI, but allow flag here for convenience
        uvicorn.run("Gen57Metrics.web.app:app", host=args.host, port=args.port, reload=True)
    else:
        uvicorn.run("Gen57Metrics.web.app:app", host=args.host, port=args.port, reload=False)
