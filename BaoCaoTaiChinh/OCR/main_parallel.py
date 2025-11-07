import os
import glob
import base64
import re
from pdf2image import convert_from_path
from openai import OpenAI
import logging
from markdownify import markdownify
import time
import multiprocessing
from typing import Optional
from utils_count import compare_page_counts

# Import utils từ utils_parallel_num_worker.py
from utils_parallel_num_worker import (
    process_images_parallel
)

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

PDF = "/home/ubuntu/fintech/OCR/data/Ngành Bảo hiểm/BIC/2014/Bao_cao_tai_chinh/BIC_2014_1_4_1.pdf"
PDF = "/home/ubuntu/fintech/BaoCaoTaiChinh/OCR/data/test/33_pages_test.pdf"
OUT_DIR = "/home/ubuntu/fintech/BaoCaoTaiChinh/OCR/data/out_images"
MODEL = "rednote-hilab/dots.ocr"
API = "http://103.253.20.30:30010/v1"
OUT_MD = "data/33_pages_test.md"

# Config cho parallel processing
PDF_CONVERT_THREADS = multiprocessing.cpu_count()  # Số cores để convert PDF
# OCR_MAX_WORKERS phải ≤ server max_num_seqs (hiện tại server = 8)
# Nên set = 8 để tận dụng tối đa server capacity
OCR_MAX_WORKERS = 20  # Số workers cho OCR parallel (đồng bộ với server max-num-seqs=8)

# ============================================================================
# OPTIMIZE 1: PDF -> Images với parallel conversion
# ============================================================================
def pdf2listimages(pdf_path, out_dir, thread_count=None):
    """
    Convert PDF -> Images với parallel processing
    Đặt tên file ảnh theo format: tên_file_pdf-1.png, tên_file_pdf-2.png, ...
    """
    os.makedirs(out_dir, exist_ok=True)
    
    if thread_count is None:
        thread_count = PDF_CONVERT_THREADS
    
    # Lấy tên file PDF (không có phần mở rộng) để đặt tên cho ảnh
    pdf_basename = os.path.splitext(os.path.basename(pdf_path))[0]
    
    logger.info(f"🔄 Converting PDF to images with {thread_count} threads...")
    convert_start = time.time()
    
    # Convert PDF thành images với parallel processing
    convert_from_path(
        pdf_path,
        dpi=200,
        output_folder=out_dir,
        fmt="png",
        thread_count=thread_count,  # ← TĂNG TỐC: Convert pages song song
        use_pdftocairo=True  # ← Tăng tốc: Dùng pdftocairo (nhanh hơn pdftoppm)
    )
    
    convert_time = time.time() - convert_start
    logger.info(f"✅ PDF converted to images in {convert_time:.2f} seconds")
    
    # Sử dụng pattern tên file tạm mà convert_from_path tạo ra để đảm bảo đúng thứ tự trang
    # Thông thường tên file là: [tên file pdf (có thể thêm bunch random chars)]-1.png, -2.png,...
    temp_image_paths = glob.glob(f"{out_dir}/*.png")

    # Ưu tiên extract luôn số trang từ tên file, không dựa vào thời gian modifed (đôi khi OS ghi disk không đúng order)
    def extract_page_from_tmpimg(filename):
        # Lấy ra số cuối trước .png:   ...-1.png, ...-2.png, ...
        basename = os.path.basename(filename)
        match = re.search(r'-(\d+)\.png$', basename)
        return int(match.group(1)) if match else 0
    
    temp_image_paths_sorted = sorted(temp_image_paths, key=extract_page_from_tmpimg)

    # Đổi tên các file ảnh theo format: tên_file_pdf-1.png, tên_file_pdf-2.png, ...
    image_paths = []
    for idx, temp_path in enumerate(temp_image_paths_sorted, start=1):
        new_name = f"{pdf_basename}-{idx}.png"
        new_path = os.path.join(out_dir, new_name)
        try:
            os.rename(temp_path, new_path)
            image_paths.append(new_path)
        except Exception as e:
            logger.error(f"❌ Failed to rename {temp_path} to {new_path}: {e}")
            image_paths.append(temp_path)
    logger.info(f"📄 Found {len(image_paths)} images (renamed to {pdf_basename}-N.png format)")
    return image_paths

