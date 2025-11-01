import os
import glob
import base64
import re
from pdf2image import convert_from_path
from openai import OpenAI
import logging
from markdownify import markdownify
from PIL import Image
import time
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import List, Dict, Any, Callable, Optional, Tuple
import psutil

# Import utils từ utils_parallel_batch_size_max_worker.py
from utils_parallel_batch_size_max_worker import (
    ParallelBatchProcessor,
    process_images_parallel_optimized
)

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

PDF = "/home/ubuntu/cuong_dn/fintech/OCR/data/Ngành Bảo hiểm/BIC/2014/Bao_cao_tai_chinh/BIC_2014_1_4_1.pdf"
PDF = "/home/ubuntu/cuong_dn/fintech/OCR/data/5_pages_test.pdf"
OUT_DIR = "/home/ubuntu/cuong_dn/fintech/OCR/data/out_images"
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
    logger.info(f"✅ PDF converted in {convert_time:.2f} seconds")
    
    # Tìm và sắp xếp file ảnh theo thời gian modify để đảm bảo đúng thứ tự page
    temp_image_paths = glob.glob(f"{out_dir}/*.png")
    temp_image_paths.sort(key=lambda x: os.path.getmtime(x))
    
    # Đổi tên các file ảnh theo format: tên_file_pdf-1.png, tên_file_pdf-2.png, ...
    image_paths = []
    for idx, temp_path in enumerate(temp_image_paths, start=1):
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
    """OCR image -> text (optimized: read once, no unnecessary conversions)"""
    if client is None:
        client = OpenAI(base_url=api, api_key="EMPTY", timeout=120.0)
    
    # Read file once and encode to base64
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    
    # Call OCR API
    resp = client.chat.completions.create(
        model=model,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": "Extract structured markdown from this page."},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
            ],
        }],
        temperature=0.0,
        max_tokens=4096,
        timeout=120.0
    )
    
    page_text = resp.choices[0].message.content or ""
    logger.info(f"✅ OCR: {os.path.basename(image_path)} -> {len(page_text)} chars")
    return page_text

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
        
        # Save temp markdown file (same name as image but .md extension)
        md_temp_path = os.path.splitext(image_path)[0] + ".md"
        with open(md_temp_path, "w", encoding="utf-8") as f:
            f.write(markdown)
        logger.debug(f"💾 Saved: {os.path.basename(md_temp_path)}")
        
        # Delete image after processing
        os.remove(image_path)
        logger.debug(f"🗑️  Deleted: {os.path.basename(image_path)}")
        
        return markdown
        
    except Exception as e:
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
    logger.info(f"⏱️  PDF conversion: {pdf_time:.2f}s")
    
    if not image_paths:
        logger.error("No images generated from PDF!")
        return
    
    # Step 2: Process images -> Markdown (PARALLEL)
    # Sử dụng ParallelBatchProcessor với GPU monitoring và adaptive batch processing
    ocr_start = time.time()
    logger.info(f"🚀 Processing {len(image_paths)} images in parallel...")
    
    process_images_parallel_optimized(
        image_paths=image_paths,
        process_func=process_single_image_ocr,
        max_workers=max_workers or OCR_MAX_WORKERS,
        batch_size=None,  # Auto-calculate optimal batch size
        enable_gpu_monitoring=True,
        model=model,
        api=api
    )
    
    ocr_time = time.time() - ocr_start
    logger.info(f"⏱️  OCR processing: {ocr_time:.2f}s")
    
    # Step 3: Merge markdown từ các file tạm trong out_dir
    md_files_all = glob.glob(f"{out_dir}/*.md")
    
    if not md_files_all:
        logger.error("No markdown files found in output directory!")
        return
    
    # Sắp xếp file theo số page (extract từ tên file: xxx-1.md -> 1)
    def extract_page_number(filepath):
        match = re.search(r'-(\d+)\.md$', os.path.basename(filepath))
        return int(match.group(1)) if match else 0
    
    md_files = sorted(md_files_all, key=extract_page_number)
    logger.info(f"📄 Found {len(md_files)} markdown files")
    
    # Đọc và gộp tất cả các file markdown
    md_contents = []
    for md_file in md_files:
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    md_contents.append(content)
        except Exception as e:
            logger.error(f"❌ Error reading {md_file}: {e}")
    
    if not md_contents:
        logger.error("No valid markdown content found!")
        return
    
    # Gộp và lưu file markdown cuối cùng
    os.makedirs(os.path.dirname(output_md), exist_ok=True)
    with open(output_md, "w", encoding="utf-8") as f:
        f.write("\n\n ---\n\n".join(md_contents))
    logger.info(f"💾 Saved: {output_md} ({len(md_contents)} pages)")
    
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