# Folder: /home/ubuntu/cuong_dn/fintech/OCR/data/nganh_bao_hiem
"""
Script để xử lý batch PDF files trong folder, sử dụng các hàm từ main_parallel.py
"""
import os
import logging
from pathlib import Path
import shutil

# Import tất cả các hàm và constants cần thiết từ main_parallel.py
from main_parallel import (
    pdf2finalmarkdown,
    MODEL,
    API,
    OCR_MAX_WORKERS,
    PDF_CONVERT_THREADS
)

# Cấu hình logging (đồng nhất với main_parallel.py)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Base folder path
BASE_FOLDER = "/home/ubuntu/cuong_dn/fintech/OCR/data/Ngành Bảo hiểm/BIC/2014/Bao_cao_tai_chinh"

def process(base_folder=None):
    """
    Lặp qua toàn bộ folder BASE_FOLDER, tìm file PDF, nếu chưa có file .md cùng tên thì xử lý.
    Sử dụng các hàm từ main_parallel.py để xử lý.
    
    Args:
        base_folder: Path to base folder (None = use BASE_FOLDER constant)
    """
    base_path = Path(base_folder or BASE_FOLDER)
    
    if not base_path.exists():
        logger.error(f"❌ Folder không tồn tại: {base_path}")
        return
    
    logger.info(f"🚀 Bắt đầu xử lý folder: {base_path}")
    logger.info(f"   📁 Model: {MODEL}")
    logger.info(f"   🌐 API: {API}")
    logger.info(f"   🧵 OCR Workers: {OCR_MAX_WORKERS}")
    logger.info(f"   📄 PDF Convert Threads: {PDF_CONVERT_THREADS}")
    
    # Tìm tất cả file PDF (recursive)
    pdf_files = list(base_path.rglob("*.pdf"))
    total_pdfs = len(pdf_files)
    logger.info(f"📄 Tìm thấy {total_pdfs} file PDF")
    
    if total_pdfs == 0:
        logger.warning("⚠️  Không tìm thấy file PDF nào!")
        return
    
    processed_count = 0
    skipped_count = 0
    error_count = 0
    
    for idx, pdf_path in enumerate(pdf_files, 1):
        try:
            pdf_path = pdf_path.resolve()
            md_path = pdf_path.with_suffix('.md')
            
            # Skip nếu đã có file .md
            if md_path.exists():
                logger.info(f"⏭️  [{idx}/{total_pdfs}] Bỏ qua (đã có .md): {pdf_path.name}")
                skipped_count += 1
                continue
            
            logger.info(f"\n🔄 [{idx}/{total_pdfs}] Xử lý: {pdf_path.name}")
            
            # Tạo thư mục output images tạm (cùng vị trí với PDF, tên = tên file PDF không đuôi)
            out_dir = pdf_path.parent / pdf_path.stem
            out_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                # Xử lý PDF -> Markdown sử dụng hàm từ main_parallel.py
                pdf2finalmarkdown(
                    pdf_path=str(pdf_path),
                    out_dir=str(out_dir),
                    model=MODEL,
                    api=API,
                    output_md=str(md_path),
                    max_workers=OCR_MAX_WORKERS
                )
                
                # Xóa thư mục images tạm sau khi đã gộp markdown
                if out_dir.exists():
                    shutil.rmtree(out_dir)
                    logger.debug(f"🗑️  Đã xóa thư mục tạm: {out_dir}")
                
                processed_count += 1
                logger.info(f"✅ [{idx}/{total_pdfs}] Hoàn thành: {pdf_path.name} -> {md_path.name}")
                
            except Exception as e:
                # Giữ lại thư mục tạm nếu có lỗi để debug
                logger.error(f"❌ [{idx}/{total_pdfs}] Lỗi khi xử lý {pdf_path.name}: {e}")
                logger.error(f"   Thư mục tạm được giữ lại: {out_dir}")
                error_count += 1
                continue
                
        except Exception as e:
            error_count += 1
            logger.error(f"❌ [{idx}/{total_pdfs}] Lỗi khi xử lý {pdf_path}: {e}")
            continue
    
    # Tóm tắt kết quả
    logger.info(f"\n{'='*60}")
    logger.info(f"🎯 TỔNG KẾT:")
    logger.info(f"   📊 Tổng số PDF: {total_pdfs}")
    logger.info(f"   ✅ Đã xử lý: {processed_count}")
    logger.info(f"   ⏭️  Đã bỏ qua (có sẵn .md): {skipped_count}")
    logger.info(f"   ❌ Lỗi: {error_count}")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    import sys
    
    # Cho phép truyền folder path qua command line argument
    if len(sys.argv) > 1:
        BASE_FOLDER = sys.argv[1]
        logger.info(f"📁 Sử dụng folder từ argument: {BASE_FOLDER}")
    
    process()