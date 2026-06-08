"""
Task 4 — Chunking & Indexing vào Vector Store.

Hướng dẫn:
    1. Đọc toàn bộ markdown files từ data/standardized/
    2. Chọn 1 chunking strategy (giải thích lý do)
    3. Chọn 1 embedding model (giải thích lý do)
    4. Index vào vector store (Weaviate khuyến cáo)

Chunking options (langchain-text-splitters):
    - RecursiveCharacterTextSplitter: an toàn, phổ biến
    - MarkdownHeaderTextSplitter: tốt cho file có heading
    - SemanticChunker: dùng embedding để tách (nâng cao)

Embedding model options:
    - sentence-transformers/all-MiniLM-L6-v2 (384 dim, nhẹ)
    - BAAI/bge-m3 (1024 dim, multilingual, tốt cho tiếng Việt)
    - OpenAI text-embedding-3-small (1536 dim, API)

Vector store options:
    - Weaviate (khuyến cáo: hỗ trợ hybrid search built-in)
    - ChromaDB (đơn giản, local)
    - FAISS (chỉ dense search)

Cài đặt:
    pip install langchain-text-splitters sentence-transformers weaviate-client
"""

from pathlib import Path

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"


# =============================================================================
# CONFIGURATION — Giải thích lựa chọn của bạn trong comment
# =============================================================================

# TODO: Chọn chunking strategy và giải thích vì sao
CHUNK_SIZE = 1000       # Chọn 1000 để chứa trọn vẹn ngữ cảnh của một đoạn văn/một khoản luật
CHUNK_OVERLAP = 100     # Chọn 100 để không làm đứt gãy câu giữa các chunk kế tiếp nhau
CHUNKING_METHOD = "recursive"  # Dùng recursive vì nó tách theo cấp độ đoạn văn -> câu -> từ một cách tự nhiên

# TODO: Chọn embedding model và giải thích
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # Máy bạn đang bị đầy ổ cứng (chỉ còn 300MB trống), model bge-m3 cần tới 2.2GB nên không thể tải. Chuyển sang dùng MiniLM chỉ nặng 90MB.
EMBEDDING_DIM = 384

# TODO: Chọn vector store
VECTOR_STORE = "chromadb"  # Chọn ChromaDB vì nó chạy local bằng SQLite dễ dàng trên Windows không cần Docker.


# =============================================================================
# IMPLEMENTATION
# =============================================================================

def load_documents() -> list[dict]:
    """
    Đọc toàn bộ markdown files từ data/standardized/.

    Returns:
        List of {'content': str, 'metadata': {'source': str, 'type': str}}
    """
    documents = []
    for md_file in STANDARDIZED_DIR.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        doc_type = "legal" if "legal" in str(md_file) else "news"
        documents.append({
            "content": content,
            "metadata": {"source": md_file.name, "type": doc_type}
        })
    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """
    Chunk documents theo strategy đã chọn.

    Returns:
        List of {'content': str, 'metadata': dict} — mỗi item là 1 chunk
    """
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = []
    for doc in documents:
        splits = splitter.split_text(doc["content"])
        for i, chunk_text in enumerate(splits):
            chunks.append({
                "content": chunk_text,
                "metadata": {**doc["metadata"], "chunk_index": i}
            })
    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """
    Embed toàn bộ chunks bằng model đã chọn.

    Returns:
        Mỗi chunk dict được thêm key 'embedding': list[float]
    """
    from sentence_transformers import SentenceTransformer
    
    model = SentenceTransformer(EMBEDDING_MODEL)
    texts = [c["content"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True)
    for chunk, emb in zip(chunks, embeddings):
        chunk["embedding"] = emb.tolist()
    return chunks


def index_to_vectorstore(chunks: list[dict]):
    """
    Lưu chunks vào vector store đã chọn.
    """
    import chromadb
    
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_or_create_collection(name="drug_law_docs")
    
    ids = [f"{chunk['metadata']['source']}_chunk_{chunk['metadata']['chunk_index']}" for chunk in chunks]
    embeddings = [chunk["embedding"] for chunk in chunks]
    metadatas = [chunk["metadata"] for chunk in chunks]
    documents = [chunk["content"] for chunk in chunks]
    
    # Insert chunks in batches (to avoid Chroma limits if large)
    batch_size = 5000
    for i in range(0, len(ids), batch_size):
        collection.upsert(
            ids=ids[i:i+batch_size],
            embeddings=embeddings[i:i+batch_size],
            metadatas=metadatas[i:i+batch_size],
            documents=documents[i:i+batch_size]
        )
    print(f"  - Indexed {len(chunks)} chunks into ChromaDB.")


def run_pipeline():
    """Chạy toàn bộ pipeline: load → chunk → embed → index."""
    print("=" * 50)
    print("Task 4: Chunking & Indexing")
    print(f"  Chunking: {CHUNKING_METHOD} (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    print(f"  Embedding: {EMBEDDING_MODEL} (dim={EMBEDDING_DIM})")
    print(f"  Vector Store: {VECTOR_STORE}")
    print("=" * 50)

    docs = load_documents()
    print(f"\n- Loaded {len(docs)} documents")

    chunks = chunk_documents(docs)
    print(f"- Created {len(chunks)} chunks")

    chunks = embed_chunks(chunks)
    print(f"- Embedded {len(chunks)} chunks")

    index_to_vectorstore(chunks)
    print("  - Done! Output at: ./chroma_db")


if __name__ == "__main__":
    run_pipeline()
