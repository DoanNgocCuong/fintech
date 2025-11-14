"""
Utilities to extract financial indicators from JSON data.
"""

from typing import Optional, Dict, Any, List
import json
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
    
    if isinstance(data, dict):
        for key, value in data.items():
            current_path = f"{prefix}.{key}" if prefix else key
            
            # Check if this node has ma_so and so_cuoi_nam (it's an indicator)
            if isinstance(value, dict):
                if "ma_so" in value:
                    ma_so = value.get("ma_so")
                    so_cuoi_nam = value.get("so_cuoi_nam")
                    
                    # Generate label from key name
                    label_vn = key.replace("_", " ").title()
                    label = key.replace("_", " ").title()
                    
                    # Create indicator entry
                    indicator_path = f"{current_path}.so_cuoi_nam"
                    indicators.append({
                        "key": key,
                        "path": indicator_path,
                        "ma_so": ma_so,
                        "label": label,
                        "label_vn": label_vn,
                        "full_path": current_path
                    })
                
                # Recursively process nested objects
                extract_indicators_recursive(value, current_path, key, indicators, report_type)
    
    return indicators


def get_balance_sheet_indicators(json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Get balance sheet indicators from JSON data.
    Uses both fixed mapping for main indicators and recursive extraction.
    
    Args:
        json_data: Balance sheet JSON data
        
    Returns:
        List of indicators
    """
    indicators = []
    
    # Main indicators mapping (priority indicators)
    main_indicator_paths = {
        "tong_cong_tai_san": {
            "path": "can_doi_ke_toan.tai_san.tong_cong_tai_san_270.so_cuoi_nam",
            "ma_so": 270,
            "label": "Total assets",
            "label_vn": "Tổng tài sản"
        },
        "tai_san_ngan_han": {
            "path": "can_doi_ke_toan.tai_san.A_tai_san_ngan_han_100.so_cuoi_nam",
            "ma_so": 100,
            "label": "Current assets",
            "label_vn": "Tài sản ngắn hạn"
        },
        "tai_san_dai_han": {
            "path": "can_doi_ke_toan.tai_san.B_tai_san_dai_han_200.so_cuoi_nam",
            "ma_so": 200,
            "label": "Non-current assets",
            "label_vn": "Tài sản dài hạn"
        },
        "tong_no_phai_tra": {
            "path": "can_doi_ke_toan.nguon_von.C_no_phai_tra_300.so_cuoi_nam",
            "ma_so": 300,
            "label": "Total liabilities",
            "label_vn": "Tổng nợ phải trả"
        },
        "no_ngan_han": {
            "path": "can_doi_ke_toan.nguon_von.C_no_phai_tra_300.I_no_ngan_han_310.so_cuoi_nam",
            "ma_so": 310,
            "label": "Current liabilities",
            "label_vn": "Nợ ngắn hạn"
        },
        "no_dai_han": {
            "path": "can_doi_ke_toan.nguon_von.C_no_phai_tra_300.II_no_dai_han_330.so_cuoi_nam",
            "ma_so": 330,
            "label": "Non-current liabilities",
            "label_vn": "Nợ dài hạn"
        },
        "tong_von_chu_so_huu": {
            "path": "can_doi_ke_toan.nguon_von.D_von_chu_so_huu_400.so_cuoi_nam",
            "ma_so": 400,
            "label": "Total equity",
            "label_vn": "Tổng vốn chủ sở hữu"
        },
        "tong_cong_nguon_von": {
            "path": "can_doi_ke_toan.nguon_von.tong_cong_nguon_von_440.so_cuoi_nam",
            "ma_so": 440,
            "label": "Total liabilities & equity",
            "label_vn": "Tổng nguồn vốn"
        }
    }
    
    # Extract main indicators first
    for key, config in main_indicator_paths.items():
        indicators.append({
            "key": key,
            "path": config["path"],
            "ma_so": config["ma_so"],
            "label": config["label"],
            "label_vn": config["label_vn"]
        })
    
    # Optionally: Extract all indicators recursively
    # Uncomment below to extract all indicators from JSON
    # all_indicators = extract_indicators_recursive(json_data, "", "", [], "balance-sheet")
    # indicators.extend(all_indicators)
    
    return indicators


def get_income_statement_indicators(json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Get income statement indicators from JSON data.
    
    Args:
        json_data: Income statement JSON data
        
    Returns:
        List of indicators
    """
    indicators = []
    
    # Main indicators mapping
    indicator_paths = {
        "doanh_thu_phi_bao_hiem": {
            "path": "ket_qua_hoat_dong_kinh_doanh.01_doanh_thu_phi_bao_hiem.so_cuoi_nam",
            "ma_so": "1",
            "label": "Insurance premium revenue",
            "label_vn": "Doanh thu phí bảo hiểm"
        },
        "phi_nhuong_tai_bao_hiem": {
            "path": "ket_qua_hoat_dong_kinh_doanh.02_phi_nhuong_tai_bao_hiem.so_cuoi_nam",
            "ma_so": "2",
            "label": "Reinsurance premium",
            "label_vn": "Phí nhượng tái bảo hiểm"
        },
        "doanh_thu_phi_bao_hiem_thuan": {
            "path": "ket_qua_hoat_dong_kinh_doanh.03_doanh_thu_phi_bao_hiem_thuan.so_cuoi_nam",
            "ma_so": "3",
            "label": "Net insurance premium revenue",
            "label_vn": "Doanh thu phí bảo hiểm thuần"
        },
        "doanh_thu_thuan": {
            "path": "ket_qua_hoat_dong_kinh_doanh.10_doanh_thu_thuan_hoat_dong_kinh_doanh_bao_hiem.so_cuoi_nam",
            "ma_so": "10",
            "label": "Total revenue",
            "label_vn": "Doanh thu thuần hoạt động kinh doanh bảo hiểm"
        },
        "chi_boi_thuong": {
            "path": "ket_qua_hoat_dong_kinh_doanh.11_chi_boi_thuong.so_cuoi_nam",
            "ma_so": "11",
            "label": "Claims expenses",
            "label_vn": "Chi bồi thường"
        },
        "tong_chi_phi": {
            "path": "ket_qua_hoat_dong_kinh_doanh.18_tong_chi_phi_hoat_dong_kinh_doanh_bao_hiem.so_cuoi_nam",
            "ma_so": "18",
            "label": "Total operating expenses",
            "label_vn": "Tổng chi phí hoạt động kinh doanh bảo hiểm"
        },
        "loi_nhuan_gop": {
            "path": "ket_qua_hoat_dong_kinh_doanh.19_loi_nhuan_gop_hoat_dong_kinh_doanh_bao_hiem.so_cuoi_nam",
            "ma_so": "19",
            "label": "Gross profit",
            "label_vn": "Lợi nhuận gộp hoạt động kinh doanh bảo hiểm"
        },
        "loi_nhuan_thuan": {
            "path": "ket_qua_hoat_dong_kinh_doanh.30_loi_nhuan_thuan_tu_hoat_dong_kinh_doanh.so_cuoi_nam",
            "ma_so": "30",
            "label": "Operating income",
            "label_vn": "Lợi nhuận thuần từ hoạt động kinh doanh"
        },
        "loi_nhuan_truoc_thue": {
            "path": "ket_qua_hoat_dong_kinh_doanh.50_tong_loi_nhuan_ke_toan_truoc_thue.so_cuoi_nam",
            "ma_so": "50",
            "label": "Profit before tax",
            "label_vn": "Tổng lợi nhuận kế toán trước thuế"
        },
        "loi_nhuan_sau_thue": {
            "path": "ket_qua_hoat_dong_kinh_doanh.60_loi_nhuan_sau_thue_thu_nhap_doanh_nghiep.so_cuoi_nam",
            "ma_so": "60",
            "label": "Net income",
            "label_vn": "Lợi nhuận sau thuế thu nhập doanh nghiệp"
        },
        "loi_nhuan_cong_ty_me": {
            "path": "ket_qua_hoat_dong_kinh_doanh.62_loi_nhuan_sau_thue_cua_cong_ty_me.so_cuoi_nam",
            "ma_so": "62",
            "label": "Net income (parent company)",
            "label_vn": "Lợi nhuận sau thuế của công ty mẹ"
        }
    }
    
    # Extract values for each indicator
    for key, config in indicator_paths.items():
        value = extract_value_from_json(json_data, config["path"])
        indicators.append({
            "key": key,
            "path": config["path"],
            "ma_so": config["ma_so"],
            "label": config["label"],
            "label_vn": config["label_vn"],
            "value": value
        })
    
    return indicators


def get_cash_flow_indicators(json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Get cash flow indicators from JSON data.
    
    Args:
        json_data: Cash flow JSON data
        
    Returns:
        List of indicators
    """
    indicators = []
    
    # Main indicators mapping
    indicator_paths = {
        "luu_chuyen_tien_hoat_dong": {
            "path": "bao_cao_luu_chuyen_tien_te.I_luu_chuyen_tien_tu_hoat_dong_kinh_doanh_20.so_cuoi_nam",
            "ma_so": 20,
            "label": "Operating cash flow",
            "label_vn": "Lưu chuyển tiền thuần từ hoạt động kinh doanh"
        },
        "luu_chuyen_tien_dau_tu": {
            "path": "bao_cao_luu_chuyen_tien_te.II_luu_chuyen_tien_tu_hoat_dong_dau_tu_30.so_cuoi_nam",
            "ma_so": 30,
            "label": "Investing cash flow",
            "label_vn": "Lưu chuyển tiền thuần từ hoạt động đầu tư"
        },
        "luu_chuyen_tien_tai_chinh": {
            "path": "bao_cao_luu_chuyen_tien_te.III_luu_chuyen_tien_tu_hoat_dong_tai_chinh_40.so_cuoi_nam",
            "ma_so": 40,
            "label": "Financing cash flow",
            "label_vn": "Lưu chuyển tiền thuần từ hoạt động tài chính"
        },
        "luu_chuyen_tien_thuan": {
            "path": "bao_cao_luu_chuyen_tien_te.luu_chuyen_tien_thuan_trong_ky_50.so_cuoi_nam",
            "ma_so": 50,
            "label": "Net cash flow",
            "label_vn": "Lưu chuyển tiền thuần trong kỳ"
        },
        "tien_dau_ky": {
            "path": "bao_cao_luu_chuyen_tien_te.tien_va_tuong_duong_tien_dau_ky_60.so_cuoi_nam",
            "ma_so": 60,
            "label": "Cash at beginning",
            "label_vn": "Tiền và tương đương tiền đầu kỳ"
        },
        "tien_cuoi_ky": {
            "path": "bao_cao_luu_chuyen_tien_te.tien_va_tuong_duong_tien_cuoi_ky_70.so_cuoi_nam",
            "ma_so": 70,
            "label": "Cash at end",
            "label_vn": "Tiền và tương đương tiền cuối kỳ"
        }
    }
    
    # Extract values for each indicator
    for key, config in indicator_paths.items():
        value = extract_value_from_json(json_data, config["path"])
        indicators.append({
            "key": key,
            "path": config["path"],
            "ma_so": config["ma_so"],
            "label": config["label"],
            "label_vn": config["label_vn"],
            "value": value
        })
    
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

