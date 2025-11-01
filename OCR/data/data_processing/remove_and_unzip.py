import os
import sys
import logging
import shutil
import zipfile
from pathlib import Path

# Import rarfile cho giải nén RAR
try:
    import rarfile
    RARFILE_AVAILABLE = True
    # Thiết lập đường dẫn UnRAR tool (WinRAR thường có sẵn)
    unrar_paths = [
        r"C:\Program Files\WinRAR\UnRAR.exe",
        r"C:\Program Files (x86)\WinRAR\UnRAR.exe",
    ]
    for unrar_path in unrar_paths:
        if os.path.exists(unrar_path):
            rarfile.UNRAR_TOOL = unrar_path
            break
except ImportError:
    RARFILE_AVAILABLE = False
    print("⚠️ Warning: rarfile not installed. Install with: pip install rarfile")

# ===== CẤU HÌNH =====
BASE_FOLDER = r"E:\Vietstock_Downloads_CLI\HOSE"
DELETE_ARCHIVE_AFTER_EXTRACT = True
DRY_RUN = False  # True = chỉ xem, False = thực thi

# Danh sách thư mục cần xóa
FOLDERS_TO_DELETE = [
    "Bao_cao_quan_tri",
    "Nghi_quyet_HDQT"
]

# ===== LOGGING =====
log_file = 'extract_process_v2.log'

# Create formatters - shorter format for console to prevent line wrapping
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', 
                                     datefmt='%H:%M:%S')
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# File handler with full format
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(file_formatter)

# Console handler with shorter format to prevent PowerShell line wrapping
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(console_formatter)

# Configure root logger
logging.basicConfig(
    level=logging.DEBUG,
    handlers=[file_handler, console_handler]
)

# ===== THỐNG KÊ =====
stats = {
    'zip_extracted': 0,
    'rar_extracted': 0,
    'zip_deleted': 0,
    'rar_deleted': 0,
    'folders_deleted': 0,
    'failed_archives': [],
    'failed_folders': []
}

