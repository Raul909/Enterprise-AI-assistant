from typing import Optional, Any

from sqlalchemy import String, Text, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base

class Document(Base):
    """Document model for RAG content."""

    __tablename__ = "documents"

    # We use vector_id to map to FAISS index.
    # FAISS indices are usually 0-based integers.
    vector_id: Mapped[int] = mapped_column(Integer, index=True, unique=True)

    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    department: Mapped[str] = mapped_column(String(100), default="general")
    source: Mapped[str] = mapped_column(String(255), nullable=True)

    # Store additional metadata as JSON if needed
    metadata_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "vector_id": self.vector_id,
            "title": self.title,
            "content": self.content,
            "department": self.department,
            "source": self.source,
            "created_at": self.created_at
        }
