"""
Task 6 — Lexical Search Module (BM25).

Mặc định sử dụng BM25. Nếu dùng phương pháp khác (TF-IDF, Elasticsearch,
Weaviate BM25 built-in), hãy giải thích cơ chế trong buổi demo → +5 bonus.

Cài đặt:
    pip install rank-bm25

BM25 hoạt động thế nào:
    - Term Frequency (TF): từ xuất hiện nhiều trong document → điểm cao
    - Inverse Document Frequency (IDF): từ hiếm → quan trọng hơn
    - Document length normalization: document dài không bị ưu tiên quá mức
    - Formula: score(q,d) = Σ IDF(qi) * (tf(qi,d) * (k1+1)) / (tf(qi,d) + k1*(1-b+b*|d|/avgdl))
    - k1=1.5 (term saturation), b=0.75 (length normalization)
"""

import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path
from rank_bm25 import BM25Okapi
import numpy as np

# Import functions from task 4 to reuse chunking logic
sys.path.append(os.path.dirname(__file__))
from task4_chunking_indexing import load_documents, chunk_documents

# Global variables to hold the index and corpus in memory
CORPUS: list[dict] = []  
BM25_INDEX = None

def build_bm25_index():
    """
    Xây dựng BM25 index từ corpus.
    """
    global CORPUS, BM25_INDEX
    print("Loading documents and chunking...")
    docs = load_documents()
    CORPUS = chunk_documents(docs)
    
    print(f"Building BM25 index for {len(CORPUS)} chunks...")
    # Tokenize - đơn giản dùng split() theo khoảng trắng
    tokenized_corpus = [doc["content"].lower().split() for doc in CORPUS]
    BM25_INDEX = BM25Okapi(tokenized_corpus)
    print("BM25 index built successfully!")


def lexical_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Tìm kiếm từ khóa sử dụng BM25.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,      # BM25 score
            'metadata': dict
        }
        Sorted by score descending.
    """
    if BM25_INDEX is None:
        build_bm25_index()
        
    tokenized_query = query.lower().split()
    scores = BM25_INDEX.get_scores(tokenized_query)
    
    # Get top_k indices
    top_indices = np.argsort(scores)[::-1][:top_k]
    
    results = []
    for idx in top_indices:
        if scores[idx] > 0:
            results.append({
                "content": CORPUS[idx]["content"],
                "score": float(scores[idx]),
                "metadata": CORPUS[idx]["metadata"]
            })
    return results


if __name__ == "__main__":
    # Test
    query = "Hành vi tàng trữ trái phép chất ma tuý"
    print(f"\n--- Testing Lexical Search (BM25) ---")
    print(f"Query: '{query}'\n")
    
    results = lexical_search(query, top_k=3)
    
    if not results:
        print("Không tìm thấy kết quả nào phù hợp.")
    else:
        for i, r in enumerate(results, 1):
            print(f"[{i}] Score: {r['score']:.3f} | Source: {r['metadata'].get('source', 'Unknown')}")
            # In ra 150 ký tự đầu tiên để preview
            content_preview = r['content'][:150].replace('\n', ' ')
            print(f"    Preview: {content_preview}...\n")
