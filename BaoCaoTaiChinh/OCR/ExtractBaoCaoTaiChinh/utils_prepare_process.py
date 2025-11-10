import re
from typing import Optional, List, Tuple, Dict, Any, Callable
from difflib import SequenceMatcher

from utils_markdownTable_to_xlsx import (
    extract_markdown_tables,
    _parse_markdown_table,
    _create_dataframe_from_rows,
    remove_diacritics
)

try:
    import pandas as pd
except ImportError:
    pd = None


def parse_markdown_pages(content: str) -> List[Tuple[int, str]]:
    """
    Parse markdown content thành các trang.
    
    Format markdown:
        Trang 1
        
        <nội dung trang 1>
        
        ---
        
        Trang 2
        
        <nội dung trang 2>
    
    Args:
        content (str): Nội dung markdown
        
    Returns:
        List[Tuple[int, str]]: Danh sách các tuple (page_number, page_content)
    """
    pages = []
    lines = content.split('\n')
    
    # Tìm tất cả các dòng "Trang N"
    page_starts = []
    for i, line in enumerate(lines):
        match = re.match(r'^\s*Trang\s+(\d+)\s*$', line, re.IGNORECASE)
        if match:
            page_starts.append((i, int(match.group(1))))
    
    if not page_starts:
        # Nếu không tìm thấy "Trang N", tách theo separator '---'
        parts = re.split(r'\n-{3,}\s*\n', content)
        non_empty_parts = [p.strip() for p in parts if p.strip()]
        for idx, part in enumerate(non_empty_parts, 1):
            # Loại bỏ dòng "Trang N" nếu có trong phần
            part_lines = part.split('\n')
            filtered_lines = []
            for line in part_lines:
                # Bỏ qua dòng "Trang N" và separator "---"
                if not re.match(r'^\s*Trang\s+\d+\s*$', line, re.IGNORECASE):
                    if not re.match(r'^\s*-{3,}\s*$', line):
                        filtered_lines.append(line)
            if filtered_lines:
                pages.append((idx, '\n'.join(filtered_lines)))
        return pages
    
    # Tách theo các dòng "Trang N"
    for idx, (start_line, page_num) in enumerate(page_starts):
        # Xác định end_line
        if idx + 1 < len(page_starts):
            end_line = page_starts[idx + 1][0]
        else:
            end_line = len(lines)
        
        # Lấy nội dung trang (bỏ qua dòng "Trang N" và separator "---")
        page_lines = []
        for i in range(start_line + 1, end_line):  # Bỏ qua dòng "Trang N"
            line = lines[i]
            # Bỏ qua separator "---"
            if not re.match(r'^\s*-{3,}\s*$', line):
                page_lines.append(line)
        
        page_content = '\n'.join(page_lines).strip()
        if page_content:  # Chỉ thêm nếu có nội dung
            pages.append((page_num, page_content))
    
    return pages


