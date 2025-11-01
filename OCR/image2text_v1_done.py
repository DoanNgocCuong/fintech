import os
import glob
import base64
from pdf2image import convert_from_path
from openai import OpenAI
import logging
import time
from PIL import Image

logging.basicConfig(level=logging.INFO)


def image2text(image_path, model, api, client=None):
    # Nếu client chưa được truyền vào thì khởi tạo một client OpenAI mới với base_url và api_key mặc định
    if client is None:
        client = OpenAI(base_url=api, api_key="EMPTY")
    # Mở file ảnh sử dụng thư viện PIL (Pillow)
    with Image.open(image_path) as img:
        logging.info(f"Image size: {img.size}, mode: {img.mode}")  # Ghi lại thông tin kích thước và mode của ảnh
        img = img.convert("RGB")  # Chuyển ảnh về mode RGB để đảm bảo tương thích
        img.save(image_path, "PNG")  # Lưu ảnh lại dưới định dạng PNG (ghi đè lên ảnh cũ)
    # Đọc file ảnh dưới dạng nhị phân để mã hóa thành base64
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")  # Mã hóa nội dung thành base64 và chuyển thành chuỗi utf-8
    logging.info("Base64 encoded image successfully.")  # Log thông báo đã mã hóa base64 thành công
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
    logging.info(f"Response: {resp.choices[0].message.content[:100]}")  # Log ra 100 ký tự đầu của kết quả trả về
    return resp.choices[0].message.content or ""  # Trả về nội dung tin nhắn trả lời của model, nếu không có thì trả chuỗi rỗng

MODEL = "rednote-hilab/dots.ocr"
API = "http://103.253.20.30:30010/v1"

FOLDER_PATH = "/home/ubuntu/cuong_dn/fintech/OCR/data/out_images"

def folderImages2text(folder_path, model, api, client=None):
    image_paths = sorted(glob.glob(f"{folder_path}/*.png"))
    for image_path in image_paths:
        text = image2text(image_path, model, api, client)
        logging.info(f"Text: {text}")
    return text

if __name__ == "__main__":
    start_time = time.time()
    folderImages2text(FOLDER_PATH, MODEL, API)
    end_time = time.time()
    logging.info(f"Total time: {end_time - start_time}")