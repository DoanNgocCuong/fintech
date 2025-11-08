import os

def remove_pdf_files(root_folder):
    """
    Traverse all subfolders from the given root directory and delete every .pdf file found.
    """
    for dirpath, dirnames, filenames in os.walk(root_folder):
        for filename in filenames:
            if filename.lower().endswith('.pdf'):
                file_path = os.path.join(dirpath, filename)
                try:
                    os.remove(file_path)
                    print(f"Deleted: {file_path}")
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")

if __name__ == "__main__":
    # Thay đổi đường dẫn dưới đây thành thư mục gốc bạn muốn xoá file PDF
    folder = input("Enter the root folder to delete PDFs from: ").strip()
    remove_pdf_files(folder)