def process_pages_for_financial_statements(
    pages: List[Tuple[int, str]],
    detect_func: Callable[[str], bool],
    exclude_thuyetminh: bool = True
) -> List[Tuple[int, str, List]]:
    """
    Đi qua từng trang để tìm và extract các bảng của một loại báo cáo tài chính.
    
    Hàm generic này có thể dùng cho bất kỳ loại báo cáo tài chính nào (Cân đối kế toán, 
    Kết quả hoạt động kinh doanh, Lưu chuyển tiền tệ, ...).
    
    LOGIC QUÉT TRANG:
    1. Duyệt qua từng trang trong danh sách pages
    2. Bỏ qua các trang có chứa "thuyết minh báo cáo tài chính" (nếu exclude_thuyetminh=True)
    3. Kiểm tra nếu trang có chứa loại báo cáo (sử dụng detect_func)
    4. Extract tất cả các markdown tables từ trang đó
    5. Trả về danh sách các trang có chứa báo cáo cùng với các tables của nó
    
    Args:
        pages (List[Tuple[int, str]]): Danh sách các trang (page_number, page_content)
        detect_func (Callable[[str], bool]): Hàm detect để kiểm tra xem trang có chứa loại báo cáo hay không
                                            Ví dụ: detect_candoiketoan, detect_ketquahoedongkinhdoanh, detect_luuchuyentiente
        exclude_thuyetminh (bool): Nếu True, bỏ qua các trang có chứa "thuyết minh báo cáo tài chính"
        
    Returns:
        List[Tuple[int, str, List]]: Danh sách các tuple (page_number, page_content, tables)
                                    Mỗi tuple chứa số trang, nội dung trang, và danh sách các tables
    
    Ví dụ:
        >>> from utils_markdownCanDoiKeToanText_DetectTable_to_xlsx import detect_candoiketoan
        >>> pages = parse_markdown_pages(content)
        >>> result_pages = process_pages_for_financial_statements(pages, detect_candoiketoan)
    """
    result_pages = []
    
    # QUÉT QUA TỪNG TRANG
    for page_num, page_content in pages:
        # Bỏ qua các trang có chứa "thuyết minh báo cáo tài chính" nếu exclude_thuyetminh=True
        if exclude_thuyetminh and detect_thuyetminhbaocaotaichinh(page_content):
            print(f"  Skipping page {page_num}: contains 'Thuyet Minh Bao Cao Tai Chinh'")
            continue
        
        # Kiểm tra nếu trang có chứa loại báo cáo này
        if detect_func(page_content):
            # Extract tables từ trang
            tables = extract_markdown_tables(page_content)
            if tables:
                result_pages.append((page_num, page_content, tables))
    
    return result_pages


def parse_ma_so(ma_so_str: Any) -> Optional[int]:
    """
    Parse mã số từ string hoặc số (có thể là "111", "111.", "111.1", 111.0, etc.).
    Chỉ lấy phần số nguyên (trước dấu chấm nếu có).
    
    Args:
        ma_so_str: String hoặc số chứa mã số
        
    Returns:
        Optional[int]: Mã số dạng số nguyên, hoặc None nếu không parse được
        
    Ví dụ:
        >>> parse_ma_so("111")
        111
        >>> parse_ma_so("111.")
        111
        >>> parse_ma_so("111.1")
        111
        >>> parse_ma_so(111.0)
        111
        >>> parse_ma_so(300.0)
        300
        >>> parse_ma_so("abc")
        None
    """
    if ma_so_str is None:
        return None
    
    # Nếu đã là số, convert trực tiếp
    if isinstance(ma_so_str, (int, float)):
        return int(ma_so_str)
    
    # Chuyển sang string nếu chưa phải
    if not isinstance(ma_so_str, str):
        ma_so_str = str(ma_so_str)
    
    # Loại bỏ khoảng trắng
    ma_so_str = ma_so_str.strip()
    
    if not ma_so_str:
        return None
    
    # Tách phần trước dấu chấm (nếu có)
    if '.' in ma_so_str:
        ma_so_str = ma_so_str.split('.')[0]
    
    # Loại bỏ các ký tự không phải số
    ma_so_str = re.sub(r'[^\d]', '', ma_so_str)
    
    try:
        return int(ma_so_str) if ma_so_str else None
    except ValueError:
        return None


