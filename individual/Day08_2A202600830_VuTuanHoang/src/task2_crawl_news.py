"""
Task 2 — Crawl bài báo về nghệ sĩ liên quan tới ma tuý.

Hướng dẫn:
    1. Crawl tối thiểu 5 bài báo từ các trang tin tức Việt Nam.
    2. Sử dụng Crawl4AI hoặc thư viện crawling tương tự.
    3. Lưu output vào data/landing/news/
    4. Mỗi bài lưu 1 file JSON với metadata (url, title, date_crawled, content).

Cài đặt:
    pip install crawl4ai
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"


def setup_directory():
    """Tạo thư mục data/landing/news/ nếu chưa có."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


# TODO: Điền danh sách URL bài báo cần crawl
ARTICLE_URLS = [
    "https://tuoitre.vn/ca-si-chi-dan-nguoi-mau-an-tay-co-tien-truc-phuong-to-chuc-su-dung-ma-tuy-ra-sao-2026040214370414.htm",
    "https://tuoitre.vn/dien-vien-huu-tin-lanh-7-nam-6-thang-tu-20230428114919793.htm",
    "https://cand.vn/nu-dien-vien-xin-hay-tin-em-bi-khoi-to-vi-mua-ma-tuy-ve-ban-le-post691084.html",
    "https://thanhnien.vn/ca-si-chau-viet-cuong-linh-an-13-nam-tu-giam-ve-toi-giet-nguoi-185831663.htm",
    "https://tuoitre.vn/dj-thai-hoang-bi-bat-vi-tang-tru-ma-tuy-20230425105653423.htm"
]


async def crawl_article(url: str) -> dict:
    """
    Crawl một bài báo và trả về dict chứa metadata + content.

    Returns:
        {
            "url": str,
            "title": str,
            "date_crawled": str (ISO format),
            "content_markdown": str
        }
    """
    from crawl4ai import AsyncWebCrawler
    import re

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
        
        # Lấy tiêu đề bài báo từ HTML
        title = "Unknown"
        if result.html:
            match = re.search(r'<title>(.*?)</title>', result.html, re.IGNORECASE | re.DOTALL)
            if match:
                title = match.group(1).strip()
                
        # Lấy nội dung sạch (Dùng BeautifulSoup do fit_markdown của crawl4ai phiên bản này bị lỗi)
        content = ""
        if result.html:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(result.html, "html.parser")
            # Lấy phần tử chứa nội dung chính của bài báo (hỗ trợ VnExpress, Tuổi Trẻ, Thanh Niên, CAND...)
            article = soup.select_one(".detail-content, .fck_detail, article, .detail-c, .detail__cmain, .detail-content-body")
            if article:
                content = article.get_text(separator="\n\n", strip=True)
            else:
                content = str(result.markdown.raw_markdown) if hasattr(result.markdown, 'raw_markdown') else str(result.markdown)
        else:
            content = str(result.markdown.raw_markdown) if hasattr(result.markdown, 'raw_markdown') else str(result.markdown)

        return {
            "url": url,
            "title": title,
            "date_crawled": datetime.now().isoformat(),
            "content_markdown": content,
        }


async def crawl_all():
    """Crawl toàn bộ bài báo trong ARTICLE_URLS."""
    setup_directory()

    for i, url in enumerate(ARTICLE_URLS, 1):
        print(f"[{i}/{len(ARTICLE_URLS)}] Crawling: {url}")
        article = await crawl_article(url)

        # Lưu file JSON
        filename = f"article_{i:02d}.json"
        filepath = DATA_DIR / filename
        filepath.write_text(json.dumps(article, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  - Saved: {filepath}")


if __name__ == "__main__":
    if not ARTICLE_URLS:
        print("⚠ Hãy điền ARTICLE_URLS trước khi chạy!")
        print("Gợi ý: tìm bài báo trên VnExpress, Tuổi Trẻ, Thanh Niên, ...")
    else:
        asyncio.run(crawl_all())
