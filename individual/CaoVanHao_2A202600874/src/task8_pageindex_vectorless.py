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

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to sys.path to allow running as a script directly
sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"


def upload_documents():
    """
    Upload toàn bộ markdown documents lên PageIndex.
    """
    if not PAGEINDEX_API_KEY:
        print("PAGEINDEX_API_KEY not found. Skipping upload.")
        return
    try:
        from pageindex import PageIndexClient
        # Patch the buggy SDK method at runtime to use Authorization header
        PageIndexClient._headers = lambda self: {"Authorization": f"Bearer {self.api_key}"}
        
        pi = PageIndexClient(api_key=PAGEINDEX_API_KEY)
        legal_dir = Path(__file__).parent.parent / "data" / "landing" / "legal"
        for pdf_file in legal_dir.glob("*.pdf"):
            res = pi.submit_document(file_path=str(pdf_file))
            doc_id = res.get("id") or res.get("document", {}).get("id")
            print(f"  ✓ Uploaded: {pdf_file.name} (ID: {doc_id})")
    except Exception as e:
        print(f"Upload failed: {e}")


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Vectorless retrieval sử dụng PageIndex.
    Dùng làm fallback khi hybrid search không có kết quả tốt.
    """
    if not PAGEINDEX_API_KEY:
        # Fallback to local lexical search
        from src.task6_lexical_search import lexical_search
        results = lexical_search(query, top_k=top_k)
        for r in results:
            r["source"] = "pageindex"
        return results

    try:
        from pageindex import PageIndexClient
        # Patch the buggy SDK method at runtime to use Authorization header
        PageIndexClient._headers = lambda self: {"Authorization": f"Bearer {self.api_key}"}
        
        pi = PageIndexClient(api_key=PAGEINDEX_API_KEY)
        
        # Get list of documents to query
        docs_res = pi.list_documents(limit=50)
        docs = docs_res.get("documents", [])
        
        results = []
        for doc in docs[:top_k]:
            doc_id = doc.get("id")
            if doc_id:
                query_res = pi.submit_query(doc_id=doc_id, query=query)
                answer = query_res.get("answer", "")
                score = float(query_res.get("score", 1.0))
                results.append({
                    "content": answer,
                    "score": score,
                    "metadata": doc,
                    "source": "pageindex"
                })
        
        if not results:
            raise Exception("No results retrieved from PageIndex.")
        return results
    except Exception as e:
        print(f"PageIndex query failed: {e}. Falling back to local search...")
        from src.task6_lexical_search import lexical_search
        results = lexical_search(query, top_k=top_k)
        for r in results:
            r["source"] = "pageindex"
        return results


if __name__ == "__main__":
    if not PAGEINDEX_API_KEY:
        print("PAGEINDEX_API_KEY not found. Running with local fallback:")
        results = pageindex_search("hình phạt sử dụng ma tuý", top_k=3)
        for r in results:
            print(f"[{r['score']:.3f}] {r['content'][:100]}...")
    else:
        print("Uploading documents...")
        upload_documents()

        print("\nTest query:")
        results = pageindex_search("hình phạt sử dụng ma tuý", top_k=3)
        for r in results:
            print(f"[{r['score']:.3f}] {r['content'][:100]}...")
