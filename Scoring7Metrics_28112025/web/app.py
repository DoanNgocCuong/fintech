"""
FastAPI backend API để serve data từ database cho dashboard visualization.
Sử dụng cột parsed_data để query và hiển thị dữ liệu.
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from utils_database_manager import (
    connect, DB_CONFIG, get_company_data, get_companies_list,
    get_years_list, search_evidence, get_stats
)
from utils_data_extractor import (
    format_company_data_response, extract_all_metrics,
    extract_summary, extract_evidences, GROUP_IDS, GROUP_NAMES
)

app = FastAPI(
    title="Scoring 7 Metrics Dashboard API",
    description="API để visualize và analyze 7 tiêu chí định tính từ tài liệu Đại hội cổ đông",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all headers
)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "API is running"}


@app.get("/api/stats")
async def get_statistics():
    """Get statistics về số lượng records trong database."""
    try:
        stats = get_stats()
        return {"success": True, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/companies")
async def get_companies(
    search: Optional[str] = Query(None, description="Tìm kiếm theo tên công ty")
):
    """Get list of unique companies."""
    try:
        companies = get_companies_list(search=search)
        return {
            "success": True,
            "companies": companies,
            "count": len(companies)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/years")
async def get_years(
    company_name: Optional[str] = Query(None, description="Lọc theo công ty")
):
    """Get list of unique years."""
    try:
        years = get_years_list(company_name=company_name)
        return {
            "success": True,
            "years": years,
            "company": company_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/company-data")
async def get_company_data_endpoint(
    company_name: str = Query(..., description="Tên công ty"),
    year: int = Query(..., description="Năm")
):
    """
    Lấy dữ liệu 7 tiêu chí cho một công ty và năm cụ thể.
    Sử dụng cột parsed_data từ database.
    """
    try:
        # Query parsed_data từ database
        result = get_company_data(company_name, year)
        
        if not result or not result.get('parsed_data'):
            return {
                "success": False,
                "message": f"Không tìm thấy dữ liệu cho {company_name} năm {year}",
                "company_name": company_name,
                "year": year
            }
        
        parsed_data = result['parsed_data']
        
        # Format response
        response = format_company_data_response(parsed_data, company_name, year)
        response['file_name'] = result.get('file_name')
        response['created_at'] = result.get('created_at')
        response['updated_at'] = result.get('updated_at')
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/company-timeline")
async def get_company_timeline(
    company_name: str = Query(..., description="Tên công ty"),
    years: Optional[str] = Query(None, description="Danh sách năm (comma-separated)")
):
    """
    Lấy dữ liệu 7 tiêu chí cho một công ty qua nhiều năm (timeline).
    """
    try:
        # Get all years for this company
        all_years = get_years_list(company_name=company_name)
        
        # Filter by years if provided
        if years:
            year_list = [int(y.strip()) for y in years.split(',')]
            all_years = [y for y in all_years if y in year_list]
        
        timeline = []
        for year in sorted(all_years, reverse=True):
            result = get_company_data(company_name, year)
            if result and result.get('parsed_data'):
                parsed_data = result['parsed_data']
                timeline.append({
                    "year": year,
                    "metrics": extract_all_metrics(parsed_data),
                    "summary": extract_summary(parsed_data)
                })
        
        return {
            "success": True,
            "company_name": company_name,
            "timeline": timeline
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/search-evidence")
async def search_evidence_endpoint(
    keyword: str = Query(..., description="Từ khóa tìm kiếm"),
    company_name: Optional[str] = Query(None, description="Lọc theo công ty"),
    year: Optional[int] = Query(None, description="Lọc theo năm"),
    group_id: Optional[str] = Query(None, description="Lọc theo tiêu chí")
):
    """
    Tìm kiếm trích dẫn (evidences) theo từ khóa trong parsed_data.
    """
    try:
        # Validate group_id
        if group_id and group_id not in GROUP_IDS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid group_id. Must be one of: {', '.join(GROUP_IDS)}"
            )
        
        results = search_evidence(
            keyword=keyword,
            company_name=company_name,
            year=year,
            group_id=group_id
        )
        
        return {
            "success": True,
            "results": results,
            "count": len(results)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/metrics-by-group")
async def get_metrics_by_group_endpoint(
    group_id: str = Query(..., description="Tiêu chí (governance, incentive, ...)"),
    company_name: Optional[str] = Query(None, description="Lọc theo công ty"),
    year: Optional[int] = Query(None, description="Lọc theo năm")
):
    """
    Lấy metrics của một tiêu chí cụ thể cho nhiều công ty/năm.
    """
    try:
        # Validate group_id
        if group_id not in GROUP_IDS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid group_id. Must be one of: {', '.join(GROUP_IDS)}"
            )
        
        # Get companies
        if company_name:
            companies = [company_name]
        else:
            companies = get_companies_list()
        
        # Get years
        if year:
            years = [year]
        else:
            years = get_years_list()
        
        data = []
        for comp in companies:
            for yr in years:
                result = get_company_data(comp, yr)
                if result and result.get('parsed_data'):
                    parsed_data = result['parsed_data']
                    metrics = extract_all_metrics(parsed_data)
                    if group_id in metrics:
                        data.append({
                            "company_name": comp,
                            "year": yr,
                            "metrics": metrics[group_id]
                        })
        
        return {
            "success": True,
            "group_id": group_id,
            "group_name": GROUP_NAMES.get(group_id, group_id),
            "data": data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == '__main__':
    import uvicorn
    import argparse
    
    parser = argparse.ArgumentParser(description='Scoring 7 Metrics Dashboard API Server')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload')
    args = parser.parse_args()
    
    print("=" * 80)
    print("Scoring 7 Metrics Dashboard API Server (FastAPI)")
    print("=" * 80)
    print(f"Database: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"Database: {DB_CONFIG['database']}")
    print(f"Table: company_json_documents")
    print("=" * 80)
    print(f"\nStarting server on http://{args.host}:{args.port}")
    print("\nAPI Endpoints:")
    print("  - GET /api/health")
    print("  - GET /api/stats")
    print("  - GET /api/companies?search=XXX")
    print("  - GET /api/years?company_name=XXX")
    print("  - GET /api/company-data?company_name=XXX&year=2024")
    print("  - GET /api/company-timeline?company_name=XXX")
    print("  - GET /api/search-evidence?keyword=XXX&company_name=XXX&year=2024")
    print("  - GET /api/metrics-by-group?group_id=governance")
    print("\nAPI Documentation:")
    print(f"  - Swagger UI: http://{args.host}:{args.port}/docs")
    print(f"  - ReDoc: http://{args.host}:{args.port}/redoc")
    print("\nOpen index.html in your browser to view the dashboard")
    print("=" * 80)
    
    uvicorn.run(app, host=args.host, port=args.port, reload=args.reload)