def parse_number(value: Any) -> Optional[float]:
    """
    Parse số từ cell value (có thể có dấu phẩy, dấu ngoặc đơn cho số âm, etc.).
    
    Hỗ trợ định dạng Việt Nam:
    - Dấu chấm (.) làm thousand separator: 1.234.567.890
    - Dấu phẩy (,) làm decimal separator: 1.234.567,89
    - Dấu ngoặc đơn cho số âm: (1.234.567.890)
    
    Args:
        value: Giá trị từ cell (có thể là string, int, float, None)
        
    Returns:
        Optional[float]: Số đã parse được, hoặc None nếu không parse được
        
    Ví dụ:
        >>> parse_number("1.234.567.890")
        1234567890.0
        >>> parse_number("(1.234.567.890)")
        -1234567890.0
        >>> parse_number("1.234.567,89")
        1234567.89
        >>> parse_number("")
        None
    """
    if value is None:
        return None
    
    # Nếu đã là số
    if isinstance(value, (int, float)):
        return float(value)
    
    # Chuyển sang string
    if not isinstance(value, str):
        value = str(value)
    
    # Loại bỏ khoảng trắng
    value = value.strip()
    
    if not value or value == '-':
        return None
    
    # Kiểm tra số âm (dấu ngoặc đơn hoặc dấu trừ)
    is_negative = False
    if value.startswith('(') and value.endswith(')'):
        is_negative = True
        value = value[1:-1].strip()
    elif value.startswith('-'):
        is_negative = True
        value = value[1:].strip()
    
    # Xử lý định dạng Việt Nam: dấu chấm là thousand separator, dấu phẩy là decimal separator
    # VD: 1.234.567,89 -> 1234567.89
    if ',' in value:
        # Có dấu phẩy -> có thể là decimal separator
        parts = value.split(',')
        if len(parts) == 2:
            # Có 1 dấu phẩy -> là decimal separator
            integer_part = parts[0].replace('.', '')  # Loại bỏ dấu chấm (thousand separator)
            decimal_part = parts[1]
            try:
                result = float(f"{integer_part}.{decimal_part}")
                return -result if is_negative else result
            except (ValueError, AttributeError):
                pass
    
    # Nếu không có dấu phẩy hoặc parse thất bại, xử lý dấu chấm
    # Có thể là: 1.234.567.890 (thousand separator) hoặc 1.234.567.89 (decimal ở cuối)
    if '.' in value:
        parts = value.split('.')
        if len(parts) >= 2:
            # Kiểm tra phần cuối cùng
            last_part = parts[-1]
            
            # Nếu phần cuối có 1-2 chữ số -> có thể là decimal
            if len(last_part) <= 2 and last_part.isdigit():
                # Có thể là decimal separator
                integer_part = ''.join(parts[:-1])
                decimal_part = last_part
                try:
                    result = float(f"{integer_part}.{decimal_part}")
                    return -result if is_negative else result
                except (ValueError, AttributeError):
                    pass
            
            # Nếu không, tất cả dấu chấm là thousand separator
            try:
                cleaned = value.replace('.', '')
                result = float(cleaned)
                return -result if is_negative else result
            except (ValueError, AttributeError):
                pass
    
    # Nếu không có dấu chấm và dấu phẩy, parse trực tiếp
    try:
        result = float(value)
        return -result if is_negative else result
    except (ValueError, AttributeError):
        pass
    
    # Cuối cùng, loại bỏ tất cả ký tự không phải số và dấu chấm/phẩy
    try:
        cleaned = re.sub(r'[^\d.,]', '', value)
        if cleaned:
            # Thử parse lại
            if ',' in cleaned:
                parts = cleaned.split(',')
                if len(parts) == 2:
                    integer_part = parts[0].replace('.', '')
                    decimal_part = parts[1]
                    result = float(f"{integer_part}.{decimal_part}")
                    return -result if is_negative else result
            else:
                cleaned = cleaned.replace('.', '')
                if cleaned:
                    result = float(cleaned)
                    return -result if is_negative else result
    except (ValueError, AttributeError):
        pass
    
    return None


