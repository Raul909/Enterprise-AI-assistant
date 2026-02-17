from datetime import datetime, timezone

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base

class TokenBlacklist(Base):
    """
    Model for blacklisted JWT tokens.
    Used to invalidate tokens on logout before their expiration.
    """
    __tablename__ = "token_blacklist"

    token: Mapped[str] = mapped_column(String, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    def __repr__(self):
        return f"<TokenBlacklist(token='{self.token[:10]}...', expires_at='{self.expires_at}')>"
