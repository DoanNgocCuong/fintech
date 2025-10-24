"""
Enhanced Crawler with Smart Rate Limiting
"""

import streamlit as st
from crawler_with_logging import VietstockCrawler
import time
from datetime import datetime
import pandas as pd


class SmartVietstockCrawler(VietstockCrawler):
    """Crawler với rate limiting thông minh"""
    
    def __init__(self, max_requests_per_minute=30, log_file=None):
        super().__init__(log_file)
        self.max_requests_per_minute = max_requests_per_minute
        self.request_times = []
    
    def _check_rate_limit(self):
        """Kiểm tra và delay nếu vượt rate limit"""
        now = time.time()
        
        # Loại bỏ requests cũ hơn 1 phút
        self.request_times = [t for t in self.request_times if now - t < 60]
        
        # Nếu đã vượt limit, đợi
        if len(self.request_times) >= self.max_requests_per_minute:
            sleep_time = 60 - (now - self.request_times[0])
            if sleep_time > 0:
                logger.warning(f"Rate limit reached. Sleeping {sleep_time:.1f}s...")
                time.sleep(sleep_time)
                self.request_times = []
        
        self.request_times.append(now)
    
    def download_report(self, report, folder_name, idx, total, progress_callback=None):
        """Download với rate limiting"""
        self._check_rate_limit()
        
        result = super().download_report(report, folder_name, idx, total)
        
        # Callback cho UI progress
        if progress_callback:
            progress_callback(idx, total)
        
        return result
    
    def crawl_batch_with_limits(self, stock_codes, quarters, year, 
                                 max_stocks_per_batch=20, 
                                 output_dir=None,
                                 progress_callback=None):
        """
        Crawl với giới hạn số mã per batch
        
        Args:
            stock_codes: List mã CK
            quarters: Quý cần crawl
            year: Năm
            max_stocks_per_batch: Max số mã mỗi batch (default: 20)
            progress_callback: Hàm callback cho progress UI
        """
        if len(stock_codes) > max_stocks_per_batch:
            logger.warning(f"Too many stocks ({len(stock_codes)}). Splitting into batches of {max_stocks_per_batch}")
            
            # Split into smaller batches
            all_results = []
            for i in range(0, len(stock_codes), max_stocks_per_batch):
                batch_stocks = stock_codes[i:i+max_stocks_per_batch]
                batch_num = i // max_stocks_per_batch + 1
                
                logger.info(f"Processing batch {batch_num}: {len(batch_stocks)} stocks")
                
                result = self.crawl_batch(
                    batch_stocks, 
                    quarters, 
                    year, 
                    output_dir=f"{output_dir}_batch{batch_num}" if output_dir else None
                )
                all_results.append(result)
                
                # Delay between batches
                if i + max_stocks_per_batch < len(stock_codes):
                    logger.info("Cooling down between batches (30s)...")
                    time.sleep(30)
            
            # Merge results
            merged_stats = {
                'total_stocks': sum(r['total_stocks'] for r in all_results),
                'total_reports_found': sum(r['total_reports_found'] for r in all_results),
                'total_reports_downloaded': sum(r['total_reports_downloaded'] for r in all_results),
                'failed_stocks': [s for r in all_results for s in r['failed_stocks']],
                'details': [d for r in all_results for d in r['details']]
            }
            
            return merged_stats
        else:
            return self.crawl_batch(stock_codes, quarters, year, output_dir)


