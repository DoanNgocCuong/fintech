#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Parallel Processing Utils với Adaptive Batch Size và Max Workers
================================================================

Tính năng:
- Adaptive batch sizing dựa trên độ phức tạp của dữ liệu
- Smart worker management với performance monitoring
- Thread-safe result collection
- Progress tracking và ETA calculation
- Error handling và retry mechanisms
- Memory usage optimization
- GPU monitoring integration

"""

import threading
import time
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import List, Dict, Any, Callable, Optional, Tuple
import psutil
import math
import logging

logger = logging.getLogger(__name__)


class ParallelBatchProcessor:
    """
    Advanced parallel batch processor với adaptive optimization
    Cho phép xử lý items theo batches để tối ưu throughput
    """

    def __init__(self,
                 max_workers: Optional[int] = None,
                 batch_size: Optional[int] = None,
                 memory_limit_mb: int = 2048,
                 enable_adaptive: bool = True,
                 timeout_seconds: int = 300,
                 enable_gpu_monitoring: bool = False):
        """
        Initialize parallel batch processor

        Args:
            max_workers: Maximum number of worker threads (None = auto-detect)
            batch_size: Items per batch (None = auto-calculate)
            memory_limit_mb: Memory limit in MB
            enable_adaptive: Enable adaptive optimization
            timeout_seconds: Timeout per batch
            enable_gpu_monitoring: Enable GPU usage monitoring
        """
        self.max_workers = max_workers or self._auto_detect_workers()
        self.batch_size = batch_size
        self.memory_limit_mb = memory_limit_mb
        self.enable_adaptive = enable_adaptive
        self.timeout_seconds = timeout_seconds
        self.enable_gpu_monitoring = enable_gpu_monitoring

        # Performance tracking
        self.start_time = None
        self.completed_items = 0
        self.total_items = 0
        self.error_count = 0
        self.retry_count = 0

        # Thread safety
        self.lock = threading.Lock()
        self.results = {}  # Dictionary để giữ thứ tự

        # Memory monitoring
        self.process = psutil.Process()

        # GPU monitoring
        self.gpu_monitor_thread = None
        self.gpu_stats = {
            'utilization': 0,
            'memory_used': 0,
            'memory_total': 0,
            'temperature': 0
        }

    def _auto_detect_workers(self) -> int:
        """Auto-detect optimal number of workers based on system"""
        cpu_count = psutil.cpu_count(logical=True)
        memory_gb = psutil.virtual_memory().total / (1024**3)

        # Conservative approach: don't overwhelm the system
        # For I/O bound tasks (API calls), can use more workers
        if memory_gb < 4:
            return min(5, cpu_count)
        elif memory_gb < 8:
            return min(8, cpu_count)
        else:
            return min(15, cpu_count * 2)  # I/O bound can use more

    def _calculate_optimal_batch_size(self, total_items: int, avg_time_per_item: float = None) -> int:
        """Calculate optimal batch size based on data characteristics"""
        if self.batch_size:
            return self.batch_size

        if self.enable_adaptive:
            # Estimate based on available memory
            available_memory_mb = psutil.virtual_memory().available / (1024**2)
            estimated_memory_per_item = 50  # MB per item (conservative)

            memory_based_batch = max(1, int(available_memory_mb / estimated_memory_per_item))

            # Time-based optimization
            if avg_time_per_item:
                # Aim for batches that take 30-60 seconds to process
                target_batch_time = 45  # seconds
                time_based_batch = max(1, int(target_batch_time / avg_time_per_item))
            else:
                time_based_batch = 10

            # Worker-based optimization - batch should be multiple of workers
            worker_based_batch = max(1, total_items // (self.max_workers * 2))

            # Take the minimum to be conservative
            optimal_batch = min(memory_based_batch, time_based_batch, worker_based_batch)

            # Ensure batch size is reasonable (between 1 and 50)
            return max(1, min(optimal_batch, 50))

        return 10  # Default fallback

    def _create_batches(self, items: List[Any], batch_size: int) -> List[Tuple[int, List[Any]]]:
        """
        Create batches from items list với index để giữ thứ tự
        Returns: List of (batch_index, batch_items)
        """
        batches = []
        for i in range(0, len(items), batch_size):
            batch_items = items[i:i + batch_size]
            batch_index = i // batch_size
            batches.append((batch_index, batch_items))
        return batches

    def _monitor_memory(self) -> float:
        """Monitor current memory usage"""
        memory_info = self.process.memory_info()
        memory_mb = memory_info.rss / (1024**2)
        return memory_mb

    def _should_pause_for_memory(self) -> bool:
        """Check if we should pause for memory management"""
        current_memory = self._monitor_memory()
        return current_memory > self.memory_limit_mb

    def _get_gpu_stats(self) -> Dict[str, float]:
        """Get GPU statistics using nvidia-smi"""
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu',
                 '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                stats = [float(x.strip()) for x in result.stdout.strip().split(', ')]
                return {
                    'utilization': stats[0],
                    'memory_used': stats[1],
                    'memory_total': stats[2],
                    'temperature': stats[3]
                }
        except Exception as e:
            logger.debug(f"GPU monitoring error: {e}")
        return self.gpu_stats  # Return cached stats if error

    def _start_gpu_monitoring(self):
        """Start GPU monitoring in background thread"""
        if not self.enable_gpu_monitoring:
            return

        def monitor_loop():
            while True:
                try:
                    self.gpu_stats = self._get_gpu_stats()
                    time.sleep(2)  # Update every 2 seconds
                except Exception:
                    break

        self.gpu_monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.gpu_monitor_thread.start()

    def process_parallel(self,
                        items: List[Any],
                        process_func: Callable,
                        progress_callback: Optional[Callable] = None,
                        **kwargs) -> List[Any]:
        """
        Process items in parallel với batch processing và adaptive optimization

        Args:
            items: List of items to process
            process_func: Function to process each item (not batch!)
                        Signature: process_func(item, **kwargs) -> result
            progress_callback: Optional callback for progress updates
            **kwargs: Additional arguments for process_func

        Returns:
            List of results (ordered)
        """
        self.total_items = len(items)
        self.completed_items = 0
        self.start_time = datetime.now()
        self.results = {}
        self.error_count = 0
        self.retry_count = 0

        if not items:
            return []

        # Start GPU monitoring if enabled
        if self.enable_gpu_monitoring:
            self._start_gpu_monitoring()

        # Calculate optimal batch size
        batch_size = self._calculate_optimal_batch_size(len(items))
        batches = self._create_batches(items, batch_size)

        logger.info(f"🚀 Parallel Batch Processing Setup:")
        logger.info(f"   📊 Total items: {self.total_items}")
        logger.info(f"   📦 Batch size: {batch_size} items/batch")
        logger.info(f"   🧵 Max workers: {self.max_workers} (Processing {self.max_workers} items simultaneously)")
        logger.info(f"   📋 Total batches: {len(batches)}")
        logger.info(f"   💾 Memory limit: {self.memory_limit_mb}MB")
        logger.info(f"   🔧 Adaptive mode: {'✅' if self.enable_adaptive else '❌'}")
        if self.enable_gpu_monitoring:
            logger.info(f"   🎮 GPU monitoring: ✅")
        logger.info(f"   ⚡ Parallel capacity: Up to {self.max_workers} concurrent requests")

        # Process batches in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all batches
            process_kwargs = {k: v for k, v in kwargs.items() if k != 'timeout_seconds'}
            future_to_batch = {
                executor.submit(self._process_batch_with_retry, batch_index, batch_items, process_func, **process_kwargs): batch_index
                for batch_index, batch_items in batches
            }

            # Process completed batches
            for future in as_completed(future_to_batch):
                batch_index = future_to_batch[future]
                try:
                    batch_result = future.result(timeout=self.timeout_seconds)
                    with self.lock:
                        # Store results with original item indices
                        for item_index, result in batch_result:
                            self.results[item_index] = result
                            self.completed_items += 1

                    # Progress update
                    if progress_callback:
                        progress_callback(self.completed_items, self.total_items)

                    # Memory management
                    if self._should_pause_for_memory():
                        logger.warning(f"⚠️  High memory usage ({self._monitor_memory():.1f}MB), pausing...")
                        time.sleep(1)

                    # Performance monitoring
                    self._log_progress()

                except TimeoutError:
                    self.error_count += batch_size  # Approximate
                    logger.error(f"⏰ Batch {batch_index} timeout after {self.timeout_seconds}s, skipping...")
                    continue
                except Exception as e:
                    self.error_count += batch_size  # Approximate
                    logger.error(f"❌ Batch {batch_index} processing error: {e}")
                    continue

        # Final summary
        self._log_final_summary()

        # Merge results theo đúng thứ tự
        # FIX: GIỮ TẤT CẢ items kể cả None để không mất thứ tự
        # Dùng .get(i, None) để đảm bảo tất cả indices từ 0 đến total_items-1 đều có
        ordered_results = [self.results.get(i, None) for i in range(self.total_items)]
        return ordered_results

    def _process_batch_with_retry(self,
                                 batch_index: int,
                                 batch_items: List[Any],
                                 process_func: Callable,
                                 max_retries: int = 2,
                                 **kwargs) -> List[Tuple[int, Any]]:
        """
        Process a batch with retry mechanism
        Returns: List of (item_index, result) tuples
        """
        batch_results = []
        batch_size_actual = self.batch_size or 10
        start_index = batch_index * batch_size_actual
        for attempt in range(max_retries + 1):
            try:
                # Process all items in batch
                for item_index, item in enumerate(batch_items):
                    actual_index = start_index + item_index
                    try:
                        result = process_func(item, **kwargs)
                        batch_results.append((actual_index, result))
                    except Exception as e:
                        logger.error(f"❌ Error processing item {actual_index} in batch {batch_index}: {e}")
                        batch_results.append((actual_index, None))
                        self.error_count += 1

                return batch_results

            except Exception as e:
                if attempt < max_retries:
                    self.retry_count += 1
                    logger.warning(f"🔄 Retry {attempt + 1}/{max_retries} for batch {batch_index} due to: {e}")
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"💥 Batch {batch_index} failed after {max_retries} retries: {e}")
                    # Return None results for all items in failed batch
                    for item_index in range(len(batch_items)):
                        actual_index = start_index + item_index
                        batch_results.append((actual_index, None))
                    return batch_results

    def _log_progress(self):
        """Log current progress with ETA"""
        if self.completed_items == 0:
            return

        elapsed_time = (datetime.now() - self.start_time).total_seconds()
        avg_time_per_item = elapsed_time / self.completed_items
        remaining_items = self.total_items - self.completed_items
        estimated_remaining_time = avg_time_per_item * remaining_items

        progress_percent = (self.completed_items / self.total_items) * 100
        eta = datetime.now() + timedelta(seconds=estimated_remaining_time)

        memory_usage = self._monitor_memory()

        gpu_info = ""
        if self.enable_gpu_monitoring:
            gpu_info = f" | 🎮 GPU: {self.gpu_stats['utilization']:.0f}% ({self.gpu_stats['memory_used']:.0f}/{self.gpu_stats['memory_total']:.0f}MB)"

        logger.info(f"📊 Progress: {self.completed_items}/{self.total_items} ({progress_percent:.1f}%)")
        logger.info(f"   ⏱️  Elapsed: {elapsed_time/60:.1f}min | ETA: {eta.strftime('%H:%M:%S')}")
        logger.info(f"   🚀 Speed: {avg_time_per_item:.1f}s/item | 💾 Memory: {memory_usage:.1f}MB{gpu_info}")
        logger.info(f"   ❌ Errors: {self.error_count} | 🔄 Retries: {self.retry_count}")

    def _log_final_summary(self):
        """Log final processing summary"""
        total_time = (datetime.now() - self.start_time).total_seconds()
        success_rate = ((self.total_items - self.error_count) / self.total_items) * 100 if self.total_items > 0 else 0

        logger.info(f"\n🎉 Parallel Batch Processing Complete!")
        logger.info(f"   ⏱️  Total time: {total_time/60:.1f} minutes")
        logger.info(f"   📊 Success rate: {success_rate:.1f}%")
        logger.info(f"   ❌ Errors: {self.error_count}")
        logger.info(f"   🔄 Retries: {self.retry_count}")
        logger.info(f"   💾 Peak memory: {self._monitor_memory():.1f}MB")

        if self.total_items > 0 and total_time > 0:
            throughput = self.total_items / total_time
            logger.info(f"   🚀 Throughput: {throughput:.2f} items/second")

        if self.enable_gpu_monitoring:
            logger.info(f"   🎮 GPU: {self.gpu_stats['utilization']:.0f}% | Temp: {self.gpu_stats['temperature']:.0f}°C")


# ============================================================================
# Convenience functions for OCR use case
# ============================================================================

def process_images_parallel_optimized(
    image_paths: List[str],
    process_func: Callable,
    max_workers: Optional[int] = None,
    batch_size: Optional[int] = None,
    enable_gpu_monitoring: bool = True,
    **kwargs
) -> List[Any]:
    """
    Convenience function để xử lý images với parallel batch processing

    Args:
        image_paths: List of image file paths
        process_func: Function to process each image
                     Signature: process_func(image_path, **kwargs) -> result
        max_workers: Max worker threads (None = auto-detect)
        batch_size: Images per batch (None = auto-calculate)
        enable_gpu_monitoring: Enable GPU monitoring
        **kwargs: Additional arguments for process_func

    Returns:
        List of results (ordered by image_paths order)
    """
    processor = ParallelBatchProcessor(
        max_workers=max_workers,
        batch_size=batch_size,
        enable_adaptive=True,
        enable_gpu_monitoring=enable_gpu_monitoring
    )

    def progress_callback(completed, total):
        if completed % 5 == 0 or completed == total:  # Update every 5 items
            progress_percent = (completed / total) * 100
            logger.info(f"🔄 Processed {completed}/{total} images ({progress_percent:.1f}%)...")

    results = processor.process_parallel(
        items=image_paths,
        process_func=process_func,
        progress_callback=progress_callback,
        **kwargs
    )

    return results


if __name__ == "__main__":
    # Demo usage
    import logging
    logging.basicConfig(level=logging.INFO)

    def demo_process_func(item, **kwargs):
        """Demo processing function"""
        time.sleep(0.1)  # Simulate work
        return f"Processed: {item}"

    # Test data
    test_items = list(range(100))

    print("🧪 Testing Parallel Batch Processor...")
    processor = ParallelBatchProcessor(max_workers=4, batch_size=10, enable_gpu_monitoring=True)
    results = processor.process_parallel(test_items, demo_process_func)

    print(f"✅ Demo completed with {len(results)} results")

