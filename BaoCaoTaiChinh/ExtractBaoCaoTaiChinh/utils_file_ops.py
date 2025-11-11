from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Iterable, Dict


def delete_files(files: Iterable[os.PathLike | str], retries: int = 5, delay_seconds: float = 0.3) -> Dict[str, bool]:
    """
    Safely delete a list of files. Works on Windows with simple retry for transient locks.
    
    Args:
        files: Iterable of file paths (str or Path)
        retries: Number of additional attempts after the first try
        delay_seconds: Delay between retries
    
    Returns:
        Dict[str, bool]: Mapping file path (string) -> True if deleted or non-existent, False if failed to delete
    """
    results: Dict[str, bool] = {}
    for file_item in files:
        file_path = Path(file_item)
        file_key = str(file_path)

        # Consider non-existent as success for idempotency
        if not file_path.exists():
            results[file_key] = True
            continue

        attempt = 0
        deleted = False
        while attempt <= retries and not deleted:
            try:
                file_path.unlink(missing_ok=True)
                deleted = not file_path.exists()
                if deleted:
                    results[file_key] = True
                    break
            except PermissionError:
                # Common on Windows if another handle is open; wait and retry
                pass
            except Exception:
                # Unexpected error; still retry a couple times
                pass

            attempt += 1
            if attempt <= retries:
                time.sleep(delay_seconds)

        if not deleted:
            results[file_key] = False

    return results


