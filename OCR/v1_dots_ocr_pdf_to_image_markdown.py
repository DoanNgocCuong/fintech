import os
import os
from pdf2image import convert_from_path
from openai import OpenAI
import base64, glob

PDF = "/home/ubuntu/cuong_dn/fintech/OCR/data/test-orrrr.pdf"
OUT_DIR = "/home/ubuntu/cuong_dn/fintech/OCR/data/out_images"
MODEL = "rednote-hilab/dots.ocr"
API = "http://103.253.20.30:30010/v1"

os.makedirs(OUT_DIR, exist_ok=True)

pages = convert_from_path(PDF, dpi=200, output_folder=OUT_DIR, fmt="png")

image_paths = sorted(glob.glob(f"{OUT_DIR}/*.png"))

client = OpenAI(base_url=API, api_key="EMPTY")
md_all = []
for p in image_paths:
  b64 = base64.b64encode(open(p, "rb").read()).decode("utf-8")
  resp = client.chat.completions.create(
    model=MODEL,
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
  md_all.append(resp.choices[0].message.content or "")

open("data/test-orrrr.md", "w", encoding="utf-8").write("\n\n".join(md_all))
print("Saved: data/test-orrrr.md")