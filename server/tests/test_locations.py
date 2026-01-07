"""
Tests for location endpoints.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_location_admin(client: AsyncClient, admin_user):
    """Test creating a location as admin."""
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"person_id": "ADMIN1"},
    )
    token = login_response.json()["access_token"]
    
    response = await client.post(
        "/api/v1/locations",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "New Location",
            "address": "456 Test Ave",
            "active": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Location"


@pytest.mark.asyncio
async def test_create_location_supervisor_forbidden(client: AsyncClient, supervisor_user):
    """Test that supervisors cannot create locations."""
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"person_id": "SUPER1"},
    )
    token = login_response.json()["access_token"]
    
    response = await client.post(
        "/api/v1/locations",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "New Location",
            "address": "456 Test Ave",
            "active": True,
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_locations(client: AsyncClient, admin_user, test_location):
    """Test listing locations."""
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"person_id": "ADMIN1"},
    )
    token = login_response.json()["access_token"]
    
    response = await client.get(
        "/api/v1/locations",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0



