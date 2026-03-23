"""Tests for scanner toggle (CONF-01): enable/disable scanners via API."""

import pytest
import yaml

from tests.phase_14.conftest import get_admin_token, get_user_token


@pytest.mark.asyncio
async def test_get_config_returns_scanners(auth_client, config_path):
    """GET /api/config returns full config with scanners section."""
    token = await get_admin_token(auth_client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await auth_client.get("/api/config", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "scanners" in data
    assert "semgrep" in data["scanners"]
    assert "gitleaks" in data["scanners"]
    assert "nuclei" in data["scanners"]


@pytest.mark.asyncio
async def test_patch_scanner_enabled_true(auth_client, config_path):
    """PATCH scanner to enabled=true persists to config.yml."""
    token = await get_admin_token(auth_client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await auth_client.patch(
        "/api/config/scanners/semgrep",
        json={"enabled": True},
        headers=headers,
    )
    assert resp.status_code == 200

    with open(config_path) as f:
        config = yaml.safe_load(f)
    assert config["scanners"]["semgrep"]["enabled"] is True


@pytest.mark.asyncio
async def test_patch_scanner_enabled_false(auth_client, config_path):
    """PATCH scanner to enabled=false persists to config.yml."""
    token = await get_admin_token(auth_client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await auth_client.patch(
        "/api/config/scanners/semgrep",
        json={"enabled": False},
        headers=headers,
    )
    assert resp.status_code == 200

    with open(config_path) as f:
        config = yaml.safe_load(f)
    assert config["scanners"]["semgrep"]["enabled"] is False


@pytest.mark.asyncio
async def test_patch_scanner_enabled_auto(auth_client, config_path):
    """PATCH scanner to enabled='auto' persists to config.yml."""
    token = await get_admin_token(auth_client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await auth_client.patch(
        "/api/config/scanners/semgrep",
        json={"enabled": "auto"},
        headers=headers,
    )
    assert resp.status_code == 200

    with open(config_path) as f:
        config = yaml.safe_load(f)
    assert config["scanners"]["semgrep"]["enabled"] == "auto"


@pytest.mark.asyncio
async def test_patch_unknown_scanner_404(auth_client):
    """PATCH nonexistent scanner returns 404."""
    token = await get_admin_token(auth_client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await auth_client.patch(
        "/api/config/scanners/nonexistent",
        json={"enabled": True},
        headers=headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_non_admin_forbidden(auth_client):
    """Non-admin user gets 403 on config endpoints."""
    viewer_token = await get_user_token(auth_client, "viewer1", "viewer")
    headers = {"Authorization": f"Bearer {viewer_token}"}

    resp = await auth_client.patch(
        "/api/config/scanners/semgrep",
        json={"enabled": True},
        headers=headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_unauthenticated_401(auth_client):
    """Request without auth header returns 401."""
    resp = await auth_client.patch(
        "/api/config/scanners/semgrep",
        json={"enabled": True},
    )
    assert resp.status_code == 401
