import os
import sys
import time
from pathlib import Path

# Hotpatch PyTorch to prevent Streamlit's local sources watcher from crashing
# when examining torch._classes.__getattr__ for missing custom classes
try:
    import torch
    original_getattr = torch._classes._ClassesParent.__getattr__
    def patched_getattr(self, attr):
        if attr in ('__path__', '__file__', '__package__', '_path'):
            raise AttributeError(f"Mocking {attr} to avoid PyTorch crash")
        try:
            return original_getattr(self, attr)
        except RuntimeError as e:
            raise AttributeError(str(e)) from e
    torch._classes._ClassesParent.__getattr__ = patched_getattr
    print("Successfully hotpatched torch.classes to prevent Streamlit watcher crash.")
except Exception as e:
    pass

import streamlit as st
from dotenv import load_dotenv

# 1. Setup paths and load environment variables from the student folder
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

student_env_path = PROJECT_ROOT / "individual" / "CaoVanHao_2A202600874" / ".env"
load_dotenv(dotenv_path=student_env_path)

# Import retrieval and generation modules
from individual.CaoVanHao_2A202600874.src.task9_retrieval_pipeline import retrieve
from individual.CaoVanHao_2A202600874.src.task10_generation import (
    SYSTEM_PROMPT, TEMPERATURE, TOP_P, format_context, reorder_for_llm, generate_offline_fallback
)
from google import genai
from google.genai import types