def extract_zip(zip_path: Path, extract_to: Path) -> bool:
    """Giải nén file ZIP vào thư mục đích bằng zipfile (built-in)"""
    try:
        os.makedirs(extract_to, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        logging.info(f"✅ ZIP extracted: {zip_path.name} → {extract_to}")
        return True
    except Exception as e:
        logging.error(f"❌ ZIP extraction failed: {zip_path.name} - {e}")
        return False


def extract_rar(rar_path: Path, extract_to: Path) -> bool:
    """Giải nén file RAR vào thư mục đích bằng rarfile"""
    try:
        if not RARFILE_AVAILABLE:
            raise ImportError("rarfile not installed")
        
        os.makedirs(extract_to, exist_ok=True)
        with rarfile.RarFile(rar_path) as rf:
            rf.extractall(path=extract_to)
        logging.info(f"✅ RAR extracted: {rar_path.name} → {extract_to}")
        return True
    except Exception as e:
        logging.error(f"❌ RAR extraction failed: {rar_path.name} - {e}")
        return False


def extract_archive(archive_path: Path, extract_to: Path) -> bool:
    """Giải nén file nén (ZIP hoặc RAR) vào thư mục đích"""
    file_ext = archive_path.suffix.lower()
    
    if file_ext == '.zip':
        return extract_zip(archive_path, extract_to)
    elif file_ext == '.rar':
        return extract_rar(archive_path, extract_to)
    else:
        logging.error(f"❌ Unsupported archive format: {archive_path.name}")
        return False


def remove_file(file_path: Path) -> bool:
    """Xóa file và log kết quả"""
    try:
        file_path.unlink()
        msg = f"🗑️ Deleted original: {file_path.name}"
        logging.info(msg)
        if sys.stdout.isatty():
            sys.stdout.flush()
        return True
    except Exception as e:
        logging.error(f"❌ Failed to delete {file_path.name}: {e}")
        return False

def process_archive(archive_path, processed_dirs=None) -> bool:
    """Xử lý file nén: validate, extract, xóa file gốc và tiếp tục xử lý thư mục giải nén
    
    Args:
        archive_path: Path đến file nén (Path hoặc str)
        processed_dirs: Set các thư mục đã xử lý (để tránh loop vô hạn)
    
    Returns:
        True nếu thành công, False nếu thất bại
    """
    archive_path = Path(archive_path)
    file_ext = archive_path.suffix.lower()
    
    # Tạo tên thư mục output với suffix _zip hoặc _rar
    if file_ext in ['.zip', '.rar']:
        suffix = file_ext[1:]  # Bỏ dấu chấm: .zip -> zip, .rar -> rar
        extract_to = archive_path.parent / f"{archive_path.stem}_{suffix}"
    else:
        extract_to = archive_path.parent / archive_path.stem
    
    logging.info(f"📦 Processing: {archive_path.name}")
    
    # Validate file
    if not archive_path.exists():
        logging.error(f"❌ File not found: {archive_path}")
        stats['failed_archives'].append(str(archive_path))
        return False
    
    if archive_path.stat().st_size == 0:
        logging.error(f"❌ Empty file: {archive_path}")
        stats['failed_archives'].append(str(archive_path))
        return False
    
    if DRY_RUN:
        logging.info(f"[DRY RUN] Would extract to: {extract_to}")
        return True
    
    # Extract archive (supports both ZIP and RAR)
    success = False
    
    if file_ext in ['.zip', '.rar']:
        success = extract_archive(archive_path, extract_to)
        if success:
            if file_ext == '.zip':
                stats['zip_extracted'] += 1
            else:
                stats['rar_extracted'] += 1
            
            # Delete original file if extraction successful
            if DELETE_ARCHIVE_AFTER_EXTRACT:
                if remove_file(archive_path):
                    if file_ext == '.zip':
                        stats['zip_deleted'] += 1
                    else:
                        stats['rar_deleted'] += 1
            
            # Tiếp tục xử lý các file ZIP/RAR trong thư mục vừa giải nén
            if extract_to.exists() and extract_to.is_dir():
                process_directory(extract_to, processed_dirs)
    
    if not success:
        stats['failed_archives'].append(str(archive_path))
    
    return success


def process_directory(directory: Path, processed_dirs=None):
    """Xử lý đệ quy: tìm và xử lý tất cả file ZIP/RAR trong thư mục và các thư mục con
    
    Args:
        directory: Path đến thư mục cần xử lý
        processed_dirs: Set các thư mục đã xử lý (để tránh loop vô hạn)
    """
    if processed_dirs is None:
        processed_dirs = set()
    
    # Tránh xử lý lại thư mục đã xử lý
    dir_key = str(directory.resolve())
    if dir_key in processed_dirs:
        return
    processed_dirs.add(dir_key)
    
    try:
        # Xử lý file ZIP/RAR trước (top-down)
        items = sorted(directory.iterdir())
        for item in items:
            if item.is_file() and item.suffix.lower() in ['.zip', '.rar']:
                process_archive(item, processed_dirs)
        
        # Sau đó xử lý các thư mục con
        for item in items:
            if item.is_dir():
                process_directory(item, processed_dirs)
                
    except PermissionError as e:
        logging.warning(f"⚠️ Permission denied for directory: {directory} - {e}")
    except Exception as e:
        logging.error(f"❌ Error processing directory {directory}: {e}")

def delete_unnecessary_folders(base_path):
    """Xóa các thư mục không cần thiết"""
    base_path = Path(base_path)
    
    for root, dirs, files in os.walk(base_path, topdown=False):
        for dir_name in dirs:
            if dir_name in FOLDERS_TO_DELETE:
                folder_path = Path(root) / dir_name
                logging.info(f"📁 Found folder to delete: {folder_path}")
                
                if DRY_RUN:
                    logging.info(f"[DRY RUN] Would delete: {folder_path}")
                    continue
                
                try:
                    shutil.rmtree(folder_path)
                    stats['folders_deleted'] += 1
                    logging.info(f"🗑️ Deleted folder: {folder_path}")
                except Exception as e:
                    logging.error(f"❌ Failed to delete {folder_path}: {e}")
                    stats['failed_folders'].append(str(folder_path))

def main():
    logging.info("=" * 80)
    logging.info("🚀 STARTING ARCHIVE EXTRACTION & CLEANUP PROCESS v2")
    logging.info("=" * 80)
    
    # Kiểm tra môi trường
    logging.info(f"\n📋 ENVIRONMENT CHECK:")
    logging.info(f"✓ Base folder: {BASE_FOLDER}")
    logging.info(f"✓ rarfile available: {RARFILE_AVAILABLE}")
    if RARFILE_AVAILABLE:
        logging.info(f"✓ UnRAR tool: {rarfile.UNRAR_TOOL}")
    logging.info(f"✓ DRY_RUN mode: {'ENABLED' if DRY_RUN else 'DISABLED'}")
    logging.info(f"✓ DELETE_ARCHIVE_AFTER_EXTRACT: {DELETE_ARCHIVE_AFTER_EXTRACT}")
    
    if not RARFILE_AVAILABLE:
        logging.warning("⚠️ rarfile not installed. RAR extraction will fail.")
        logging.info("Install with: pip install rarfile")
        logging.info("Note: Requires WinRAR or UnRAR executable on Windows")
    
    base_path = Path(BASE_FOLDER)
    if not base_path.exists():
        logging.error(f"❌ Base folder does not exist: {BASE_FOLDER}")
        return
    
    # Xác nhận từ người dùng
    if not DRY_RUN:
        print("\n⚠️  WARNING: This will modify your files!")
        print(f"   - Extract all ZIP/RAR files in: {BASE_FOLDER}")
        if DELETE_ARCHIVE_AFTER_EXTRACT:
            print(f"   - Delete original archives after extraction")
        print(f"   - Delete folders: {', '.join(FOLDERS_TO_DELETE)}")
        
        response = input("\n❓ Continue? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            logging.info("❌ Operation cancelled by user")
            return
    
    logging.info("\n" + "=" * 80)
    logging.info("📦 PROCESSING ARCHIVES")
    logging.info("=" * 80 + "\n")
    
    # Xử lý đệ quy: bắt đầu từ thư mục gốc, đi từ cha xuống con
    # Cứ gặp ZIP/RAR thì giải nén, sau đó tiếp tục xử lý thư mục vừa giải nén
    process_directory(base_path)
    
    logging.info("\n" + "=" * 80)
    logging.info("📁 DELETING UNNECESSARY FOLDERS")
    logging.info("=" * 80 + "\n")
    
    delete_unnecessary_folders(base_path)
    
    # In tổng kết
    logging.info("\n" + "=" * 80)
    logging.info("📊 SUMMARY REPORT")
    logging.info("=" * 80)
    logging.info(f"\n✅ ZIP files extracted: {stats['zip_extracted']}")
    logging.info(f"✅ RAR files extracted: {stats['rar_extracted']}")
    logging.info(f"🗑️  ZIP files deleted: {stats['zip_deleted']}")
    logging.info(f"🗑️  RAR files deleted: {stats['rar_deleted']}")
    logging.info(f"🗑️  Folders deleted: {stats['folders_deleted']}")
    logging.info(f"❌ Failed archives: {len(stats['failed_archives'])}")
    logging.info(f"❌ Failed folder deletions: {len(stats['failed_folders'])}")
    
    # Ghi danh sách file thất bại
    if stats['failed_archives']:
        failed_file = 'failed_archives_v2.txt'
        with open(failed_file, 'w', encoding='utf-8') as f:
            for archive in stats['failed_archives']:
                f.write(f"{archive}\n")
        logging.info(f"\n📝 Failed archives list saved to: {failed_file}")
    
    logging.info("\n✅ PROCESS COMPLETED")
    logging.info("=" * 80 + "\n")

if __name__ == "__main__":
    main()
