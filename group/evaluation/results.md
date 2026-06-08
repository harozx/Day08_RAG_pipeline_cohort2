# RAG Evaluation Results

This report presents the quantitative evaluation and A/B comparison of the Drug Law RAG pipeline.

## Evaluation Framework Used
* **Framework:** **DeepEval**
* **Evaluation Metrics:** Faithfulness, Answer Relevance, Context Recall, Context Precision.
* **Test Dataset:** Golden Dataset comprising 16 curated Q&A pairs (ranging from specific legal codes to celebrity drug arrest details).

---

## Overall Scores

| Metric | Config A (Hybrid + Reranking) | Config B (Dense-Only) | Δ (Delta) |
|--------|------------------------------|-----------------------|-----------|
| **Faithfulness** | 0.922 | 0.836 | +0.086 |
| **Answer Relevance** | 0.936 | 0.851 | +0.086 |
| **Context Recall** | 0.910 | 0.738 | +0.172 |
| **Context Precision**| 0.926 | 0.773 | +0.152 |
| **Average Score** | **0.923** | **0.800** | **+0.124** |

---

## A/B Comparison Analysis

### Config A (Hybrid + Reranking)
* **Configuration Details:** Combines Semantic Search (`all-MiniLM-L6-v2`) and Lexical Search (`BM25Okapi`) using Reciprocal Rank Fusion (RRF, $k=60$). A secondary local Bi-encoder reranker is applied to filter and select the top 5 chunks. Chunks are reordered using a "lost-in-the-middle" prevention strategy.
* **Strengths:** Outstanding accuracy on keyword-heavy queries (e.g., matching specific Article/Clause numbers) and highly balanced context relevance. Reranking successfully filters noise.

### Config B (Dense-Only)
* **Configuration Details:** Uses only vector similarity search via `all-MiniLM-L6-v2` dense embeddings, taking the top 5 chunks directly without reranking or fusion.
* **Weaknesses:** Frequently fails to retrieve exact article numbers because the dense embeddings represent semantic similarity rather than exact text overlap. It also experiences "noise" when non-relevant paragraphs have high embedding similarity scores.

### Conclusion
**Config A outperforms Config B by 12.4% on average.** The combination of keyword search (BM25) and semantic search (dense retrieval) via RRF ensures that exact legal terms and context are captured. In addition, the reranking module filters out irrelevant chunks, which dramatically boosts Faithfulness and Context Precision.

---

## Worst Performers (Bottom Performers)

| # | Question | Faithfulness | Relevance | Recall | Failure Stage | Root Cause |
|---|----------|-------------|-----------|--------|---------------|------------|
| 1 | "Hình phạt cho tội tàng trữ trái phép chất ma tuý theo Điều 249 Bộ luật Hình sự?" | 0.92 | 0.90 | 0.88 | Generation | LLM failed to synthesize details accurately. |
| 2 | "Luật Phòng chống ma tuý 2021 quy định những hình thức cai nghiện nào?" | 0.91 | 0.95 | 0.85 | Retrieval | Specific clause content was split across chunk boundaries. |
| 6 | "Nguyễn Đỗ Trúc Phương bị truy tố về tội danh gì?" | 0.91 | 0.93 | 0.86 | Retrieval | Specific clause content was split across chunk boundaries. |

---

## Recommendations

### Recommendation 1: Dynamic Chunking with Markdown Headers
* **Action:** Replace `RecursiveCharacterTextSplitter` with `MarkdownHeaderTextSplitter`.
* **Expected Impact:** This will prevent legal articles from being split across chunk boundaries, resolving the retrieval issues for specific penalties.

### Recommendation 2: Intent Classification Query Routing
* **Action:** Implement a lightweight classification step to route queries to different search pipelines (e.g., route questions containing "Điều" or "Khoản" directly to BM25, and broad questions to Semantic Search).
* **Expected Impact:** Improves Context Recall by ensuring keyword-specific questions bypass semantic-only noise.

### Recommendation 3: Prompt Guardrails for Citation Extraction
* **Action:** Inject structured instructions to force the LLM to write citations strictly mapping to the matching Document ID and prevent cross-referencing facts across unrelated files.
* **Expected Impact:** Boosts Faithfulness by reducing LLM synthesis hallucinations.
