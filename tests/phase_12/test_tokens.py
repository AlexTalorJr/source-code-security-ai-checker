"""Tests for API token management (AUTH-03)."""

import pytest
from tests.phase_12.conftest import get_admin_token


@pytest.mark.asyncio
async def test_create_and_revoke_token(auth_client):
    """User can generate and revoke a personal API token."""
    token = await get_admin_token(auth_client)
    headers = {"Authorization": f"Bearer {token}"}

    # Create token
    resp = await auth_client.post(
        "/api/tokens",
        json={"name": "ci-token"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "ci-token"
    assert data["raw_token"].startswith("nvsec_")
    new_token_id = data["id"]

    # Revoke token
    resp = await auth_client.delete(
        f"/api/tokens/{new_token_id}",
        headers=headers,
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_token_shown_once(auth_client):
    """Raw token only appears in creation response, not in list."""
    token = await get_admin_token(auth_client)
    headers = {"Authorization": f"Bearer {token}"}

    # Create
    resp = await auth_client.post(
        "/api/tokens",
        json={"name": "once-token"},
        headers=headers,
    )
    assert "raw_token" in resp.json()

    # List -- should NOT contain raw_token
    resp = await auth_client.get("/api/tokens", headers=headers)
    assert resp.status_code == 200
    for t in resp.json():
        assert "raw_token" not in t
        assert "token_prefix" in t


@pytest.mark.asyncio
async def test_token_prefix_format(auth_client):
    """Generated token has nvsec_ prefix."""
    token = await get_admin_token(auth_client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await auth_client.post(
        "/api/tokens",
        json={"name": "prefix-test"},
        headers=headers,
    )
    raw = resp.json()["raw_token"]
    assert raw.startswith("nvsec_")
    assert len(raw) > 10  # nvsec_ + at least some hex


@pytest.mark.asyncio
async def test_new_token_works_for_auth(auth_client):
    """A newly created token can authenticate API requests."""
    admin_token = await get_admin_token(auth_client)
    headers = {"Authorization": f"Bearer {admin_token}"}

    resp = await auth_client.post(
        "/api/tokens",
        json={"name": "auth-test"},
        headers=headers,
    )
    new_raw = resp.json()["raw_token"]

    # Use new token
    resp = await auth_client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {new_raw}"},
    )
    assert resp.status_code == 200
