# Folder: /home/ubuntu/cuong_dn/fintech/OCR/data/nganh_bao_hiem
"""
Script để xử lý batch PDF files trong folder, sử dụng các hàm từ main_parallel.py
- Case 1: .md đã gen ra có số trang ko khớp với pdf (đã code utils_count.py để so sánh số trang)
- Case 2: Temp Folder chứa ảnh và .md của 1 file markdown bị dừng giữa chừng, cần dọn dẹp toàn bộ folder này bằng việc (check nếu pdf chưa có .md thì luôn tạo folder mới)
- Case 3: Luôn cần check xem số trang của .md sau khi merge đã khơp chưa bằng cách dùng def pdf2finalmarkdown (def này thì gọi đến hàm compare_page_counts để so sánh số trang)) 
"""
import os
import logging
from pathlib import Path
import shutil
import re
from utils_count import compare_page_counts

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
BASE_FOLDER = "/home/ubuntu/fintech/OCR/data/Ngành Bảo hiểm/BVH/2025/Bao_cao_tai_chinh"
BASE_FOLDER = "/home/ubuntu/fintech/OCR/data/test"

def prepare_pdf_processing(pdf_path: Path, idx: int, total_pdfs: int) -> tuple[bool, Path]:
    """
    Kiểm tra trạng thái markdown hiện có và chuẩn bị thư mục out_dir cho xử lý.

    Returns:
        (skip, out_dir)
        - skip=True: bỏ qua file PDF này (đã có .md đúng số trang)
        - skip=False: tiếp tục xử lý; out_dir được làm sạch và tạo mới
    """
    md_path = pdf_path.with_suffix('.md')
    logger.info(
        f"🔎 [{idx}/{total_pdfs}] Kiểm tra PDF: {pdf_path.name} | MD: {md_path.name} (exists={md_path.exists()})"
    )

    # Nếu đã có .md: so khớp số trang; đúng thì skip, sai thì xóa để xử lý lại
    if md_path.exists():
        try:
            pdf_pages, md_pages, is_match = compare_page_counts(str(pdf_path), str(md_path))
            logger.info(
                f"   📑 Trang PDF={pdf_pages} | 📄 Trang MD={md_pages} | ✅ Khớp={is_match}"
            )
        except Exception as e:
            logger.warning(f"⚠️  Không thể so khớp số trang: {e}")
            pdf_pages, md_pages, is_match = 0, 0, False
        if is_match:
            logger.info(f"⏭️  [{idx}/{total_pdfs}] Bỏ qua (đã có markdown đúng số trang): {md_path.name}")
            return True, pdf_path.parent / pdf_path.stem
        else:
            logger.error(
                f"❌ [{idx}/{total_pdfs}] Lỗi: Số trang PDF ({pdf_pages}) ≠ Markdown ({md_pages}). Xóa .md và xử lý lại."
            )
            try:
                os.remove(md_path)
                logger.info(f"🗑️  Đã xóa file markdown cũ: {md_path}")
            except Exception as e:
                logger.warning(f"⚠️ Không thể xóa {md_path}: {e}")

    # Chuẩn bị thư mục out_dir sạch
    out_dir = pdf_path.parent / pdf_path.stem
    logger.info(f"🗂️  Chuẩn bị thư mục tạm: {out_dir}")
    if out_dir.exists():
        try:
            logger.debug(f"   🧹 Xóa thư mục tạm cũ: {out_dir}")
            shutil.rmtree(out_dir)
            logger.debug(f"   ✅ Đã xóa: {out_dir}")
        except Exception as e:
            logger.warning(f"⚠️ Không thể xóa thư mục tạm {out_dir}: {e}")
    out_dir.mkdir(parents=True, exist_ok=True)
    logger.debug(f"   📁 Đã tạo mới thư mục tạm: {out_dir}")

    # Log số ảnh tạm nếu có (thường 0 trước khi convert)
    number_of_pdf_pages = len(list(out_dir.rglob("*.png")))
    logger.info(f"📷  Ảnh tạm hiện có trong out_dir: {number_of_pdf_pages}")

    return False, out_dir

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

            skip, out_dir = prepare_pdf_processing(pdf_path, idx, total_pdfs)
            if skip:
                skipped_count += 1
                continue
            
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