"""
RAG (Retrieval-Augmented Generation) service for building context from vector store.
"""

import os
from typing import List, Dict, Any
from pathlib import Path

import faiss
import pickle
from sentence_transformers import SentenceTransformer

from core.config import settings
from core.logging import get_logger

logger = get_logger(__name__)


class RAGService:
    """
    Service for retrieval-augmented generation.
    Handles document retrieval, context building, and relevance filtering.
    """
    
    def __init__(self):
        self._model: SentenceTransformer | None = None
        self._index: faiss.Index | None = None
        self._documents: List[Dict[str, Any]] = []
        self._initialized = False
    
    @property
    def model(self) -> SentenceTransformer:
        """Lazy load embedding model."""
        if self._model is None:
            logger.info("Loading embedding model", model=settings.embedding_model)
            self._model = SentenceTransformer(settings.embedding_model)
        return self._model
    
    def initialize(self) -> None:
        """Load the FAISS index and documents from disk."""
        if self._initialized:
            return
        
        vector_store_path = Path(settings.vector_store_path)
        index_path = vector_store_path / "index.faiss"
        docs_path = vector_store_path / "docs.pkl"
        
        try:
            if index_path.exists() and docs_path.exists():
                self._index = faiss.read_index(str(index_path))
                with open(docs_path, "rb") as f:
                    self._documents = pickle.load(f)
                self._initialized = True
                logger.info(
                    "RAG service initialized",
                    num_documents=len(self._documents),
                    index_size=self._index.ntotal if self._index else 0
                )
            else:
                logger.warning(
                    "Vector store files not found",
                    index_path=str(index_path),
                    docs_path=str(docs_path)
                )
                # Create empty index
                self._index = faiss.IndexFlatL2(384)  # Default dimension for MiniLM
                self._documents = []
                self._initialized = True
        except Exception as e:
            logger.error("Failed to initialize RAG service", error=str(e))
            raise
    
    def semantic_search(
        self,
        query: str,
        top_k: int | None = None,
        department: str | None = None,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search on the document index.
        
        Args:
            query: Search query
            top_k: Number of results to return
            department: Filter by department (optional)
            min_score: Minimum relevance score threshold
        
        Returns:
            List of relevant documents with scores
        """
        if not self._initialized:
            self.initialize()
        
        if not self._index or self._index.ntotal == 0:
            logger.warning("Search attempted on empty index")
            return []
        
        top_k = top_k or settings.vector_search_top_k
        
        # Encode query
        query_embedding = self.model.encode([query])
        
        # Search
        distances, indices = self._index.search(query_embedding, min(top_k * 2, self._index.ntotal))
        
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < 0 or idx >= len(self._documents):
                continue
            
            doc = self._documents[idx]
            
            # Convert L2 distance to similarity score (0-1)
            # Lower distance = higher similarity
            score = 1 / (1 + dist)
            
            if score < min_score:
                continue
            
            # Department filtering
            if department and department != "*":
                doc_dept = doc.get("department", "public")
                if doc_dept not in [department, "public", "general"]:
                    continue
            
            results.append({
                "content": doc.get("content", doc) if isinstance(doc, dict) else doc,
                "title": doc.get("title", f"Document {idx}") if isinstance(doc, dict) else f"Document {idx}",
                "department": doc.get("department", "public") if isinstance(doc, dict) else "public",
                "source": doc.get("source", "unknown") if isinstance(doc, dict) else "unknown",
                "score": score,
                "index": idx
            })
            
            if len(results) >= top_k:
                break
        
        return results
    
    def format_context(
        self,
        results: List[Dict[str, Any]],
        max_tokens: int = 2000
    ) -> str:
        """
        Format search results into a context string for the LLM.
        
        Args:
            results: List of search results from semantic_search
            max_tokens: Approximate max tokens for context

        Returns:
            Formatted context string
        """
        if not results:
            return "No relevant documents found."
        
        context_parts = []
        total_chars = 0
        max_chars = max_tokens * 4  # Rough approximation
        
        for i, doc in enumerate(results, 1):
            content = doc["content"]
            title = doc["title"]
            score = doc["score"]
            
            # Truncate if needed
            if len(content) > 1000:
                content = content[:1000] + "..."
            
            part = f"[Document {i}: {title}] (relevance: {score:.2f})\n{content}\n"
            
            if total_chars + len(part) > max_chars:
                break
            
            context_parts.append(part)
            total_chars += len(part)
        
        return "\n".join(context_parts)

    def build_context(
        self,
        query: str,
        department: str | None = None,
        max_tokens: int = 2000
    ) -> str:
        """
        Build a context string for the LLM from relevant documents.

        Args:
            query: User query
            department: User's department for filtering
            max_tokens: Approximate max tokens for context

        Returns:
            Formatted context string
        """
        results = self.semantic_search(query, department=department)
        return self.format_context(results, max_tokens)
    
    def add_documents(
        self,
        documents: List[Dict[str, Any]],
        save: bool = True
    ) -> int:
        """
        Add new documents to the index.
        
        Args:
            documents: List of documents with 'content' field
            save: Whether to save to disk
        
        Returns:
            Number of documents added
        """
        if not self._initialized:
            self.initialize()
        
        if not documents:
            return 0
        
        # Extract content and create embeddings
        contents = [doc.get("content", str(doc)) for doc in documents]
        embeddings = self.model.encode(contents)
        
        # Create index if needed
        if self._index is None:
            dim = embeddings.shape[1]
            self._index = faiss.IndexFlatL2(dim)
        
        # Add to index
        self._index.add(embeddings)
        self._documents.extend(documents)
        
        if save:
            self._save_to_disk()
        
        logger.info("Documents added to index", count=len(documents))
        return len(documents)
    
    def _save_to_disk(self) -> None:
        """Save the index and documents to disk."""
        vector_store_path = Path(settings.vector_store_path)
        vector_store_path.mkdir(parents=True, exist_ok=True)
        
        faiss.write_index(self._index, str(vector_store_path / "index.faiss"))
        with open(vector_store_path / "docs.pkl", "wb") as f:
            pickle.dump(self._documents, f)
        
        logger.info("Vector store saved to disk")


# Global RAG service instance
rag_service = RAGService()


def build_context(query: str, department: str | None = None) -> str:
    """Convenience function for building context."""
    return rag_service.build_context(query, department)
