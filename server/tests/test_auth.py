"""
Tests for authentication endpoints.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, admin_user):
    """Test successful login."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"person_id": "ADMIN1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert "user" in data
    assert data["user"]["person_id"] == "ADMIN1"


@pytest.mark.asyncio
async def test_login_invalid_user(client: AsyncClient):
    """Test login with invalid user."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"person_id": "INVALID"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_me_endpoint(client: AsyncClient, admin_user):
    """Test /me endpoint with valid token."""
    # First login to get token
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"person_id": "ADMIN1"},
    )
    token = login_response.json()["access_token"]
    
    # Use token to access /me
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["person_id"] == "ADMIN1"


@pytest.mark.asyncio
async def test_me_endpoint_no_token(client: AsyncClient):
    """Test /me endpoint without token."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401

