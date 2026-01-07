"""
Tests for payroll endpoints.
"""
import pytest
from httpx import AsyncClient
from datetime import date


@pytest.mark.asyncio
async def test_create_payroll_period_admin(client: AsyncClient, admin_user):
    """Test creating a payroll period as admin."""
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"person_id": "ADMIN1"},
    )
    token = login_response.json()["access_token"]
    
    response = await client.post(
        "/api/v1/payroll/periods",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "period_type": "monthly",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["period_type"] == "monthly"


@pytest.mark.asyncio
async def test_list_payroll_periods(client: AsyncClient, admin_user):
    """Test listing payroll periods."""
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"person_id": "ADMIN1"},
    )
    token = login_response.json()["access_token"]
    
    response = await client.get(
        "/api/v1/payroll/periods",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)



