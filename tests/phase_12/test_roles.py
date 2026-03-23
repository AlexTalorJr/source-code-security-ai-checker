"""Tests for role-based access control (AUTH-04, AUTH-05, AUTH-06)."""

import hashlib
import secrets

import pytest
from scanner.models.user import APIToken, User
from scanner.dashboard.auth import hash_password
from sqlalchemy import select
from tests.phase_12.conftest import get_admin_token


async def _create_user_with_token(client, username, role):
    """Helper: create user and return Bearer token."""
    admin_token = await get_admin_token(client)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Create user via API
    resp = await client.post(
        "/api/users",
        json={"username": username, "password": "password123", "role": role},
        headers=admin_headers,
    )
    assert resp.status_code == 201, f"Failed to create {role} user: {resp.text}"
    user_id = resp.json()["id"]

    # Create token directly in DB for this user
    app = client._transport.app  # type: ignore
    raw = f"nvsec_{secrets.token_hex(32)}"
    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    async with app.state.session_factory() as session:
        token = APIToken(
            user_id=user_id,
            token_hash=token_hash,
            name=f"{role}-test-token",
        )
        session.add(token)
        await session.commit()
    return raw


@pytest.mark.asyncio
async def test_admin_full_access(auth_client):
    """Admin role has full access to all endpoints (AUTH-04)."""
    token = await get_admin_token(auth_client)
    headers = {"Authorization": f"Bearer {token}"}

    # Admin can list users
    resp = await auth_client.get("/api/users", headers=headers)
    assert resp.status_code == 200

    # Admin can list scans
    resp = await auth_client.get("/api/scans", headers=headers)
    assert resp.status_code == 200

    # Admin can list scanners
    resp = await auth_client.get("/api/scanners", headers=headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_viewer_restricted(auth_client):
    """Viewer can view results but cannot trigger scans or change settings (AUTH-05)."""
    viewer_token = await _create_user_with_token(auth_client, "viewer1", "viewer")
    headers = {"Authorization": f"Bearer {viewer_token}"}

    # Viewer can view scans
    resp = await auth_client.get("/api/scans", headers=headers)
    assert resp.status_code == 200

    # Viewer CANNOT trigger scan
    resp = await auth_client.post(
        "/api/scans",
        json={"repo_url": "https://github.com/test/repo"},
        headers=headers,
    )
    assert resp.status_code == 403

    # Viewer CANNOT create users
    resp = await auth_client.post(
        "/api/users",
        json={"username": "hack", "password": "password123", "role": "admin"},
        headers=headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_scanner_role_limits(auth_client):
    """Scanner can trigger scans via API but not access admin endpoints (AUTH-06)."""
    scanner_token = await _create_user_with_token(auth_client, "scanner1", "scanner")
    headers = {"Authorization": f"Bearer {scanner_token}"}

    # Scanner can view scans
    resp = await auth_client.get("/api/scans", headers=headers)
    assert resp.status_code == 200

    # Scanner CANNOT manage users
    resp = await auth_client.get("/api/users", headers=headers)
    assert resp.status_code == 403

    resp = await auth_client.post(
        "/api/users",
        json={"username": "hack2", "password": "password123", "role": "admin"},
        headers=headers,
    )
    assert resp.status_code == 403