# ============================================================================
# OCR Functions
# ============================================================================
def image2text(image_path, model, api, client=None):
    """OCR image -> text with explicit retry logs."""
    if client is None:
        client = OpenAI(base_url=api, api_key="EMPTY", timeout=180.0)

    # Read file once and encode to base64
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")

    # Đoạn này thực hiện retry (thử lại tối đa max_attempts lần), mỗi lần fail thì backoff và log chi tiết
    max_attempts = 3  # Số lần thử lại tối đa
    for attempt in range(1, max_attempts + 1):  # Lặp qua từng lần thử
        try:
            # Gửi request nhận diện OCR qua API client
            resp = client.chat.completions.create(
                model=model,  # Chọn model cho OCR
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract structured markdown from this page."},  # Yêu cầu tạo markdown có cấu trúc
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
                    ],
                }],
                temperature=0.0,    # Đặt nhiệt thấp nhất để kết quả ổn định
                max_tokens=4096,    # Giới hạn token đầu ra
                timeout=180.0,      # Timeout cho request
            )
            page_text = resp.choices[0].message.content or ""  # Lấy kết quả markdown, fallback sang rỗng nếu không có
            logger.info(f"✅ OCR: {os.path.basename(image_path)} -> {len(page_text)} chars (attempt {attempt})")  # Log thành công, số ký tự trả về
            return page_text  # Trả về nội dung
        except Exception as e:
            if attempt < max_attempts:
                # Nếu chưa hết số lần thử lại, log cảnh báo kèm số lần retry và lỗi
                logger.warning(
                    f"⚠️ Retry {attempt}/{max_attempts - 1} for {os.path.basename(image_path)}: {type(e).__name__}: {e}"
                )
                # Thực hiện "exponential backoff": càng lỗi nhiều càng chờ lâu dần (delay = 1s, 2s, 4s,...)
                try:
                    time.sleep(1.0 * (2 ** (attempt - 1)))
                except Exception:
                    pass  # Nếu sleep cũng lỗi thì bỏ qua luôn
            else:
                # Nếu hết số lần thử lại, log lỗi cuối cùng và trả chuỗi rỗng
                logger.error(f"❌ Exhausted retries for {os.path.basename(image_path)}: {type(e).__name__}: {e}")
                return ""

def text2markdown(page_text):
    """Convert HTML to markdown"""
    return markdownify(page_text, heading_style="ATX")

# ============================================================================
# OPTIMIZE 2: OCR Processing Function với utils_parallel_batch_size_max_worker.py
# ============================================================================
def process_single_image_ocr(image_path: str, model: str, api: str, **kwargs) -> Optional[str]:
    """
    Process single image: OCR -> Markdown -> Save temp file -> Delete image
    Function này sẽ được dùng bởi ParallelBatchProcessor
    
    Args:
        image_path: Path to image file
        model: Model name
        api: API endpoint
        **kwargs: Additional arguments (ignored)
        
    Returns:
        markdown text or None if error
    """
    try:
        # Create thread-safe client
        client = OpenAI(base_url=api, api_key="EMPTY", timeout=120.0)
        
        # OCR: image -> text -> markdown
        page_text = image2text(image_path, model, api, client)
        markdown = text2markdown(page_text)
        
        # Check content sau khi OCR thành công: nếu trống thì set placeholder
        if not markdown.strip():
            markdown = "*[Trang trống]*"
            logger.warning(f"⚠️  Trang trống: {os.path.basename(image_path)}")
        
        # CHỈ tạo file .md khi OCR thành công (không có exception)
        md_temp_path = os.path.splitext(image_path)[0] + ".md"
        with open(md_temp_path, "w", encoding="utf-8") as f:
            f.write(markdown)
        logger.debug(f"💾 Saved: {os.path.basename(md_temp_path)}")
        
        return markdown
        
    except Exception as e:
        # Nếu OCR lỗi thì KHÔNG tạo file .md
        logger.error(f"❌ Error processing {image_path}: {e}")
        return None

