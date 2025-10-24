"""
Vietstock Financial Reports Crawler - With Logging
"""

import requests
import os
import pandas as pd
from bs4 import BeautifulSoup
import time
import re
import json
from datetime import datetime
from loguru import logger


class VietstockCrawler:
    """Crawler với logging đầy đủ"""
    
    def __init__(self, log_file=None):
        """
        Initialize crawler
        Args:
            log_file: Path to log file. If None, auto-generate
        """
        if log_file is None:
            log_file = f"logs/crawler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        # Tạo thư mục logs
        os.makedirs("logs", exist_ok=True)
        
        # Configure logger
        logger.add(
            log_file,
            rotation="10 MB",
            retention="30 days",
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}"
        )
        
        logger.info("="*70)
        logger.info("Vietstock Crawler Initialized")
        logger.info("="*70)
        
        # Setup session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://finance.vietstock.vn',
            'Referer': 'https://finance.vietstock.vn/tai-lieu/bao-cao-tai-chinh.htm',
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        })
        
        self.token = None
    
    def get_token(self):
        """Lấy RequestVerificationToken"""
        logger.info("Getting RequestVerificationToken...")
        
        try:
            url = 'https://finance.vietstock.vn/tai-lieu/bao-cao-tai-chinh.htm'
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            token_input = soup.find('input', {'name': '__RequestVerificationToken'})
            
            if token_input:
                self.token = token_input.get('value')
                logger.success(f"Token obtained: {self.token[:20]}...")
                return self.token
            
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and '__RequestVerificationToken' in script.string:
                    match = re.search(r'__RequestVerificationToken["\'\s:=]+([a-zA-Z0-9_-]+)', script.string)
                    if match:
                        self.token = match.group(1)
                        logger.success(f"Token obtained from script: {self.token[:20]}...")
                        return self.token
            
            logger.error("Token not found in HTML")
            return None
            
        except Exception as e:
            logger.exception(f"Error getting token: {e}")
            return None
    
    def extract_quarter(self, text):
        """Trích xuất quý từ text"""
        if not text:
            return None
        
        text_lower = text.lower()
        patterns = [
            r'qu[yý]\s*(\d)',
            r'q\s*(\d)',
            r'quy\s*(\d)',
            r'quarter\s*(\d)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                quarter = int(match.group(1))
                if 1 <= quarter <= 4:
                    return quarter
        
        return None
    
    def get_reports(self, stock_code, year):
        """Lấy tất cả báo cáo và phân loại theo quý"""
        logger.info(f"Fetching reports for {stock_code} - {year}")
        
        api_url = 'https://finance.vietstock.vn/data/getrptfile'
        all_reports_by_quarter = {0: [], 1: [], 2: [], 3: [], 4: []}
        
        for test_id in range(1, 11):
            payload = {
                'stockCode': stock_code,
                'documentTypeID': 1,
                'reportTermID': test_id,
                'yearPeriod': year,
                'exchangeID': 0,
                'orderBy': 2,
                'orderDir': 2,
                'page': 1,
                'pageSize': 50,
                '__RequestVerificationToken': self.token
            }
            
            try:
                response = self.session.post(api_url, data=payload, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    
                    if isinstance(data, list) and len(data) > 0:
                        logger.debug(f"reportTermID={test_id}: Found {len(data)} reports")
                        
                        for report in data:
                            title = report.get('Title', '')
                            url = report.get('Url', '')
                            
                            quarter = self.extract_quarter(title)
                            if quarter is None:
                                quarter = self.extract_quarter(url)
                            
                            if quarter is None:
                                if 'năm' in title.lower() or 'annual' in title.lower():
                                    quarter = 0
                                else:
                                    continue
                            
                            if report not in all_reports_by_quarter[quarter]:
                                all_reports_by_quarter[quarter].append(report)
                                logger.debug(f"Added: {title[:50]}... -> Q{quarter}")
                
                time.sleep(0.2)
                
            except Exception as e:
                logger.warning(f"Error with reportTermID={test_id}: {e}")
                continue
        
        # Log summary
        for q, reports in all_reports_by_quarter.items():
            if len(reports) > 0:
                q_text = "Annual" if q == 0 else f"Q{q}"
                logger.info(f"{stock_code} - {q_text}: {len(reports)} reports")
        
        return all_reports_by_quarter
    
    def download_report(self, report, folder_name, idx, total):
        """Download một báo cáo"""
        file_title = report.get('Title', f'Report_{idx}').strip()
        file_url = report.get('Url', '').strip()
        file_ext = report.get('FileExt', '.pdf').strip()
        
        if not file_url:
            logger.warning(f"No URL for report: {file_title}")
            return None
        
        if file_url.startswith('//'):
            file_url = f'https:{file_url}'
        elif not file_url.startswith('http'):
            file_url = f'https://finance.vietstock.vn{file_url}'
        
        safe_title = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in file_title)
        safe_title = safe_title.strip().replace('  ', ' ')
        
        if not safe_title.lower().endswith(('.pdf', '.xls', '.xlsx', '.doc', '.docx')):
            if file_ext and not file_ext.startswith('.'):
                file_ext = f'.{file_ext}'
            safe_title += file_ext
        
        file_path = os.path.join(folder_name, safe_title)
        
        logger.info(f"[{idx}/{total}] Downloading: {file_title[:50]}...")
        
        try:
            file_response = self.session.get(file_url, stream=True, timeout=30)
            file_response.raise_for_status()
            
            with open(file_path, 'wb') as f:
                for chunk in file_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size = os.path.getsize(file_path) / 1024
            logger.success(f"Downloaded: {safe_title} ({file_size:.1f} KB)")
            
            return {
                'Tên báo cáo': file_title,
                'Kích thước (KB)': f"{file_size:.1f}",
                'URL': file_url,
                'Đường dẫn': file_path
            }
            
        except Exception as e:
            logger.error(f"Failed to download {file_title}: {e}")
            return None
    
    def crawl_batch(self, stock_codes, quarters, year, output_dir=None):
        """Crawl batch với progress callback"""
        logger.info("="*70)
        logger.info("BATCH CRAWL START")
        logger.info(f"Stocks: {stock_codes}")
        logger.info(f"Quarters: {quarters}")
        logger.info(f"Year: {year}")
        logger.info("="*70)
        
        # Get token
        if not self.get_token():
            logger.error("Failed to get token. Aborting.")
            return None
        
        # Create output directory
        if output_dir is None:
            output_dir = f"BATCH_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Output directory: {output_dir}")
        
        # Stats
        stats = {
            'total_stocks': len(stock_codes),
            'total_reports_found': 0,
            'total_reports_downloaded': 0,
            'failed_stocks': [],
            'details': []
        }
        
        # Process each stock
        for stock_idx, stock_code in enumerate(stock_codes, 1):
            logger.info("─"*70)
            logger.info(f"[{stock_idx}/{len(stock_codes)}] Processing: {stock_code}")
            logger.info("─"*70)
            
            try:
                # Get reports
                reports_by_quarter = self.get_reports(stock_code, year)
                
                # Determine quarters to download
                quarters_to_download = []
                if quarters == 'all':
                    quarters_to_download = [1, 2, 3, 4]
                else:
                    quarters_to_download = quarters
                
                stock_found = 0
                stock_downloaded = 0
                
                # Download each quarter
                for quarter in quarters_to_download:
                    target_reports = reports_by_quarter.get(quarter, [])
                    
                    if len(target_reports) == 0:
                        logger.warning(f"{stock_code} Q{quarter}: No reports")
                        continue
                    
                    logger.info(f"{stock_code} Q{quarter}: {len(target_reports)} reports found")
                    stock_found += len(target_reports)
                    
                    # Create folder
                    folder_name = os.path.join(output_dir, f"{stock_code}_Q{quarter}_{year}")
                    os.makedirs(folder_name, exist_ok=True)
                    
                    # Save metadata
                    metadata_file = os.path.join(folder_name, 'metadata.json')
                    with open(metadata_file, 'w', encoding='utf-8') as f:
                        json.dump(target_reports, f, ensure_ascii=False, indent=2)
                    
                    # Download files
                    report_info = []
                    for idx, report in enumerate(target_reports, 1):
                        result = self.download_report(report, folder_name, idx, len(target_reports))
                        if result:
                            result['Mã CK'] = stock_code
                            result['Quý'] = quarter
                            result['Năm'] = year
                            report_info.append(result)
                            stock_downloaded += 1
                        
                        time.sleep(0.5)
                    
                    # Save CSV
                    if report_info:
                        df = pd.DataFrame(report_info)
                        csv_path = os.path.join(folder_name, f'{stock_code}_Q{quarter}_{year}.csv')
                        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                        logger.info(f"Saved CSV: {csv_path}")
                
                # Update stats
                stats['total_reports_found'] += stock_found
                stats['total_reports_downloaded'] += stock_downloaded
                stats['details'].append({
                    'stock_code': stock_code,
                    'reports_found': stock_found,
                    'reports_downloaded': stock_downloaded
                })
                
                logger.success(f"{stock_code}: {stock_downloaded}/{stock_found} reports downloaded")
                
                time.sleep(2)
                
            except Exception as e:
                logger.exception(f"Error processing {stock_code}: {e}")
                stats['failed_stocks'].append(stock_code)
        
        # Save summary
        summary_df = pd.DataFrame(stats['details'])
        summary_path = os.path.join(output_dir, 'SUMMARY_REPORT.csv')
        summary_df.to_csv(summary_path, index=False, encoding='utf-8-sig')
        
        stats_path = os.path.join(output_dir, 'batch_stats.json')
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        logger.info("="*70)
        logger.info("BATCH CRAWL COMPLETED")
        logger.info(f"Total stocks: {stats['total_stocks']}")
        logger.info(f"Reports found: {stats['total_reports_found']}")
        logger.info(f"Reports downloaded: {stats['total_reports_downloaded']}")
        logger.info(f"Failed stocks: {len(stats['failed_stocks'])}")
        logger.info("="*70)
        
        return stats
