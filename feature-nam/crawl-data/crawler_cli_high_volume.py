# crawler_cli.py (version 14 - Multi-Year & Precise Resume)
import requests
import os
import pandas as pd
from bs4 import BeautifulSoup
import time
import re
import json
from datetime import datetime
from loguru import logger
from urllib.parse import urljoin
from collections import defaultdict

# ==============================================================================
# PHẦN CẤU HÌNH
# ==============================================================================
CONFIG = {
    # 1. Đường dẫn đến file CSV chứa danh sách cổ phiếu
    # "csv_path": "danh_sach_co_phieu_anfin.csv",
    "csv_path": "hose_stocks_filterd_insurance.csv", # ngành ngân hàng và năng lượng

    # 2. Danh sách các NĂM cần crawl dữ liệu.
    # Bạn có thể nhập một hoặc nhiều năm. Ví dụ: [2024, 2023, 2022]
    "years_list": [2025, 2021, 2020, 2019, 2018, 2017, 2016, 2015, 2014],

    # 3. Các loại tài liệu cần crawl (để trống [] nếu muốn crawl tất cả)
    "document_types": [],

    # 4. Các Sàn Giao Dịch cần crawl (để trống [] nếu muốn crawl tất cả)
    "allowed_exchanges": ["HOSE"],

    # 5. Tên thư mục đầu ra
    "output_dir": "D:/Vietstock_Downloads_CLI",

    # 6. Tên file ghi lại tiến trình (Checkpoint)
    "progress_log_file": "_progress.log",

    # 7. Tạm dừng giữa mỗi lần gọi API (giây).
    "api_delay": 1.5
}
# ==============================================================================

# --- CÁC THÀNH PHẦN CỐT LÕI ---
DOCUMENT_TYPES = {
    "Báo cáo tài chính": {"id": 1, "folder": "Bao_cao_tai_chinh"}, "Nghị quyết HĐQT": {"id": 23, "folder": "Nghi_quyet_HDQT"},
    "Giải trình KQKD": {"id": 8, "folder": "Giai_trinh_KQKD"}, "Báo cáo quản trị": {"id": 9, "folder": "Bao_cao_quan_tri"},
    "Báo cáo thường niên": {"id": 2, "folder": "Bao_cao_thuong_nien"}, "Nghị quyết ĐHĐCĐ": {"id": 4, "folder": "Nghi_quyet_DHDCD"},
    "Tài liệu ĐHĐCĐ": {"id": 5, "folder": "Tai_lieu_DHDCD"},
}

