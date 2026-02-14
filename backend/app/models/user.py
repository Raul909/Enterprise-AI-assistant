"""
User model for authentication and role-based access control.
"""

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class UserRole(str, Enum):
    """User roles for RBAC."""
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"


class User(Base):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    # Override id from Base to add index
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    
    # Authentication
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Profile
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    department: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    
    # Role & Permissions
    role: Mapped[UserRole] = mapped_column(
        String(50), default=UserRole.EMPLOYEE, nullable=False
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timestamps
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="user", lazy="dynamic"
    )
    
    def __repr__(self) -> str:
        return f"<User {self.email}>"
    
    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == UserRole.ADMIN


# Import here to avoid circular imports
from models.audit_log import AuditLog  # noqa: E402, F401
