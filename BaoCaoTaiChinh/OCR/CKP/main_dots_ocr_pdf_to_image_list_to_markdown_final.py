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

# Cấu hình logging để hiển thị log ra console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

PDF = "/home/ubuntu/cuong_dn/fintech/OCR/data/5_pages_test.pdf"
OUT_DIR = "/home/ubuntu/cuong_dn/fintech/OCR/data/out_images"
MODEL = "rednote-hilab/dots.ocr"
API = "http://103.253.20.30:30010/v1"
OUT_MD = "data/33_pages_test.md"

def pdf2listimages(pdf_path, out_dir):
    """
    Convert PDF -> Images
    Đặt tên file ảnh theo format: tên_file_pdf-1.png, tên_file_pdf-2.png, ...
    """
    os.makedirs(out_dir, exist_ok=True)
    
    # Lấy tên file PDF (không có phần mở rộng) để đặt tên cho ảnh
    pdf_basename = os.path.splitext(os.path.basename(pdf_path))[0]
    
    logger.info(f"🔄 Converting PDF to images...")
    convert_start = time.time()
    
    # Convert PDF thành images (tên file tạm thời sẽ được đổi sau)
    images = convert_from_path(pdf_path, dpi=200, output_folder=out_dir, fmt="png")
    
    convert_time = time.time() - convert_start
    logger.info(f"✅ PDF converted in {convert_time:.2f} seconds")
    
    # Tìm tất cả file ảnh đã được tạo và sắp xếp theo thời gian modify (để đảm bảo đúng thứ tự page)
    temp_image_paths = glob.glob(f"{out_dir}/*.png")
    # Sắp xếp theo thời gian modify để đảm bảo đúng thứ tự page
    temp_image_paths.sort(key=lambda x: os.path.getmtime(x))
    
    # Đổi tên các file ảnh theo format: tên_file_pdf-1.png, tên_file_pdf-2.png, ...
    image_paths = []
    for idx, temp_path in enumerate(temp_image_paths, start=1):
        new_name = f"{pdf_basename}-{idx}.png"
        new_path = os.path.join(out_dir, new_name)
        
        try:
            os.rename(temp_path, new_path)
            image_paths.append(new_path)
            logger.debug(f"Renamed: {os.path.basename(temp_path)} -> {new_name}")
        except Exception as e:
            logger.error(f"❌ Failed to rename {temp_path} to {new_path}: {e}")
            # Nếu không đổi được tên, vẫn dùng file cũ
            image_paths.append(temp_path)
    
    logger.info(f"📄 Found {len(image_paths)} images (renamed to {pdf_basename}-N.png format)")
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
        client = OpenAI(base_url=api, api_key="EMPTY", timeout=120.0)
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
        timeout=120.0
    )
    page_text = resp.choices[0].message.content or ""
    logger.info(f"Response from {os.path.basename(image_path)}: {page_text[:100]}")  # Log ra 100 ký tự đầu của kết quả trả về
    return page_text  # Trả về nội dung tin nhắn trả lời của model, nếu không có thì trả chuỗi rỗng



def text2markdown(page_text):
    # Chuyển đổi HTML về markdown bằng markdownify (nếu page_text là HTML)
    return markdownify(page_text, heading_style="ATX")

def pdf2finalmarkdown(pdf_path, out_dir, model, api, output_md):
    """
    Convert PDF -> Images -> OCR -> Markdown
    Lưu markdown tạm cho từng page, sau đó gộp lại từ các file tạm
    """
    logger.info(f"🚀 Start processing: {pdf_path}")
    client = OpenAI(base_url=api, api_key="EMPTY", timeout=120.0)
    image_paths = pdf2listimages(pdf_path, out_dir)
    logger.info(f"📄 Found {len(image_paths)} images")
    
    # Process từng image và lưu markdown tạm
    for img_path in image_paths:
        try:
            page_text = image2text(img_path, model, api, client)
            markdown = text2markdown(page_text)
            
            # Lưu file markdown tạm (cùng tên với image nhưng đuôi .md)
            md_temp_path = os.path.splitext(img_path)[0] + ".md"
            try:
                with open(md_temp_path, "w", encoding="utf-8") as f:
                    f.write(markdown)
                logger.info(f"💾 Saved markdown: {os.path.basename(md_temp_path)} (at {md_temp_path})")
            except Exception as e:
                logger.warning(f"⚠️  Failed to save temp markdown {md_temp_path}: {e}")
            
            logger.info(f"✅ Processed: {os.path.basename(img_path)}")
            
            # Xóa ảnh sau khi đã process thành công
            try:
                os.remove(img_path)
                logger.info(f"🗑️  Deleted: {os.path.basename(img_path)}")
            except Exception as e:
                logger.warning(f"⚠️  Failed to delete image {img_path}: {e}")
        except Exception as e:
            logger.error(f"❌ Error processing {img_path}: {e}")
            continue
    
    # Gộp markdown từ các file tạm
    # Tìm tất cả file .md trong out_dir và sắp xếp theo thứ tự (dựa trên số page nếu có)
    md_files_all = glob.glob(f"{out_dir}/*.md")
    
    if not md_files_all:
        logger.error("No markdown files found in output directory!")
        return
    
    # Sắp xếp file theo số page (nếu có trong tên file, ví dụ: xxx-1.md, xxx-2.md)
    # Extract số từ tên file và sắp xếp theo số đó
    def extract_page_number(filepath):
        """Extract số page từ tên file (ví dụ: xxx-1.md → 1)"""
        basename = os.path.basename(filepath)
        # Tìm số ở cuối tên file, trước phần mở rộng
        match = re.search(r'-(\d+)\.md$', basename)
        if match:
            return int(match.group(1))
        # Nếu không tìm thấy, dùng tên file để sort
        return 0
    
    md_files = sorted(md_files_all, key=extract_page_number)
    
    logger.info(f"📄 Found {len(md_files)} markdown files in {out_dir}")
    
    # Đọc và gộp tất cả các file markdown
    md_contents = []
    for md_file in md_files:
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:  # Chỉ thêm nếu có nội dung
                    md_contents.append(content)
                    logger.debug(f"✅ Read: {os.path.basename(md_file)}")
                else:
                    logger.warning(f"⚠️  Empty file: {os.path.basename(md_file)}")
        except Exception as e:
            logger.error(f"❌ Error reading {md_file}: {e}")
            continue
    
    if not md_contents:
        logger.error("No valid markdown content found!")
        return
    
    # Gộp và lưu file markdown cuối cùng
    logger.info(f"✅ Merging {len(md_contents)} markdown pages")
    os.makedirs(os.path.dirname(output_md), exist_ok=True)
    with open(output_md, "w", encoding="utf-8") as f:
        f.write("\n\n ---\n\n".join(md_contents))
    logger.info(f"💾 Saved: {output_md}")
    
    # Xóa các file markdown tạm sau khi đã gộp
    for md_file in md_files:
        try:
            os.remove(md_file)
            logger.debug(f"🗑️  Deleted temp file: {os.path.basename(md_file)}")
        except Exception as e:
            logger.warning(f"⚠️  Failed to delete {md_file}: {e}")

if __name__ == "__main__":
    start_time = time.time()
    pdf2finalmarkdown(PDF, OUT_DIR, MODEL, API, OUT_MD)
    end_time = time.time()
    logger.info(f"Total time: {end_time - start_time}")