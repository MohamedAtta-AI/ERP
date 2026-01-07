"""
Tests for person/employee endpoints.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_persons_admin(client: AsyncClient, admin_user):
    """Test listing persons as admin."""
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"person_id": "ADMIN1"},
    )
    token = login_response.json()["access_token"]
    
    response = await client.get(
        "/api/v1/persons",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_person(client: AsyncClient, admin_user):
    """Test getting a specific person."""
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"person_id": "ADMIN1"},
    )
    token = login_response.json()["access_token"]
    
    response = await client.get(
        f"/api/v1/persons/{admin_user.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["person_id"] == "ADMIN1"


@pytest.mark.asyncio
async def test_list_persons_supervisor(client: AsyncClient, supervisor_user, worker_user):
    """Test listing persons as supervisor (should see own workers)."""
    # Set supervisor relationship
    worker_user.supervisor_id = supervisor_user.id
    await supervisor_user.awaitable_attrs.session.commit()
    
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"person_id": "SUPER1"},
    )
    token = login_response.json()["access_token"]
    
    response = await client.get(
        "/api/v1/persons",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)



