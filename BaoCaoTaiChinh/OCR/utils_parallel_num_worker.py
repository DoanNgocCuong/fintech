import time
import glob
import os
import logging
import threading
import concurrent.futures
from typing import List, Dict, Callable, Any

logger = logging.getLogger(__name__)

# Window time để group các requests hoàn thành trong cùng một wave (từ file test)
WINDOW_S = 5.0  # window to group the first completion wave

def estimate_concurrency_by_first_wave(end_times: List[float]) -> int:
    """
    Ước tính số lượng concurrent requests dựa trên first wave completion.
    Từ file test: utils_test_ocr_parallel_number_workers_insted_of_locust_test.py
    """
    if not end_times:
        return 0
    first = min(end_times)
    return sum(1 for t in end_times if t <= first + WINDOW_S)

def process_images_parallel(
    list_image_paths: List[str],
    max_workers: int = 8,
    model: str = "",
    api: str = "",
    process_func: Callable = None,
) -> Dict[str, any]:
    """
    Chạy OCR song song trên một list các ảnh.

    Args:
        list_image_paths (List[str]): Danh sách đường dẫn tới các file ảnh để OCR.
        max_workers (int): Số lượng luồng (threads) tối đa chạy song song.
        model (str): Tên model sử dụng cho OCR.
        api (str): Endpoint API để gọi OCR.
        process_func (Callable): Hàm thực thi xử lý OCR cho từng ảnh, nhận đối số (img_path, model, api).

    Returns:
        Dict[str, any]: 
            - results: List các dict gồm {"path": ..., "ok": bool, "start": float, "end": float, "dur": float, "err": str}
            - total_ok: Tổng số ảnh xử lý thành công
            - total_err: Tổng số ảnh bị lỗi
            - total: Tổng số ảnh đầu vào
            - total_dur: Tổng thời gian xử lý (giây)
            - fastest_dur: Thời gian xử lý nhanh nhất (giây)
            - slowest_dur: Thời gian xử lý chậm nhất (giây)
            - approx_conc: Ước tính số lượng concurrent requests (số lượng bắn song song)
    """
    if process_func is None:
        # Import hàm xử lý mặc định nếu chưa cung cấp process_func.
        from main_parallel import process_single_image_ocr
        process_func = process_single_image_ocr

    results = []  # Lưu lại kết quả từng ảnh sau khi xử lý {"path": ..., "ok": ...}
    start_time = time.time()  # Đánh dấu thời điểm bắt đầu xử lý
    
    # Counter để đánh số task ID (thread-safe)
    task_counter = {"count": 0}
    task_counter_lock = threading.Lock()

    # Wrapper function để đo start time ĐÚNG cách (theo pattern từ file test)
    def ocr_wrapper(img_path: str) -> Dict[str, Any]:
        """
        Wrapper function để đo start time TRƯỚC khi gọi process_func.
        Theo pattern từ utils_test_ocr_parallel_number_workers_insted_of_locust_test.py
        """
        # Lấy task ID (thread-safe)
        with task_counter_lock:
            task_counter["count"] += 1
            task_id = task_counter["count"]
        
        file_basename = os.path.basename(img_path)
        thread_id = threading.get_ident()  # Thread ID (không phải PID vì dùng threads)
        task_start = time.time()  # Đo thời gian bắt đầu task TRƯỚC khi gọi process_func
        
        # Log với task ID và thread ID để dễ track
        logger.info(f"🚀 OCR START #{task_id}: {file_basename} | thread_id={thread_id}")
        
        ok = False
        err = ""
        try:
            # Gọi process_func và đo thời gian chính xác
            res = process_func(img_path, model, api)
            ok = bool(res and res.strip())
        except Exception as e:
            ok = False
            err = f"{type(e).__name__}: {e}"
        
        task_end = time.time()  # Đo thời gian kết thúc task
        task_dur = task_end - task_start  # Tính duration từ lúc start đến lúc OCR xong
        
        # Log thời gian duration cho từng task khi hoàn thiện (theo pattern từ file test)
        status_msg = f"✅ OCR COMPLETED #{task_id}: {file_basename} | ok={ok} | dur={task_dur:.2f}s | thread_id={thread_id}"
        if not ok and err:
            status_msg += f" | {err}"
        logger.info(status_msg)
        
        return {
            "path": img_path,
            "task_id": task_id,
            "thread_id": thread_id,
            "ok": ok,
            "start": task_start,
            "end": task_end,
            "dur": task_dur,
            "err": err
        }

    # Sử dụng ThreadPoolExecutor để thực thi đa luồng
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Gửi từng tác vụ xử lý ảnh lên thread pool, nhận lại future object cho từng ảnh
        # Sử dụng wrapper function để đo start time đúng cách
        futures = {
            executor.submit(ocr_wrapper, img_path): img_path 
            for img_path in list_image_paths
        }

        # Duyệt trên các tương lai hoàn thành (có thể không đúng thứ tự)
        for future in concurrent.futures.as_completed(futures):
            # Lấy kết quả từ wrapper function (đã có đầy đủ start, end, dur, err)
            result = future.result()
            results.append(result)

    # Tổng số ảnh thành công (ok=True)
    total_ok = sum(1 for r in results if r["ok"])
    # Tổng số ảnh không thành công
    total_err = len(results) - total_ok
    
    # Tính fastest và slowest duration (theo pattern từ file test)
    durations = [r["dur"] for r in results if r["ok"]]
    fastest_dur = min(durations) if durations else 0
    slowest_dur = max(durations) if durations else 0
    
    # Tính approximate parallelism/concurrency (số lượng bắn song song)
    # Sắp xếp results theo end time (theo pattern từ file test)
    results_sorted = sorted(results, key=lambda r: r["end"])
    end_times = [r["end"] for r in results_sorted if r["ok"]]
    approx_conc = estimate_concurrency_by_first_wave(end_times)
    
    total_dur = time.time() - start_time

    # Trả về dict chứa kết quả chi tiết cũng như tổng hợp
    return {
        "results": results,  # Kết quả cho từng ảnh (có start, end, dur, err)
        "total_ok": total_ok,  # Số ảnh OK
        "total_err": total_err,  # Số ảnh lỗi
        "total": len(list_image_paths),  # Tổng số ảnh
        "total_dur": total_dur,  # Tổng thời gian xử lý (giây)
        "fastest_dur": fastest_dur,  # Thời gian xử lý nhanh nhất (giây)
        "slowest_dur": slowest_dur,  # Thời gian xử lý chậm nhất (giây)
        "approx_conc": approx_conc,  # Ước tính số lượng concurrent requests (số lượng bắn song song)
    }
    
def main():
    image_paths = glob.glob("/home/ubuntu/fintech/BaoCaoTaiChinh/OCR/data/out_images/*.png")
    result = process_images_parallel(
        list_image_paths=image_paths,
        max_workers=8,
        model="rednote-hilab/dots.ocr",
        api="http://103.253.20.30:30010/v1"
    )
    print(result)
    
if __name__ == "__main__":
    main()