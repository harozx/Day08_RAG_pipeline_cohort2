"""
Task 9 — Retrieval Pipeline Hoàn Chỉnh.

Kết hợp semantic search + lexical search + reranking + PageIndex fallback
thành một pipeline thống nhất.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from task5_semantic_search import semantic_search
from task6_lexical_search import lexical_search
from task7_reranking import rerank, rerank_rrf
from task8_pageindex_vectorless import pageindex_search


# =============================================================================
# CONFIGURATION
# =============================================================================

SCORE_THRESHOLD = 0.3   # Nếu best score < threshold → fallback PageIndex
DEFAULT_TOP_K = 5
RERANK_METHOD = "rrf"  # "cross_encoder" | "mmr" | "rrf"


def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    use_reranking: bool = True,
) -> list[dict]:
    """
    Retrieval pipeline hoàn chỉnh với fallback logic.
    """
    print(f"  [Task 9] Executing Semantic & Lexical search for query...")
    # Step 1: Song song chạy semantic + lexical
    dense_results = semantic_search(query, top_k=top_k * 2)
    sparse_results = lexical_search(query, top_k=top_k * 2)

    # Đánh dấu source
    for r in dense_results: r["source"] = "semantic"
    for r in sparse_results: r["source"] = "lexical"

    # Step 2: Merge & Rerank (dùng RRF mặc định)
    if use_reranking:
        print(f"  [Task 9] Merging results using RRF...")
        final_results = rerank(
            method="rrf", 
            ranked_lists=[dense_results, sparse_results], 
            top_k=top_k
        )
    else:
        # Nếu không rerank, chỉ lấy kết quả semantic
        final_results = dense_results[:top_k]

    # Gán nhãn hybrid
    for item in final_results:
        item["source"] = "hybrid"

    # Step 4: Check threshold → fallback
    if not final_results or final_results[0].get("score", 0) < score_threshold:
        print(f"  ⚠ Hybrid score quá thấp. Fallback → PageIndex")
        try:
            fallback = pageindex_search(query, top_k=top_k)
            if fallback:
                return fallback
        except Exception as e:
            print(f"  ⚠ Fallback PageIndex thất bại ({e}). Vẫn trả về Hybrid results.")

    return final_results[:top_k]


if __name__ == "__main__":
    test_queries = [
        "Hình phạt cho tội tàng trữ trái phép chất ma tuý",
        "Nghệ sĩ nào bị bắt vì sử dụng ma tuý năm 2024",
    ]

    for q in test_queries:
        print(f"\nQuery: {q}")
        print("-" * 60)
        results = retrieve(q, top_k=3)
        for i, r in enumerate(results, 1):
            print(f"  {i}. [{r.get('score', 0):.3f}] [{r.get('source', 'unknown')}] {r['content'][:80]}...")
