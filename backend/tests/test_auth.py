import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import os
import sys

# Add backend/app to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../app")))

from models.user import User

@pytest.mark.asyncio
async def test_register_login_logout(client: AsyncClient, db_session: AsyncSession):
    # Register
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User",
            "department": "Engineering",
            "role": "employee"
        }
    )
    assert register_response.status_code == 201

    # Login
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123"
        }
    )
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]

    # Verify access to protected route
    headers = {"Authorization": f"Bearer {access_token}"}
    me_response = await client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 200

    # Logout
    logout_response = await client.post("/api/v1/auth/logout", headers=headers)
    assert logout_response.status_code == 200

    # Verify access denied after logout
    me_response_revoked = await client.get("/api/v1/auth/me", headers=headers)
    assert me_response_revoked.status_code == 401
    assert "Token has been revoked" in me_response_revoked.json()["detail"]
