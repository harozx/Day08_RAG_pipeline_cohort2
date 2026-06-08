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
from src.task4_chunking_indexing import load_documents, chunk_documents

# Load corpus và phân đoạn thành các chunks đồng nhất với Task 4
try:
    docs = load_documents()
    CORPUS = chunk_documents(docs)
except Exception as e:
    print(f"⚠ Không thể tải corpus: {e}")
    CORPUS = []

_BM25 = None


def get_bm25_index():
    """Tải và lưu cache index BM25 Okapi."""
    global _BM25
    if _BM25 is None:
        from rank_bm25 import BM25Okapi
        tokenized_corpus = [doc["content"].lower().split() for doc in CORPUS]
        _BM25 = BM25Okapi(tokenized_corpus)
    return _BM25


def build_bm25_index(corpus: list[dict]):
    """
    Xây dựng BM25 index từ corpus.

    Args:
        corpus: List of {'content': str, 'metadata': dict}
    """
    from rank_bm25 import BM25Okapi
    tokenized_corpus = [doc["content"].lower().split() for doc in corpus]
    return BM25Okapi(tokenized_corpus)


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
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
    if not CORPUS:
        return []

    bm25 = get_bm25_index()
    tokenized_query = query.lower().split()
    scores = bm25.get_scores(tokenized_query)

    # Sắp xếp index theo điểm số BM25 giảm dần
    scored_indices = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)

    results = []
    for idx, score in scored_indices[:top_k]:
        results.append({
            "content": CORPUS[idx]["content"],
            "score": float(score),
            "metadata": CORPUS[idx]["metadata"]
        })
    return results


if __name__ == "__main__":
    # Test
    results = lexical_search("Điều 248 tàng trữ trái phép chất ma tuý", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")
