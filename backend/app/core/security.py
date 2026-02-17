"""
Security utilities for JWT authentication and password hashing.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.config import settings
from db.session import get_db
from models.token_blacklist import TokenBlacklist


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def create_token(data: dict, token_type: str = "access") -> str:
    """
    Create a JWT token.
    
    Args:
        data: Data to encode in the token
        token_type: Either "access" or "refresh"
    
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if token_type == "access":
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.jwt_access_token_expire_minutes
        )
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.jwt_refresh_token_expire_days
        )
    
    to_encode.update({
        "exp": expire,
        "type": token_type,
        "iat": datetime.now(timezone.utc)
    })
    
    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )


def create_access_token(user_id: int, email: str, role: str) -> str:
    """Create an access token for a user."""
    return create_token({
        "sub": str(user_id),
        "email": email,
        "role": role
    }, token_type="access")


def create_refresh_token(user_id: int) -> str:
    """Create a refresh token for a user."""
    return create_token({
        "sub": str(user_id)
    }, token_type="refresh")


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT token.
    
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Dependency to get the current authenticated user from JWT token.
    Returns a dict with user info from the token.
    """
    payload = decode_token(token)

    # Check if token is blacklisted
    result = await db.execute(
        select(TokenBlacklist).where(TokenBlacklist.token == token)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_type = payload.get("type")
    if token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "id": int(user_id),
        "email": payload.get("email"),
        "role": payload.get("role")
    }


async def get_current_active_user(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Dependency to ensure the current user is active."""
    # In a full implementation, you would check the database
    # For now, we trust the token
    return current_user


def require_role(*allowed_roles: str):
    """
    Dependency factory to require specific roles.
    
    Usage:
        @router.get("/admin")
        async def admin_endpoint(user=Depends(require_role("admin"))):
            ...
    """
    async def role_checker(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user['role']}' not authorized for this action"
            )
        return user
    return role_checker


def require_admin():
    """Require admin role."""
    return require_role("admin")


def require_manager_or_admin():
    """Require manager or admin role."""
    return require_role("admin", "manager")
