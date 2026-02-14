"""
Pydantic schemas for user operations.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    """User roles for RBAC."""
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"


# ============== Request Schemas ==============

class UserCreate(BaseModel):
    """Schema for creating a new user."""
    
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str | None = Field(default=None, max_length=255)
    department: str | None = Field(default=None, max_length=100)
    role: UserRole = Field(default=UserRole.EMPLOYEE)


class UserUpdate(BaseModel):
    """Schema for updating a user (partial update allowed)."""
    
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, max_length=255)
    department: str | None = Field(default=None, max_length=100)
    role: UserRole | None = None
    is_active: bool | None = None


class UserUpdatePassword(BaseModel):
    """Schema for updating user password."""
    
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


# ============== Response Schemas ==============

class UserResponse(BaseModel):
    """Schema for user response (public data)."""
    
    id: int
    email: EmailStr
    full_name: str | None
    department: str | None
    role: UserRole
    is_active: bool
    is_verified: bool
    last_login: datetime | None
    created_at: datetime
    
    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    """Schema for paginated user list."""
    
    users: list[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============== Auth Schemas ==============

class LoginRequest(BaseModel):
    """Schema for login request."""
    
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Schema for login response."""
    
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """Schema for token refresh."""
    
    refresh_token: str


class TokenPayload(BaseModel):
    """Schema for JWT token payload."""
    
    sub: int  # user_id
    email: str
    role: str
    exp: datetime
    type: str  # "access" or "refresh"
