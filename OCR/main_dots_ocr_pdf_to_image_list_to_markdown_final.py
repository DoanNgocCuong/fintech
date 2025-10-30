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