"""
Task 10 — Generation Có Citation.

Hướng dẫn:
    1. Chọn top_k, top_p phù hợp (giải thích lý do)
    2. Sắp xếp lại chunks sau reranking để tránh "lost in the middle"
    3. Inject context vào prompt
    4. Yêu cầu LLM trả lời có citation
    5. Nếu không đủ evidence → "I cannot verify this information"
"""

import os
from dotenv import load_dotenv

load_dotenv()

from .task9_retrieval_pipeline import retrieve


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
# Chọn 0.3 vì: RAG cần factual, ít sáng tạo
TEMPERATURE = 0.3


# =============================================================================
# SYSTEM PROMPT
# =============================================================================

SYSTEM_PROMPT = """Answer the following question comprehensively in Vietnamese.
For every statement of fact or claim, immediately insert a citation in brackets
linking to the specific source (e.g., [Luật Phòng chống ma tuý 2021, Điều 3]
or [VnExpress, 2024]).

If the information is not explicitly stated in the provided context or knowledge
base, state 'Tôi không thể xác minh thông tin này từ nguồn hiện có' rather than
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
    Strategy: đặt chunks quan trọng nhất ở đầu và cuối, kém quan trọng ở giữa.
    """
    if len(chunks) <= 2:
        return chunks
        
    sorted_chunks = sorted(chunks, key=lambda x: x.get("score", 0.0), reverse=True)
    
    even_chunks = [sorted_chunks[i] for i in range(0, len(sorted_chunks), 2)]
    odd_chunks = [sorted_chunks[i] for i in range(1, len(sorted_chunks), 2)]
    
    return even_chunks + list(reversed(odd_chunks))


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
        source = chunk.get("metadata", {}).get("source", f"Source {i}")
        doc_type = chunk.get("metadata", {}).get("type", "unknown")
        context_parts.append(
            f"[Document {i} | Source: {source} | Type: {doc_type}]\n"
            f"{chunk['content']}\n"
        )
    return "\n---\n".join(context_parts)


# =============================================================================
# GENERATION
# =============================================================================

def generate_offline_fallback(query: str, chunks: list[dict]) -> str:
    """
    Tạo câu trả lời ngoại tuyến dựa trên các chunks tìm được khi không có LLM.
    """
    if not chunks:
        return "Tôi không thể tìm thấy thông tin phù hợp trong nguồn tài liệu hiện có."
        
    response_parts = [
        "Đây là câu trả lời ngoại tuyến được tổng hợp từ các tài liệu tìm thấy:",
        f"Dựa trên truy vấn '{query}', tôi đã tìm thấy các nguồn tài liệu liên quan sau:"
    ]
    for i, chunk in enumerate(chunks, 1):
        source = chunk.get("metadata", {}).get("source", "Tài liệu")
        snippet = chunk["content"][:250].strip().replace("\n", " ")
        response_parts.append(f"- [{source}] {snippet}...")
        
    response_parts.append("\nVui lòng cấu hình OPENAI_API_KEY trong file .env để nhận câu trả lời đầy đủ từ mô hình ngôn ngữ lớn.")
    return "\n".join(response_parts)


def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """
    End-to-end RAG generation có citation.
    """
    # Step 1: Retrieve
    chunks = retrieve(query, top_k=top_k)
    
    # Step 2: Reorder
    reordered = reorder_for_llm(chunks)
    
    # Step 3: Format context
    context = format_context(reordered)
    
    # Step 4: Build prompt
    user_message = f"Context:\n{context}\n\n---\n\nQuestion: {query}"
    
    # Step 5: Call LLM
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")
    
    # Ignore placeholder keys
    if gemini_key and (gemini_key.startswith("gemini_xxx") or gemini_key.startswith("your_")):
        gemini_key = ""
    if openai_key and (openai_key.startswith("sk-xxx") or openai_key.startswith("openai_xxx")):
        openai_key = ""

    answer = None
    if gemini_key:
        try:
            print("Calling Gemini API...")
            from google import genai
            from google.genai import types
            
            client = genai.Client(api_key=gemini_key)
            combined_prompt = f"{SYSTEM_PROMPT}\n\n---\n\n{user_message}"
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=combined_prompt,
                config=types.GenerateContentConfig(
                    temperature=TEMPERATURE,
                    top_p=TOP_P,
                )
            )
            answer = response.text
        except Exception as e:
            print(f"Gemini API call failed: {e}.")
            
    if not answer and openai_key:
        try:
            print("Calling OpenAI API...")
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                temperature=TEMPERATURE,
                top_p=TOP_P,
            )
            answer = response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI API call failed: {e}.")
            
    if not answer:
        print("Using offline generated fallback...")
        answer = generate_offline_fallback(query, chunks)
        
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
        "Quy trình cai nghiện bắt buộc theo Luật Phòng chống ma tuý 2021?",
    ]

    for q in test_queries:
        print(f"\n{'='*70}")
        print(f"Q: {q}")
        print("=" * 70)
        result = generate_with_citation(q)
        print(f"\nA: {result['answer']}")
        print(f"\n[Sources: {len(result['sources'])} chunks | via {result['retrieval_source']}]")
