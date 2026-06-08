import os
import sys
import re
from pathlib import Path
from dotenv import load_dotenv

# Setup project root and Python path to import tasks from CaoVanHao_2A202600874
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# Load dotenv from student individual folder
student_env_path = PROJECT_ROOT / "individual" / "CaoVanHao_2A202600874" / ".env"
load_dotenv(dotenv_path=student_env_path)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# Import RAG pipeline functions from individual tasks
from individual.CaoVanHao_2A202600874.src.task9_retrieval_pipeline import retrieve
from individual.CaoVanHao_2A202600874.src.task5_semantic_search import semantic_search
from individual.CaoVanHao_2A202600874.src.task10_generation import (
    SYSTEM_PROMPT, TEMPERATURE, TOP_P, format_context, reorder_for_llm, generate_offline_fallback
)
from google import genai
from google.genai import types

# Initialize FastAPI app
app = FastAPI(
    title="Drug Law RAG Chatbot API",
    description="Backend API for Drug Law Conversational RAG Chatbot",
    version="1.0.0"
)

# Enable CORS so frontend (usually at port 5173) can communicate with backend (port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request and Response schemas
class ChatMessage(BaseModel):
    role: str # 'user' or 'assistant'
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage]
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    standalone_query: str
    sources: List[Dict[str, Any]]

# Query rewriting helper
def rewrite_query_with_history(query: str, chat_history: List[ChatMessage], api_key: str) -> str:
    if not chat_history:
        return query
        
    history_str = ""
    # Get last 4 messages to avoid context overflow
    for msg in chat_history[-4:]:
        role = "User" if msg.role == "user" else "Assistant"
        history_str += f"{role}: {msg.content}\n"
        
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
            if rewritten:
                return rewritten
        except Exception as e:
            print(f"Error during query rewriting: {e}", file=sys.stderr)
            
    return query

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    api_key = request.gemini_api_key or os.getenv("GEMINI_API_KEY", "")
    openai_key = request.openai_api_key or os.getenv("OPENAI_API_KEY", "")
    
    # 1. Rewrite query with conversational context
    standalone_query = rewrite_query_with_history(request.message, request.history, api_key)
    
    # 2. Retrieve top 5 relevant document chunks
    try:
        chunks = retrieve(standalone_query, top_k=5)
    except Exception as e:
        print(f"Error retrieving documents: {e}", file=sys.stderr)
        chunks = []
        
    # 3. Format context
    reordered_chunks = reorder_for_llm(chunks)
    context = format_context(reordered_chunks)
    
    # 4. Generate response using LLM (Gemini -> OpenAI -> Offline Fallback)
    user_message = f"Context:\n{context}\n\n---\n\nQuestion: {request.message}"
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
            print(f"Gemini API generation failed, trying OpenAI: {e}", file=sys.stderr)
            
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
            print(f"OpenAI API generation failed: {e}", file=sys.stderr)
            
    if not answer:
        # Generate offline fallback
        answer = generate_offline_fallback(request.message, chunks)
        
    return ChatResponse(
        answer=answer,
        standalone_query=standalone_query,
        sources=chunks
    )

@app.get("/api/stats")
async def stats_endpoint():
    api_key = os.getenv("GEMINI_API_KEY", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")
    pageindex_key = os.getenv("PAGEINDEX_API_KEY", "")
    
    return {
        "status": {
            "gemini": "ONLINE" if api_key else "OFFLINE",
            "openai": "ONLINE" if openai_key else "OFFLINE",
            "pageindex": "ACTIVE" if (pageindex_key and not pageindex_key.startswith("pi_")) else "FALLBACK"
        },
        "stats": {
            "indexed_documents": 8,
            "total_chunks": 55,
            "embedding_dimension": 384,
            "indexer_status": "100% Synced"
        },
        "vectorized_documents": {
            "legal": [
                "Bộ luật Hình sự 2015 (Chương XX)",
                "Luật Phòng, chống ma túy 2021",
                "Nghị định 105/2021/NĐ-CP"
            ],
            "news": [
                "Chi Dân / An Tây / Trúc Phương (Tin tức ma túy)",
                "Diễn viên hài Hữu Tín (Tin tức ma túy)"
            ]
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
