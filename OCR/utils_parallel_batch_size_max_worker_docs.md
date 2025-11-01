```bash
🚀 Using ParallelBatchProcessor with GPU monitoring...
   🎮 Max workers: 8 (Server max-num-seqs: 8)
   📊 Total images to process: 33
   🔧 Adaptive batch processing: ✅
   ⚡ Parallel capacity: 8 OCR requests simultaneously

🚀 Parallel Batch Processing Setup:
   📊 Total items: 33
   📦 Batch size: 2 items/batch
   🧵 Max workers: 8 (Processing 8 items simultaneously)
   📋 Total batches: 17
   💾 Memory limit: 2048MB
   🔧 Adaptive mode: ✅
   🎮 GPU monitoring: ✅
   ⚡ Parallel capacity: Up to 8 concurrent requests
 
```

Giải thích ý nghĩa các log:

## Giải thích log

### Phần 1: Cấu hình từ `main_parallel.py`

```
🚀 Using ParallelBatchProcessor with GPU monitoring...
   🎮 Max workers: 8 (Server max-num-seqs: 8)
```
- Client dùng 8 workers
- Server hỗ trợ tối đa 8 requests song song

```
   📊 Total images to process: 33
```
- Có 33 ảnh cần OCR

```
   ⚡ Parallel capacity: 8 OCR requests simultaneously
```
- Có thể xử lý 8 ảnh cùng lúc

---

### Phần 2: Cấu hình từ `utils_parallel_batch_size_max_worker.py`

```
🚀 Parallel Batch Processing Setup:
   📊 Total items: 33
   📦 Batch size: 2 items/batch
```
- 33 items tổng cộng
- Chia thành batches, mỗi batch 2 items

```
   🧵 Max workers: 8 (Processing 8 items simultaneously)
```
- Có 8 workers, xử lý tối đa 8 items cùng lúc

```
   📋 Total batches: 17
```
- 33 items ÷ 2 items/batch ≈ 17 batches (batch cuối chỉ có 1 item)

---

## Cách hoạt động

```
33 images → Chia thành 17 batches (mỗi batch = 2 images)
           ↓
17 batches → Xử lý song song với 8 workers
           ↓
┌─────────────────────────────────────────┐
│ Worker 1: Batch 1 (2 images)  │
│ Worker 2: Batch 2 (2 images)  │
│ Worker 3: Batch 3 (2 images)  │
│ Worker 4: Batch 4 (2 images)  │
│ Worker 5: Batch 5 (2 images)  │
│ Worker 6: Batch 6 (2 images)  │
│ Worker 7: Batch 7 (2 images)  │
│ Worker 8: Batch 8 (2 images)  │ ← 8 workers xử lý 16 images cùng lúc
└─────────────────────────────────────────┘
           ↓
Batch 9, 10, 11... → Chờ workers rảnh → Tiếp tục xử lý
```

## Timeline

```
Time 0s:   Workers 1-8 bắt đầu xử lý batches 1-8 (16 images)
           ↓
Time ~5s:  Workers 1-4 hoàn thành → Nhận batches 9-12
           ↓
Time ~10s: Workers 5-8 hoàn thành → Nhận batches 13-16
           ↓
Time ~15s: Workers nhận batch 17 (1 image cuối)
           ↓
Time ~20s: Hoàn thành tất cả 33 images
```

## Tóm tắt

- 8 requests OCR được xử lý cùng lúc
- 17 batches (mỗi batch 2 images, batch cuối 1)
- Các batches xử lý tuần tự nhưng các images trong mỗi batch xử lý song song

Ví dụ:
- Time 0-5s: 8 workers xử lý 16 images (8 batches × 2 images)
- Time 5-10s: 8 workers xử lý 16 images tiếp theo (8 batches × 2 images)
- Time 10-15s: 1 worker xử lý 1 image cuối (batch 17)

Tổng thời gian: ~20s thay vì ~165s nếu xử lý tuần tự (33 × 5s/image)ư