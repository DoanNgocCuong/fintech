"""
Database utilities for company_json_documents table.
Sử dụng cột parsed_data để query dữ liệu cho UI.
"""

import json
from typing import Optional, Dict, Any, List

try:
    import psycopg2
    from psycopg2.extras import Json as PsycopgJson
except ImportError:
    psycopg2 = None
    PsycopgJson = None


# Database configuration
DB_CONFIG: Dict[str, Any] = {
    'host': '103.253.20.30',
    'port': 29990,
    'database': 'financial-reporting-database',
    'user': 'postgres',
    'password': 'postgres',
}

TABLE_NAME = 'company_json_documents'


def connect() -> "psycopg2.extensions.connection":
    """Kết nối đến PostgreSQL database."""
    if psycopg2 is None:
        raise ImportError("psycopg2 is required. Install with: pip install psycopg2-binary")
    return psycopg2.connect(**DB_CONFIG)


def get_company_data(company_name: str, year: int) -> Optional[Dict[str, Any]]:
    """
    Lấy dữ liệu công ty từ parsed_data.
    
    Args:
        company_name: Tên công ty
        year: Năm
        
    Returns:
        Dict chứa parsed_data hoặc None nếu không tìm thấy
    """
    if psycopg2 is None:
        raise ImportError("psycopg2 is required. Install with: pip install psycopg2-binary")
    
    conn = None
    cursor = None
    try:
        conn = connect()
        cursor = conn.cursor()
        
        # Query parsed_data column
        query = """
        SELECT parsed_data, file_name, created_at, updated_at
        FROM company_json_documents
        WHERE company_name = %s AND year = %s
        LIMIT 1
        """
        cursor.execute(query, (company_name, year))
        row = cursor.fetchone()
        
        if row:
            parsed_data = row[0]  # JSONB được convert tự động thành dict
            return {
                'parsed_data': parsed_data,
                'file_name': row[1],
                'created_at': row[2].isoformat() if row[2] else None,
                'updated_at': row[3].isoformat() if row[3] else None
            }
        return None
    except Exception as e:
        print(f"Error getting company data: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_companies_list(search: Optional[str] = None) -> List[str]:
    """
    Lấy danh sách tất cả công ty.
    
    Args:
        search: Từ khóa tìm kiếm (optional)
        
    Returns:
        List tên công ty
    """
    if psycopg2 is None:
        raise ImportError("psycopg2 is required. Install with: pip install psycopg2-binary")
    
    conn = None
    cursor = None
    try:
        conn = connect()
        cursor = conn.cursor()
        
        if search:
            query = """
            SELECT DISTINCT company_name
            FROM company_json_documents
            WHERE company_name ILIKE %s
            ORDER BY company_name
            """
            cursor.execute(query, (f'%{search}%',))
        else:
            query = """
            SELECT DISTINCT company_name
            FROM company_json_documents
            ORDER BY company_name
            """
            cursor.execute(query)
        
        companies = [row[0] for row in cursor.fetchall()]
        return companies
    except Exception as e:
        print(f"Error getting companies list: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_years_list(company_name: Optional[str] = None) -> List[int]:
    """
    Lấy danh sách các năm có dữ liệu.
    
    Args:
        company_name: Lọc theo công ty (optional)
        
    Returns:
        List các năm (sorted DESC)
    """
    if psycopg2 is None:
        raise ImportError("psycopg2 is required. Install with: pip install psycopg2-binary")
    
    conn = None
    cursor = None
    try:
        conn = connect()
        cursor = conn.cursor()
        
        if company_name:
            query = """
            SELECT DISTINCT year
            FROM company_json_documents
            WHERE company_name = %s
            ORDER BY year DESC
            """
            cursor.execute(query, (company_name,))
        else:
            query = """
            SELECT DISTINCT year
            FROM company_json_documents
            ORDER BY year DESC
            """
            cursor.execute(query)
        
        years = [row[0] for row in cursor.fetchall()]
        return years
    except Exception as e:
        print(f"Error getting years list: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def search_evidence(keyword: str, company_name: Optional[str] = None, 
                   year: Optional[int] = None, group_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Tìm kiếm trích dẫn (evidences) trong parsed_data.
    
    Args:
        keyword: Từ khóa tìm kiếm
        company_name: Lọc theo công ty (optional)
        year: Lọc theo năm (optional)
        group_id: Lọc theo tiêu chí (optional)
        
    Returns:
        List các evidences tìm thấy
    """
    if psycopg2 is None:
        raise ImportError("psycopg2 is required. Install with: pip install psycopg2-binary")
    
    conn = None
    cursor = None
    try:
        conn = connect()
        cursor = conn.cursor()
        
        # Build WHERE clause
        conditions = ["parsed_data::text LIKE %s"]
        params = [f'%{keyword}%']
        
        if company_name:
            conditions.append("company_name = %s")
            params.append(company_name)
        
        if year:
            conditions.append("year = %s")
            params.append(year)
        
        query = f"""
        SELECT company_name, year, parsed_data
        FROM company_json_documents
        WHERE {' AND '.join(conditions)}
        """
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            company_name_val, year_val, parsed_data = row
            
            # Extract evidences từ parsed_data
            if parsed_data and isinstance(parsed_data, dict):
                analysis_result = parsed_data.get('analysis_result', [])
                for item in analysis_result:
                    item_group_id = item.get('group_id')
                    
                    # Filter by group_id if provided
                    if group_id and item_group_id != group_id:
                        continue
                    
                    evidences = item.get('evidences', [])
                    for evidence in evidences:
                        quote = evidence.get('quote', '')
                        if keyword.lower() in quote.lower():
                            results.append({
                                'company_name': company_name_val,
                                'year': year_val,
                                'group_id': item_group_id,
                                'group_name': item.get('group_name', ''),
                                'quote': quote,
                                'source_ref': evidence.get('source_ref', '')
                            })
        
        return results
    except Exception as e:
        print(f"Error searching evidence: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_stats() -> Dict[str, Any]:
    """
    Lấy thống kê số lượng records.
    
    Returns:
        Dict chứa stats
    """
    if psycopg2 is None:
        raise ImportError("psycopg2 is required. Install with: pip install psycopg2-binary")
    
    conn = None
    cursor = None
    try:
        conn = connect()
        cursor = conn.cursor()
        
        # Total companies
        cursor.execute("SELECT COUNT(DISTINCT company_name) FROM company_json_documents")
        total_companies = cursor.fetchone()[0]
        
        # Total years
        cursor.execute("SELECT COUNT(DISTINCT year) FROM company_json_documents")
        total_years = cursor.fetchone()[0]
        
        # Total records
        cursor.execute("SELECT COUNT(*) FROM company_json_documents")
        total_records = cursor.fetchone()[0]
        
        # Companies by year
        cursor.execute("""
            SELECT year, COUNT(DISTINCT company_name) as count
            FROM company_json_documents
            GROUP BY year
            ORDER BY year DESC
        """)
        companies_by_year = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            'total_companies': total_companies,
            'total_years': total_years,
            'total_records': total_records,
            'companies_by_year': companies_by_year
        }
    except Exception as e:
        print(f"Error getting stats: {e}")
        return {}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

