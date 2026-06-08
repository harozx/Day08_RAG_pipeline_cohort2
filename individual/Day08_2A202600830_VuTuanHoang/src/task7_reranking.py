"""
Task 7 — Reranking Module.

Chọn 1 trong các phương pháp:
    - Cross-encoder reranker: Jina Reranker v2 (multilingual) hoặc Qwen3-Reranker
    - MMR (Maximal Marginal Relevance): tự implement
    - RRF (Reciprocal Rank Fusion): tự implement

Nếu dùng MMR hoặc RRF, đảm bảo hiểu và giải thích được cơ chế.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()
JINA_API_KEY = os.getenv("JINA_API_KEY", "")

def rerank_cross_encoder(
    query: str, candidates: list[dict], top_k: int = 5
) -> list[dict]:
    """
    Rerank candidates sử dụng cross-encoder model (Jina Reranker API).
    """
    if not JINA_API_KEY:
        print("Warning: Không tìm thấy JINA_API_KEY. Vui lòng thêm vào file .env")
        return candidates[:top_k]
        
    import requests
    try:
        response = requests.post(
            "https://api.jina.ai/v1/rerank",
            headers={"Authorization": f"Bearer {JINA_API_KEY}"},
            json={
                "model": "jina-reranker-v2-base-multilingual",
                "query": query,
                "documents": [c["content"] for c in candidates],
                "top_n": top_k
            }
        )
        if response.status_code == 200:
            reranked = response.json()["results"]
            return [
                {**candidates[r["index"]], "score": r["relevance_score"]}
                for r in reranked
            ]
        else:
            print(f"Lỗi gọi Jina API: {response.text}")
            return candidates[:top_k]
    except Exception as e:
        print(f"Exception calling Jina: {e}")
        return candidates[:top_k]

def cosine_sim(v1, v2):
    import numpy as np
    a = np.array(v1)
    b = np.array(v2)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def rerank_mmr(
    query_embedding: list[float],
    candidates: list[dict],
    top_k: int = 5,
    lambda_param: float = 0.7,
) -> list[dict]:
    """
    Maximal Marginal Relevance — chọn candidates vừa relevant vừa diverse.

    MMR = λ * sim(query, doc) - (1-λ) * max(sim(doc, selected_docs))
    """
    selected = []
    remaining = list(range(len(candidates)))

    for _ in range(min(top_k, len(candidates))):
        best_idx = None
        best_score = float('-inf')

        for idx in remaining:
            # Relevance to query
            relevance = cosine_sim(query_embedding, candidates[idx]["embedding"])

            # Max similarity to already selected
            max_sim_to_selected = 0
            for sel_idx in selected:
                sim = cosine_sim(candidates[idx]["embedding"], candidates[sel_idx]["embedding"])
                max_sim_to_selected = max(max_sim_to_selected, sim)

            # MMR score
            mmr_score = lambda_param * relevance - (1 - lambda_param) * max_sim_to_selected

            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = idx

        if best_idx is not None:
            selected.append(best_idx)
            remaining.remove(best_idx)

    # Convert selected indices back to candidates
    results = []
    for i in selected:
        # Cập nhật score thành MMR logic hoặc giữ nguyên để biết thứ tự
        results.append(candidates[i])
    return results


def rerank_rrf(
    ranked_lists: list[list[dict]], top_k: int = 5, k: int = 60
) -> list[dict]:
    """
    Reciprocal Rank Fusion — gộp kết quả từ nhiều ranker (Semantic + Lexical).

    RRF(d) = Σ 1 / (k + rank_r(d))
    """
    rrf_scores = {}  # content -> score
    content_map = {}  # content -> full dict

    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, 1):
            key = item["content"]
            rrf_scores[key] = rrf_scores.get(key, 0) + 1 / (k + rank)
            content_map[key] = item

    # Sort by RRF score descending
    sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

    results = []
    for content, score in sorted_items[:top_k]:
        item = content_map[content].copy()
        item["score"] = score
        results.append(item)

    return results


# =============================================================================
# Main rerank interface
# =============================================================================

def rerank(
    query: str = None,
    candidates: list[dict] = None,
    top_k: int = 5,
    method: str = "rrf",  # Đặt mặc định là RRF để chạy tốt nhất không cần API key
    query_embedding: list[float] = None,
    ranked_lists: list[list[dict]] = None
) -> list[dict]:
    """
    Unified reranking interface.
    """
    if method == "cross_encoder":
        return rerank_cross_encoder(query, candidates, top_k)
    elif method == "mmr":
        if query_embedding is None or candidates is None:
            raise ValueError("Call rerank_mmr with query_embedding and candidates")
        return rerank_mmr(query_embedding, candidates, top_k)
    elif method == "rrf":
        if ranked_lists is None:
            raise ValueError("Call rerank_rrf with ranked_lists")
        return rerank_rrf(ranked_lists, top_k)
    else:
        raise ValueError(f"Unknown rerank method: {method}")


if __name__ == "__main__":
    # Test with dummy data
    print("Testing RRF (Reciprocal Rank Fusion) Reranker:")
    
    # Giả lập kết quả từ Semantic Search (Mô hình AI)
    semantic_results = [
        {"content": "Điều 248: Tội tàng trữ trái phép chất ma tuý", "score": 0.8, "metadata": {"source": "semantic"}},
        {"content": "Hình phạt tù từ 2-7 năm cho tội tàng trữ", "score": 0.6, "metadata": {"source": "semantic"}},
        {"content": "Nghệ sĩ X bị bắt vì sử dụng ma tuý", "score": 0.7, "metadata": {"source": "semantic"}},
    ]
    
    # Giả lập kết quả từ Lexical Search (BM25)
    lexical_results = [
        {"content": "Nghệ sĩ X bị bắt vì sử dụng ma tuý", "score": 25.5, "metadata": {"source": "lexical"}},
        {"content": "Điều 248: Tội tàng trữ trái phép chất ma tuý", "score": 18.2, "metadata": {"source": "lexical"}},
    ]
    
    # Gộp 2 danh sách bằng RRF
    results = rerank(method="rrf", ranked_lists=[semantic_results, lexical_results], top_k=3)
    
    for i, r in enumerate(results, 1):
        print(f"[{i}] RRF Score: {r['score']:.4f} | {r['content']}")
