import os
import glob
import base64
from openai import OpenAI
import logging
import time
from PIL import Image
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, retry_if_result
from openai import APIError, InternalServerError

# Cấu hình logging để hiển thị log ra console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Ngưỡng kích thước ảnh cho model dots.ocr
MAX_TOTAL_PIXELS = 11_289_600  # Tối đa: 11,289,600 pixels (ví dụ: 3360 × 3360px)
MIN_TOTAL_PIXELS = 360_000  # Tối thiểu: 600 × 600px


def resize_image_if_needed(img, max_pixels=MAX_TOTAL_PIXELS):
    """
    Resize ảnh nếu vượt quá ngưỡng tối đa, giữ nguyên tỷ lệ khung hình
    """
    width, height = img.size
    total_pixels = width * height
    
    if total_pixels > max_pixels:
        # Tính toán kích thước mới giữ nguyên tỷ lệ
        scale_factor = (max_pixels / total_pixels) ** 0.5
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        logging.warning(f"Image too large ({width}x{height} = {total_pixels:,} pixels). Resizing to {new_width}x{new_height} = {new_width*new_height:,} pixels")
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        return img, True
    return img, False

def validate_and_prepare_image(image_path):
    """
    Validate và chuẩn bị ảnh: kiểm tra kích thước, resize nếu cần, convert sang RGB
    """
    try:
        with Image.open(image_path) as img:
            original_size = img.size
            original_pixels = original_size[0] * original_size[1]
            
            # Kiểm tra ảnh quá nhỏ
            if original_pixels < MIN_TOTAL_PIXELS:
                logging.warning(f"Image too small: {original_size[0]}x{original_size[1]} = {original_pixels:,} pixels (< {MIN_TOTAL_PIXELS:,})")
            
            # Resize nếu quá lớn
            img = img.convert("RGB")  # Chuyển về RGB trước
            img, was_resized = resize_image_if_needed(img, MAX_TOTAL_PIXELS)
            
            # Lưu lại ảnh đã xử lý
            img.save(image_path, "PNG")
            
            final_size = img.size
            final_pixels = final_size[0] * final_size[1]
            logging.info(f"Image ready: {final_size[0]}x{final_size[1]} = {final_pixels:,} pixels (original: {original_size[0]}x{original_size[1]} = {original_pixels:,})")
            
            return True
    except Exception as e:
        logging.error(f"Error validating image {image_path}: {str(e)}")
        return False

def check_server_health(api, timeout=5):
    """Kiểm tra server có đang hoạt động không"""
    try:
        client = OpenAI(base_url=api, api_key="EMPTY", timeout=timeout)
        # Thử gọi endpoint /v1/models để check health
        client.models.list()
        return True
    except Exception as e:
        logging.warning(f"Server health check failed: {str(e)}")
        return False

@retry(
    stop=stop_after_attempt(5),  # Retry tối đa 5 lần
    wait=wait_exponential(multiplier=3, min=5, max=60),  # Wait lâu hơn: 5s, 15s, 45s, 60s
    retry=retry_if_exception_type((InternalServerError, APIError, Exception)),
    reraise=True
)
def image2text_with_retry(image_path, model, api, client):
    """
    Xử lý ảnh với retry logic và health check
    """
    # Validate và chuẩn bị ảnh
    if not validate_and_prepare_image(image_path):
        raise ValueError(f"Failed to validate/prepare image: {image_path}")
    
    # Kiểm tra server health trước khi gửi request
    if not check_server_health(api, timeout=10):
        logging.warning("Server health check failed, waiting before retry...")
        time.sleep(10)  # Đợi thêm nếu server có vấn đề
    
    # Đọc file ảnh dưới dạng nhị phân để mã hóa thành base64
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    
    logging.info("Base64 encoded image successfully.")
    
    # Tạo request với timeout dài hơn
    try:
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
            timeout=120.0  # Timeout 2 phút cho mỗi request
        )
        
        content = resp.choices[0].message.content or ""
        logging.info(f"Response: {content[:100]}")
        return content
    except InternalServerError as e:
        # Lỗi 500 - có thể engine đã crash, cần đợi lâu hơn
        logging.error(f"Internal Server Error (engine may have crashed): {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Request failed: {str(e)}")
        raise

def image2text(image_path, model, api, client=None, create_new_client=False):
    """
    Xử lý ảnh với error handling
    Nếu create_new_client=True, sẽ tạo client mới để tránh state pollution
    """
    if client is None or create_new_client:
        client = OpenAI(base_url=api, api_key="EMPTY", timeout=120.0)
    
    try:
        return image2text_with_retry(image_path, model, api, client)
    except InternalServerError as e:
        # Engine crash - cần đợi và thử lại với client mới
        logging.error(f"Engine may have crashed. Waiting 30 seconds before retry with new client...")
        time.sleep(30)
        # Tạo client mới
        new_client = OpenAI(base_url=api, api_key="EMPTY", timeout=120.0)
        try:
            return image2text_with_retry(image_path, model, api, new_client)
        except Exception as e2:
            logging.error(f"Failed after engine recovery attempt: {str(e2)}")
            raise
    except Exception as e:
        logging.error(f"Failed to process {image_path} after all retries: {str(e)}")
        raise  # Re-raise để caller có thể xử lý

