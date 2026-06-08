"""
Task 3 — Convert toàn bộ file trong data/landing/ thành Markdown.

Sử dụng MarkItDown của Microsoft:
    https://github.com/microsoft/markitdown

Cài đặt:
    pip install markitdown

Hướng dẫn:
    1. Scan toàn bộ file trong data/landing/ (PDF, DOCX, JSON)
    2. Convert sang Markdown
    3. Lưu vào data/standardized/ giữ nguyên cấu trúc thư mục
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import json
import time
from pathlib import Path

import fitz
from dotenv import load_dotenv
from openai import OpenAI
from markitdown import MarkItDown

LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"


def convert_legal_docs():
    """Convert PDF/DOCX files trong data/landing/legal/ sang markdown."""
    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)

    load_dotenv()
    
    # Sử dụng LLM cấu hình từ .env để trích xuất text trong trường hợp PDF scan
    client = OpenAI(
        api_key=os.getenv("API_KEY"),
        base_url=os.getenv("LLM_ENDPOINT")
    )
    md = MarkItDown(llm_client=client, llm_model=os.getenv("MODEL"))

    for filepath in legal_dir.iterdir():
        if filepath.suffix.lower() in (".pdf", ".docx", ".doc"):
            print(f"Converting: {filepath.name}")
            output_path = output_dir / f"{filepath.stem}.md"
            
            if filepath.suffix.lower() == ".pdf":
                doc = fitz.open(str(filepath))
                text = ""
                for page in doc:
                    text += page.get_text()
                
                if len(text.strip()) < 100:
                    # Là PDF scan
                    print("  -> Scanned PDF detected, using LLM OCR for each page...")
                    md_text = ""
                    for i, page in enumerate(doc):
                        print(f"     Processing page {i+1}/{len(doc)}")
                        pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
                        img_path = str(output_dir / f"temp_page_{i}.png")
                        pix.save(img_path)
                        try:
                            res = md.convert(img_path)
                            md_text += res.text_content + "\n\n"
                        except Exception as e:
                            print(f"     Error on page {i+1}: {e}")
                        finally:
                            if os.path.exists(img_path):
                                os.remove(img_path)
                        
                        # Chờ 5 giây giữa các trang để tránh văng Rate Limit (15 req/min)
                        time.sleep(5)
                    
                    output_path.write_text(md_text, encoding="utf-8")
                    print(f"  - Saved: {output_path}")
                    doc.close()
                    continue
                else:
                    doc.close()

            result = md.convert(str(filepath))
            output_path.write_text(result.text_content, encoding="utf-8")
            print(f"  - Saved: {output_path}")


def convert_news_articles():
    """Convert JSON crawled articles trong data/landing/news/ sang markdown."""
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)

    for filepath in news_dir.iterdir():
        if filepath.suffix.lower() == ".json":
            print(f"Converting: {filepath.name}")
            # Đọc JSON, extract content_markdown hoặc content['body'], lưu thành .md
            data = json.loads(filepath.read_text(encoding="utf-8"))
            output_path = output_dir / f"{filepath.stem}.md"
            
            # Thêm metadata header
            header = f"# {data.get('title', 'Unknown')}\n\n"
            header += f"**Source:** {data.get('url', 'N/A')}\n"
            header += f"**Crawled:** {data.get('date_crawled', 'N/A')}\n\n---\n\n"
            
            # Lấy nội dung
            text_content = ""
            if "content" in data and isinstance(data["content"], dict):
                text_content = data["content"].get("body", "")
            else:
                text_content = data.get("content_markdown", "")
                
            content = header + text_content
            output_path.write_text(content, encoding="utf-8")
            print(f"  - Saved: {output_path}")


def convert_all():
    """Convert toàn bộ files."""
    print("=" * 50)
    print("Task 3: Convert to Markdown (MarkItDown)")
    print("=" * 50)

    print("\n--- Legal Documents ---")
    convert_legal_docs()

    print("\n--- News Articles ---")
    convert_news_articles()

    print("\n- Done! Output at:", OUTPUT_DIR)


if __name__ == "__main__":
    convert_all()
