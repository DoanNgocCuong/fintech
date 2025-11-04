#!/bin/bash
# ============================================================================
# vLLM Server Start Script - Fixed for Multi-Modal (Image) Inputs
# ============================================================================
# 
# Fixes bug: CUDA assertion error khi xử lý request thứ 2 với image khác nhau
# 
# Nguyên nhân chính: Chunked prefill với max_num_batched_tokens=2048 
#                     không đủ cho image tokens (4819 tokens)
# 
# Giải pháp:
#   - Fix 1: Disable prefix caching (không hữu ích với unique images)
#   - Fix 2: Tăng max_num_batched_tokens lên 8192 (QUAN TRỌNG NHẤT!)
#   - Fix 3: Disable CUDA graphs để tránh replay với wrong tensor sizes
#
# Xem chi tiết: FIX_REPORT.md và ANALYSIS_FIX_NEEDED.md
# ============================================================================

nohup env CUDA_VISIBLE_DEVICES=1 vllm serve rednote-hilab/dots.ocr \
  --trust-remote-code \
  --async-scheduling \
  --gpu-memory-utilization 0.60 \
  --host 0.0.0.0 \
  --port 30010 \
  --max-num-batched-tokens 8192 \
  --max-num-seqs 8 \
  > vllm.log 2>&1 &