def find_value_column(df) -> Optional[str]:
    """
    Tìm cột chứa giá trị số cuối năm từ DataFrame.
    
    Các tên cột có thể: "Năm nay", "Số cuối năm", "31/12/2024", "Cuối năm", etc.
    
    Args:
        df: DataFrame chứa dữ liệu (pandas.DataFrame)
        
    Returns:
        Optional[str]: Tên cột chứa giá trị, hoặc None nếu không tìm thấy
        
    Raises:
        ImportError: Nếu pandas chưa được cài đặt
    """
    if pd is None:
        raise ImportError("pandas is required for find_value_column. Install with: pip install pandas")
    
    if df.empty:
        return None
    
    # Các pattern để tìm cột chứa giá trị
    value_patterns = [
        r'năm nay',
        r'số cuối năm',
        r'cuối năm',
        r'\d{1,2}/\d{1,2}/\d{4}',
        r'31/12/\d{4}',
        r'31-12-\d{4}',
        r'\d{4}-\d{2}-\d{2}',
    ]
    
    for col in df.columns:
        col_lower = str(col).lower()
        # Loại bỏ dấu tiếng Việt để so sánh
        col_no_diacritics = remove_diacritics(col_lower)
        
        for pattern in value_patterns:
            if re.search(pattern, col_no_diacritics, re.IGNORECASE):
                return col
        
        # Nếu cột có tên là số hoặc chứa nhiều số (có thể là cột giá trị)
        if re.search(r'\d{4,}', col_lower):  # Chứa ít nhất 4 chữ số liên tiếp
            return col
    
    # Nếu không tìm thấy, thử các cột sau cột "Mã số" và "CHỈ TIÊU"
    ma_so_col = None
    chi_tieu_col = None
    
    for col in df.columns:
        col_lower = str(col).lower()
        col_no_diacritics = remove_diacritics(col_lower)
        
        if 'mã số' in col_no_diacritics or 'ma so' in col_no_diacritics:
            ma_so_col = col
        elif 'chỉ tiêu' in col_no_diacritics or 'chi tieu' in col_no_diacritics:
            chi_tieu_col = col
    
    # Lấy cột thứ 3 trở đi (sau Mã số và CHỈ TIÊU)
    if ma_so_col and chi_tieu_col:
        cols = df.columns.tolist()
        try:
            ma_so_idx = cols.index(ma_so_col)
            chi_tieu_idx = cols.index(chi_tieu_col)
            # Lấy cột đầu tiên sau Mã số và CHỈ TIÊU (không phải Thuyết minh)
            for i in range(max(ma_so_idx, chi_tieu_idx) + 1, len(cols)):
                col = cols[i]
                col_lower = str(col).lower()
                col_no_diacritics = remove_diacritics(col_lower)
                
                # Bỏ qua cột Thuyết minh
                if 'thuyết minh' not in col_no_diacritics and 'thuyet minh' not in col_no_diacritics:
                    # Kiểm tra xem cột này có chứa số không
                    sample_value = df[col].dropna().head(5)
                    if not sample_value.empty:
                        # Nếu có ít nhất 1 giá trị có thể parse thành số
                        for val in sample_value:
                            if parse_number(val) is not None:
                                return col
        except (ValueError, IndexError):
            pass
    
    # Mặc định: lấy cột thứ 3 (sau Mã số và CHỈ TIÊU)
    if len(df.columns) >= 3:
        return df.columns[2]
    
    return None


