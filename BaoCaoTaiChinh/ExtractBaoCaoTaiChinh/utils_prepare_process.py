import re
from typing import Optional, List, Tuple, Dict, Any, Callable
from difflib import SequenceMatcher 

from utils_markdownTable_to_xlsx import (
    extract_markdown_tables,
    _parse_markdown_table,
    _create_dataframe_from_rows,
    remove_diacritics,
    _is_separator_line
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
                                            Ví dụ: detect_candoiketoan, detect_ketquahoatdongkinhdoanh, detect_luuchuyentiente
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


def normalize_ma_so(ma_so: str) -> str:
    """
    Normalize mã số bằng cách loại bỏ số 0 đứng đầu ở phần nguyên.
    Hỗ trợ cả mã số chính (1, 01, 001) và mã số phụ (1.1, 01.1, 001.1).
    
    Args:
        ma_so (str): Mã số dạng string (ví dụ: "1", "01", "1.1", "01.1", "001.2")
        
    Returns:
        str: Mã số đã được normalize (ví dụ: "1", "1.1", "1.2")
        
    Ví dụ:
        >>> normalize_ma_so("1")
        "1"
        >>> normalize_ma_so("01")
        "1"
        >>> normalize_ma_so("001")
        "1"
        >>> normalize_ma_so("1.1")
        "1.1"
        >>> normalize_ma_so("01.1")
        "1.1"
        >>> normalize_ma_so("001.1")
        "1.1"
        >>> normalize_ma_so("01.2")
        "1.2"
    """
    if not ma_so or not isinstance(ma_so, str):
        return ma_so
    
    # Loại bỏ khoảng trắng
    ma_so = ma_so.strip()
    
    if not ma_so:
        return ma_so
    
    # Kiểm tra xem có dấu chấm không
    if '.' in ma_so:
        # Có phần thập phân (1.1, 01.1, etc.)
        parts = ma_so.split('.')
        if len(parts) == 2:
            integer_part = parts[0].strip()
            decimal_part = parts[1].strip()
            
            # FIX: Nếu phần thập phân chỉ có số 0 (0, 00, 000, ...), coi như không có phần thập phân
            # Điều này xử lý trường hợp Excel trả về float 100.0 thành string "100.0"
            if decimal_part and decimal_part.replace('0', '').strip() == '':
                # Phần thập phân chỉ có số 0 -> normalize như số nguyên
                try:
                    integer_part_int = int(integer_part)
                    return str(integer_part_int)
                except ValueError:
                    return integer_part
            
            # Normalize phần nguyên (loại bỏ số 0 đứng đầu)
            try:
                integer_part_int = int(integer_part)
                integer_part_normalized = str(integer_part_int)
            except ValueError:
                integer_part_normalized = integer_part
            
            # Giữ nguyên phần thập phân (nếu không phải toàn số 0)
            if decimal_part:
                return f"{integer_part_normalized}.{decimal_part}"
            else:
                return integer_part_normalized
        else:
            # Nhiều hơn 1 dấu chấm -> không hợp lệ, trả về nguyên bản
            return ma_so
    else:
        # Chỉ có phần nguyên (1, 01, 001)
        try:
            # Loại bỏ số 0 đứng đầu
            num = int(ma_so)
            return str(num)
        except ValueError:
            # Không parse được -> trả về nguyên bản
            return ma_so


def parse_ma_so_full(ma_so_str: Any) -> Optional[str]:
    """
    Parse mã số đầy đủ từ string hoặc số (có thể là "1", "1.1", "1.2", "01.3", etc.).
    Trả về mã số dạng string đã được normalize (loại bỏ số 0 đứng đầu) để hỗ trợ mã số phụ.
    
    Hàm này sẽ normalize mã số: "01.1" -> "1.1", "01.2" -> "1.2", "001.3" -> "1.3"
    để đảm bảo có thể match cả "1.1" và "01.1", "1.2" và "01.2", etc.
    
    Args:
        ma_so_str: String hoặc số chứa mã số
        
    Returns:
        Optional[str]: Mã số dạng string đã được normalize (ví dụ: "1", "1.1", "1.2"), hoặc None nếu không parse được
        
    Ví dụ:
        >>> parse_ma_so_full("1")
        "1"
        >>> parse_ma_so_full("01")
        "1"
        >>> parse_ma_so_full("1.1")
        "1.1"
        >>> parse_ma_so_full("01.1")
        "1.1"
        >>> parse_ma_so_full("001.2")
        "1.2"
        >>> parse_ma_so_full("01.2")
        "1.2"
        >>> parse_ma_so_full("111")
        "111"
        >>> parse_ma_so_full(111.0)
        "111"
        >>> parse_ma_so_full(1.1)
        "1.1"
        >>> parse_ma_so_full("abc")
        None
    """
    if ma_so_str is None:
        return None
    
    # Chuyển sang string
    if not isinstance(ma_so_str, str):
        # Nếu là số float (1.1, 1.2), giữ nguyên phần thập phân
        if isinstance(ma_so_str, float):
            # Kiểm tra xem có phần thập phân không
            if ma_so_str == int(ma_so_str):
                return str(int(ma_so_str))
            else:
                # Giữ nguyên định dạng float nhưng normalize
                return normalize_ma_so(str(ma_so_str))
        else:
            ma_so_str = str(ma_so_str)
    
    # Loại bỏ khoảng trắng
    ma_so_str = ma_so_str.strip()
    
    if not ma_so_str:
        return None
    
    # Loại bỏ các ký tự không phải số, dấu chấm
    # Giữ lại số và dấu chấm (để hỗ trợ mã số phụ như 1.1, 1.2)
    cleaned = re.sub(r'[^\d.]', '', ma_so_str)
    
    if not cleaned:
        return None
    
    # Normalize mã số (loại bỏ số 0 đứng đầu)
    return normalize_ma_so(cleaned)


def parse_number(value: Any) -> Optional[float]:
    """
    Parse số từ cell value (có thể có dấu phẩy, dấu ngoặc đơn cho số âm, etc.).
    
    Hỗ trợ cả định dạng Việt Nam và Mỹ:
    
    Định dạng Việt Nam:
    - Dấu chấm (.) làm thousand separator: 1.234.567.890
    - Dấu phẩy (,) làm decimal separator: 1.234.567,89
    - Dấu ngoặc đơn cho số âm: (1.234.567.890)
    
    Định dạng Mỹ:
    - Dấu phẩy (,) làm thousand separator: 2,438,488,070,081
    - Dấu chấm (.) làm decimal separator: 1,234.56
    - Dấu ngoặc đơn cho số âm: (1,877,469,473,712)
    
    Logic detect format:
    1. Nếu có cả comma và dot: detect dựa trên vị trí (dot ở cuối → US format)
    2. Nếu chỉ có comma: Check pattern (nhiều comma → US format, 1 comma → có thể decimal)
    3. Nếu chỉ có dot: VN format
    
    Args:
        value: Giá trị từ cell (có thể là string, int, float, None)
        
    Returns:
        Optional[float]: Số đã parse được, hoặc None nếu không parse được
        
    Ví dụ:
        >>> parse_number("1.234.567.890")  # VN format
        1234567890.0
        >>> parse_number("2,438,488,070,081")  # US format
        2438488070081.0
        >>> parse_number("(1.234.567.890)")  # VN format negative
        -1234567890.0
        >>> parse_number("(1,877,469,473,712)")  # US format negative
        -1877469473712.0
        >>> parse_number("1.234.567,89")  # VN format with decimal
        1234567.89
        >>> parse_number("1,234.56")  # US format with decimal
        1234.56

**Format VN cũ (vẫn hoạt động):**
- `1.234.567.890` → `1234567890.0` ✓
- `(1.234.567.890)` → `-1234567890.0` ✓
- `1.234.567,89` → `1234567.89` ✓
- `1.234,56` → `1234.56` ✓
- `1234567890` → `1234567890.0` ✓

**Format Mỹ mới (mới thêm):**
- `2,438,488,070,081` → `2438488070081.0` ✓
- `(1,877,469,473,712)` → `-1877469473712.0` ✓
- `(415,040)` → `-415040.0` ✓
- `1,234.56` → `1234.56` ✓

### Logic detect:

1. Có cả comma và dot:
   - `1.234,56` (comma sau dot) → VN format ✓
   - `1,234.56` (dot sau comma) → US format ✓

2. Chỉ có comma:
   - Nhiều comma → US format (thousand separator)
   - 1 comma + phần sau ≤ 2 chữ số → VN format (có thể là decimal)

3. Chỉ có dot:
   - Giữ nguyên logic cũ → VN format ✓

### Kết luận:

- Format VN cũ hoạt động bình thường
- Đã thêm hỗ trợ format Mỹ
- Không ảnh hưởng đến code cũ
- Auto-detect format tự động

JSON sẽ có dữ liệu đúng cho cả format VN và Mỹ.        
    """
    if value is None:
        return None
    
    # Nếu đã là số
    if isinstance(value, (int, float)):
        try:
            # Tránh trả về NaN
            if pd is not None and pd.isna(value):
                return None
        except Exception:
            pass
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
    
    has_comma = ',' in value
    has_dot = '.' in value
    
    # CASE 1: Có cả comma và dot → Detect format dựa trên pattern
    if has_comma and has_dot:
        # Check format: "1,234.56" (US) vs "1.234,56" (VN)
        comma_pos = value.rfind(',')
        dot_pos = value.rfind('.')
        
        if comma_pos > dot_pos:
            # Comma ở sau dot → VN format: "1.234,56"
            parts = value.split(',')
            if len(parts) == 2:
                integer_part = parts[0].replace('.', '')  # Remove thousand separators
                decimal_part = parts[1]
                try:
                    result = float(f"{integer_part}.{decimal_part}")
                    return -result if is_negative else result
                except (ValueError, AttributeError):
                    pass
        else:
            # Dot ở sau comma → US format: "1,234.56"
            parts = value.split('.')
            if len(parts) == 2:
                integer_part = parts[0].replace(',', '')  # Remove thousand separators
                decimal_part = parts[1]
                try:
                    result = float(f"{integer_part}.{decimal_part}")
                    return -result if is_negative else result
                except (ValueError, AttributeError):
                    pass
    
    # CASE 2: Chỉ có comma (không có dot)
    elif has_comma and not has_dot:
        # Có thể là US format (comma = thousand) hoặc VN format (comma = decimal)
        # Detect: Nếu có nhiều comma hoặc comma tạo group 3 chữ số → US format
        parts = value.split(',')
        
        if len(parts) == 2:
            # Chỉ có 1 comma → có thể là decimal separator (VN) hoặc thousand separator (US)
            # Check pattern: nếu phần sau comma có 3 chữ số → US format (thousand)
            # Nếu phần sau comma có 1-2 chữ số → có thể là decimal (VN)
            if len(parts[1]) <= 2 and parts[1].isdigit():
                # Có thể là VN format với decimal separator
                integer_part = parts[0].replace('.', '')
                decimal_part = parts[1]
                try:
                    result = float(f"{integer_part}.{decimal_part}")
                    return -result if is_negative else result
                except (ValueError, AttributeError):
                    pass
            
            # Hoặc có thể là US format (thousand separator) với chỉ 1 group
            # VD: "415,040" → "415040"
            try:
                cleaned = value.replace(',', '')
                result = float(cleaned)
                return -result if is_negative else result
            except (ValueError, AttributeError):
                pass
        else:
            # Nhiều comma → US format (thousand separator)
            # VD: "2,438,488,070,081" → "2438488070081"
            try:
                cleaned = value.replace(',', '')
                result = float(cleaned)
                return -result if is_negative else result
            except (ValueError, AttributeError):
                pass
    
    # CASE 3: Chỉ có dot (không có comma) → VN format
    elif has_dot and not has_comma:
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
    
    # CASE 4: Không có comma và dot → Parse trực tiếp
    try:
        result = float(value)
        return -result if is_negative else result
    except (ValueError, AttributeError):
        pass
    
    # CASE 5: Fallback - loại bỏ tất cả ký tự không phải số và dấu chấm/phẩy
    try:
        cleaned = re.sub(r'[^\d.,]', '', value)
        if cleaned:
            # Thử parse lại với logic tương tự
            if ',' in cleaned and '.' in cleaned:
                # Có cả 2 → detect format
                comma_pos = cleaned.rfind(',')
                dot_pos = cleaned.rfind('.')
                if comma_pos > dot_pos:
                    # VN format
                    parts = cleaned.split(',')
                    if len(parts) == 2:
                        integer_part = parts[0].replace('.', '')
                        decimal_part = parts[1]
                        result = float(f"{integer_part}.{decimal_part}")
                        return -result if is_negative else result
                else:
                    # US format
                    parts = cleaned.split('.')
                    if len(parts) == 2:
                        integer_part = parts[0].replace(',', '')
                        decimal_part = parts[1]
                        result = float(f"{integer_part}.{decimal_part}")
                        return -result if is_negative else result
            elif ',' in cleaned:
                # Chỉ có comma → US format (thousand separator)
                cleaned_no_comma = cleaned.replace(',', '')
                result = float(cleaned_no_comma)
                return -result if is_negative else result
            elif '.' in cleaned:
                # Chỉ có dot → VN format (thousand separator)
                cleaned_no_dot = cleaned.replace('.', '')
                result = float(cleaned_no_dot)
                return -result if is_negative else result
    except (ValueError, AttributeError):
        pass
    
    return None


def find_value_column(df) -> Optional[str]:
    """
    Tìm cột giá trị (số tiền).
    
    QUY TẮC MỚI:
    - Ưu tiên: Cột cuối cùng (vì đã bỏ cột thuyết minh ở cuối rồi)
    - Fallback: Cột có chuỗi số dài nhất (theo tổng số chữ số), bỏ qua tên cột.
    
    Quy tắc chi tiết:
    - Bỏ qua các cột meta: 'mã số', 'chỉ tiêu', 'thuyết minh'
    - Ưu tiên chọn cột cuối cùng (sau khi đã bỏ cột thuyết minh)
    - Nếu cột cuối không hợp lệ, fallback về logic cũ: chọn cột có nhiều số nhất
    """
    if pd is None:
        raise ImportError("pandas is required for find_value_column. Install with: pip install pandas")
    if df.empty:
        return None
    
    def is_vn_number_like(s: Any) -> bool:
        if s is None:
            return False
        if isinstance(s, (int, float)):
            return True
        if not isinstance(s, str):
            s = str(s)
        s = s.strip()
        if not s or s == '-':
            return False
        # Cho phép định dạng: số, dấu . , , khoảng trắng, (), và VND (bị bỏ qua)
        s = re.sub(r'\s+', '', s, flags=re.UNICODE)
        s = re.sub(r'(?i)vnd', '', s)
        return bool(re.fullmatch(r'\(?[0-9][0-9\.,]*\)?', s))
    
    def digit_score(s: Any) -> int:
        if s is None:
            return 0
        if isinstance(s, (int, float)):
            return len(re.sub(r'\D', '', str(int(abs(s))))) if s == s else 0  # guard NaN
        if not isinstance(s, str):
            s = str(s)
        # Bỏ VND và khoảng trắng, chỉ đếm chữ số
        s = re.sub(r'(?i)vnd', '', s)
        digits = re.sub(r'\D', '', s)
        return len(digits)
    
    # Xác định các cột bị loại trừ theo tên
    excluded_by_name = set()
    cols = list(df.columns)
    for col in cols:
        col_lower = str(col).lower()
        col_no_diacritics = remove_diacritics(col_lower)
        if ('ma so' in col_no_diacritics) or ('mã số' in col_no_diacritics):
            excluded_by_name.add(col)
        if ('chi tieu' in col_no_diacritics) or ('chỉ tiêu' in col_no_diacritics):
            excluded_by_name.add(col)
        if ('thuyet minh' in col_no_diacritics) or ('thuyết minh' in col_no_diacritics):
            excluded_by_name.add(col)
    
    # ƯU TIÊN: Cột cuối cùng (sau khi đã bỏ cột thuyết minh)
    # Không cần check giá trị, cứ lấy cột cuối cùng luôn (vì đã bỏ cột thuyết minh rồi)
    if len(cols) > 0:
        last_col = cols[-1]
        if last_col not in excluded_by_name:
            # Cột cuối không phải là cột meta -> trả về luôn
            return last_col
    
    # FALLBACK: Logic cũ - tìm cột có nhiều số nhất
    best_col = None
    best_score = -1
    best_index = -1
    
    for idx, col in enumerate(cols):
        if col in excluded_by_name:
            continue
        series = df[col]
        # Lấy 3 giá trị dữ liệu đầu không rỗng
        sample_values = series.dropna().head(3).tolist()
        if not sample_values:
            continue
        # Tính điểm chỉ với các ô có dạng số hợp lệ theo VN
        values_considered = [v for v in sample_values if is_vn_number_like(v)]
        if not values_considered:
            continue
        score = sum(digit_score(v) for v in values_considered)
        if (score > best_score) or (score == best_score and idx > best_index):
            best_score = score
            best_col = col
            best_index = idx
    
    return best_col


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


def update_json_with_ma_so_full(data: Dict[str, Any], ma_so: str, value: Optional[float]) -> bool:
    """
    Cập nhật giá trị vào JSON structure dựa trên mã số đầy đủ (hỗ trợ mã số phụ như "1.1", "1.2").
    
    Hàm này tương tự update_json_with_ma_so nhưng hỗ trợ mã số dạng string để có thể
    phân biệt mã số chính (1) và mã số phụ (1.1, 1.2, 1.3).
    
    Hàm này sẽ normalize cả hai phía trước khi so sánh để có thể match:
    - "1.1" với "1.1", "01.1", "001.1"
    - "1.2" với "1.2", "01.2", "001.2"
    - "1" với "1", "01", "001"
    
    Args:
        data (Dict[str, Any]): JSON structure (có thể là nested dict)
        ma_so (str): Mã số cần tìm (ví dụ: "1", "1.1", "1.2", "01.1", "01.2")
        value (Optional[float]): Giá trị cần cập nhật
        
    Returns:
        bool: True nếu tìm thấy và cập nhật được, False nếu không
        
    Ví dụ:
        >>> data = {"section": {"ma_so": "1.1", "so_cuoi_nam": None}}
        >>> update_json_with_ma_so_full(data, "1.1", 1234.56)
        True
        >>> data["section"]["so_cuoi_nam"]
        1234.56
        >>> # Có thể match "01.1" với "1.1"
        >>> data2 = {"section": {"ma_so": "1.1", "so_cuoi_nam": None}}
        >>> update_json_with_ma_so_full(data2, "01.1", 1234.56)
        True
    """
    if not isinstance(data, dict):
        return False
    
    # Normalize mã số cần tìm
    ma_so_normalized = normalize_ma_so(str(ma_so))
    
    for key, val in data.items():
        if isinstance(val, dict):
            # Kiểm tra nếu có key "ma_so" và giá trị khớp (so sánh sau khi normalize)
            if "ma_so" in val:
                val_ma_so = val["ma_so"]
                # Normalize cả hai phía trước khi so sánh
                val_ma_so_normalized = normalize_ma_so(str(val_ma_so))
                
                # So sánh sau khi normalize
                if val_ma_so_normalized == ma_so_normalized:
                    val["so_cuoi_nam"] = value
                    return True
            
            # Đệ quy vào các dict con
            if update_json_with_ma_so_full(val, ma_so, value):
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


def _remove_markdown_tables(text: str) -> str:
    """
    Loại bỏ tất cả các bảng markdown khỏi văn bản, chỉ giữ lại phần text thông thường.
    
    Hàm này giúp tránh false positive khi check các từ khóa trong bảng markdown.
    Ví dụ: Tránh match "Thuyết minh" trong cột header của bảng với "thuyết minh báo cáo tài chính".
    
    Args:
        text (str): Văn bản chứa các bảng markdown
        
    Returns:
        str: Văn bản đã loại bỏ các bảng markdown
    """
    lines = text.split('\n')
    result_lines = []
    in_table = False
    
    for line in lines:
        stripped = line.strip()
        
        # Check if line is part of a table
        if stripped.startswith('|'):
            # Check if it's a separator line
            if _is_separator_line(stripped):
                # Skip separator line
                in_table = True
                continue
            
            # This is a table row, skip it
            in_table = True
            continue
        else:
            # End of table or regular text
            in_table = False
            result_lines.append(line)
    
    return '\n'.join(result_lines)


def detect_thuyetminhbaocaotaichinh(text: str, threshold: float = 0.8) -> bool:
    """
    Phát hiện xem văn bản có chứa "thuyết minh báo cáo tài chính" hay không.
    
    Logic:
    1. Loại bỏ tất cả các bảng markdown khỏi văn bản (chỉ check trong text thông thường)
    2. Lowercase toàn bộ văn bản
    3. Loại bỏ dấu tiếng Việt
    4. So khớp fuzzy 80% với "thuyet minh bao cao tai chinh"
    
    Lưu ý:
        Hàm này KHÔNG tìm kiếm trong các bảng markdown, chỉ tìm trong phần text thông thường.
        Điều này giúp tránh false positive khi "Thuyết minh" xuất hiện trong cột header của bảng
        (ví dụ: bảng "Báo cáo kết quả hoạt động kinh doanh" có cột "Thuyết minh").
    
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
        >>> # Không match "Thuyết minh" trong cột header của bảng
        >>> detect_thuyetminhbaocaotaichinh("| Mã số | Thuyết minh |")  # False
    """
    # Bước 1: Loại bỏ tất cả các bảng markdown (chỉ check trong text thông thường)
    text_without_tables = _remove_markdown_tables(text)
    
    # Bước 2: Lowercase và loại bỏ dấu
    text_lower = text_without_tables.lower()
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