def enhanced_crawler_view():
    """Enhanced UI với limits"""
    st.header("🚀 Smart Crawler (với Rate Limiting)")
    
    with st.sidebar:
        st.header("⚙️ Cấu hình")
        
        # Stock codes
        st.subheader("1️⃣ Mã chứng khoán")
        
        # Option 1: Manual input
        input_method = st.radio(
            "Phương thức nhập",
            ["Nhập thủ công", "Tải file CSV", "Tất cả mã VN30"]
        )
        
        if input_method == "Nhập thủ công":
            stock_input = st.text_area(
                "Nhập mã CK (cách nhau bởi dấu phẩy)",
                value="BID, FPT, VNM",
                help="Khuyến nghị: ≤ 20 mã mỗi lần"
            )
            stock_codes = [s.strip().upper() for s in stock_input.split(',') if s.strip()]
        
        elif input_method == "Tải file CSV":
            uploaded_file = st.file_uploader("Upload CSV (cột 'stock_code')", type=['csv'])
            if uploaded_file:
                df = pd.read_csv(uploaded_file)
                stock_codes = df['stock_code'].str.upper().tolist()
            else:
                stock_codes = []
        
        else:  # VN30
            vn30_stocks = [
                "ACB", "BID", "BVH", "CTG", "FPT", "GAS", "GVR", "HDB", 
                "HPG", "MBB", "MSN", "MWG", "NVL", "PDR", "PLX", "POW",
                "SAB", "SSB", "SSI", "STB", "TCB", "TPB", "VCB", "VHM",
                "VIB", "VIC", "VJC", "VNM", "VPB", "VRE"
            ]
            stock_codes = st.multiselect(
                "Chọn mã từ VN30",
                options=vn30_stocks,
                default=vn30_stocks[:5]
            )
        
        # Warning for too many stocks
        if len(stock_codes) > 20:
            st.warning(f"⚠️ Số mã nhiều ({len(stock_codes)}). Sẽ tự động chia batch.")
        elif len(stock_codes) > 50:
            st.error(f"❌ Quá nhiều mã ({len(stock_codes)}). Khuyến nghị ≤ 50.")
        
        st.info(f"✅ Tổng: {len(stock_codes)} mã")
        
        # Year & Quarters
        st.subheader("2️⃣ Năm & Quý")
        year = st.number_input("Năm", 2020, 2030, 2025)
        
        quarters = st.multiselect(
            "Chọn quý",
            [1, 2, 3, 4],
            default=[1, 2]
        )
        
        # Advanced settings
        with st.expander("⚙️ Cài đặt nâng cao"):
            max_stocks_per_batch = st.slider(
                "Max mã mỗi batch",
                min_value=5,
                max_value=50,
                value=20,
                help="Số mã tối đa mỗi batch để tránh rate limit"
            )
            
            max_requests_per_minute = st.slider(
                "Max requests/phút",
                min_value=10,
                max_value=60,
                value=30,
                help="Giới hạn số requests mỗi phút"
            )
        
        # Estimate time
        estimated_time = len(stock_codes) * len(quarters) * 0.5  # 30s per stock-quarter
        st.info(f"⏱️ Thời gian ước tính: {estimated_time/60:.1f} phút")
        
        st.markdown("---")
        
        start_button = st.button(
            "🚀 Bắt đầu Crawl",
            type="primary",
            use_container_width=True,
            disabled=len(stock_codes) == 0
        )
    
    # Main area
    if start_button:
        # Progress tracking
        progress_container = st.container()
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Create crawler
        crawler = SmartVietstockCrawler(
            max_requests_per_minute=max_requests_per_minute
        )
        
        with progress_container:
            st.info("🔄 Đang khởi động crawler...")
        
        try:
            # Crawl with progress updates
            def update_progress(current, total):
                progress = int((current / total) * 100)
                progress_bar.progress(progress)
                status_text.text(f"Đang tải: {current}/{total} files")
            
            results = crawler.crawl_batch_with_limits(
                stock_codes=stock_codes,
                quarters=quarters if quarters else 'all',
                year=year,
                max_stocks_per_batch=max_stocks_per_batch,
                progress_callback=update_progress
            )
            
            if results:
                st.success("✅ Crawl hoàn tất!")
                
                # Display results
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Tổng mã", results['total_stocks'])
                with col2:
                    st.metric("Báo cáo tìm được", results['total_reports_found'])
                with col3:
                    st.metric("Báo cáo tải về", results['total_reports_downloaded'])
                with col4:
                    success_rate = (results['total_reports_downloaded'] / results['total_reports_found'] * 100) if results['total_reports_found'] > 0 else 0
                    st.metric("Success Rate", f"{success_rate:.1f}%")
                
                # Details
                if results['details']:
                    st.markdown("### 📋 Chi tiết")
                    df = pd.DataFrame(results['details'])
                    st.dataframe(df, use_container_width=True)
        
        except Exception as e:
            st.error(f"❌ Lỗi: {e}")


if __name__ == "__main__":
    st.set_page_config(page_title="Smart Crawler", page_icon="🚀", layout="wide")
    enhanced_crawler_view()