IMAGE = "/home/ubuntu/cuong_dn/fintech/OCR/data/out_images/c30c39bc-b402-4597-a9c9-c19ef8533c32-72.png"
MODEL = "rednote-hilab/dots.ocr"
API = "http://103.253.20.30:30010/v1"

FOLDER_PATH = "/home/ubuntu/cuong_dn/fintech/OCR/data/out_images"

def folderImages2text(folder_path, model, api, client=None, delay_between_requests=3.0, create_new_client_per_request=False):
    """
    Xử lý tất cả ảnh trong folder và trả về danh sách kết quả
    
    Args:
        folder_path: Đường dẫn đến folder chứa ảnh
        model: Tên model
        api: API endpoint
        client: OpenAI client (nếu None sẽ tạo mới)
        delay_between_requests: Thời gian delay giữa các requests (giây) - mặc định 3s để tránh crash
        create_new_client_per_request: Tạo client mới cho mỗi request để tránh state pollution
    """
    if client is None:
        client = OpenAI(base_url=api, api_key="EMPTY", timeout=120.0)
    
    image_paths = sorted(glob.glob(f"{folder_path}/*.png"))
    logging.info(f"Found {len(image_paths)} images in folder: {folder_path}")
    logging.info(f"Delay between requests: {delay_between_requests}s")
    
    results = []
    failed_images = []
    consecutive_failures = 0
    max_consecutive_failures = 3
    
    for idx, image_path in enumerate(image_paths, 1):
        logging.info(f"Processing image {idx}/{len(image_paths)}: {os.path.basename(image_path)}")
        
        try:
            # Tạo client mới nếu cần hoặc sau vài requests để tránh state pollution
            use_new_client = create_new_client_per_request or (idx % 10 == 0)
            
            text = image2text(image_path, model, api, client, create_new_client=use_new_client)
            
            results.append({
                "image_path": image_path,
                "text": text,
                "status": "success"
            })
            consecutive_failures = 0  # Reset counter
            logging.info(f"✅ Completed image {idx}/{len(image_paths)}")
            
        except InternalServerError as e:
            consecutive_failures += 1
            failed_images.append(image_path)
            results.append({
                "image_path": image_path,
                "text": None,
                "status": "failed",
                "error": f"InternalServerError: {str(e)}"
            })
            logging.error(f"❌ Failed image {idx}/{len(image_paths)} (consecutive failures: {consecutive_failures}): {str(e)}")
            
            # Nếu engine crash nhiều lần liên tiếp, đợi lâu hơn
            if consecutive_failures >= max_consecutive_failures:
                wait_time = 60  # Đợi 1 phút
                logging.warning(f"Too many consecutive failures ({consecutive_failures}). Waiting {wait_time}s for engine recovery...")
                time.sleep(wait_time)
                consecutive_failures = 0  # Reset sau khi đợi
                # Tạo client mới
                client = OpenAI(base_url=api, api_key="EMPTY", timeout=120.0)
                
        except Exception as e:
            consecutive_failures += 1
            failed_images.append(image_path)
            results.append({
                "image_path": image_path,
                "text": None,
                "status": "failed",
                "error": str(e)
            })
            logging.error(f"❌ Failed image {idx}/{len(image_paths)}: {str(e)}")
        
        # Delay giữa các requests - tăng delay sau mỗi failure
        if idx < len(image_paths):
            current_delay = delay_between_requests
            if consecutive_failures > 0:
                current_delay *= (1 + consecutive_failures * 0.5)  # Tăng delay theo số lần fail
            logging.debug(f"Waiting {current_delay:.1f}s before next request...")
            time.sleep(current_delay)
    
    successful = len(results) - len(failed_images)
    logging.info(f"Successfully processed {successful}/{len(results)} images")
    
    if failed_images:
        logging.warning(f"Failed images ({len(failed_images)}): {[os.path.basename(img) for img in failed_images[:5]]}")
    
    return results

if __name__ == "__main__":
    start_time = time.time()
    results = folderImages2text(FOLDER_PATH, MODEL, API, delay_between_requests=1.0)
    end_time = time.time()
    
    successful = sum(1 for r in results if r.get("status") == "success")
    failed = len(results) - successful
    
    logging.info(f"Total time: {end_time - start_time:.2f} seconds")
    logging.info(f"Successfully processed: {successful} images")
    if failed > 0:
        logging.info(f"Failed: {failed} images")