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
from sentence_transformers import SentenceTransformer

VECTORSTORE_PATH = Path(__file__).parent.parent / "data" / "vectorstore.pkl"
_model = None
_chunks = None

def get_model():
    global _model
    if _model is None:
        print("Loading sentence-transformers/all-MiniLM-L6-v2 for query encoding...")
        _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _model

def get_chunks():
    global _chunks
    if _chunks is None:
        if not VECTORSTORE_PATH.exists():
            from src.task4_chunking_indexing import run_pipeline
            run_pipeline()
        with open(VECTORSTORE_PATH, "rb") as f:
            _chunks = pickle.load(f)
    return _chunks

def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm ngữ nghĩa sử dụng vector similarity.
    """
    chunks = get_chunks()
    if not chunks:
        return []
        
    model = get_model()
    query_emb = model.encode(query)
    
    # Normalize query embedding
    query_emb_norm = query_emb / (np.linalg.norm(query_emb) + 1e-9)
    
    results = []
    for chunk in chunks:
        emb = np.array(chunk["embedding"])
        emb_norm = emb / (np.linalg.norm(emb) + 1e-9)
        score = float(np.dot(query_emb_norm, emb_norm))
        results.append({
            "content": chunk["content"],
            "score": score,
            "metadata": chunk.get("metadata", {})
        })
        
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


if __name__ == "__main__":
    # Test
    results = semantic_search("hình phạt cho tội tàng trữ ma tuý", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")
