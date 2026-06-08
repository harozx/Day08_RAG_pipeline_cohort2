import os
import sys
import time
import re
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
except Exception:
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
from individual.CaoVanHao_2A202600874.src.task5_semantic_search import semantic_search
from individual.CaoVanHao_2A202600874.src.task10_generation import (
    SYSTEM_PROMPT, TEMPERATURE, TOP_P, format_context, reorder_for_llm, generate_offline_fallback
)
from google import genai
from google.genai import types

# =============================================================================
# STREAMLIT PAGE CONFIGURATION
# =============================================================================
st.set_page_config(
    page_title="Drug Law Conversational RAG Chatbot",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CUSTOM CSS INJECTION FOR PREMIUM AESTHETICS & MICRO-ANIMATIONS
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
    background: linear-gradient(135deg, #070913 0%, #0f1328 50%, #161936 100%) !important;
    color: #f1f5f9 !important;
}

/* Sidebar Custom Styling */
[data-testid="stSidebar"] {
    background-color: #070914 !important;
    border-right: 1px solid rgba(99, 102, 241, 0.15);
}

/* Header/Title Container */
.header-container {
    background: rgba(15, 23, 42, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 24px;
    padding: 1.5rem 2rem;
    margin-bottom: 2rem;
    backdrop-filter: blur(12px);
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.4);
}

.title-gradient {
    background: linear-gradient(to right, #6366f1, #a855f7, #ec4899);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.8rem;
    font-weight: 800;
    letter-spacing: -1px;
}

/* Custom Styled Sidebar Cards */
.sidebar-card {
    background: rgba(30, 41, 59, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    padding: 12px 16px;
    margin-bottom: 12px;
}

/* Chat Bubbles Container Alignment */
.chat-message-user {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 1.2rem;
    animation: fadeInRight 0.4s ease;
}
.chat-bubble-user {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
    color: white;
    padding: 14px 20px;
    border-radius: 24px 24px 4px 24px;
    max-width: 70%;
    box-shadow: 0 4px 20px rgba(79, 70, 229, 0.25);
    font-size: 1.05rem;
    line-height: 1.5;
}

.chat-message-bot {
    display: flex;
    justify-content: flex-start;
    margin-bottom: 1.2rem;
    animation: fadeInLeft 0.4s ease;
}
.chat-bubble-bot {
    background: rgba(22, 27, 49, 0.55);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(99, 102, 241, 0.15);
    color: #e2e8f0;
    padding: 16px 22px;
    border-radius: 24px 24px 24px 4px;
    max-width: 80%;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    font-size: 1.05rem;
    line-height: 1.6;
}

/* Premium Citation Badge style */
.source-badge {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(168, 85, 247, 0.2) 100%);
    color: #a5b4fc;
    border: 1px solid rgba(99, 102, 241, 0.4);
    border-radius: 8px;
    padding: 2px 8px;
    font-size: 0.82rem;
    font-weight: 600;
    display: inline-block;
    margin: 2px 4px;
    box-shadow: 0 2px 8px rgba(99, 102, 241, 0.15);
}

/* Stat text styling */
.stat-label {
    color: #94a3b8;
    font-size: 0.85rem;
    font-weight: 500;
}
.stat-val {
    color: #f1f5f9;
    font-size: 1rem;
    font-weight: 700;
}

/* Glassmorphic Intro Container */
.intro-container {
    background: rgba(26, 32, 58, 0.35);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(99, 102, 241, 0.15);
    border-radius: 28px;
    padding: 2.5rem;
    margin-top: 1rem;
    margin-bottom: 2rem;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4);
}

/* Animations */
@keyframes fadeInLeft {
    from { opacity: 0; transform: translateX(-20px); }
    to { opacity: 1; transform: translateX(0); }
}
@keyframes fadeInRight {
    from { opacity: 0; transform: translateX(20px); }
    to { opacity: 1; transform: translateX(0); }
}

/* Quick Question Buttons styling overrides */
div.stButton > button {
    background: rgba(30, 41, 59, 0.3) !important;
    color: #e2e8f0 !important;
    border: 1px solid rgba(99, 102, 241, 0.2) !important;
    border-radius: 24px !important;
    padding: 10px 20px !important;
    font-size: 0.92rem !important;
    font-weight: 500 !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
div.stButton > button:hover {
    background: linear-gradient(135deg, #4f46e5 0%, #a855f7 100%) !important;
    color: white !important;
    border-color: transparent !important;
    box-shadow: 0 6px 20px rgba(124, 58, 237, 0.3) !important;
    transform: translateY(-3px) !important;
}

/* Code block customization */
code {
    background-color: rgba(30, 41, 59, 0.5) !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
    border-radius: 6px !important;
    color: #f43f5e !important;
    padding: 2px 6px !important;
    font-size: 0.9rem !important;
}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# CITATION HIGHLIGHTER ENGINE
# =============================================================================

def highlight_citations(text: str) -> str:
    """
    Tìm các thẻ trích dẫn dạng [Nguồn, Điều...] và thay bằng thẻ HTML badge sang trọng.
    Bỏ qua các liên kết Markdown thông thường dạng [text](link).
    """
    # Regex đảm bảo không match markdown links: tìm bracket mở không đi sau một bracket đóng,
    # và bracket đóng không đi trước một dấu ngoặc tròn mở.
    pattern = r'(?<!\])\[([^\]\(\)]+)\](?!\()'
    return re.sub(pattern, r"<span class='source-badge'>[\1]</span>", text)

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
    st.image("https://img.icons8.com/color/120/scales.png", width=65)
    st.markdown("<h2 style='margin:0; font-weight:800; font-size:1.45rem;'>COHORT 2 — RAG</h2>", unsafe_allow_html=True)
    st.markdown("<p class='stat-label' style='margin-bottom:1rem;'>Hệ thống tra cứu pháp lý & tin tức ma túy</p>", unsafe_allow_html=True)
    st.write("---")
    
    # API key indicators
    api_key = os.getenv("GEMINI_API_KEY", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")
    pageindex_key = os.getenv("PAGEINDEX_API_KEY", "")
    
    st.markdown("#### 🌐 **Trạng thái API**")
    if api_key:
        st.success("🟢 Gemini API: ONLINE")
    else:
        st.warning("🟡 Gemini API: OFFLINE")
        
    if pageindex_key and not pageindex_key.startswith("pi_"):
        st.success("🟢 PageIndex: ACTIVE")
    else:
        st.info("🔵 PageIndex: FALLBACK")
        
    st.write("---")
    
    # System stats card
    st.markdown("#### 📈 **RAG System Stats**")
    st.markdown(
        """
        <div class="sidebar-card">
            <span class="stat-label">Indexed Documents:</span> <span class="stat-val">8 files</span><br>
            <span class="stat-label">Total Text Chunks:</span> <span class="stat-val">55 chunks</span><br>
            <span class="stat-label">Embedding Dim:</span> <span class="stat-val">384 (MiniLM)</span><br>
            <span class="stat-label">Indexer Status:</span> <span class="stat-val" style="color:#10b981;">100% Synced</span>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Indexed Documents List Card
    st.markdown("#### 📂 **Tài liệu đã Vector hóa**")
    st.markdown(
        """
        <div class="sidebar-card" style="font-size:0.85rem; line-height:1.4;">
            ⚖️ <b>Văn bản pháp luật (3):</b>
            <ul style="margin:4px 0 8px 12px; padding:0;">
                <li>Bộ luật Hình sự 2015 (Chương XX)</li>
                <li>Luật Phòng, chống ma túy 2021</li>
                <li>Nghị định 105/2021/NĐ-CP</li>
            </ul>
            📰 <b>Tin tức báo chí (5):</b>
            <ul style="margin:4px 0 0 12px; padding:0;">
                <li>Chi Dân / An Tây / Trúc Phương</li>
                <li>Diễn viên hài Hữu Tín</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.write("---")
    
    # Quick clear button
    if st.button("🧹 Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
        
    # Team members info
    st.markdown("<p class='stat-label' style='text-align:center; margin-top:20px;'>Được phát triển bởi: <br><b>Cao Văn Hảo — 2A202600874</b></p>", unsafe_allow_html=True)

# =============================================================================
# MAIN INTERFACE
# =============================================================================
st.markdown(
    """
    <div class="header-container">
        <div style="display:flex; align-items:center; gap:15px;">
            <img src="https://img.icons8.com/color/120/scales.png" width="55" />
            <div>
                <span class="title-gradient">Drug Law Conversational RAG</span>
                <p style="margin:4px 0 0 0; color:#94a3b8; font-size:1.1rem;">Hỏi đáp thông minh về Luật ma túy & Hồ sơ nghệ sĩ vi phạm pháp luật</p>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Render introductory screen if no message history
if not st.session_state.messages:
    st.markdown(
        """
        <div class="intro-container">
            <h3 style="margin-top:0; color:#818cf8; font-weight:700;">👋 Chào mừng bạn đến với RAG Chatbot!</h3>
            <p>Hệ thống tích hợp kỹ thuật <b>Hybrid Search (Dense + Sparse)</b>, chấm điểm lại ứng viên bằng <b>Reranking</b>, kết hợp cơ chế <b>PageIndex fallback</b> ngoại tuyến và mô hình ngôn ngữ lớn <b>Gemini 2.5 Flash</b> để đưa ra câu trả lời chuẩn xác nhất kèm trích dẫn văn bản luật đối chiếu.</p>
            <div style="margin-top:20px; display:flex; gap:30px;">
                <div>
                    <h5 style="color:#a855f7; margin-bottom:5px; font-weight:600;">⚡ Hybrid Retrieval</h5>
                    <span class="stat-label">Kết hợp thế mạnh tìm kiếm từ khóa chính xác BM25 và độ hiểu ngữ nghĩa của Vector Embeddings.</span>
                </div>
                <div>
                    <h5 style="color:#ec4899; margin-bottom:5px; font-weight:600;">📚 Citation Badges</h5>
                    <span class="stat-label">Hỗ trợ trích dẫn nguồn văn bản rõ ràng đến từng Điều, Khoản của Luật hoặc đầu báo.</span>
                </div>
                <div>
                    <h5 style="color:#3b82f6; margin-bottom:5px; font-weight:600;">🔄 Conversational RAG</h5>
                    <span class="stat-label">Hỏi tiếp nối tự nhiên nhờ cơ chế Query Rewriting tự động viết lại câu hỏi theo ngữ cảnh chat.</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# Sample questions grid
st.markdown("#### 💡 **Câu hỏi gợi ý hỏi nhanh:**")
col1, col2, col3 = st.columns(3)
quick_q = None

with col1:
    if st.button("⚖️ Hình phạt tàng trữ ma túy theo Điều 249?"):
        quick_q = "Hình phạt cho tội tàng trữ trái phép chất ma tuý theo Điều 249 Bộ luật Hình sự?"
with col2:
    if st.button("📰 Ca sĩ Chi Dân & An Tây bị truy tố tội gì?"):
        quick_q = "Ca sĩ Chi Dân và người mẫu An Tây bị truy tố về những tội danh gì?"
with col3:
    if st.button("🏥 Có các hình thức cai nghiện nào theo luật 2021?"):
        quick_q = "Luật Phòng chống ma tuý 2021 quy định những hình thức cai nghiện nào?"

st.write("---")

# Render Chat History
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f"""
        <div class="chat-message-user">
            <div class="chat-bubble-user">{message["content"]}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Highlight citations in bot response to render nice badges
        highlighted_answer = highlight_citations(message["content"])
        
        st.markdown(f"""
        <div class="chat-message-bot">
            <div class="chat-bubble-bot">{highlighted_answer}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Display sources if any for this assistant response
        if "sources" in message and message["sources"]:
            with st.expander("📚 Nguồn thông tin đối chiếu (%d tài liệu được dùng)" % len(message["sources"])):
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
    user_input = st.chat_input("Nhập câu hỏi của bạn tại đây về Luật ma túy hoặc tin tức nghệ sĩ...")

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
        
    # 3. Highlight citations in bot response
    highlighted_answer = highlight_citations(result["answer"])
    
    # Display Bot Response
    st.markdown(f"""
    <div class="chat-message-bot">
        <div class="chat-bubble-bot">{highlighted_answer}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 4. Display sources in expander
    if result["sources"]:
        with st.expander("📚 Nguồn thông tin đối chiếu (%d tài liệu được dùng)" % len(result["sources"])):
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
