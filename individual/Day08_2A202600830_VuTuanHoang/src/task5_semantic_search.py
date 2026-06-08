"""
Task 5 — Semantic Search Module.

Viết module tìm kiếm ngữ nghĩa (dense retrieval) trên vector store.

Yêu cầu:
    - Input: query string + top_k
    - Output: danh sách chunks có score, sorted descending
    - Phải tương thích với embedding model và vector store ở Task 4
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import chromadb
from sentence_transformers import SentenceTransformer

# Load model global để không phải load lại mỗi khi gọi hàm search
try:
    print("Loading embedding model all-MiniLM-L6-v2...")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
except Exception as e:
    model = None
    print(f"Lỗi load model: {e}")

def semantic_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Tìm kiếm ngữ nghĩa sử dụng vector similarity với ChromaDB.
    """
    if model is None:
        return []

    # Bước 1: Embed query bằng cùng model ở Task 4
    query_embedding = model.encode(query).tolist()
    
    # Bước 2: Query vector store
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_collection(name="drug_law_docs")
    
    # ChromaDB trả về distance (thường là L2 hoặc cosine distance). 
    # Mặc định của Chroma là L2, nhưng ta có thể lấy ngược lại làm score.
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )
    
    # Bước 3: Return top_k results
    out = []
    if not results["documents"] or not results["documents"][0]:
        return out
        
    for i in range(len(results["documents"][0])):
        # Vì mặc định Chroma dùng L2 distance, distance càng nhỏ càng tốt.
        # Ở đây ta chuyển đổi một cách tương đối để distance nhỏ -> score cao.
        distance = results["distances"][0][i]
        score = 1.0 / (1.0 + distance)
        
        out.append({
            "content": results["documents"][0][i],
            "score": score,
            "metadata": results["metadatas"][0][i]
        })
    return out


if __name__ == "__main__":
    # Test
    query = "hình phạt cho tội tàng trữ ma tuý"
    print(f"\n--- Testing Semantic Search ---")
    print(f"Query: '{query}'\n")
    
    results = semantic_search(query, top_k=3)
    
    if not results:
        print("Không tìm thấy kết quả nào phù hợp.")
    else:
        for i, r in enumerate(results, 1):
            print(f"[{i}] Score: {r['score']:.3f} | Source: {r['metadata'].get('source', 'Unknown')}")
            # In ra 150 ký tự đầu tiên để preview
            content_preview = r['content'][:150].replace('\n', ' ')
            print(f"    Preview: {content_preview}...\n")
