"""
Task 10 — Generation Có Citation.

Hướng dẫn:
    1. Chọn top_k, top_p phù hợp (giải thích lý do)
    2. Sắp xếp lại chunks sau reranking để tránh "lost in the middle"
    3. Inject context vào prompt
    4. Yêu cầu LLM trả lời có citation
    5. Nếu không đủ evidence → "I cannot verify this information"
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
from dotenv import load_dotenv

load_dotenv()

from task9_retrieval_pipeline import retrieve


# =============================================================================
# CONFIGURATION — Giải thích lựa chọn
# =============================================================================

# top_k: Số chunks đưa vào context
# Chọn 5 vì: đủ evidence mà không quá dài gây lost in the middle
TOP_K = 5

# top_p (nucleus sampling): Xác suất tích luỹ cho token generation
# Chọn 0.9 vì: đủ diverse nhưng không quá random
TOP_P = 0.9

# temperature: Độ ngẫu nhiên của output
# Chọn 0.1 vì: RAG cần factual, ít sáng tạo, yêu cầu trích dẫn chính xác
TEMPERATURE = 0.1


# =============================================================================
# SYSTEM PROMPT
# =============================================================================

SYSTEM_PROMPT = """Bạn là một chuyên gia pháp lý và trợ lý tìm kiếm thông tin về Luật Phòng Chống Ma Túy Việt Nam.
Nhiệm vụ của bạn là trả lời câu hỏi dựa TRÊN TÀI LIỆU (Context) ĐƯỢC CUNG CẤP.

For every statement of fact or claim, immediately insert a citation in brackets
linking to the specific source (e.g., [Luật Phòng chống ma tuý 2021, Điều 3]
or [VnExpress, 2024]).

If the information is not explicitly stated in the provided context or knowledge
base, state 'Tôi không thể xác minh thông tin này từ nguồn tài liệu hiện có' rather than
guessing.

Rules:
- Only use information from the provided context
- Every factual claim MUST have a citation
- If context is insufficient, say so clearly
- Structure your answer with clear paragraphs"""


# =============================================================================
# DOCUMENT REORDERING (tránh lost in the middle)
# =============================================================================

def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """
    Sắp xếp chunks để tránh "lost in the middle" effect.

    LLM nhớ tốt thông tin ở ĐẦU và CUỐI prompt, quên thông tin ở GIỮA.
    Strategy: đặt chunks quan trọng nhất ở đầu và cuối, kém quan trọng ở giữa.

    Input order (by score):  [1, 2, 3, 4, 5]
    Output order:            [1, 3, 5, 4, 2]
    (best first, worst in middle, second-best last)
    """
    if len(chunks) <= 2:
        return chunks

    reordered = []
    # Lẻ ở đầu
    for i in range(0, len(chunks), 2):
        reordered.append(chunks[i])
    # Chẵn ở cuối (reversed)
    for i in range(len(chunks) - 1 - (len(chunks) % 2 == 0), 0, -2):
        reordered.append(chunks[i])

    return reordered


# =============================================================================
# CONTEXT FORMATTING
# =============================================================================

def format_context(chunks: list[dict]) -> str:
    """
    Format chunks thành context string cho prompt.
    Mỗi chunk có label source để LLM có thể cite.
    """
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        metadata = chunk.get("metadata", {})
        source = metadata.get("source", f"Source {i}")
        doc_type = metadata.get("type", "unknown")
        
        context_parts.append(
            f"[Tài liệu {i} | Nguồn: {source} | Loại: {doc_type}]\n"
            f"{chunk['content']}\n"
        )
    return "\n---\n".join(context_parts)


# =============================================================================
# GENERATION
# =============================================================================

def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """
    End-to-end RAG generation có citation.
    """
    print("  [Task 10] Retrieving relevant documents...")
    # Step 1: Retrieve
    chunks = retrieve(query, top_k=top_k)

    if not chunks:
        return {
            "answer": "Tôi không tìm thấy tài liệu nào liên quan đến câu hỏi này.",
            "sources": [],
            "retrieval_source": "none"
        }

    # Step 2: Reorder
    reordered = reorder_for_llm(chunks)

    # Step 3: Format context
    context = format_context(reordered)

    # Step 4: Build prompt
    user_message = f"""Dưới đây là các tài liệu tham khảo (Context):\n{context}\n\n---\n\nCâu hỏi: {query}"""

    print("  [Task 10] Generating answer via LLM API...")
    # Step 5: Call LLM
    from openai import OpenAI
    client = OpenAI(
        api_key=os.getenv("API_KEY"),
        base_url=os.getenv("LLM_ENDPOINT")
    )

    try:
        response = client.chat.completions.create(
            model=os.getenv("MODEL", "gemini-2.0-flash"),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=TEMPERATURE,
            top_p=TOP_P,
        )
        answer = response.choices[0].message.content
    except Exception as e:
        answer = f"Lỗi gọi API: {e}"

    # Step 6: Return
    return {
        "answer": answer,
        "sources": chunks,
        "retrieval_source": chunks[0].get("source", "hybrid") if chunks else "none"
    }


if __name__ == "__main__":
    test_queries = [
        "Hình phạt cho tội tàng trữ trái phép chất ma tuý theo pháp luật Việt Nam?",
        "Những nghệ sĩ nào đã bị bắt vì liên quan tới ma tuý?",
    ]

    for q in test_queries:
        print(f"\n{'='*70}")
        print(f"Q: {q}")
        print("=" * 70)
        result = generate_with_citation(q)
        print(f"\n--- TRẢ LỜI ---\n{result['answer']}")
        print(f"\n[Dựa trên: {len(result['sources'])} đoạn tài liệu | Thông qua công nghệ: {result['retrieval_source']}]")