def find_ma_so_column(df) -> Optional[str]:
    """
    Tìm cột chứa mã số từ DataFrame.
    
    Logic tìm kiếm (theo thứ tự ưu tiên):
    1. Tìm cột có tên chứa "mã số" hoặc "ma so"
    2. Tìm cột có tên chứa "mã" và "số" (có thể tách rời, như "Mã Thuyết số")
    3. Tìm cột có giá trị là số (100, 110, 111, etc.) và không phải cột giá trị (có ngày tháng)
    4. Mặc định: cột đầu tiên (nếu không tìm thấy)
    
    Args:
        df: DataFrame chứa dữ liệu (pandas.DataFrame)
        
    Returns:
        Optional[str]: Tên cột chứa mã số, hoặc None nếu không tìm thấy
        
    Raises:
        ImportError: Nếu pandas chưa được cài đặt
    """
    if pd is None:
        raise ImportError("pandas is required for find_ma_so_column. Install with: pip install pandas")
    
    if df.empty:
        return None
    
    # Bước 1: Tìm cột có tên chứa "ma so" (sau khi lowercase và bỏ dấu)
    # Cho phép match 3/4 ký tự (75%) - ví dụ: "m so" cũng match với "ma so"
    target_pattern = "ma so"
    
    for col in df.columns:
        col_lower = str(col).lower()
        col_no_diacritics = remove_diacritics(col_lower)
        
        # Kiểm tra chứa "ma so" chính xác (nhanh hơn)
        if target_pattern in col_no_diacritics:
            return col
        
        # Kiểm tra match 3/4 ký tự (75%) - fuzzy matching
        # Tìm các cặp từ liên tiếp và so khớp với threshold 0.75
        words = col_no_diacritics.split()
        if len(words) >= 2:
            # Thử các cặp từ liên tiếp
            for i in range(len(words) - 1):
                candidate = f"{words[i]} {words[i+1]}"
                similarity = SequenceMatcher(None, target_pattern, candidate).ratio()
                if similarity >= 0.75:  # 3/4 = 0.75 (cho phép "m so", "ma so", etc.)
                    return col
    
    # Bước 3: Tìm cột có giá trị là số (100, 110, 111, etc.)
    # Kiểm tra các cột không phải là cột giá trị (có ngày tháng hoặc "VND")
    value_col_keywords = ['vnd', 'năm', 'nam', 'ngày', 'ngay', '/', '-']
    
    for col in df.columns:
        col_lower = str(col).lower()
        col_no_diacritics = remove_diacritics(col_lower)
        
        # Bỏ qua cột có chứa từ khóa giá trị
        is_value_col = any(keyword in col_no_diacritics for keyword in value_col_keywords)
        if is_value_col:
            continue
        
        # Kiểm tra xem cột này có chứa giá trị số hợp lệ (mã số) không
        # Mã số thường là số nguyên từ 100 trở lên
        sample_values = df[col].dropna().head(10)
        ma_so_count = 0
        
        for val in sample_values:
            # Parse giá trị
            if pd.api.types.is_numeric_dtype(type(val)):
                # Nếu là số, kiểm tra xem có phải mã số không (>= 100)
                if isinstance(val, (int, float)) and val >= 100:
                    ma_so_count += 1
            else:
                # Nếu là string, thử parse
                parsed = parse_ma_so(str(val))
                if parsed is not None and parsed >= 100:
                    ma_so_count += 1
        
        # Nếu có ít nhất 50% giá trị là mã số hợp lệ (>= 100)
        if len(sample_values) > 0 and ma_so_count >= len(sample_values) * 0.5:
            return col
    
    # Bước 4: Mặc định: cột đầu tiên (nếu không tìm thấy)
    if len(df.columns) > 0:
        return df.columns[0]
    
    return None

def update_json_with_ma_so(data: Dict[str, Any], ma_so: int, value: Optional[float]) -> bool:
    """
    Cập nhật giá trị vào JSON structure dựa trên mã số.
    
    Hàm này có thể dùng chung cho tất cả các loại báo cáo tài chính có cấu trúc JSON
    với mã số (ma_so) và giá trị (so_cuoi_nam, so_dau_nam, etc.).
    
    Với cấu trúc nested/hierarchical, hàm sẽ đệ quy tìm và cập nhật giá trị.
    
    Args:
        data (Dict[str, Any]): JSON structure (có thể là nested dict)
        ma_so (int): Mã số cần tìm
        value (Optional[float]): Giá trị cần cập nhật
        
    Returns:
        bool: True nếu tìm thấy và cập nhật được, False nếu không
        
    Ví dụ:
        >>> data = {"section": {"ma_so": 100, "so_cuoi_nam": None}}
        >>> update_json_with_ma_so(data, 100, 1234.56)
        True
        >>> data["section"]["so_cuoi_nam"]
        1234.56
    """
    if not isinstance(data, dict):
        return False
    
    for key, val in data.items():
        if isinstance(val, dict):
            # Kiểm tra nếu có key "ma_so" và giá trị khớp
            if "ma_so" in val and val["ma_so"] == ma_so:
                val["so_cuoi_nam"] = value
                return True
            
            # Đệ quy vào các dict con
            if update_json_with_ma_so(val, ma_so, value):
                return True
    
    return False


