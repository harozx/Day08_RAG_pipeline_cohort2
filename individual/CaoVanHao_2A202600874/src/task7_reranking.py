"""
Task 7 — Reranking Module.

Chọn 1 trong các phương pháp:
    - Cross-encoder reranker: Jina Reranker v2 (multilingual) hoặc Qwen3-Reranker
    - MMR (Maximal Marginal Relevance): tự implement
    - RRF (Reciprocal Rank Fusion): tự implement

Nếu dùng MMR hoặc RRF, đảm bảo hiểu và giải thích được cơ chế.
"""

from typing import Optional


import os
import requests
import numpy as np
from typing import Optional
from sentence_transformers import SentenceTransformer

def rerank_cross_encoder(
    query: str, candidates: list[dict], top_k: int = 5
) -> list[dict]:
    """
    Rerank candidates sử dụng cross-encoder model (Jina Reranker API với local Bi-encoder fallback).
    """
    if not candidates:
        return []
        
    jina_api_key = os.environ.get("JINA_API_KEY")
    if jina_api_key:
        try:
            response = requests.post(
                "https://api.jina.ai/v1/rerank",
                headers={"Authorization": f"Bearer {jina_api_key}"},
                json={
                    "model": "jina-reranker-v2-base-multilingual",
                    "query": query,
                    "documents": [c["content"] for c in candidates],
                    "top_n": top_k
                },
                timeout=15
            )
            if response.status_code == 200:
                reranked = response.json().get("results", [])
                results = []
                for r in reranked:
                    item = candidates[r["index"]].copy()
                    item["score"] = float(r["relevance_score"])
                    results.append(item)
                return results
        except Exception as e:
            print(f"Jina reranker failed: {e}. Falling back to local Bi-encoder...")

    # Local bi-encoder fallback
    print("Using local Bi-encoder fallback for reranking...")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    query_emb = model.encode(query)
    query_emb_norm = query_emb / (np.linalg.norm(query_emb) + 1e-9)
    
    results = []
    for c in candidates:
        c_copy = c.copy()
        if "embedding" in c_copy and c_copy["embedding"] is not None:
            emb = np.array(c_copy["embedding"])
        else:
            emb = model.encode(c_copy["content"])
        emb_norm = emb / (np.linalg.norm(emb) + 1e-9)
        c_copy["score"] = float(np.dot(query_emb_norm, emb_norm))
        results.append(c_copy)
        
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def rerank_mmr(
    query_embedding: list[float],
    candidates: list[dict],
    top_k: int = 5,
    lambda_param: float = 0.7,
) -> list[dict]:
    """
    Maximal Marginal Relevance — chọn candidates vừa relevant vừa diverse.
    """
    if not candidates:
        return []
        
    q_emb = np.array(query_embedding)
    q_emb_norm = q_emb / (np.linalg.norm(q_emb) + 1e-9)
    
    model = None
    candidate_embs = []
    for c in candidates:
        if "embedding" in c and c["embedding"] is not None:
            emb = np.array(c["embedding"])
        else:
            if model is None:
                model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
            emb = model.encode(c["content"])
        emb_norm = emb / (np.linalg.norm(emb) + 1e-9)
        candidate_embs.append(emb_norm)
        
    selected = []
    remaining = list(range(len(candidates)))
    
    # Select first element
    best_first_idx = None
    best_first_sim = -1.0
    for idx in remaining:
        sim = float(np.dot(q_emb_norm, candidate_embs[idx]))
        if sim > best_first_sim:
            best_first_sim = sim
            best_first_idx = idx
            
    if best_first_idx is not None:
        selected.append(best_first_idx)
        remaining.remove(best_first_idx)
        
    # Select remaining elements
    while len(selected) < min(top_k, len(candidates)):
        best_idx = None
        best_score = float('-inf')
        
        for idx in remaining:
            relevance = float(np.dot(q_emb_norm, candidate_embs[idx]))
            
            max_sim_to_selected = -1.0
            for sel_idx in selected:
                sim = float(np.dot(candidate_embs[idx], candidate_embs[sel_idx]))
                if sim > max_sim_to_selected:
                    max_sim_to_selected = sim
                    
            mmr_score = lambda_param * relevance - (1.0 - lambda_param) * max_sim_to_selected
            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = idx
                
        if best_idx is not None:
            selected.append(best_idx)
            remaining.remove(best_idx)
            
    return [candidates[i] for i in selected]


def rerank_rrf(
    ranked_lists: list[list[dict]], top_k: int = 5, k: int = 60
) -> list[dict]:
    """
    Reciprocal Rank Fusion — gộp kết quả từ nhiều ranker.
    """
    rrf_scores = {}
    content_map = {}
    
    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, 1):
            key = item["content"].strip()
            rrf_scores[key] = rrf_scores.get(key, 0) + 1.0 / (k + rank)
            if key not in content_map:
                content_map[key] = item.copy()
                
    sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    
    results = []
    for key, score in sorted_items[:top_k]:
        item = content_map[key]
        item["score"] = score
        results.append(item)
        
    return results


def rerank(
    query: str,
    candidates: list[dict],
    top_k: int = 5,
    method: str = "cross_encoder",  # "cross_encoder" | "mmr" | "rrf"
) -> list[dict]:
    """
    Unified reranking interface.
    """
    if method == "cross_encoder":
        return rerank_cross_encoder(query, candidates, top_k)
    elif method == "mmr":
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        query_embedding = model.encode(query).tolist()
        return rerank_mmr(query_embedding, candidates, top_k)
    elif method == "rrf":
        if candidates and isinstance(candidates[0], list):
            return rerank_rrf(candidates, top_k)
        else:
            return rerank_rrf([candidates], top_k)
    else:
        raise ValueError(f"Unknown rerank method: {method}")


if __name__ == "__main__":
    # Test with dummy data
    dummy_candidates = [
        {"content": "Điều 248: Tội tàng trữ trái phép chất ma tuý", "score": 0.8, "metadata": {}},
        {"content": "Nghệ sĩ X bị bắt vì sử dụng ma tuý", "score": 0.7, "metadata": {}},
        {"content": "Hình phạt tù từ 2-7 năm cho tội tàng trữ", "score": 0.6, "metadata": {}},
    ]
    results = rerank("hình phạt tàng trữ ma tuý", dummy_candidates, top_k=2)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content']}")
