#!/usr/bin/env python3

import os
from typing import Optional

try:
    from PyPDF2 import PdfReader
    print("✓ PyPDF2 imported thành công")
except Exception as e:
    print(f"✗ Lỗi import PyPDF2: {e}")
    PdfReader = None
    exit(1)

def test_pdf_read(pdf_path: str):
    """Test đọc PDF với debug chi tiết"""
    print(f"\n=== DEBUG PDF: {pdf_path} ===")
    
    # Kiểm tra file tồn tại
    if not os.path.exists(pdf_path):
        print(f"✗ File không tồn tại: {pdf_path}")
        return None
        
    # Kiểm tra kích thước file
    try:
        file_size = os.path.getsize(pdf_path)
        print(f"✓ File tồn tại, kích thước: {file_size:,} bytes")
    except Exception as e:
        print(f"✗ Lỗi kiểm tra file: {e}")
        return None
    
    # Kiểm tra quyền đọc
    if not os.access(pdf_path, os.R_OK):
        print(f"✗ Không có quyền đọc file")
        return None
    print(f"✓ Có quyền đọc file")
    
    # Thử đọc với PyPDF2
    try:
        print("Đang thử đọc với PyPDF2...")
        reader = PdfReader(pdf_path)
        page_count = len(reader.pages)
        print(f"✓ Đọc thành công! Số trang: {page_count}")
        
        # Thử đọc metadata
        try:
            metadata = reader.metadata
            if metadata:
                print(f"  - Title: {metadata.get('/Title', 'N/A')}")
                print(f"  - Author: {metadata.get('/Author', 'N/A')}")
                print(f"  - Creator: {metadata.get('/Creator', 'N/A')}")
        except:
            print("  - Không đọc được metadata")
            
        return page_count
        
    except Exception as e:
        print(f"✗ Lỗi đọc PDF với PyPDF2: {type(e).__name__}: {e}")
        
        # Thử với các thư viện khác nếu có
        try:
            import fitz  # PyMuPDF
            print("Thử với PyMuPDF...")
            doc = fitz.open(pdf_path)
            page_count = len(doc)
            doc.close()
            print(f"✓ PyMuPDF đọc thành công: {page_count} trang")
            return page_count
        except ImportError:
            print("PyMuPDF không có sẵn")
        except Exception as e2:
            print(f"✗ PyMuPDF cũng lỗi: {e2}")
            
        return None

if __name__ == "__main__":
    # Test với file PDF của bạn
    pdf_path = "/home/ubuntu/fintech/OCR/data/test/5_pages_test.pdf"
    result = test_pdf_read(pdf_path)
    
    if result:
        print(f"\n🎉 Kết quả cuối cùng: {result} trang")
    else:
        print(f"\n❌ Không thể đọc được PDF")