class VietstockCrawler:
    def __init__(self, api_delay=1.5):
        log_file = f"logs/crawler_cli_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        os.makedirs("logs", exist_ok=True)
        logger.add(log_file, rotation="10 MB", retention="30 days", level="DEBUG", format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}")
        logger.info("="*70); logger.info("Vietstock CLI Crawler (v14 - Multi-Year) Initialized"); logger.info("="*70)
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0'})
        self.token = None
        self.api_delay = api_delay

    def _get_report_period(self, title):
        title = title.lower();
        if 'quý 4' in title or 'q4' in title: return 'Q4';
        if 'quý 3' in title or 'q3' in title: return 'Q3';
        if 'quý 2' in title or 'q2' in title: return 'Q2';
        if 'quý 1' in title or 'q1' in title: return 'Q1';
        if '6 tháng' in title: return '6M';
        if 'năm' in title and not any(q in title for q in ['quý', '6 tháng']): return 'Annual'
        return None
    def _is_consolidated(self, title): return 'hợp nhất' in title.lower()
    def _filter_financial_reports(self, documents):
        best_reports_by_period = {'Q1': None, 'Q2': None, 'Q3': None, 'Q4': None, 'Annual': None}
        for doc in documents:
            title = doc.get('Title', ''); period = self._get_report_period(title)
            if period is None or period == '6M': continue
            is_new_consolidated = self._is_consolidated(title)
            current_best_doc = best_reports_by_period.get(period)
            if not current_best_doc or (is_new_consolidated and not self._is_consolidated(current_best_doc.get('Title', ''))):
                best_reports_by_period[period] = doc
        return [doc for doc in best_reports_by_period.values() if doc is not None]

    def get_token(self, stock_code, max_retries=3):
        time.sleep(self.api_delay)
        for attempt in range(max_retries):
            try:
                url = f'https://finance.vietstock.vn/{stock_code}/tai-tai-lieu.htm'; response = self.session.get(url, timeout=15); response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser'); token_input = soup.find('input', {'name': '__RequestVerificationToken'})
                if token_input and token_input.get('value'): self.token = token_input.get('value'); return self.token
                return None
            except requests.exceptions.RequestException as e:
                logger.warning(f"Lỗi mạng khi lấy token cho {stock_code} (Lần {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1: time.sleep((attempt + 1) * 5)
                else: logger.error(f"Không thể lấy token cho {stock_code} sau {max_retries} lần thử."); return None
        return None

    def get_documents(self, stock_code, year, doc_type_id, max_retries=3):
        time.sleep(self.api_delay)
        if not self.token: return []
        for attempt in range(max_retries):
            try:
                api_url = 'https://finance.vietstock.vn/data/getdocument'; payload = {'code': stock_code, 'page': 1, 'pageSize': 1000, 'year': year, 'type': doc_type_id, '__RequestVerificationToken': self.token}
                self.session.headers.update({'Referer': f'https://finance.vietstock.vn/{stock_code}/tai-tai-lieu.htm?doctype={doc_type_id}'})
                response = self.session.post(api_url, data=payload, timeout=15); response.raise_for_status(); data = response.json()
                if isinstance(data, list): return data
                return []
            except requests.exceptions.RequestException as e:
                logger.warning(f"Lỗi mạng khi lấy documents cho {stock_code} năm {year} (Lần {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1: time.sleep((attempt + 1) * 5)
                else: logger.error(f"Không thể lấy documents cho {stock_code} năm {year} sau {max_retries} lần thử."); return []
        return []

    def get_files_in_folder(self, report_id, max_retries=3):
        time.sleep(self.api_delay)
        if not self.token: return []
        for attempt in range(max_retries):
            try:
                api_url = 'https://finance.vietstock.vn/Data/ViewDocument'; payload = {'id': report_id, '__RequestVerificationToken': self.token}
                response = self.session.post(api_url, data=payload, timeout=15); response.raise_for_status(); files = response.json()
                if isinstance(files, list): return files
                return []
            except requests.exceptions.RequestException as e:
                logger.warning(f"Lỗi mạng khi lấy files in folder cho ID {report_id} (Lần {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1: time.sleep((attempt + 1) * 5)
                else: logger.error(f"Không thể lấy files in folder cho ID {report_id} sau {max_retries} lần thử."); return []
        return []

    def download_document(self, doc_info, folder_path, short_filename, max_retries=3):
        original_title = doc_info.get('Title', 'N/A').strip()
        raw_url = doc_info.get('Url', '').strip()
        if not raw_url: return None, "URL trống"
        file_url = urljoin('https://finance.vietstock.vn/', raw_url)
        file_path = os.path.join(folder_path, short_filename)
        if os.path.exists(file_path):
            logger.info(f" -> Bỏ qua (đã tồn tại): {short_filename}")
            return {'Mã CK': doc_info.get('StockCode'), 'Sàn': doc_info.get('Exchange'), 'Ngành': doc_info.get('Sector'), 'Năm': doc_info.get('Year'), 'Tên File Đã Lưu': short_filename, 'Tên Gốc': original_title, 'Kích thước (KB)': f"{os.path.getsize(file_path)/1024:.1f}", 'URL': file_url}, None
        time.sleep(self.api_delay)
        for attempt in range(max_retries):
            try:
                file_response = self.session.get(file_url, stream=True, timeout=30); file_response.raise_for_status()
                with open(file_path, 'wb') as f:
                    for chunk in file_response.iter_content(chunk_size=8192): f.write(chunk)
                file_size_kb = os.path.getsize(file_path) / 1024
                logger.success(f" -> Tải thành công: {short_filename} ({file_size_kb:.1f} KB)")
                return {'Mã CK': doc_info.get('StockCode'), 'Sàn': doc_info.get('Exchange'), 'Ngành': doc_info.get('Sector'), 'Năm': doc_info.get('Year'), 'Tên File Đã Lưu': short_filename, 'Tên Gốc': original_title, 'Kích thước (KB)': f"{file_size_kb:.1f}", 'URL': file_url}, None
            except requests.exceptions.RequestException as e:
                error_reason = f"Lỗi mạng: {e}"
                if attempt < max_retries - 1: time.sleep((attempt + 1) * 5)
                else: return None, error_reason
            except Exception as e: return None, f"Lỗi hệ thống: {e}"
        return None, "Không xác định"

def run_crawl():
    logger.info(f"Bắt đầu với cấu hình: Năm={CONFIG['years_list']}, Sàn={CONFIG['allowed_exchanges']}")
    output_dir = CONFIG["output_dir"]
    os.makedirs(output_dir, exist_ok=True)
    
    # --- LOAD CHECKPOINT ---
    progress_log_path = os.path.join(output_dir, CONFIG["progress_log_file"])
    # Set chứa các "MÃ_NĂM" đã hoàn thành. Ví dụ: {'FPT_2024', 'VIC_2023'}
    completed_checkpoints = set()
    if os.path.exists(progress_log_path):
        with open(progress_log_path, 'r', encoding='utf-8') as f:
            completed_checkpoints = {line.strip() for line in f if line.strip()}
        logger.success(f"Đã tải {len(completed_checkpoints)} checkpoints từ lần chạy trước.")

    # --- LOAD CSV ---
    try:
        stocks_df = pd.read_csv(CONFIG["csv_path"], dtype=str)
        stocks_df.rename(columns=lambda x: x.strip(), inplace=True)
        stocks_df['Mã CK'] = stocks_df['Mã CK'].str.strip().str.upper()
        stocks_df = stocks_df[~stocks_df['Sàn'].isin(['Unknown', 'Error'])]
        if CONFIG["allowed_exchanges"]:
            stocks_df = stocks_df[stocks_df['Sàn'].isin(CONFIG["allowed_exchanges"])]
        logger.info(f"Số lượng mã cổ phiếu cần xử lý: {len(stocks_df)}")
    except Exception as e: logger.error(f"Lỗi đọc file CSV: {e}"); return

    doc_types_to_crawl = CONFIG.get("document_types", [])
    doc_type_ids = [info['id'] for info in DOCUMENT_TYPES.values()] if not doc_types_to_crawl else [DOCUMENT_TYPES[name]['id'] for name in doc_types_to_crawl if name in DOCUMENT_TYPES]
    crawler = VietstockCrawler(api_delay=CONFIG["api_delay"])
    stats = {'details': [], 'failed': []}
    
    # --- VÒNG LẶP CHÍNH (MÃ CK -> CÁC NĂM) ---
    total_stocks = len(stocks_df)
    years_list = CONFIG["years_list"]
    # Sắp xếp năm giảm dần để crawl năm mới nhất trước
    years_list.sort(reverse=True) 

    for index, stock_info in stocks_df.iterrows():
        stock_code = stock_info['Mã CK']; sector = stock_info['Ngành']; exchange = stock_info['Sàn']
        current_idx = stocks_df.index.get_loc(index) + 1
        logger.info(f"=== Đang xử lý mã: {stock_code} ({current_idx}/{total_stocks}) ===")
        
        # Biến cờ để chỉ lấy token khi thực sự cần crawl ít nhất 1 năm
        token_acquired = False 

        for year in years_list:
            checkpoint_key = f"{stock_code}_{year}"
            
            # KIỂM TRA CHECKPOINT: Nếu năm này của mã này đã xong thì bỏ qua
            if checkpoint_key in completed_checkpoints:
                logger.info(f" >> Năm {year}: Đã hoàn thành trước đó. Bỏ qua.")
                continue
            
            # Nếu chưa có token thì lấy token (chỉ 1 lần cho mỗi mã)
            if not token_acquired:
                if not crawler.get_token(stock_code):
                    logger.error(f"Bỏ qua {stock_code} do không lấy được token.")
                    break # Thoát vòng lặp năm, chuyển sang mã tiếp theo
                token_acquired = True

            logger.info(f" >> Đang crawl năm: {year}")
            
            # --- Bắt đầu crawl cho MÃ CỤ THỂ và NĂM CỤ THỂ ---
            year_success = True # Giả định thành công, nếu có lỗi critical sẽ set False
            for doc_id in doc_type_ids:
                doc_type_info = next(v for v in DOCUMENT_TYPES.values() if v['id'] == doc_id)
                documents = crawler.get_documents(stock_code, year, doc_id)
                if doc_id == 1: documents = crawler._filter_financial_reports(documents)
                
                if not documents: continue

                safe_sector = re.sub(r'[\\/*?:"<>|]', "_", sector)
                folder_path = os.path.join(output_dir, exchange, safe_sector, stock_code, str(year), doc_type_info['folder'])
                os.makedirs(folder_path, exist_ok=True)
                folder_metadata = []
                
                for file_idx, doc in enumerate(documents, 1):
                    files_to_process = [doc] if doc.get('Url') else crawler.get_files_in_folder(doc.get('ID', ''))
                    for sub_idx, file_info in enumerate(files_to_process, 1):
                        ext = os.path.splitext(file_info.get('Url', ''))[1] or '.pdf'
                        short_fn = f"{stock_code}_{year}_{doc_id}_{file_idx}_{sub_idx}{ext}"
                        doc_meta = {'StockCode': stock_code, 'Exchange': exchange, 'Sector': sector, 'Year': year, 'Title': file_info.get('Title'), 'Url': file_info.get('Url')}
                        
                        res, err = crawler.download_document(doc_meta, folder_path, short_fn)
                        if res: stats['details'].append(res); folder_metadata.append(res)
                        else:
                            stats['failed'].append({**doc_meta, 'Lý Do Lỗi': err})
                            # Tùy chọn: Nếu muốn strict, có thể set year_success = False ở đây nếu tải lỗi
                
                if folder_metadata:
                    pd.DataFrame(folder_metadata).to_csv(os.path.join(folder_path, '_index.csv'), index=False, encoding='utf-8-sig')

            # Nếu chạy hết các loại tài liệu cho năm nay mà không bị crash, ghi checkpoint
            if year_success:
                with open(progress_log_path, 'a', encoding='utf-8') as f: f.write(f"{checkpoint_key}\n")
                completed_checkpoints.add(checkpoint_key) # Cập nhật set in-memory
                logger.success(f" >> Hoàn tất năm {year} cho {stock_code}. Đã ghi checkpoint.")

    # --- TỔNG KẾT ---
    logger.info("="*70); logger.info("QUÁ TRÌNH CRAWL HOÀN TẤT");
    logger.info(f"Tổng file thành công phiên này: {len(stats['details'])}"); logger.info(f"Tổng file lỗi phiên này: {len(stats['failed'])}")
    if stats['failed']: pd.DataFrame(stats['failed']).to_csv(os.path.join(output_dir, '_FAILED_DOWNLOADS.csv'), index=False, encoding='utf-8-sig')
    if stats['details']: pd.DataFrame(stats['details']).to_csv(os.path.join(output_dir, '_SUCCESS_DOWNLOADS.csv'), index=False, encoding='utf-8-sig')

if __name__ == "__main__":
    run_crawl()