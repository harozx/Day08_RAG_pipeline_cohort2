"""
Task 5 — Semantic Search Module.

Viết module tìm kiếm ngữ nghĩa (dense retrieval) trên vector store.

Yêu cầu:
    - Input: query string + top_k
    - Output: danh sách chunks có score, sorted descending
    - Phải tương thích với embedding model và vector store ở Task 4
"""

import pickle
import numpy as np
from pathlib import Path

_MODEL = None

def get_embedding_model():
    """Tải và lưu cache mô hình embedding sentence-transformers/all-MiniLM-L6-v2."""
    global _MODEL
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer
        _MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _MODEL


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm ngữ nghĩa sử dụng vector similarity (Cosine similarity).

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,      # Nội dung chunk
            'score': float,      # Cosine similarity score
            'metadata': dict     # source, type, chunk_index
        }
        Sorted by score descending.
    """
    db_path = Path(__file__).parent.parent / "data" / "vector_store.pkl"
    if not db_path.exists():
        print(f"⚠ Không tìm thấy file vector store tại {db_path}!")
        return []

    # Đọc chunks và embeddings từ file persistent store
    with open(db_path, "rb") as f:
        chunks = pickle.load(f)

    # Bước 1: Embed query bằng cùng model ở Task 4
    model = get_embedding_model()
    query_embedding = model.encode(query)

    # Tính toán độ tương đồng Cosine
    q_norm = np.linalg.norm(query_embedding)
    if q_norm == 0:
        q_norm = 1.0

    output = []
    for chunk in chunks:
        doc_embedding = np.array(chunk["embedding"])
        d_norm = np.linalg.norm(doc_embedding)
        if d_norm == 0:
            d_norm = 1.0
        
        # Dot product / (norm(q) * norm(d))
        dot_product = np.dot(query_embedding, doc_embedding)
        score = float(dot_product / (q_norm * d_norm))

        output.append({
            "content": chunk["content"],
            "score": score,
            "metadata": {
                "source": chunk["metadata"].get("source", ""),
                "type": chunk["metadata"].get("type", ""),
                "chunk_index": int(chunk["metadata"].get("chunk_index", 0))
            }
        })

    # Sắp xếp giảm dần theo điểm tương đồng Cosine
    output.sort(key=lambda x: x["score"], reverse=True)
    return output[:top_k]


if __name__ == "__main__":
    # Test
    results = semantic_search("hình phạt cho tội tàng trữ ma tuý", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")
