"""
Semantic search over the vector store.
"""

import os
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional

import faiss
from sentence_transformers import SentenceTransformer


# Configuration
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
VECTOR_STORE_PATH = Path(os.getenv("VECTOR_STORE_PATH", "."))
TOP_K = int(os.getenv("VECTOR_SEARCH_TOP_K", "5"))


# Lazy-loaded globals
_model: Optional[SentenceTransformer] = None
_index: Optional[faiss.Index] = None
_docs: Optional[List[Dict[str, Any]]] = None


def _load_resources():
    """Load model and index if not already loaded."""
    global _model, _index, _docs
    
    if _model is None:
        print(f"Loading embedding model: {EMBEDDING_MODEL}")
        _model = SentenceTransformer(EMBEDDING_MODEL)
    
    if _index is None:
        index_path = VECTOR_STORE_PATH / "index.faiss"
        docs_path = VECTOR_STORE_PATH / "docs.pkl"
        
        if index_path.exists() and docs_path.exists():
            print(f"Loading index from {index_path}")
            _index = faiss.read_index(str(index_path))
            with open(docs_path, "rb") as f:
                _docs = pickle.load(f)
            print(f"Loaded {_index.ntotal} vectors and {len(_docs)} documents")
        else:
            print("Warning: Vector store not found, creating empty index")
            _index = faiss.IndexFlatL2(384)  # Default dimension for MiniLM
            _docs = []


def semantic_search(
    query: str,
    department: Optional[str] = None,
    top_k: int = TOP_K,
    min_score: float = 0.0
) -> List[Dict[str, Any]]:
    """
    Perform semantic search on the vector store.
    
    Args:
        query: Search query
        department: Optional department filter
        top_k: Number of results to return
        min_score: Minimum similarity score (0-1)
    
    Returns:
        List of matching documents with scores
    """
    _load_resources()
    
    if _index is None or _index.ntotal == 0:
        return []
    
    # Encode query
    query_embedding = _model.encode([query])
    
    # Search (get more than needed for filtering)
    search_k = min(top_k * 3, _index.ntotal)
    distances, indices = _index.search(query_embedding, search_k)
    
    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx < 0 or idx >= len(_docs):
            continue
        
        doc = _docs[idx]
        
        # Convert L2 distance to similarity score
        # Lower distance = higher similarity
        score = 1 / (1 + dist)
        
        if score < min_score:
            continue
        
        # Department filtering
        if department and department.lower() != "all":
            doc_dept = doc.get("department", "general").lower()
            allowed_depts = ["public", "general", department.lower()]
            if doc_dept not in allowed_depts:
                continue
        
        results.append({
            "content": doc.get("content", ""),
            "title": doc.get("title", "Untitled"),
            "department": doc.get("department", "general"),
            "source": doc.get("source", "unknown"),
            "score": round(score, 4),
            "index": int(idx)
        })
        
        if len(results) >= top_k:
            break
    
    return results


def search_by_embedding(
    embedding: List[float],
    top_k: int = TOP_K
) -> List[Dict[str, Any]]:
    """
    Search using a pre-computed embedding vector.
    
    Args:
        embedding: Query embedding vector
        top_k: Number of results
    
    Returns:
        List of matching documents
    """
    _load_resources()
    
    if _index is None or _index.ntotal == 0:
        return []
    
    import numpy as np
    query_vector = np.array([embedding], dtype=np.float32)
    
    distances, indices = _index.search(query_vector, top_k)
    
    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx < 0 or idx >= len(_docs):
            continue
        
        doc = _docs[idx]
        score = 1 / (1 + dist)
        
        results.append({
            **doc,
            "score": round(score, 4),
            "index": int(idx)
        })
    
    return results


def get_document_count() -> int:
    """Get total number of documents in the index."""
    _load_resources()
    return len(_docs) if _docs else 0


def get_index_stats() -> Dict[str, Any]:
    """Get statistics about the vector store."""
    _load_resources()
    
    if _index is None:
        return {"status": "not_initialized"}
    
    departments = {}
    if _docs:
        for doc in _docs:
            dept = doc.get("department", "unknown")
            departments[dept] = departments.get(dept, 0) + 1
    
    return {
        "total_vectors": _index.ntotal if _index else 0,
        "total_documents": len(_docs) if _docs else 0,
        "departments": departments,
        "embedding_dimension": _index.d if _index else 0
    }


# Example usage
if __name__ == "__main__":
    # Test search
    results = semantic_search("vacation policy", top_k=3)
    
    print("\nSearch Results:")
    for r in results:
        print(f"\n[{r['score']:.3f}] {r['title']}")
        print(f"  Department: {r['department']}")
        print(f"  Content: {r['content'][:100]}...")
