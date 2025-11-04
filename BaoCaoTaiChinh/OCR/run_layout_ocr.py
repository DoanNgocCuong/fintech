#!/usr/bin/env python3
import argparse
import os
from pathlib import Path
from typing import List

import torch
from dots_ocr.utils import dict_promptmode_to_prompt
from qwen_vl_utils import process_vision_info
from transformers import AutoModelForCausalLM, AutoProcessor
import json
import fitz


def convert_pdf_first_page_to_jpg(pdf_path: Path, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{pdf_path.stem}_page1.jpg"
    doc = fitz.open(str(pdf_path))
    page = doc.load_page(0)
    pix = page.get_pixmap(dpi=200)
    pix.save(str(out_path))
    doc.close()
    return out_path



def load_model(weights_dir: Path, device_str: str):
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    # Use float32 for both CPU and GPU to avoid dtype conflicts
    use_cuda = device_str.startswith("cuda") and torch.cuda.is_available()
    target_dtype = torch.float32  # Always use float32

    model = AutoModelForCausalLM.from_pretrained(
        str(weights_dir),
        attn_implementation=None,
        torch_dtype=target_dtype,
        device_map={"": device_str},
        trust_remote_code=True,
    )
    processor = AutoProcessor.from_pretrained(str(weights_dir), trust_remote_code=True, use_fast=True)
    
    # Force all model components to float32
    model = model.to(dtype=target_dtype, device=device_str)
    if hasattr(model, "config"):
        model.config.torch_dtype = target_dtype
    
    # Force vision tower to float32
    if hasattr(model, "vision_tower"):
        model.vision_tower = model.vision_tower.to(dtype=torch.float32, device=device_str)
        # Also force any conv/linear layers in vision tower
        for module in model.vision_tower.modules():
            if hasattr(module, 'weight') and module.weight is not None:
                module.weight.data = module.weight.data.to(dtype=torch.float32)
            if hasattr(module, 'bias') and module.bias is not None:
                module.bias.data = module.bias.data.to(dtype=torch.float32)
        
        # Monkey patch the forward method to disable bf16
        original_forward = model.vision_tower.forward
        def patched_forward(hidden_states, grid_thw, bf16=False):
            return original_forward(hidden_states, grid_thw, bf16=False)
        model.vision_tower.forward = patched_forward
    
    return model, processor


def run_ocr(image_path: Path, prompt: str, model, processor) -> str:
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": str(image_path)},
                {"type": "text", "text": prompt},
            ],
        }
    ]
    text_input = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    image_inputs, video_inputs = process_vision_info(messages)
    
    # Force image_inputs to float32 before processing
    if image_inputs is not None:
        for i, img in enumerate(image_inputs):
            if hasattr(img, 'convert'):
                image_inputs[i] = img.convert('RGB')
    
    inputs = processor(text=[text_input], images=image_inputs, videos=video_inputs, padding=True, return_tensors="pt")
    
    # Debug: check dtype before any conversion
    print(f"Before conversion - pixel_values dtype: {inputs['pixel_values'].dtype if 'pixel_values' in inputs else 'None'}")
    
    # Get model device and dtype
    device = next(model.parameters()).device
    dtype = next(model.parameters()).dtype
    
    # Force ALL inputs to model's exact dtype and device
    def force_dtype_device(obj):
        if torch.is_tensor(obj):
            if obj.is_floating_point():
                return obj.to(device=device, dtype=dtype)
            else:
                return obj.to(device=device)
        if isinstance(obj, (list, tuple)):
            return type(obj)(force_dtype_device(x) for x in obj)
        if isinstance(obj, dict):
            return {k: force_dtype_device(v) for k, v in obj.items()}
        return obj
    
    # Apply to all tensor fields in inputs
    inputs = force_dtype_device(inputs)
    
    # Double-check critical tensors are on correct device
    for key in ['input_ids', 'attention_mask', 'pixel_values']:
        if key in inputs and inputs[key] is not None:
            inputs[key] = inputs[key].to(device=device)
            if inputs[key].is_floating_point():
                inputs[key] = inputs[key].to(dtype=dtype)
    
    # Debug: print tensor dtypes
    print(f"Model dtype: {dtype}")
    print(f"Model device: {device}")
    for key in ['input_ids', 'attention_mask', 'pixel_values']:
        if key in inputs and inputs[key] is not None:
            print(f"{key}: dtype={inputs[key].dtype}, device={inputs[key].device}")

    with torch.inference_mode():
        generated_ids = model.generate(**inputs, max_new_tokens=1024)
    trimmed = [out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)]
    return processor.batch_decode(trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]


def main() -> None:
    # Step 1: Parse command-line arguments
    parser = argparse.ArgumentParser(description="Run DotsOCR inference on an image or PDF")
    parser.add_argument("input", help="Path to image or PDF")
    parser.add_argument(
        "--weights",
        default=str(Path(__file__).parent / "dots.ocr" / "weights" / "DotsOCR"),
        help="Path to DotsOCR weights directory",
    )
    parser.add_argument(
        "--prompt",
        default="Extract layout elements in English.",
        help="Prompt text for the model",
    )
    parser.add_argument("--out", default=None, help="Optional path to save raw text output")
    parser.add_argument("--gpu", type=int, default=0, help="GPU index to use if CUDA is available (default: 0)")
    args = parser.parse_args()

    # Step 2: Resolve input path and check existence
    inp = Path(args.input).expanduser().resolve()
    if not inp.exists():
        raise FileNotFoundError(f"Input not found: {inp}")

    # Step 3: Handle PDF conversion if necessary
    if inp.suffix.lower() == ".pdf":
        tmp_dir = Path("./tmp_images")
        image_path = convert_pdf_first_page_to_jpg(inp, tmp_dir)
    else:
        image_path = inp

    # Step 4: Resolve device (GPU or CPU)
    if torch.cuda.is_available():
        device_str = f"cuda:{args.gpu}"
    else:
        device_str = "cpu"

    # Step 5: Load model and processor
    model, processor = load_model(Path(args.weights), device_str)

    # Step 6: Run OCR
    output = run_ocr(image_path, args.prompt, model, processor)

    # Step 7: Print output (truncated)
    print("\n--- OCR Output (truncated 2000 chars) ---\n")
    print(output[:2000])

    # Step 8: Save output if requested
    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
        print(f"\nSaved output to {args.out}")


if __name__ == "__main__":
    main()