# =============================================================================
# STREAMLIT PAGE CONFIGURATION
# =============================================================================
st.set_page_config(
    page_title="Drug Law QA Chatbot",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CUSTOM CSS INJECTION FOR PREMIUM AESTHETICS
# =============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');

/* Apply modern Outfit font to entire app */
html, body, [class*="css"], .stMarkdown {
    font-family: 'Outfit', sans-serif !important;
}

/* Premium Dark Gradient Background */
.stApp {
    background: linear-gradient(135deg, #0b0f19 0%, #151a2e 100%) !important;
    color: #f1f5f9 !important;
}

/* Sidebar Custom Styling */
[data-testid="stSidebar"] {
    background-color: #0c0f1c !important;
    border-right: 1px solid rgba(255, 255, 255, 0.05);
}

/* Title Gradient */
.title-container {
    padding: 1.5rem 0 0.5rem 0;
}
.title-gradient {
    background: linear-gradient(to right, #6366f1, #a855f7, #ec4899);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 3.2rem;
    font-weight: 800;
    letter-spacing: -1px;
}

/* Chat Input Styling */
.stChatInput {
    border-radius: 30px !important;
    border: 1px solid rgba(99, 102, 241, 0.3) !important;
    background: rgba(30, 41, 59, 0.4) !important;
    color: white !important;
    backdrop-filter: blur(10px);
}

/* Custom Chat Bubbles */
.chat-message-user {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 1rem;
}
.chat-bubble-user {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
    color: white;
    padding: 12px 18px;
    border-radius: 20px 20px 4px 20px;
    max-width: 75%;
    box-shadow: 0 4px 15px rgba(79, 70, 229, 0.3);
    font-size: 1.05rem;
    line-height: 1.5;
}

.chat-message-bot {
    display: flex;
    justify-content: flex-start;
    margin-bottom: 1rem;
}
.chat-bubble-bot {
    background: rgba(26, 31, 51, 0.6);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.05);
    color: #e2e8f0;
    padding: 14px 20px;
    border-radius: 20px 20px 20px 4px;
    max-width: 80%;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    font-size: 1.05rem;
    line-height: 1.6;
}

/* Source badge custom styling */
.source-badge {
    background: rgba(99, 102, 241, 0.15);
    color: #818cf8;
    border: 1px solid rgba(99, 102, 241, 0.3);
    border-radius: 12px;
    padding: 2px 8px;
    font-size: 0.8rem;
    margin-right: 5px;
    font-weight: 500;
}

/* Quick Question Buttons */
div.stButton > button {
    background: rgba(30, 41, 59, 0.4) !important;
    color: #e2e8f0 !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 20px !important;
    padding: 8px 16px !important;
    font-size: 0.9rem !important;
    transition: all 0.3s ease !important;
}
div.stButton > button:hover {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
    color: white !important;
    border-color: transparent !important;
    box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25) !important;
    transform: translateY(-2px) !important;
}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# CONVERSATIONAL QUERY REWRITER
# =============================================================================

def rewrite_query_with_history(query: str, chat_history: list, api_key: str) -> str:
    """Sử dụng LLM để viết lại câu hỏi phụ thuộc vào lịch sử chat."""
    if not chat_history:
        return query
        
    history_str = ""
    # Lấy tối đa 4 lượt thoại gần nhất để tránh tràn context
    for msg in chat_history[-4:]:
        role = "User" if msg["role"] == "user" else "Assistant"
        history_str += f"{role}: {msg['content']}\n"
        
    prompt = f"""Given the following conversation history and a follow-up question, rewrite the follow-up question to be a standalone, self-contained question (in Vietnamese) that can be used for document search.
Do not answer the question, just return the rewritten question.

Conversation History:
{history_str}

Follow-up Question: {query}

Standalone Question:"""

    if api_key:
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            rewritten = response.text.strip()
            return rewritten
        except Exception:
            pass
    return query

# =============================================================================
# CORE CHATBOT LOGIC
# =============================================================================

def process_rag_chat(query: str, api_key: str, openai_key: str):
    """Xử lý truy vấn RAG đầy đủ với chat memory và citation."""
    # Step 1: Rewrite query with context if history exists
    standalone_query = rewrite_query_with_history(query, st.session_state.messages, api_key)
    
    # Step 2: Retrieve chunks (top 5) using the task 9 hybrid pipeline
    chunks = retrieve(standalone_query, top_k=5)
    
    # Step 3: Reorder and format context for generation
    reordered = reorder_for_llm(chunks)
    context = format_context(reordered)
    
    # Step 4: Generate answer with system prompt
    user_message = f"Context:\n{context}\n\n---\n\nQuestion: {query}"
    
    answer = None
    if api_key:
        try:
            client = genai.Client(api_key=api_key)
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
            st.error(f"Lỗi gọi Gemini API: {e}")
            
    if not answer and openai_key:
        try:
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
            st.error(f"Lỗi gọi OpenAI API: {e}")
            
    if not answer:
        answer = generate_offline_fallback(query, chunks)
        
    return {
        "answer": answer,
        "sources": chunks,
        "standalone_query": standalone_query
    }

# =============================================================================
# INITIALIZE STATE
# =============================================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

# =============================================================================
# SIDEBAR CONTROL PANEL
# =============================================================================
with st.sidebar:
    st.image("https://img.icons8.com/color/120/scales.png", width=70)
    st.markdown("### **ĐỒ ÁN NHÓM**")
    st.markdown("### **Hệ Thống RAG Hỏi Đáp Pháp Luật**")
    st.write("---")
    
    # API key indicators
    api_key = os.getenv("GEMINI_API_KEY", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")
    pageindex_key = os.getenv("PAGEINDEX_API_KEY", "")
    
    st.markdown("#### **Trạng thái kết nối API**")
    if api_key:
        st.success("🟢 Gemini API: Sẵn sàng")
    else:
        st.warning("🟡 Gemini API: Sử dụng Offline Fallback")
        
    if pageindex_key and not pageindex_key.startswith("pi_"):
        st.success("🟢 PageIndex (Vectify): Sẵn sàng")
    else:
        st.info("🔵 PageIndex (Vectify): Offline Fallback")
        
    st.write("---")
    
    # Quick clear button
    if st.button("🧹 Xóa lịch sử chat"):
        st.session_state.messages = []
        st.rerun()
        
    # Team members info
    st.markdown("#### **Thành viên nhóm**")
    st.info("👤 Cao Văn Hảo - 2A202600874")
    
    # System settings info
    st.markdown("#### **RAG Configuration**")
    st.write(f"- Chunk Size: 500 characters")
    st.write(f"- Retrieval: Hybrid (BM25 + Semantic)")
    st.write(f"- Reranking: Cross-Encoder (Local/Jina)")

# =============================================================================
# MAIN INTERFACE
# =============================================================================
st.markdown("<div class='title-container'><span class='title-gradient'>⚖️ Drug Law RAG Chatbot</span></div>", unsafe_allow_html=True)
st.write("Hệ thống chatbot thông minh hỗ trợ giải đáp pháp luật phòng, chống ma túy và tra cứu tin tức sự kiện liên quan.")

# Sample questions grid
st.markdown("#### **Câu hỏi gợi ý tra cứu:**")
col1, col2, col3 = st.columns(3)
quick_q = None

with col1:
    if st.button("⚖️ Tội tàng trữ ma túy phạt ra sao?"):
        quick_q = "Hình phạt cho tội tàng trữ trái phép chất ma tuý theo Điều 249 Bộ luật Hình sự?"
with col2:
    if st.button("📰 Ca sĩ Chi Dân bị bắt ở đâu?"):
        quick_q = "Ca sĩ Chi Dân bị truy tố về tội danh gì và bị bắt ở đâu?"
with col3:
    if st.button("🏥 Có các hình thức cai nghiện nào?"):
        quick_q = "Luật Phòng chống ma tuý 2021 quy định những hình thức cai nghiện nào?"

# Render Chat History
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f"""
        <div class="chat-message-user">
            <div class="chat-bubble-user">{message["content"]}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="chat-message-bot">
            <div class="chat-bubble-bot">{message["content"]}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Display sources if any for this assistant response
        if "sources" in message and message["sources"]:
            with st.expander("📚 Xem nguồn tài liệu đối chiếu (%d tài liệu)" % len(message["sources"])):
                for idx, src in enumerate(message["sources"], 1):
                    source_name = src.get("metadata", {}).get("source", "Tài liệu gốc")
                    doc_type = src.get("metadata", {}).get("type", "news")
                    score = src.get("score", 0.0)
                    
                    st.markdown(f"""
                    **Tài liệu {idx} | Nguồn:** `{source_name}` | **Loại:** `{doc_type}` | **Độ khớp:** `{score:.3f}`
                    """)
                    st.caption(f"Trích đoạn: \"...{src['content'].strip()}...\"")
                    st.markdown("---")

# Input area
if quick_q:
    user_input = quick_q
else:
    user_input = st.chat_input("Nhập câu hỏi của bạn tại đây về Luật phòng chống ma túy...")

if user_input:
    # 1. Display User Message
    st.markdown(f"""
    <div class="chat-message-user">
        <div class="chat-bubble-user">{user_input}</div>
    </div>
    """, unsafe_allow_html=True)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # 2. Process RAG Call with spinner
    with st.spinner("🔍 Đang tìm kiếm tài liệu pháp luật và tạo câu trả lời..."):
        result = process_rag_chat(user_input, api_key, openai_key)
        
    # 3. Display Bot Response
    st.markdown(f"""
    <div class="chat-message-bot">
        <div class="chat-bubble-bot">{result["answer"]}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 4. Display sources in expander
    if result["sources"]:
        with st.expander("📚 Xem nguồn tài liệu đối chiếu (%d tài liệu)" % len(result["sources"])):
            for idx, src in enumerate(result["sources"], 1):
                source_name = src.get("metadata", {}).get("source", "Tài liệu gốc")
                doc_type = src.get("metadata", {}).get("type", "news")
                score = src.get("score", 0.0)
                
                st.markdown(f"""
                **Tài liệu {idx} | Nguồn:** `{source_name}` | **Loại:** `{doc_type}` | **Độ khớp:** `{score:.3f}`
                """)
                st.caption(f"Trích đoạn: \"...{src['content'].strip()}...\"")
                st.markdown("---")
                
    # 5. Save Bot response and sources in history
    st.session_state.messages.append({
        "role": "assistant",
        "content": result["answer"],
        "sources": result["sources"]
    })
    
    # Force refresh page to render clean
    st.rerun()