# ============================================================================
# Main Pipeline: PDF -> Images (parallel) -> OCR (parallel) -> Markdown
# ============================================================================
def pdf2finalmarkdown(pdf_path, out_dir, model, api, output_md, max_workers=None):
    """
    Convert PDF -> Images (parallel) -> OCR (parallel) -> Markdown
    
    Args:
        pdf_path: Path to PDF file
        out_dir: Output directory for images
        model: Model name
        api: API endpoint
        output_md: Output markdown file path
        max_workers: Max workers for OCR (None = auto-detect)
    """
    total_start = time.time()
    
    logger.info(f"🚀 Start processing: {pdf_path}")
    
    # Step 1: Convert PDF -> Images (PARALLEL)
    pdf_start = time.time()
    image_paths = pdf2listimages(pdf_path, out_dir, thread_count=PDF_CONVERT_THREADS)
    pdf_time = time.time() - pdf_start
    logger.info(f"✅ PDF converted to images in {pdf_time:.2f} seconds")
    if not image_paths:
        logger.error("No images generated from PDF!")
        return
    
    # Step 2: Process images -> Markdown (PARALLEL)
    # Sử dụng process_images_parallel từ utils_parallel_num_worker.py
    ocr_start = time.time()
    logger.info(f"🚀 Processing {len(image_paths)} images in parallel...")
    
    result = process_images_parallel(
        list_image_paths=image_paths,
        max_workers=max_workers or OCR_MAX_WORKERS,
        model=model,
        api=api,
        process_func=process_single_image_ocr
    )
    
    ocr_time = time.time() - ocr_start
    
    # Log kết quả xử lý
    logger.info(f"✅ OCR completed: {result['total_ok']}/{result['total']} images successful, {result['total_err']} errors")
    logger.info(f"⏱️  OCR processing time: {ocr_time:.2f}s")
    
    # Step 3: Merge markdown từ các file tạm trong out_dir
    md_files_all = glob.glob(f"{out_dir}/*.md")
    
    if not md_files_all:
        logger.error("No markdown files found in output directory!")
        return
    
    # Check nếu có trang OCR lỗi (thiếu file .md) → DỪNG LUÔN
    if len(md_files_all) < len(image_paths):
        missing_count = len(image_paths) - len(md_files_all)
        logger.error(f"❌ Có {missing_count} trang OCR lỗi (không tạo file .md) - DỪNG XỬ LÝ")
        logger.error(f"   Tổng số images: {len(image_paths)} | Số file .md: {len(md_files_all)}")
        
        # Tìm và log các file image không có file .md tương ứng
        md_basenames = {os.path.splitext(os.path.basename(md_file))[0] for md_file in md_files_all}
        missing_images = []
        for image_path in image_paths:
            image_basename = os.path.splitext(os.path.basename(image_path))[0]
            if image_basename not in md_basenames:
                missing_images.append(os.path.basename(image_path))
        
        if missing_images:
            logger.error(f"   📋 Danh sách các file image OCR lỗi ({len(missing_images)} files):")
            for img_file in sorted(missing_images):
                logger.error(f"      - {img_file}")
            
            # Lưu vào file fail.log
            fail_log_path = "fail.log"
            try:
                with open(fail_log_path, "a", encoding="utf-8") as f:
                    f.write(f"\n{'='*80}\n")
                    f.write(f"PDF: {pdf_path}\n")
                    f.write(f"Thời gian: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Tổng số images: {len(image_paths)} | Số file .md: {len(md_files_all)} | Thiếu: {missing_count}\n")
                    f.write(f"Danh sách các file image OCR lỗi ({len(missing_images)} files):\n")
                    for img_file in sorted(missing_images):
                        f.write(f"  - {img_file}\n")
                    f.write(f"{'='*80}\n")
                logger.info(f"💾 Đã lưu thông tin lỗi vào: {fail_log_path}")
            except Exception as e:
                logger.error(f"❌ Không thể ghi vào file {fail_log_path}: {e}")
        
        return
    
    # Sắp xếp file theo số page (extract từ tên file: xxx-1.md -> 1)
    def extract_page_number(filepath):
        match = re.search(r'-(\d+)\.md$', os.path.basename(filepath))
        return int(match.group(1)) if match else 0
    
    md_files = sorted(md_files_all, key=extract_page_number)
    logger.info(f"📄 Found {len(md_files)} markdown files")
    
    # Đọc và gộp tất cả các file markdown
    # Lưu ý: Chỉ có file .md khi OCR thành công (đã xử lý trang trống ở bước OCR)
    md_data = []  # List of (page_num, content)
    for md_file in md_files:
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
                # Extract số trang từ tên file (ví dụ: xxx-5.md -> 5)
                page_num = extract_page_number(md_file)
                md_data.append((page_num, content))
        except Exception as e:
            logger.error(f"❌ Error reading {md_file}: {e}")
    
    if not md_data:
        logger.error("No valid markdown content found!")
        return
    
    # Sắp xếp lại theo số trang (đảm bảo thứ tự đúng)
    md_data.sort(key=lambda x: x[0])
    
    # Gộp và lưu file markdown cuối cùng (dùng số trang từ tên file, không phải số tuần tự)
    os.makedirs(os.path.dirname(output_md), exist_ok=True)
    merged = []
    for page_num, content in md_data:
        # Số trang lấy từ đuôi file .png (ví dụ: xxx-5.png -> Trang 5)
        merged.append(f"Trang {page_num}\n\n{content}\n\n---")
    merged_text = "\n\n".join(merged).rstrip("-\n")
    with open(output_md, "w", encoding="utf-8") as f:
        f.write(merged_text)
    logger.info(f"💾 Saved: {output_md} ({len(md_data)} pages)")
   
    # So sánh số trang của pdf và số trang của markdown
    pdf_pages, md_pages, is_match = compare_page_counts(pdf_path, output_md)
    logger.info(f"PDF pages: {pdf_pages}")
    logger.info(f"Markdown pages: {md_pages}")
    logger.info(f"Match: {is_match}")
    if not is_match:
        logger.error(f"❌ Số trang của pdf ({pdf_pages}) không bằng số trang của markdown ({md_pages})")
        # Thêm đường dẫn của file markdown fail và pdf fail vào file fail.txt
        with open("fail.txt", "a", encoding="utf-8") as f:
            f.write(f"{pdf_path} -> {output_md}\n")
        return
    
    # Xóa các file markdown tạm
    for md_file in md_files:
        try:
            os.remove(md_file)
        except Exception as e:
            logger.warning(f"⚠️  Failed to delete {md_file}: {e}")
    
    total_time = time.time() - total_start
    logger.info(f"\n🎯 TOTAL TIME: {total_time/60:.1f} minutes")
    logger.info(f"   📄 PDF conversion: {pdf_time:.2f}s")
    logger.info(f"   🔍 OCR processing: {ocr_time:.2f}s")
    logger.info(f"   📝 Merge & save: {(total_time - pdf_time - ocr_time):.2f}s")

if __name__ == "__main__":
    start_time = time.time()
    pdf2finalmarkdown(PDF, OUT_DIR, MODEL, API, OUT_MD, max_workers=OCR_MAX_WORKERS)
    end_time = time.time()
    logger.info(f"⏱️  Total execution time: {end_time - start_time:.2f} seconds")