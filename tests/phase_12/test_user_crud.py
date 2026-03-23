"""Tests for user management API (AUTH-01)."""

import pytest
from tests.phase_12.conftest import get_admin_token, TEST_ADMIN_USER


@pytest.mark.asyncio
async def test_admin_creates_user(auth_client):
    """Admin can create a user with username, password, and role."""
    token = await get_admin_token(auth_client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await auth_client.post(
        "/api/users",
        json={"username": "newuser", "password": "password123", "role": "viewer"},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "newuser"
    assert data["role"] == "viewer"
    assert data["is_active"] is True
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_admin_lists_users(auth_client):
    """Admin can list all users."""
    token = await get_admin_token(auth_client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await auth_client.get("/api/users", headers=headers)
    assert resp.status_code == 200
    users = resp.json()
    assert len(users) >= 1  # At least the admin user
    assert any(u["username"] == TEST_ADMIN_USER for u in users)


@pytest.mark.asyncio
async def test_duplicate_username_returns_409(auth_client):
    """Creating user with existing username returns 409."""
    token = await get_admin_token(auth_client)
    headers = {"Authorization": f"Bearer {token}"}

    await auth_client.post(
        "/api/users",
        json={"username": "dupuser", "password": "password123", "role": "viewer"},
        headers=headers,
    )
    resp = await auth_client.post(
        "/api/users",
        json={"username": "dupuser", "password": "password456", "role": "viewer"},
        headers=headers,
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_admin_deactivates_user(auth_client):
    """Admin can deactivate a user."""
    token = await get_admin_token(auth_client)
    headers = {"Authorization": f"Bearer {token}"}

    # Create a user to deactivate
    resp = await auth_client.post(
        "/api/users",
        json={"username": "todeactivate", "password": "password123", "role": "viewer"},
        headers=headers,
    )
    user_id = resp.json()["id"]

    resp = await auth_client.delete(f"/api/users/{user_id}", headers=headers)
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_password_min_length_enforced(auth_client):
    """Password shorter than 8 chars is rejected."""
    token = await get_admin_token(auth_client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await auth_client.post(
        "/api/users",
        json={"username": "shortpw", "password": "short", "role": "viewer"},
        headers=headers,
    )
    assert resp.status_code == 422
