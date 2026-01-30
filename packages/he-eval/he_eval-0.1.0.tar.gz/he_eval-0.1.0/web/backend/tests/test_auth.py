"""Tests for authentication endpoints."""

import pytest
from httpx import AsyncClient

from app.models import User


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, regular_user: User):
    """Test successful login returns JWT token."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "user@test.com", "password": "user123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, regular_user: User):
    """Test login with wrong password fails."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "user@test.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Test login with nonexistent user fails."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@test.com", "password": "password"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_token_exchange(client: AsyncClient, regular_user: User):
    """Test exchanging code for API key."""
    # For now, the code is the user's email
    response = await client.post(
        "/api/v1/auth/token",
        json={"code": "user@test.com"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "api_key" in data
    assert data["api_key"].startswith("sk-")
    assert data["user_email"] == "user@test.com"
    assert data["user_name"] == "Test User"
    assert "expires_at" in data


@pytest.mark.asyncio
async def test_token_exchange_invalid_code(client: AsyncClient):
    """Test exchanging invalid code fails."""
    response = await client.post(
        "/api/v1/auth/token",
        json={"code": "invalid-code"},
    )
    assert response.status_code == 400
    assert "Invalid code" in response.json()["detail"]


@pytest.mark.asyncio
async def test_jwt_auth(client: AsyncClient, user_token: str, regular_user: User):
    """Test that JWT token works for authenticated endpoints."""
    response = await client.get(
        "/api/v1/assignments",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_api_key_auth(
    client: AsyncClient, user_api_key: str, regular_user: User
):
    """Test that API key works for authenticated endpoints."""
    response = await client.get(
        "/api/v1/assignments",
        headers={"Authorization": f"Bearer {user_api_key}"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_no_auth_fails(client: AsyncClient):
    """Test that unauthenticated requests fail."""
    response = await client.get("/api/v1/assignments")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_invalid_token_fails(client: AsyncClient):
    """Test that invalid token fails."""
    response = await client.get(
        "/api/v1/assignments",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401
