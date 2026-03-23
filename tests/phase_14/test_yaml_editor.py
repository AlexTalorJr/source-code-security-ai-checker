"""Tests for YAML editor (CONF-03): raw YAML get/put via API."""

import pytest
import yaml

from tests.phase_14.conftest import get_admin_token, get_user_token, TEST_CONFIG


@pytest.mark.asyncio
async def test_get_config_yaml(auth_client, config_path):
    """GET /api/config/yaml returns raw YAML text."""
    token = await get_admin_token(auth_client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await auth_client.get("/api/config/yaml", headers=headers)
    assert resp.status_code == 200
    assert "text/plain" in resp.headers.get("content-type", "")
    assert "scanners:" in resp.text


@pytest.mark.asyncio
async def test_put_valid_yaml(auth_client, config_path):
    """PUT /api/config/yaml with valid YAML updates config.yml."""
    token = await get_admin_token(auth_client)
    headers = {"Authorization": f"Bearer {token}"}

    modified_config = dict(TEST_CONFIG)
    modified_config = {**TEST_CONFIG}
    # Deep copy scanners to avoid mutating TEST_CONFIG
    import copy
    modified = copy.deepcopy(TEST_CONFIG)
    modified["scanners"]["semgrep"]["timeout"] = 99

    yaml_text = yaml.dump(modified, default_flow_style=False, sort_keys=False)

    resp = await auth_client.put(
        "/api/config/yaml",
        content=yaml_text.encode("utf-8"),
        headers=headers,
    )
    assert resp.status_code == 200

    with open(config_path) as f:
        config = yaml.safe_load(f)
    assert config["scanners"]["semgrep"]["timeout"] == 99


@pytest.mark.asyncio
async def test_put_invalid_yaml_syntax(auth_client):
    """PUT with invalid YAML syntax returns 422."""
    token = await get_admin_token(auth_client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await auth_client.put(
        "/api/config/yaml",
        content=b"scanners:\n  semgrep:\n    timeout: [invalid",
        headers=headers,
    )
    assert resp.status_code == 422
    assert "error" in resp.json()["detail"].lower() or "yaml" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_put_invalid_schema(auth_client):
    """PUT with valid YAML but invalid schema returns 422."""
    token = await get_admin_token(auth_client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await auth_client.put(
        "/api/config/yaml",
        content=b"scanners:\n  semgrep:\n    timeout: not_a_number\n",
        headers=headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_schema_validation(auth_client):
    """PUT with wrong field type returns 422 with field-specific error."""
    token = await get_admin_token(auth_client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await auth_client.put(
        "/api/config/yaml",
        content=b"scanners:\n  semgrep:\n    enabled: 42\n    timeout: invalid\n",
        headers=headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_non_admin_yaml_forbidden(auth_client):
    """Non-admin user gets 403 on GET /api/config/yaml."""
    viewer_token = await get_user_token(auth_client, "viewer2", "viewer")
    headers = {"Authorization": f"Bearer {viewer_token}"}

    resp = await auth_client.get("/api/config/yaml", headers=headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_put_preserves_non_scanner_config(auth_client, config_path):
    """PUT full YAML preserves ai and gate sections."""
    token = await get_admin_token(auth_client)
    headers = {"Authorization": f"Bearer {token}"}

    import copy
    full_config = copy.deepcopy(TEST_CONFIG)
    full_config["ai"]["max_cost_per_scan"] = 10.0
    yaml_text = yaml.dump(full_config, default_flow_style=False, sort_keys=False)

    resp = await auth_client.put(
        "/api/config/yaml",
        content=yaml_text.encode("utf-8"),
        headers=headers,
    )
    assert resp.status_code == 200

    with open(config_path) as f:
        config = yaml.safe_load(f)
    assert "scanners" in config
    assert "ai" in config
    assert config["ai"]["max_cost_per_scan"] == 10.0
    assert "gate" in config
