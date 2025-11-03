
python 3.11.8
# Hoo to HOOT MODEL 


## 1. 
```bash
pip install torch==2.7.0 torchvision==0.22.0 torchaudio==2.7.0 --index-url https://download.pytorch.org/whl/cu126
```

## 2. Download Model Weights
```python
python3 tools/download_model.py

## with modelscope
python3 tools/download_model.py --type modelscope
```
```bash
pip install vllm==0.6.3.post1
```

## 3. Deployment 

```bash
# Launch vLLM model server
vllm serve rednote-hilab/dots.ocr --trust-remote-code --async-scheduling --gpu-memory-utilization 0.95
```

**1. Nếu muốn dùng GPU thứ 1 (ví dụ máy có nhiều GPU, muốn chỉ định card số 1):**

```bash
sudo lsof -i :30005
```
```bash
CUDA_VISIBLE_DEVICES=1 vllm serve rednote-hilab/dots.ocr --trust-remote-code --async-scheduling --gpu-memory-utilization 0.60
```

```bash
CUDA_VISIBLE_DEVICES=1 vllm serve rednote-hilab/dots.ocr \
  --trust-remote-code \
  --async-scheduling \
  --gpu-memory-utilization 0.70 \
  --host 0.0.0.0 \
  --port 30010
```
```bash
nohup CUDA_VISIBLE_DEVICES=1 vllm serve rednote-hilab/dots.ocr \
  --trust-remote-code --async-scheduling \
  --gpu-memory-utilization 0.60 \
  --host 0.0.0.0 --port 30010 > vllm.log 2>&1 &
```

```bash
nohup env CUDA_VISIBLE_DEVICES=1 vllm serve rednote-hilab/dots.ocr \
  --trust-remote-code --async-scheduling \
  --gpu-memory-utilization 0.60 \
  --host 0.0.0.0 --port 30010 > vllm.log 2>&1 &
```

- `vllm serve`: Khởi động vLLM model server cho inference.
- `rednote-hilab/dots.ocr`: Chỉ định model dots.ocr cần load từ repo.
- `--trust-remote-code`: Cho phép thực thi code model từ repo gốc, bắt buộc với model custom.
- `--async-scheduling`: Bật chế độ xếp lịch bất đồng bộ (asynchronous scheduling) để phục vụ nhiều request nhanh hơn.
- `--gpu-memory-utilization 0.95`: Sử dụng tối đa 95% bộ nhớ VRAM trên GPU, để đạt hiệu năng tốt nhất.

**Tóm lại:**  
- Lệnh này sẽ khởi động server để cung cấp APIs cho inference dots.ocr, tự động dùng toàn bộ tài nguyên GPU được phép bởi CUDA_VISIBLE_DEVICES.  
- Nếu không chỉ định, mặc định dùng GPU 0. Nếu muốn dùng GPU 1, thêm `CUDA_VISIBLE_DEVICES=1`.

## 3. Deployment với Docker Compose

Thay vì chạy trực tiếp, bạn có thể sử dụng Docker Compose để quản lý service dễ dàng hơn:

### Yêu cầu:
- Docker và Docker Compose đã cài đặt
- NVIDIA Container Toolkit đã cài đặt và cấu hình
- Nvidia runtime đã được enable

### Sử dụng:

**1. Tạo file `.env` (tùy chọn) để cấu hình:**
```bash
# Copy file example và chỉnh sửa theo nhu cầu
CUDA_VISIBLE_DEVICES=1
MODEL=rednote-hilab/dots.ocr
GPU_MEMORY_UTILIZATION=0.60
PORT=30010
```

**2. Khởi động service:**
```bash
docker-compose up -d
```

**3. Xem logs:**
```bash
# Xem logs real-time
docker-compose logs -f

# Hoặc xem logs của container
docker logs -f vllm-ocr
```

**4. Dừng service:**
```bash
docker-compose down
```

**5. Restart service:**
```bash
docker-compose restart
```

**Lợi ích khi dùng Docker Compose:**
- Tự động restart nếu container crash
- Quản lý logs dễ dàng
- Dễ dàng thay đổi cấu hình thông qua biến môi trường
- Tách biệt môi trường, không ảnh hưởng đến hệ thống chính
- Health check tự động để đảm bảo service hoạt động

**Lưu ý:**
- Model weights sẽ được cache trong `~/.cache/huggingface` để không phải download lại mỗi lần restart
- Logs được lưu trong thư mục `./logs` 
- Container sẽ sử dụng GPU được chỉ định trong `CUDA_VISIBLE_DEVICES`


[1](https://github.com/rednote-hilab/dots.ocr)



# cODE INNEERENCE 

```PYTHON 
import os
import glob
import base64
from pdf2image import convert_from_path
from openai import OpenAI
import logging

logging.basicConfig(level=logging.INFO)

PDF = "/home/ubuntu/cuong_dn/fintech/OCR/data/test-orrrr.pdf"
OUT_DIR = "/home/ubuntu/cuong_dn/fintech/OCR/data/out_images"
MODEL = "rednote-hilab/dots.ocr"
API = "http://103.253.20.30:30010/v1"
OUT_MD = "data/test-orrrr.md"

def pdf2listimages(pdf_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    convert_from_path(pdf_path, dpi=200, output_folder=out_dir, fmt="png")
    image_paths = sorted(glob.glob(f"{out_dir}/*.png"))
    logging.info(f"Found {len(image_paths)} images")
    return image_paths

def image2text(image_path, model, api, client=None):
    if client is None:
        client = OpenAI(base_url=api, api_key="EMPTY")
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
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
    )
    logging.info(f"Response: {resp.choices[0].message.content[:100]}")
    return resp.choices[0].message.content or ""

from markdownify import markdownify as md

def text2markdown(page_text):
    # Chuyển đổi HTML về markdown bằng markdownify (nếu page_text là HTML)
    return md(page_text, heading_style="ATX")

def pdf2finalmarkdown(pdf_path, out_dir, model, api, output_md):
    client = OpenAI(base_url=api, api_key="EMPTY")
    image_paths = pdf2listimages(pdf_path, out_dir)
    md_all = []
    for img_path in image_paths:
        page_text = image2text(img_path, model, api, client)
        markdown = text2markdown(page_text)
        md_all.append(markdown)
    logging.info(f"Found {len(md_all)} markdown")
    os.makedirs(os.path.dirname(output_md), exist_ok=True)
    with open(output_md, "w", encoding="utf-8") as f:
        f.write("\n\n".join(md_all))
    logging.info(f"Saved: {output_md}")

if __name__ == "__main__":
    pdf2finalmarkdown(PDF, OUT_DIR, MODEL, API, OUT_MD)
```
