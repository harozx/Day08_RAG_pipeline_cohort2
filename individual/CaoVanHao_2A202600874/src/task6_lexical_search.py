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

from pathlib import Path

import pickle
import numpy as np
from pathlib import Path
from rank_bm25 import BM25Okapi

VECTORSTORE_PATH = Path(__file__).parent.parent / "data" / "vectorstore.pkl"
_bm25 = None
_corpus = None

def get_corpus_and_bm25():
    global _bm25, _corpus
    if _bm25 is None or _corpus is None:
        if not VECTORSTORE_PATH.exists():
            from src.task4_chunking_indexing import run_pipeline
            run_pipeline()
        with open(VECTORSTORE_PATH, "rb") as f:
            _corpus = pickle.load(f)
            
        tokenized_corpus = [doc["content"].lower().split() for doc in _corpus]
        _bm25 = BM25Okapi(tokenized_corpus)
    return _corpus, _bm25


def build_bm25_index(corpus: list[dict]):
    """
    Xây dựng BM25 index từ corpus.
    """
    tokenized_corpus = [doc["content"].lower().split() for doc in corpus]
    return BM25Okapi(tokenized_corpus)


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm từ khóa sử dụng BM25.
    """
    corpus, bm25 = get_corpus_and_bm25()
    if not corpus or not bm25:
        return []
        
    tokenized_query = query.lower().split()
    scores = bm25.get_scores(tokenized_query)
    
    top_indices = np.argsort(scores)[::-1][:top_k]
    
    results = []
    for idx in top_indices:
        results.append({
            "content": corpus[idx]["content"],
            "score": float(scores[idx]),
            "metadata": corpus[idx].get("metadata", {})
        })
    return results


if __name__ == "__main__":
    # Test
    results = lexical_search("Điều 248 tàng trữ trái phép chất ma tuý", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")
