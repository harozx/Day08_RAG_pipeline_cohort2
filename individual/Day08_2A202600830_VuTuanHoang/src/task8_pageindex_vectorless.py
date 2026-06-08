"""
Task 8 — PageIndex Vectorless RAG.

Đăng ký tài khoản tại: https://pageindex.ai/
SDK & sample code: https://github.com/VectifyAI/PageIndex

PageIndex cho phép RAG mà không cần vector store — sử dụng
structural understanding của document thay vì embedding.

Cài đặt:
    pip install pageindex

Hướng dẫn:
    1. Đăng ký account tại pageindex.ai
    2. Lấy API key
    3. Upload documents
    4. Query sử dụng PageIndex API
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"


def upload_documents():
    """
    Upload toàn bộ markdown documents lên PageIndex.
    """
    from pageindex import PageIndex
    
    pi = PageIndex(api_key=PAGEINDEX_API_KEY)
    
    for md_file in STANDARDIZED_DIR.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        if not content.strip():
            print(f"  - Skipped empty file: {md_file.name}")
            continue
            
        try:
            pi.upload(
                content=content,
                metadata={"filename": md_file.name, "type": md_file.parent.name}
            )
            print(f"  ✓ Uploaded: {md_file.name}")
        except Exception as e:
            print(f"  x Lỗi khi upload {md_file.name}: {e}")


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Vectorless retrieval sử dụng PageIndex.
    Dùng làm fallback khi hybrid search không có kết quả tốt.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,
            'metadata': dict,
            'source': 'pageindex'   # Đánh dấu nguồn retrieval
        }
    """
    from pageindex import PageIndex
    
    pi = PageIndex(api_key=PAGEINDEX_API_KEY)
    results = pi.query(query=query, top_k=top_k)
    
    return [
        {
            "content": r.text,
            "score": getattr(r, 'score', 0.0),
            "metadata": getattr(r, 'metadata', {}),
            "source": "pageindex"
        }
        for r in results
    ]


if __name__ == "__main__":
    print("=" * 50)
    print("Task 8: PageIndex Vectorless RAG")
    print("=" * 50)
    
    if not PAGEINDEX_API_KEY:
        print("\n[CẢNH BÁO] Không tìm thấy PAGEINDEX_API_KEY trong file .env!")
        print("  Vui lòng truy cập https://pageindex.ai/ để đăng ký tài khoản.")
        print("  Sau đó tạo API Key và dán vào file .env dưới dạng: PAGEINDEX_API_KEY=xxx")
    else:
        print("\n1. Uploading documents...")
        upload_documents()

        print("\n2. Test query:")
        query = "hình phạt sử dụng ma tuý"
        print(f"Query: '{query}'\n")
        try:
            results = pageindex_search(query, top_k=3)
            if not results:
                print("Không tìm thấy kết quả nào.")
            for i, r in enumerate(results, 1):
                print(f"[{i}] Score: {r['score']:.3f}")
                content_preview = r['content'][:150].replace('\n', ' ')
                print(f"    Preview: {content_preview}...\n")
        except Exception as e:
            print(f"Lỗi khi tìm kiếm: {e}")
