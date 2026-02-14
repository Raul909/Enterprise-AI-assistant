"""
Audit log model for tracking tool executions and user actions.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class AuditLog(Base):
    """Audit log for tracking all tool executions and important user actions."""
    
    __tablename__ = "audit_logs"
    
    # Override id from Base
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    
    # User reference
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    
    # Action details
    action_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    tool_name: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    
    # Request/Response
    query: Mapped[str] = mapped_column(Text, nullable=False)
    response_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Metadata
    execution_time_ms: Mapped[float] = mapped_column(Float, default=0)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Context
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    # Timestamps (override to add index)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="audit_logs")
    
    def __repr__(self) -> str:
        return f"<AuditLog {self.id}: {self.action_type}>"


# Import here to avoid circular imports
from models.user import User  # noqa: E402, F401
