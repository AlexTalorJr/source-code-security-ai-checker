"""Tests for scanner settings (CONF-02): timeout, extra_args via API."""

import pytest
import yaml

from tests.phase_14.conftest import get_admin_token


@pytest.mark.asyncio
async def test_patch_timeout_valid(auth_client, config_path):
    """PATCH with valid timeout persists to config.yml."""
    token = await get_admin_token(auth_client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await auth_client.patch(
        "/api/config/scanners/semgrep",
        json={"timeout": 60},
        headers=headers,
    )
    assert resp.status_code == 200

    with open(config_path) as f:
        config = yaml.safe_load(f)
    assert config["scanners"]["semgrep"]["timeout"] == 60


@pytest.mark.asyncio
async def test_patch_timeout_too_low(auth_client):
    """PATCH with timeout < 30 returns 422."""
    token = await get_admin_token(auth_client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await auth_client.patch(
        "/api/config/scanners/semgrep",
        json={"timeout": 10},
        headers=headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_patch_timeout_too_high(auth_client):
    """PATCH with timeout > 900 returns 422."""
    token = await get_admin_token(auth_client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await auth_client.patch(
        "/api/config/scanners/semgrep",
        json={"timeout": 1000},
        headers=headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_patch_extra_args_valid(auth_client, config_path):
    """PATCH with valid extra_args persists to config.yml."""
    token = await get_admin_token(auth_client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await auth_client.patch(
        "/api/config/scanners/semgrep",
        json={"extra_args": ["--verbose", "--debug"]},
        headers=headers,
    )
    assert resp.status_code == 200

    with open(config_path) as f:
        config = yaml.safe_load(f)
    assert config["scanners"]["semgrep"]["extra_args"] == ["--verbose", "--debug"]


@pytest.mark.asyncio
async def test_patch_combined_settings(auth_client, config_path):
    """PATCH with multiple fields updates all of them."""
    token = await get_admin_token(auth_client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await auth_client.patch(
        "/api/config/scanners/semgrep",
        json={"enabled": True, "timeout": 120, "extra_args": ["--flag"]},
        headers=headers,
    )
    assert resp.status_code == 200

    with open(config_path) as f:
        config = yaml.safe_load(f)
    assert config["scanners"]["semgrep"]["enabled"] is True
    assert config["scanners"]["semgrep"]["timeout"] == 120
    assert config["scanners"]["semgrep"]["extra_args"] == ["--flag"]


@pytest.mark.asyncio
async def test_timeout_validation(auth_client):
    """PATCH with timeout=29 returns 422 with timeout range error."""
    token = await get_admin_token(auth_client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await auth_client.patch(
        "/api/config/scanners/semgrep",
        json={"timeout": 29},
        headers=headers,
    )
    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert "timeout" in detail.lower() or "30" in str(detail)


@pytest.mark.asyncio
async def test_extra_args_validation(auth_client):
    """PATCH with empty string in extra_args returns 422."""
    token = await get_admin_token(auth_client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await auth_client.patch(
        "/api/config/scanners/semgrep",
        json={"extra_args": ["valid", ""]},
        headers=headers,
    )
    assert resp.status_code == 422
