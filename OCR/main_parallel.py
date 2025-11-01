import os
import glob
import base64
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

PDF = "/home/ubuntu/cuong_dn/fintech/OCR/data/33_pages_test.pdf"
OUT_DIR = "/home/ubuntu/cuong_dn/fintech/OCR/data/out_images"
MODEL = "rednote-hilab/dots.ocr"
API = "http://103.253.20.30:30010/v1"
OUT_MD = "data/33_pages_test.md"

# Config cho parallel processing
PDF_CONVERT_THREADS = multiprocessing.cpu_count()  # Số cores để convert PDF
# OCR_MAX_WORKERS phải ≤ server max_num_seqs (hiện tại server = 8)
# Nên set = 8 để tận dụng tối đa server capacity
OCR_MAX_WORKERS = 8  # Số workers cho OCR parallel (đồng bộ với server max-num-seqs=8)

# ============================================================================
# OPTIMIZE 1: PDF -> Images với parallel conversion
# ============================================================================
def pdf2listimages(pdf_path, out_dir, thread_count=None):
    """
    Convert PDF -> Images với parallel processing
    Tăng tốc bằng cách convert nhiều pages đồng thời
    """
    os.makedirs(out_dir, exist_ok=True)
    
    if thread_count is None:
        thread_count = PDF_CONVERT_THREADS
    
    logger.info(f"🔄 Converting PDF to images with {thread_count} threads...")
    convert_start = time.time()
    
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
    
    image_paths = sorted(glob.glob(f"{out_dir}/*.png"))
    logger.info(f"Found {len(image_paths)} images")
    return image_paths

# ============================================================================
# OCR Functions
# ============================================================================
def image2text(image_path, model, api, client=None):
    """OCR image -> text"""
    if client is None:
        client = OpenAI(base_url=api, api_key="EMPTY", timeout=120.0)
    
    # Optimize: Đọc file 1 lần, không cần convert RGB và save lại
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    
    logger.info(f"Base64 encoded: {os.path.basename(image_path)}")
    
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
    logger.info(f"Response from {os.path.basename(image_path)}: {page_text[:100]}")
    return page_text

def text2markdown(page_text):
    """Chuyển đổi HTML về markdown"""
    return markdownify(page_text, heading_style="ATX")

# ============================================================================
# OPTIMIZE 2: OCR Processing Function với utils_parallel_batch_size_max_worker.py
# ============================================================================
def process_single_image_ocr(image_path: str, model: str, api: str, **kwargs) -> Optional[str]:
    """
    Process single image: OCR -> Markdown -> Delete image
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
        # Tạo client riêng cho mỗi thread (thread-safe)
        client = OpenAI(base_url=api, api_key="EMPTY", timeout=120.0)
        
        # OCR image -> text
        page_text = image2text(image_path, model, api, client)
        
        # Convert text -> markdown
        markdown = text2markdown(page_text)
        
        logger.info(f"✅ Processed: {os.path.basename(image_path)}")
        
        # Xóa ảnh sau khi process thành công
        try:
            os.remove(image_path)
            logger.info(f"🗑️  Deleted: {os.path.basename(image_path)}")
        except Exception as e:
            logger.warning(f"⚠️  Failed to delete {image_path}: {e}")
        
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
    
    # Step 2: Process images -> Markdown (PARALLEL với utils_parallel_batch_size_max_worker.py)
    # Sử dụng ParallelBatchProcessor với GPU monitoring và adaptive batch processing
    logger.info(f"🚀 Using ParallelBatchProcessor with GPU monitoring...")
    logger.info(f"   🎮 Max workers: {max_workers or OCR_MAX_WORKERS}")
    logger.info(f"   🔧 Adaptive batch processing: ✅")
    
    md_all = process_images_parallel_optimized(
        image_paths=image_paths,
        process_func=process_single_image_ocr,
        max_workers=max_workers or OCR_MAX_WORKERS,
        batch_size=None,  # Auto-calculate optimal batch size
        enable_gpu_monitoring=True,  # Monitor GPU usage in real-time
        model=model,
        api=api
    )
    
    if not md_all:
        logger.error("No markdown generated!")
        return
    
    # Step 3: Save markdown file
    logger.info(f"✅ Found {len(md_all)} markdown pages")
    os.makedirs(os.path.dirname(output_md), exist_ok=True)
    with open(output_md, "w", encoding="utf-8") as f:
        f.write("\n\n".join(md_all))
    logger.info(f"💾 Saved: {output_md}")
    
    total_time = time.time() - total_start
    logger.info(f"\n🎯 TOTAL TIME: {total_time/60:.1f} minutes")
    logger.info(f"   📄 PDF conversion: {pdf_time:.2f}s")
    logger.info(f"   🔍 OCR processing: {total_time - pdf_time:.2f}s")

if __name__ == "__main__":
    start_time = time.time()
    pdf2finalmarkdown(PDF, OUT_DIR, MODEL, API, OUT_MD, max_workers=OCR_MAX_WORKERS)
    end_time = time.time()
    logger.info(f"⏱️  Total execution time: {end_time - start_time:.2f} seconds")