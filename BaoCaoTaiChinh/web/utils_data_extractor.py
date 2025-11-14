"""
Utilities to extract financial indicators from JSON data.
"""

from typing import Optional, Dict, Any, List
import json
import re
from pathlib import Path


def extract_value_from_json(json_data: Dict[str, Any], path: str) -> Optional[float]:
    """
    Extract value from JSON using dot notation path.
    
    Args:
        json_data: JSON data dictionary
        path: Dot notation path (e.g., "can_doi_ke_toan.tai_san.tong_cong_tai_san_270.so_cuoi_nam")
        
    Returns:
        Value if found, None otherwise
    """
    try:
        keys = path.split('.')
        value = json_data
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return None
            else:
                return None
        
        # Try to convert to float
        if isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, str):
            # Try to parse string number
            try:
                return float(value.replace(',', ''))
            except (ValueError, AttributeError):
                return None
        
        return None
    except Exception as e:
        print(f"Error extracting value from path {path}: {e}")
        return None


def extract_all_indicators_recursive(data: Dict[str, Any], prefix: str = "", indicators: List[Dict] = None) -> List[Dict]:
    """
    Recursively extract all indicators from JSON data.
    
    Args:
        data: JSON data dictionary
        prefix: Current path prefix
        indicators: List to collect indicators
        
    Returns:
        List of indicators with path, ma_so, and value
    """
    if indicators is None:
        indicators = []
    
    if isinstance(data, dict):
        for key, value in data.items():
            current_path = f"{prefix}.{key}" if prefix else key
            
            # Check if this is an indicator (has ma_so and so_cuoi_nam)
            if isinstance(value, dict):
                if "ma_so" in value and "so_cuoi_nam" in value:
                    indicators.append({
                        "key": key,
                        "path": f"{current_path}.so_cuoi_nam",
                        "ma_so": value.get("ma_so"),
                        "value": value.get("so_cuoi_nam"),
                        "full_path": current_path
                    })
                
                # Recursively process nested objects
                extract_all_indicators_recursive(value, current_path, indicators)
            elif isinstance(value, (int, float)):
                # Direct value
                if prefix and "so_cuoi_nam" in prefix:
                    indicators.append({
                        "key": key,
                        "path": current_path,
                        "ma_so": None,
                        "value": value,
                        "full_path": current_path
                    })
    
    return indicators


def extract_indicators_recursive(data: Dict[str, Any], prefix: str = "", parent_key: str = "", indicators: List[Dict] = None, report_type: str = "balance-sheet") -> List[Dict]:
    """
    Recursively extract all indicators from JSON data.
    Extracts all fields that have ma_so and so_cuoi_nam.
    Uses ten_chi_tieu for labels when available.
    
    Args:
        data: JSON data dictionary
        prefix: Current path prefix
        parent_key: Parent key name
        indicators: List to collect indicators
        report_type: Report type for label mapping
        
    Returns:
        List of indicators
    """
    if indicators is None:
        indicators = []
    
    if not isinstance(data, dict):
        return indicators
    
    try:
        for key, value in data.items():
            if not isinstance(key, str):
                continue
                
            current_path = f"{prefix}.{key}" if prefix else key
            
            # Check if this node has ma_so (it's an indicator)
            if isinstance(value, dict):
                # Check if this dict has ma_so field (it's an indicator node)
                if "ma_so" in value:
                    ma_so = value.get("ma_so")
                    so_cuoi_nam = value.get("so_cuoi_nam")
                    ten_chi_tieu = value.get("ten_chi_tieu")
                    
                    # Use ten_chi_tieu if available, otherwise generate from key
                    if ten_chi_tieu:
                        label_vn = str(ten_chi_tieu)
                        label = str(ten_chi_tieu)  # Can be improved with translation mapping
                    else:
                        # Generate label from key name - improve formatting
                        # Remove numbers and underscores, make readable
                        clean_key = key
                        # Remove trailing numbers like "_100", "_20", etc.
                        clean_key = re.sub(r'_\d+$', '', clean_key)
                        # Replace underscores with spaces and title case
                        label_vn = clean_key.replace("_", " ").title()
                        label = clean_key.replace("_", " ").title()
                    
                    # Create indicator entry with hierarchy info
                    indicator_path = f"{current_path}.so_cuoi_nam"
                    # Calculate level based on path depth
                    level = current_path.count('.')
                    # Get parent path (remove last key)
                    parent_path = '.'.join(current_path.split('.')[:-1]) if '.' in current_path else None
                    
                    indicators.append({
                        "key": key,
                        "path": indicator_path,
                        "ma_so": ma_so,
                        "label": label,
                        "label_vn": label_vn,
                        "full_path": current_path,
                        "level": level,
                        "parent_path": parent_path,
                        "has_children": False  # Will be set later when building tree
                    })
                
                # IMPORTANT: Always recurse into nested dicts to find ALL indicators
                # Even if this node has ma_so, it might have children with ma_so too
                extract_indicators_recursive(value, current_path, key, indicators, report_type)
    except Exception as e:
        # Log error but continue processing
        print(f"Error in extract_indicators_recursive at path {prefix}: {e}")
    
    return indicators


