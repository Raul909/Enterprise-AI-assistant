"""
RAG (Retrieval-Augmented Generation) service for building context from vector store.
"""

import os
from typing import List, Dict, Any
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy import select

from core.config import settings
from core.logging import get_logger
from db.session import async_session_factory
from models.document import Document

logger = get_logger(__name__)


class RAGService:
    """
    Service for retrieval-augmented generation.
    Handles document retrieval, context building, and relevance filtering.
    """
    
    def __init__(self):
        self._model: SentenceTransformer | None = None
        self._index: faiss.Index | None = None
        self._initialized = False
    
    @property
    def model(self) -> SentenceTransformer:
        """Lazy load embedding model."""
        if self._model is None:
            logger.info("Loading embedding model", model=settings.embedding_model)
            self._model = SentenceTransformer(settings.embedding_model)
        return self._model
    
    async def initialize(self) -> None:
        """Load the FAISS index from disk."""
        if self._initialized:
            return
        
        vector_store_path = Path(settings.vector_store_path)
        index_path = vector_store_path / "index.faiss"
        docs_path = vector_store_path / "docs.pkl"
        
        try:
            if index_path.exists():
                self._index = faiss.read_index(str(index_path))
                self._initialized = True
                logger.info(
                    "RAG service initialized",
                    index_size=self._index.ntotal if self._index else 0
                )
            else:
                logger.warning(
                    "Vector store index not found",
                    index_path=str(index_path)
                )
                # Create empty index
                self._index = faiss.IndexFlatL2(384)  # Default dimension for MiniLM
                self._initialized = True
        except Exception as e:
            logger.error("Failed to initialize RAG service", error=str(e))
            raise
    
    async def semantic_search(
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
            await self.initialize()
        
        if not self._index or self._index.ntotal == 0:
            logger.warning("Search attempted on empty index")
            return []
        
        top_k = top_k or settings.vector_search_top_k
        
        # Encode query
        query_embedding = self.model.encode([query])
        
        # Search
        distances, indices = self._index.search(query_embedding, min(top_k * 2, self._index.ntotal))
        
        # indices[0] contains the vector_ids
        found_indices = [int(idx) for idx in indices[0] if idx >= 0]
        if not found_indices:
            return []
            
        # Map vector_id back to score/distance
        score_map = {}
        for dist, idx in zip(distances[0], indices[0]):
            if idx >= 0:
                # Convert L2 distance to similarity score (0-1)
                score = 1 / (1 + dist)
                score_map[int(idx)] = score

        # Fetch documents from DB
        results = []
        async with async_session_factory() as session:
            stmt = select(Document).where(Document.vector_id.in_(found_indices))
            db_docs = (await session.execute(stmt)).scalars().all()
            
            # Create a dict for O(1) lookup
            docs_by_id = {doc.vector_id: doc for doc in db_docs}
            
            # Maintain the order returned by FAISS
            for idx in found_indices:
                if idx not in docs_by_id:
                    continue

                doc = docs_by_id[idx]
                score = score_map.get(idx, 0.0)

                if score < min_score:
                    continue

                # Department filtering
                if department and department != "*":
                    doc_dept = doc.department
                    if doc_dept not in [department, "public", "general"]:
                        continue

                results.append({
                    "content": doc.content,
                    "title": doc.title,
                    "department": doc.department,
                    "source": doc.source,
                    "score": score,
                    "index": idx
                })

                if len(results) >= top_k:
                    break
        
        return results
    
    async def build_context(
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
        results = await self.semantic_search(query, department=department)
        
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
    
    async def add_documents(
        self,
        documents: List[Dict[str, Any]],
        save: bool = True
    ) -> int:
        """
        Add new documents to the index and database.
        
        Args:
            documents: List of documents with 'content' field
            save: Whether to save to disk
        
        Returns:
            Number of documents added
        """
        if not self._initialized:
            await self.initialize()
        
        if not documents:
            return 0
        
        # Extract content and create embeddings
        contents = [doc.get("content", str(doc)) for doc in documents]
        embeddings = self.model.encode(contents)
        
        # Create index if needed
        if self._index is None:
            dim = embeddings.shape[1]
            self._index = faiss.IndexFlatL2(dim)
        
        start_idx = self._index.ntotal

        # Add to index
        self._index.add(embeddings)

        # Add to DB
        async with async_session_factory() as session:
            for i, doc_data in enumerate(documents):
                vector_id = start_idx + i
                new_doc = Document(
                    vector_id=vector_id,
                    content=doc_data.get("content", str(doc_data)),
                    title=doc_data.get("title", f"Document {vector_id}"),
                    department=doc_data.get("department", "public"),
                    source=doc_data.get("source", "unknown"),
                    metadata_json=doc_data
                )
                session.add(new_doc)
            await session.commit()
        
        if save:
            self._save_to_disk()
        
        logger.info("Documents added to index", count=len(documents))
        return len(documents)
    
    def _save_to_disk(self) -> None:
        """Save the index to disk."""
        vector_store_path = Path(settings.vector_store_path)
        vector_store_path.mkdir(parents=True, exist_ok=True)
        
        if self._index:
            faiss.write_index(self._index, str(vector_store_path / "index.faiss"))
        
        logger.info("Vector store index saved to disk")


# Global RAG service instance
rag_service = RAGService()


# Note: This is async now
async def build_context(query: str, department: str | None = None) -> str:
    """Convenience function for building context."""
    return await rag_service.build_context(query, department)
