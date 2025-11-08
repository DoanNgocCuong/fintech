import os
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

from main_parallel import MODEL, API, process_single_image_ocr
import shutil
from pathlib import Path


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


IMAGE_PATH = "/home/ubuntu/fintech/BaoCaoTaiChinh/OCR/data/out_images/33_pages_test-8.png"
NUM_REQUESTS = 1
WINDOW_S = 5.0  # window to group the first completion wave


def estimate_concurrency_by_first_wave(end_times: List[float]) -> int:
    if not end_times:
        return 0
    first = min(end_times)
    return sum(1 for t in end_times if t <= first + WINDOW_S)


def main() -> None:
    if not os.path.exists(IMAGE_PATH):
        logger.error(f"Image not found: {IMAGE_PATH}")
        return

    # Only test: call process_single_image_ocr concurrently with unique temp copies to avoid write collision
    logger.info("\n===== CONCURRENCY TEST: process_single_image_ocr with unique temp copies =====")
    src = Path(IMAGE_PATH)
    tmp_dir = Path(src.parent) / "tmp_conc"
    try:
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)
        tmp_dir.mkdir(parents=True, exist_ok=True)

        temp_images: List[Path] = []
        for i in range(1, NUM_REQUESTS + 1):
            dst = tmp_dir / f"img_{i}.png"
            shutil.copy2(src, dst)
            temp_images.append(dst)

        def ocr_proc(idx: int, p: Path) -> Dict[str, Any]:
            s = time.time()
            logger.info(f"PROC START #{idx}")
            ok = True
            err = ""
            try:
                _ = process_single_image_ocr(str(p), MODEL, API)
            except Exception as e:
                ok = False
                err = f"{type(e).__name__}: {e}"
            e = time.time()
            logger.info(f"PROC END   #{idx} | ok={ok} | dur={e-s:.2f}s {('| ' + err) if not ok else ''}")
            return {"idx": idx, "ok": ok, "start": s, "end": e, "dur": e - s, "err": err}

        results2: List[Dict[str, Any]] = []
        t2 = time.time()
        with ThreadPoolExecutor(max_workers=NUM_REQUESTS) as ex:
            futures2 = [ex.submit(ocr_proc, i, p) for i, p in enumerate(temp_images, start=1)]
            for fut in as_completed(futures2):
                results2.append(fut.result())
        t3 = time.time()

        results2.sort(key=lambda r: r["end"])
        end_times2 = [r["end"] for r in results2 if r["ok"]]
        approx_conc2 = estimate_concurrency_by_first_wave(end_times2)

        total_ok2 = sum(1 for r in results2 if r["ok"]) if results2 else 0
        total_err2 = len(results2) - total_ok2

        logger.info("\n===== SECOND TEST SUMMARY =====")
        logger.info(f"Total requests: {len(results2)} | OK: {total_ok2} | ERR: {total_err2}")
        logger.info(f"Wall time: {t3 - t2:.2f}s")
        if results2:
            logger.info(f"Fastest: {min(r['dur'] for r in results2):.2f}s | Slowest: {max(r['dur'] for r in results2):.2f}s")
        logger.info(f"Approx parallelism (first-wave within {WINDOW_S:.1f}s): {approx_conc2}")
    finally:
        try:
            if tmp_dir.exists():
                shutil.rmtree(tmp_dir)
        except Exception:
            pass


if __name__ == "__main__":
    main()


