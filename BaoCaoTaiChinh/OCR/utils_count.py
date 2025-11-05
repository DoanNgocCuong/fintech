import re
from typing import Optional

# Hỗ trợ cả PyPDF2 version cũ và mới
PdfReader = None
PdfFileReader = None

try:
    # Thử import PyPDF2 version mới (>= 2.0)
    from PyPDF2 import PdfReader
except ImportError:
    try:
        # Fallback: PyPDF2 version cũ (< 2.0) dùng PdfFileReader
        from PyPDF2 import PdfFileReader
    except ImportError:
        PdfReader = None
        PdfFileReader = None

"""
Tiện ích đếm số trang

- count_pdf_pages(pdf_path): Đếm số trang của một file PDF (ưu tiên PyPDF2, fallback PyMuPDF/pdf2image).
- count_markdown_pages(md_path): Đếm số trang trong file markdown được ghép theo format:
  
  Trang 1

  <nội dung trang 1>

  ---

  Trang 2

  <nội dung trang 2>

Ghi chú:
- count_markdown_pages ưu tiên đếm theo tiêu đề 'Trang N' (dòng riêng).
- Nếu tiêu đề không có, fallback tách theo separator '---' (bỏ các đoạn rỗng).
"""


def count_pdf_pages(pdf_path: str) -> Optional[int]:
    """Đếm số trang của PDF.

    Args:
        pdf_path: Đường dẫn đến file PDF.

    Returns:
        Số trang (int) nếu đọc được, None nếu lỗi hoặc thiếu thư viện.

    Yêu cầu:
        - Ưu tiên dùng PyPDF2 (PdfReader). Nếu không cài, fallback PyMuPDF hoặc pdf2image.
    """
    # Method 1: PyPDF2 (version mới hoặc cũ)
    if PdfReader is not None:
        try:
            reader = PdfReader(pdf_path)
            return len(reader.pages)
        except Exception:
            pass
    elif PdfFileReader is not None:
        try:
            reader = PdfFileReader(open(pdf_path, 'rb'))
            page_count = reader.getNumPages()
            reader.stream.close()
            return page_count
        except Exception:
            pass
    
    # Method 2: PyMuPDF (fitz)
    try:
        import fitz
        doc = fitz.open(pdf_path)
        page_count = len(doc)
        doc.close()
        return page_count
    except ImportError:
        pass
    except Exception:
        pass
    
    # Method 3: pdf2image (convert và đếm)
    try:
        from pdf2image import convert_from_path
        images = convert_from_path(pdf_path, first_page=1, last_page=1)
        if images:
            # Nếu có thể convert, thử convert tất cả để đếm
            # Nhưng cách này chậm, nên chỉ dùng khi không có method khác
            # Thực tế, nếu đã có pdf2image thì nên dùng PyMuPDF hoặc cài PyPDF2
            pass
    except ImportError:
        pass
    except Exception:
        pass
    
    return None


def count_markdown_pages(md_path: str) -> Optional[int]:
    """Đếm số trang trong file markdown đã ghép theo format:

        Trang 1

        <nội dung trang 1>

        ---

        Trang 2

        <nội dung trang 2>

    Quy tắc đếm:
        - Ưu tiên đếm số dòng tiêu đề có dạng: '^Trang\\s+\\d+$' (theo dòng).
        - Nếu không thấy tiêu đề, fallback tách theo '---' (bỏ các đoạn rỗng).

    Args:
        md_path: Đường dẫn đến file .md cuối sau khi ghép.

    Returns:
        Số trang (int) nếu đọc được, None nếu lỗi.
    """
    try:
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return None

    # 1) Đếm theo tiêu đề "Trang N" (dòng riêng)
    header_matches = re.findall(r"(?m)^\s*Trang\s+\d+\s*$", content)
    if header_matches:
        return len(header_matches)

    # 2) Fallback: tách theo separator '---' và bỏ đoạn rỗng
    parts = re.split(r"\n-{3,}\s*\n", content)
    non_empty_parts = [p for p in parts if p.strip()]
    if non_empty_parts:
        return len(non_empty_parts)

    return 0


def compare_page_counts(pdf_path: str, md_path: str) -> tuple[int, int, bool]:
    """So sánh số trang giữa một file PDF và file Markdown đã ghép.

    Args:
        pdf_path: Đường dẫn tới file PDF nguồn.
        md_path: Đường dẫn tới file Markdown cuối (đã ghép theo định dạng Trang N / ---).

    Returns:
        Tuple (pdf_pages, md_pages, is_match):
            - pdf_pages: số trang đọc được từ PDF (0 nếu không đọc được)
            - md_pages: số trang đếm được từ Markdown (0 nếu lỗi)
            - is_match: True nếu bằng nhau, ngược lại False

    Ghi chú:
        Hàm không ném exception; nếu không đọc được trả về 0 để tiện log/monitoring.
    """
    pdf_pages = count_pdf_pages(pdf_path) or 0
    md_pages = count_markdown_pages(md_path) or 0
    print(f"PDF pages: {pdf_pages}")
    print(f"Markdown pages: {md_pages}")
    return pdf_pages, md_pages, (pdf_pages == md_pages)

def main():
    """
    test
    """
    pdf_path = "/home/ubuntu/fintech/OCR/data/test/5_pages_test.pdf"
    md_path = "/home/ubuntu/fintech/OCR/data/test/5_pages_test.md"
    pdf_pages, md_pages, is_match = compare_page_counts(pdf_path, md_path)
    print(f"PDF pages: {pdf_pages}")
    print(f"Markdown pages: {md_pages}")
    print(f"Match: {is_match}")

if __name__ == "__main__":
    main()
