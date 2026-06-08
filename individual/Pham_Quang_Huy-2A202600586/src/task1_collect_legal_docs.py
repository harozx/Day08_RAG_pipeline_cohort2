"""
Task 1 — Thu thập văn bản pháp luật về ma tuý và các chất cấm.

Hướng dẫn:
    1. Tìm tối thiểu 3 văn bản pháp luật (PDF/DOCX) từ các nguồn chính thống.
    2. Tải về và lưu vào data/landing/legal/
    3. Đặt tên file rõ ràng, không dấu, có năm ban hành.

Gợi ý nguồn:
    - https://thuvienphapluat.vn
    - https://vanban.chinhphu.vn
    - https://luatvietnam.vn

Gợi ý văn bản:
    - Luật Phòng, chống ma tuý 2021 (73/2021/QH15)
    - Nghị định 105/2021/NĐ-CP
    - Bộ luật Hình sự 2015 (sửa đổi 2017) - Chương XX
    - Nghị định 57/2022/NĐ-CP về danh mục chất ma tuý
"""

from pathlib import Path
import requests

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"

# Hướng dẫn gợi ý các tệp văn bản pháp luật cần thu thập
DOCUMENT_URLS = {
    "luat-phong-chong-ma-tuy-2021.pdf": "https://csdt.khanhhoa.gov.vn/uploads/tai-lieu/2021/11/luat-phong-chong-ma-tuy-2021.pdf",
    "nghi-dinh-105-2021.docx": "https://chinhphu.vn/media/chinhphu/2021/12/nd-105-cp.docx", 
    "bo-luat-hinh-su-2015.pdf": "https://laocai.gov.vn/uploads/tai-lieu/2017/08/bo-luat-hinh-su-2015.pdf"
}


def setup_directory():
    """Tạo thư mục data/landing/legal/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ Thư mục đã sẵn sàng: {DATA_DIR}")


def download_file(url: str, filename: str):
    """Tải một file từ URL và lưu vào thư mục DATA_DIR."""
    filepath = DATA_DIR / filename
    
    # Kiểm tra xem file đã tồn tại và không rỗng (> 1KB) chưa
    if filepath.exists() and filepath.stat().st_size > 1024:
        print(f"✓ File đã tồn tại và hợp lệ: {filename} ({filepath.stat().st_size} bytes)")
        return
        
    try:
        print(f"⌛ Đang tải file: {filename} từ {url}...")
        response = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code == 200:
            filepath.write_bytes(response.content)
            print(f"✓ Đã tải thành công: {filepath} ({len(response.content)} bytes)")
        else:
            print(f"✗ Thất bại khi tải {filename}. HTTP Status Code: {response.status_code}")
    except Exception as e:
        print(f"✗ Lỗi khi tải {filename}: {e}")


def collect_legal_docs():
    """Thu thập toàn bộ tài liệu pháp luật được yêu cầu."""
    setup_directory()
    for filename, url in DOCUMENT_URLS.items():
        download_file(url, filename)
    print("✓ Hoàn thành nhiệm vụ thu thập tài liệu pháp luật (Task 1).")


if __name__ == "__main__":
    collect_legal_docs()