def get_balance_sheet_indicators(json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Get balance sheet indicators from JSON data.
    Recursively extracts ALL indicators from the JSON structure.
    
    Args:
        json_data: Balance sheet JSON data
        
    Returns:
        List of indicators
    """
    if not isinstance(json_data, dict):
        print("Warning: json_data is not a dict in get_balance_sheet_indicators")
        return []
    
    # Extract all indicators recursively from the JSON structure
    indicators = extract_indicators_recursive(json_data, "", "", [], "balance-sheet")
    
    print(f"Extracted {len(indicators)} balance sheet indicators")
    
    # Sort indicators by ma_so for consistent ordering
    def sort_key(x):
        ma_so = x["ma_so"]
        if isinstance(ma_so, (int, float)):
            return (ma_so, x["full_path"])
        elif isinstance(ma_so, str):
            try:
                # Try to convert to float for proper numeric sorting
                return (float(ma_so), x["full_path"])
            except ValueError:
                return (999999, x["full_path"])
        else:
            return (999999, x["full_path"])
    
    indicators.sort(key=sort_key)
    
    return indicators


def get_income_statement_indicators(json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Get income statement indicators from JSON data.
    Recursively extracts ALL indicators from the JSON structure.
    
    Args:
        json_data: Income statement JSON data
        
    Returns:
        List of indicators
    """
    if not isinstance(json_data, dict):
        print("Warning: json_data is not a dict in get_income_statement_indicators")
        return []
    
    # Extract all indicators recursively from the JSON structure
    indicators = extract_indicators_recursive(json_data, "", "", [], "income-statement")
    
    print(f"Extracted {len(indicators)} income statement indicators")
    
    # Sort indicators by ma_so for consistent ordering
    # Handle both numeric and string ma_so (e.g., "1", "1.1", "2.1")
    def sort_key(x):
        ma_so = x["ma_so"]
        if isinstance(ma_so, (int, float)):
            return (ma_so, x["full_path"])
        elif isinstance(ma_so, str):
            try:
                # Try to convert to float for proper numeric sorting
                return (float(ma_so), x["full_path"])
            except ValueError:
                return (999999, x["full_path"])
        else:
            return (999999, x["full_path"])
    
    indicators.sort(key=sort_key)
    
    return indicators


def get_cash_flow_indicators(json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Get cash flow indicators from JSON data.
    Recursively extracts ALL indicators from the JSON structure.
    
    Args:
        json_data: Cash flow JSON data
        
    Returns:
        List of indicators
    """
    if not isinstance(json_data, dict):
        print("Warning: json_data is not a dict in get_cash_flow_indicators")
        return []
    
    # Extract all indicators recursively from the JSON structure
    indicators = extract_indicators_recursive(json_data, "", "", [], "cash-flow")
    
    print(f"Extracted {len(indicators)} cash flow indicators")
    
    # Sort indicators by ma_so for consistent ordering
    def sort_key(x):
        ma_so = x["ma_so"]
        if isinstance(ma_so, (int, float)):
            return (ma_so, x["full_path"])
        elif isinstance(ma_so, str):
            try:
                # Try to convert to float for proper numeric sorting
                return (float(ma_so), x["full_path"])
            except ValueError:
                return (999999, x["full_path"])
        else:
            return (999999, x["full_path"])
    
    indicators.sort(key=sort_key)
    
    return indicators


def get_indicators_for_report_type(json_data: Dict[str, Any], report_type: str) -> List[Dict[str, Any]]:
    """
    Get indicators for a specific report type.
    
    Args:
        json_data: JSON data
        report_type: Report type ("balance-sheet", "income-statement", "cash-flow")
        
    Returns:
        List of indicators
    """
    if report_type == "balance-sheet":
        return get_balance_sheet_indicators(json_data)
    elif report_type == "income-statement":
        return get_income_statement_indicators(json_data)
    elif report_type == "cash-flow":
        return get_cash_flow_indicators(json_data)
    else:
        return []

