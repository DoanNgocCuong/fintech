import os
import glob
import base64
from pdf2image import convert_from_path
from openai import OpenAI
import logging
from markdownify import markdownify
from PIL import Image
import time

# Cấu hình logging để hiển thị log ra console
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

def pdf2listimages(pdf_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    convert_from_path(pdf_path, dpi=200, output_folder=out_dir, fmt="png")
    image_paths = sorted(glob.glob(f"{out_dir}/*.png"))
    logger.info(f"Found {len(image_paths)} images")
    return image_paths

# def image2text(image_path, model, api, client=None):
#     if client is None:
#         client = OpenAI(base_url=api, api_key="EMPTY")
#     with open(image_path, "rb") as f:
#         b64 = base64.b64encode(f.read()).decode("utf-8")
#     resp = client.chat.completions.create(
#         model=model,
#         messages=[{
#             "role": "user",
#             "content": [
#                 {"type": "text", "text": "Extract structured markdown from this page."},
#                 {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
#             ],
#         }],
#         temperature=0.0,
#         max_tokens=4096,
#     )
#     logging.info(f"Response: {resp.choices[0].message.content[:100]}")
#     return resp.choices[0].message.content or ""

def image2text(image_path, model, api, client=None):
    # Nếu client chưa được truyền vào thì khởi tạo một client OpenAI mới với base_url và api_key mặc định
    if client is None:
        client = OpenAI(base_url=api, api_key="EMPTY")
    # Mở file ảnh sử dụng thư viện PIL (Pillow)
    with Image.open(image_path) as img:
        logger.info(f"Image size: {img.size}, mode: {img.mode}")  # Ghi lại thông tin kích thước và mode của ảnh
        img = img.convert("RGB")  # Chuyển ảnh về mode RGB để đảm bảo tương thích
        img.save(image_path, "PNG")  # Lưu ảnh lại dưới định dạng PNG (ghi đè lên ảnh cũ)
    # Đọc file ảnh dưới dạng nhị phân để mã hóa thành base64
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")  # Mã hóa nội dung thành base64 và chuyển thành chuỗi utf-8
    logger.info("Base64 encoded image successfully.")  # Log thông báo đã mã hóa base64 thành công
    # Tạo request gửi tới API OpenAI với thông tin ảnh đã được encode base64
    resp = client.chat.completions.create(
        model=model,  # Tên model sử dụng
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": "Extract structured markdown from this page."},  # Yêu cầu trích xuất markdown
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
                # Truyền ảnh đã encode base64 dưới dạng image_url
            ],
        }],
        temperature=0.0,  # Đặt nhiệt độ model về 0 (kết quả ổn định)
        max_tokens=4096,  # Số lượng token tối đa trả về
    )
    logger.info(f"Response: {resp.choices[0].message.content[:100]}")  # Log ra 100 ký tự đầu của kết quả trả về
    return resp.choices[0].message.content or ""  # Trả về nội dung tin nhắn trả lời của model, nếu không có thì trả chuỗi rỗng



def text2markdown(page_text):
    # Chuyển đổi HTML về markdown bằng markdownify (nếu page_text là HTML)
    return markdownify(page_text, heading_style="ATX")

def pdf2finalmarkdown(pdf_path, out_dir, model, api, output_md):
    logger.info(f"Start processing: {pdf_path}")
    client = OpenAI(base_url=api, api_key="EMPTY")
    image_paths = pdf2listimages(pdf_path, out_dir)
    logger.info(f"Found {len(image_paths)} images")
    
    md_all = []
    for img_path in image_paths:
        page_text = image2text(img_path, model, api, client)
        markdown = text2markdown(page_text)
        logger.info(f"Processed image: {img_path}")
        md_all.append(markdown)
        # Xóa ảnh sau khi đã process thành công
        try:
            os.remove(img_path)
            logger.info(f"Deleted image: {img_path}")
        except Exception as e:
            logger.warning(f"Failed to delete image {img_path}: {e}")
    logger.info(f"Found {len(md_all)} markdown")
    os.makedirs(os.path.dirname(output_md), exist_ok=True)
    with open(output_md, "w", encoding="utf-8") as f:
        f.write("\n\n".join(md_all))
    logger.info(f"Saved: {output_md}")

if __name__ == "__main__":
    start_time = time.time()
    pdf2finalmarkdown(PDF, OUT_DIR, MODEL, API, OUT_MD)
    end_time = time.time()
    logger.info(f"Total time: {end_time - start_time}")