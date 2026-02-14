"""
Admin API endpoints for user management and system monitoring.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from core.security import require_role, get_password_hash, get_current_user
from db.session import get_db
from models.user import User
from models.audit_log import AuditLog
from schemas.user import UserResponse, UserUpdate, UserListResponse, UserCreate

router = APIRouter(prefix="/admin", tags=["Admin"])


# ============== User Management ==============

@router.get("/users", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    department: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "manager")),
):
    """
    List all users with pagination and filters (admin/manager only).
    """
    query = select(User)
    
    # Apply filters
    if department:
        query = query.where(User.department == department)
    if role:
        query = query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    
    # Pagination
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(User.created_at.desc())
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    return UserListResponse(
        users=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin", "manager")),
):
    """
    Get a specific user by ID (admin/manager only).
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin")),
):
    """
    Create a new user (admin only).
    """
    # Check if email exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        department=user_data.department,
        role=user_data.role.value,
        is_verified=True,  # Admin-created users are pre-verified
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin")),
):
    """
    Update a user (admin only).
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields
    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            if field == "role":
                setattr(user, field, value.value)
            else:
                setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_role("admin")),
):
    """
    Delete a user (admin only). Cannot delete yourself.
    """
    if user_id == current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    await db.delete(user)
    await db.commit()


# ============== Audit Logs ==============

@router.get("/audit-logs")
async def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    user_id: int | None = None,
    action_type: str | None = None,
    tool_name: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin")),
):
    """
    Get audit logs with pagination and filters (admin only).
    """
    query = select(AuditLog)
    
    # Apply filters
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if action_type:
        query = query.where(AuditLog.action_type == action_type)
    if tool_name:
        query = query.where(AuditLog.tool_name == tool_name)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    
    # Pagination and ordering
    query = query.order_by(desc(AuditLog.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return {
        "logs": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action_type": log.action_type,
                "tool_name": log.tool_name,
                "query": log.query[:200] if log.query else None,
                "success": log.success,
                "execution_time_ms": log.execution_time_ms,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# ============== System Stats ==============

@router.get("/stats")
async def get_system_stats(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_role("admin")),
):
    """
    Get system statistics (admin only).
    """
    # User counts
    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    active_users = (await db.execute(
        select(func.count(User.id)).where(User.is_active == True)
    )).scalar() or 0
    
    # Audit log counts
    total_queries = (await db.execute(
        select(func.count(AuditLog.id)).where(AuditLog.action_type == "tool_execution")
    )).scalar() or 0
    
    # Tool usage
    tool_usage = await db.execute(
        select(AuditLog.tool_name, func.count(AuditLog.id))
        .where(AuditLog.tool_name.isnot(None))
        .group_by(AuditLog.tool_name)
    )
    
    return {
        "users": {
            "total": total_users,
            "active": active_users,
        },
        "queries": {
            "total": total_queries,
        },
        "tool_usage": {row[0]: row[1] for row in tool_usage.all()},
    }
