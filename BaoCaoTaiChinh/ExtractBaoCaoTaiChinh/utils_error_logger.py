"""
Utility functions for error logging across the pipeline.

This module provides logging utilities for tracking errors in:
1. Markdown → XLSX conversion
2. XLSX → JSON conversion  
3. JSON → DB upload

Workflow:
---------
- 1 markdown file → 1 XLSX file → 1 JSON file → 1 DB record
- If any step fails, log to appropriate error log file
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class ErrorLogEntry:
    """Single error log entry."""
    timestamp: str
    file_path: str
    step: str  # 'markdown_to_xlsx', 'xlsx_to_json', 'json_to_db'
    error_type: str
    error_message: str
    details: Optional[Dict[str, Any]] = None


def log_error(
    log_file: str,
    file_path: str,
    step: str,
    error: Exception,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an error to a log file.
    
    Args:
        log_file: Path to log file
        file_path: Path to the file that caused the error
        step: Step in pipeline ('markdown_to_xlsx', 'xlsx_to_json', 'json_to_db')
        error: Exception object
        details: Optional additional details
    """
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    entry = ErrorLogEntry(
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        file_path=str(file_path),
        step=step,
        error_type=type(error).__name__,
        error_message=str(error),
        details=details or {}
    )
    
    # Read existing logs
    existing_entries: List[Dict[str, Any]] = []
    if log_path.exists():
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                existing_entries = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing_entries = []
    
    # Append new entry
    existing_entries.append(asdict(entry))
    
    # Write back
    try:
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(existing_entries, f, ensure_ascii=False, indent=2)
    except Exception as e:
        # If we can't write to log file, print error (fallback)
        try:
            print(f"[ERROR] Cannot write to log file {log_file}: {e}")
        except:
            pass


def log_simple_error(
    log_file: str,
    file_path: str,
    step: str,
    reason: str
) -> None:
    """
    Log a simple error (without Exception object).
    
    Args:
        log_file: Path to log file
        file_path: Path to the file that caused the error
        step: Step in pipeline
        reason: Error reason/description
    """
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Read existing logs
    existing_lines: List[str] = []
    if log_path.exists():
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                existing_lines = f.readlines()
        except IOError:
            existing_lines = []
    
    # Append new entry (text format for simplicity)
    with open(log_path, 'a', encoding='utf-8') as f:
        if not existing_lines:  # First entry - write header
            f.write("=" * 80 + "\n")
            f.write("ERROR LOG\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated at: {timestamp}\n")
            f.write("=" * 80 + "\n\n")
        
        f.write(f"[{timestamp}] {step}\n")
        f.write(f"  File: {file_path}\n")
        f.write(f"  Reason: {reason}\n\n")


# Predefined log file paths - separated by report type
# Markdown → XLSX logs
MARKDOWN_TO_XLSX_LOG_CanDoiKeToan = "error_log_markdown_to_xlsx_CanDoiKeToan.txt"
MARKDOWN_TO_XLSX_LOG_KetQuaHoatDongKinhDoanh = "error_log_markdown_to_xlsx_KetQuaHoatDongKinhDoanh.txt"
MARKDOWN_TO_XLSX_LOG_LuuChuyenTienTe = "error_log_markdown_to_xlsx_LuuChuyenTienTe.txt"

# XLSX → JSON logs
XLSX_TO_JSON_LOG_CanDoiKeToan = "error_log_xlsx_to_json_CanDoiKeToan.txt"
XLSX_TO_JSON_LOG_KetQuaHoatDongKinhDoanh = "error_log_xlsx_to_json_KetQuaHoatDongKinhDoanh.txt"
XLSX_TO_JSON_LOG_LuuChuyenTienTe = "error_log_xlsx_to_json_LuuChuyenTienTe.txt"

# JSON → DB logs (already separated in individual scripts)
JSON_TO_DB_LOG = "error_log_json_to_db.txt"

# Backward compatibility (deprecated - use specific logs above)
MARKDOWN_TO_XLSX_LOG = "error_log_markdown_to_xlsx.txt"
XLSX_TO_JSON_LOG = "error_log_xlsx_to_json.txt"