def replace_null_in_dict(data: Any, replacement: float) -> Any:
    """
    Recursively replace null values in a nested dictionary/list structure.
    
    Hàm này có thể dùng chung cho tất cả các loại báo cáo tài chính khi cần thay thế
    giá trị null trong JSON structure bằng một giá trị mặc định (ví dụ: 0).
    
    Args:
        data: Dictionary, list, or primitive value
        replacement: Value to replace null with
    
    Returns:
        Modified data structure with null replaced
    
    Ví dụ:
        >>> data = {"ma_so": 100, "so_cuoi_nam": None, "children": [{"ma_so": 111, "so_cuoi_nam": None}]}
        >>> result = replace_null_in_dict(data, 0)
        >>> result["so_cuoi_nam"]
        0
        >>> result["children"][0]["so_cuoi_nam"]
        0
    """
    if data is None:
        return replacement
    elif isinstance(data, dict):
        return {key: replace_null_in_dict(value, replacement) for key, value in data.items()}
    elif isinstance(data, list):
        return [replace_null_in_dict(item, replacement) for item in data]
    else:
        return data


def detect_thuyetminhbaocaotaichinh(text: str, threshold: float = 0.8) -> bool:
    """
    Phát hiện xem văn bản có chứa "thuyết minh báo cáo tài chính" hay không.
    
    Logic:
    1. Lowercase toàn bộ văn bản
    2. Loại bỏ dấu tiếng Việt
    3. So khớp fuzzy 80% với "thuyet minh bao cao tai chinh"
    
    Args:
        text (str): Văn bản cần kiểm tra
        threshold (float): Ngưỡng so khớp (mặc định: 0.8 = 80%)
        
    Returns:
        bool: True nếu tìm thấy "thuyết minh báo cáo tài chính", False nếu không
        
    Ví dụ:
        >>> detect_thuyetminhbaocaotaichinh("THUYẾT MINH BÁO CÁO TÀI CHÍNH")  # True
        >>> detect_thuyetminhbaocaotaichinh("THUYET MINH BAO CAO TAI CHINH")   # True
        >>> detect_thuyetminhbaocaotaichinh("Thuyết minh báo cáo")             # True (fuzzy)
        >>> detect_thuyetminhbaocaotaichinh("Bảng cân đối kế toán")            # False
    """
    # Lowercase và loại bỏ dấu
    text_lower = text.lower()
    text_khong_dau = remove_diacritics(text_lower)
    
    # Pattern chuẩn để so khớp (ưu tiên pattern đầy đủ, sau đó là pattern ngắn hơn)
    # Chỉ focus vào "thuyet minh" để tránh match với "báo cáo tài chính" chung chung
    patterns = [
        "thuyet minh bao cao tai chinh",  # Pattern đầy đủ
        "thuyet minh bao cao",            # Pattern rút gọn
    ]
    
    # Kiểm tra từng pattern (ưu tiên pattern dài hơn)
    for pattern in patterns:
        # Kiểm tra nếu pattern xuất hiện trực tiếp
        if pattern in text_khong_dau:
            return True
        
        # Fuzzy matching: tìm cụm từ có độ dài tương tự và so khớp
        words = text_khong_dau.split()
        pattern_words = pattern.split()
        
        if len(pattern_words) > len(words):
            continue
        
        for i in range(len(words) - len(pattern_words) + 1):
            candidate = ' '.join(words[i:i+len(pattern_words)])
            similarity = SequenceMatcher(None, pattern, candidate).ratio()
            
            if similarity >= threshold:
                return True
    
    return False

