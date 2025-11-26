"""
Utility script: clean (delete) JSON files in a folder and its subfolders.

SCOPE:
------
- Delete all `.json` files under a given root directory.
- Support recursive and non-recursive modes.
- Support dry-run mode to preview which files would be deleted.

USAGE:
------
    python utils_clean_json_files.py <target_folder> [--no-recursive] [--dry-run]

EXAMPLES:
---------
1) Preview (dry run) all JSON files that would be deleted:
    python utils_clean_json_files.py "D:\\GIT\\Fintech\\fintech\\BaoCaoTaiChinh\\ExtractBaoCaoTaiChinh\\test\\test" --dry-run

2) Delete all JSON files recursively (NO dry run):
    python utils_clean_json_files.py "D:\\path\\to\\folder"

3) Delete only JSON files in the top-level folder (non-recursive):
    python utils_clean_json_files.py "D:\\path\\to\\folder" --no-recursive

DESIGN (SOLID):
---------------
- Single Responsibility:
  - JsonFileCleaner: responsible only for finding and deleting JSON files.
  - main(): responsible for CLI parsing and orchestration.
- Open/Closed:
  - JsonFileCleaner can be extended (for example, to support filtering by pattern)
    without changing existing client code.
- Dependency Inversion:
  - High-level main() depends on the abstraction JsonFileCleaner API,
    not on low-level filesystem details.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class JsonFileCleanerConfig:
    """Configuration for JsonFileCleaner."""

    root: Path
    recursive: bool = True
    dry_run: bool = False


class JsonFileCleaner:
    """
    Service class to find and delete JSON files under a root directory.

    Public API:
        - collect_json_files() -> List[Path]
        - delete_files(files: List[Path]) -> int
    """

    def __init__(self, config: JsonFileCleanerConfig) -> None:
        self._config = config

    def collect_json_files(self) -> List[Path]:
        """
        Collect all `.json` files under the configured root.

        Returns:
            List of file paths.
        """
        root = self._config.root
        if not root.exists():
            raise FileNotFoundError(f"Root path does not exist: {root}")
        if not root.is_dir():
            raise NotADirectoryError(f"Root path is not a directory: {root}")

        if self._config.recursive:
            files = [p for p in root.rglob("*.json") if p.is_file()]
        else:
            files = [p for p in root.glob("*.json") if p.is_file()]

        return sorted(files)

    def delete_files(self, files: List[Path]) -> int:
        """
        Delete the provided list of files.

        If dry_run is True, do not actually delete, only log.

        Returns:
            Number of successfully deleted files (or that would be deleted in dry-run).
        """
        deleted_count = 0
        dry_run = self._config.dry_run

        for f in files:
            try:
                if dry_run:
                    print(f"[DRY-RUN] Would delete: {f}")
                else:
                    f.unlink(missing_ok=True)
                    print(f"Deleted: {f}")
                deleted_count += 1
            except Exception as e:
                # Log but continue with other files
                try:
                    print(f"  ✗ Failed to delete {f}: {e}")
                except UnicodeEncodeError:
                    print("  [ERROR] Failed to delete file (encoding issue in path).")

        return deleted_count


def _parse_args(argv: List[str]) -> JsonFileCleanerConfig:
    """
    Parse CLI arguments into JsonFileCleanerConfig.

    Args:
        argv: Command-line arguments (excluding the script name).

    Returns:
        JsonFileCleanerConfig instance.
    """
    if not argv:
        print("Usage: python utils_clean_json_files.py <target_folder> [--no-recursive] [--dry-run]")
        sys.exit(1)

    target_arg = argv[0]
    extra_args = argv[1:]

    recursive = "--no-recursive" not in extra_args
    dry_run = "--dry-run" in extra_args

    root = Path(target_arg)
    return JsonFileCleanerConfig(root=root, recursive=recursive, dry_run=dry_run)


def main() -> None:
    """CLI entry point."""
    config = _parse_args(sys.argv[1:])
    cleaner = JsonFileCleaner(config)

    print("=" * 80)
    print("JSON FILE CLEANER")
    print("=" * 80)
    print(f"Root folder   : {config.root}")
    print(f"Recursive     : {config.recursive}")
    print(f"Dry run       : {config.dry_run}")
    print("=" * 80)

    try:
        files = cleaner.collect_json_files()
    except (FileNotFoundError, NotADirectoryError) as e:
        print(f"✗ {e}")
        sys.exit(1)

    if not files:
        print("No JSON files found.")
        sys.exit(0)

    print(f"Found {len(files)} JSON file(s).")
    deleted = cleaner.delete_files(files)

    print("=" * 80)
    if config.dry_run:
        print(f"DRY-RUN MODE: {deleted} file(s) would be deleted.")
    else:
        print(f"Deleted {deleted} JSON file(s).")
    print("=" * 80)


if __name__ == "__main__":
    main()


