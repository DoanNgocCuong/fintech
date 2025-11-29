"""
Utilities to extract metrics từ parsed_data.
Tất cả functions làm việc với parsed_data (KHÔNG phải json_raw).
"""

from typing import Optional, Dict, Any, List


# 7 Tiêu chí (Groups)
GROUP_IDS = [
    'governance',
    'incentive',
    'payout',
    'capital',
    'ownership',
    'strategy',
    'risk'
]

GROUP_NAMES = {
    'governance': 'Quản trị (Governance)',
    'incentive': 'Chính sách đãi ngộ (Incentive)',
    'payout': 'Chính sách chi trả (Payout)',
    'capital': 'Vốn và huy động vốn (Capital)',
    'ownership': 'Cơ cấu sở hữu (Ownership)',
    'strategy': 'Chiến lược (Strategy)',
    'risk': 'Rủi ro (Risk)'
}


def extract_metrics_from_parsed_data(parsed_data: Dict[str, Any], group_id: str) -> Dict[str, Any]:
    """
    Extract metrics cho một tiêu chí từ parsed_data.
    
    Args:
        parsed_data: Parsed data từ database
        group_id: Tiêu chí (governance, incentive, payout, ...)
        
    Returns:
        Dict chứa metrics cho group_id đó
    """
    if not isinstance(parsed_data, dict):
        return {}
    
    analysis_result = parsed_data.get('analysis_result', [])
    
    # Tìm item có group_id tương ứng
    for item in analysis_result:
        if item.get('group_id') == group_id:
            metrics = item.get('metrics', {})
            return metrics.get(group_id, {})
    
    return {}


def extract_all_metrics(parsed_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Extract tất cả metrics từ parsed_data.
    
    Args:
        parsed_data: Parsed data từ database
        
    Returns:
        Dict với key là group_id, value là metrics dict
    """
    if not isinstance(parsed_data, dict):
        return {}
    
    all_metrics = {}
    analysis_result = parsed_data.get('analysis_result', [])
    
    for item in analysis_result:
        group_id = item.get('group_id')
        if group_id:
            metrics = item.get('metrics', {})
            all_metrics[group_id] = metrics.get(group_id, {})
    
    return all_metrics


def extract_summary(parsed_data: Dict[str, Any], group_id: Optional[str] = None) -> Dict[str, str]:
    """
    Extract summary từ parsed_data.
    
    Args:
        parsed_data: Parsed data từ database
        group_id: Tiêu chí cụ thể (optional, nếu None thì lấy tất cả)
        
    Returns:
        Dict với key là group_id, value là summary string
    """
    if not isinstance(parsed_data, dict):
        return {}
    
    summaries = {}
    analysis_result = parsed_data.get('analysis_result', [])
    
    for item in analysis_result:
        item_group_id = item.get('group_id')
        if item_group_id:
            if group_id is None or item_group_id == group_id:
                summary = item.get('summary', '')
                summaries[item_group_id] = summary
    
    return summaries


def extract_evidences(parsed_data: Dict[str, Any], group_id: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
    """
    Extract evidences từ parsed_data.
    
    Args:
        parsed_data: Parsed data từ database
        group_id: Tiêu chí cụ thể (optional, nếu None thì lấy tất cả)
        
    Returns:
        Dict với key là group_id, value là list evidences
    """
    if not isinstance(parsed_data, dict):
        return {}
    
    all_evidences = {}
    analysis_result = parsed_data.get('analysis_result', [])
    
    for item in analysis_result:
        item_group_id = item.get('group_id')
        if item_group_id:
            if group_id is None or item_group_id == group_id:
                evidences = item.get('evidences', [])
                all_evidences[item_group_id] = evidences
    
    return all_evidences


def get_metrics_by_group(parsed_data: Dict[str, Any], group_id: str) -> Dict[str, Any]:
    """
    Lấy metrics theo group từ parsed_data.
    Alias cho extract_metrics_from_parsed_data.
    
    Args:
        parsed_data: Parsed data từ database
        group_id: Tiêu chí
        
    Returns:
        Dict chứa metrics
    """
    return extract_metrics_from_parsed_data(parsed_data, group_id)


def parse_parsed_data_jsonb(parsed_data_jsonb: Any) -> Dict[str, Any]:
    """
    Parse JSONB thành Python dict (nếu cần).
    Thường thì psycopg2 tự động convert JSONB thành dict.
    
    Args:
        parsed_data_jsonb: JSONB từ database
        
    Returns:
        Python dict
    """
    if isinstance(parsed_data_jsonb, dict):
        return parsed_data_jsonb
    elif isinstance(parsed_data_jsonb, str):
        import json
        return json.loads(parsed_data_jsonb)
    else:
        return {}


def format_company_data_response(parsed_data: Dict[str, Any], company_name: str, year: int) -> Dict[str, Any]:
    """
    Format response cho API /api/company-data.
    
    Args:
        parsed_data: Parsed data từ database
        company_name: Tên công ty
        year: Năm
        
    Returns:
        Formatted response dict
    """
    metrics = extract_all_metrics(parsed_data)
    summaries = extract_summary(parsed_data)
    evidences = extract_evidences(parsed_data)
    
    return {
        'success': True,
        'company_name': company_name,
        'year': year,
        'metrics': metrics,
        'summary': summaries,
        'evidences': evidences
    }

