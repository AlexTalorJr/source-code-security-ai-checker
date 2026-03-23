"""Tests for scan profile CRUD API endpoints."""

import pytest
import yaml

from tests.phase_15.conftest import get_admin_token, get_user_token


pytestmark = pytest.mark.anyio


class TestCreateProfile:
    """POST /api/config/profiles"""

    async def test_create_profile_success(self, auth_client, config_path):
        token = await get_admin_token(auth_client)
        resp = await auth_client.post(
            "/api/config/profiles",
            json={
                "name": "my_profile",
                "description": "Test profile",
                "scanners": {"semgrep": {}},
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "ok"
        assert data["profile"] == "my_profile"

        # Verify persistence
        with open(config_path) as f:
            cfg = yaml.safe_load(f)
        assert "my_profile" in cfg["profiles"]
        assert cfg["profiles"]["my_profile"]["description"] == "Test profile"

    async def test_create_profile_duplicate_returns_409(self, auth_client):
        token = await get_admin_token(auth_client)
        # quick_scan already exists in TEST_CONFIG
        resp = await auth_client.post(
            "/api/config/profiles",
            json={"name": "quick_scan", "scanners": {"semgrep": {}}},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 409

    async def test_create_profile_empty_scanners_returns_422(self, auth_client):
        token = await get_admin_token(auth_client)
        resp = await auth_client.post(
            "/api/config/profiles",
            json={"name": "empty_profile", "scanners": {}},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    async def test_create_profile_invalid_name_returns_422(self, auth_client):
        token = await get_admin_token(auth_client)
        # Name with spaces
        resp = await auth_client.post(
            "/api/config/profiles",
            json={"name": "bad name", "scanners": {"semgrep": {}}},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

        # Name starting with number
        resp = await auth_client.post(
            "/api/config/profiles",
            json={"name": "123start", "scanners": {"semgrep": {}}},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

        # YAML reserved word
        resp = await auth_client.post(
            "/api/config/profiles",
            json={"name": "true", "scanners": {"semgrep": {}}},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    async def test_create_profile_at_limit_returns_400(self, auth_client, config_path):
        token = await get_admin_token(auth_client)
        # Config already has 1 profile (quick_scan), create 9 more to reach 10
        for i in range(9):
            resp = await auth_client.post(
                "/api/config/profiles",
                json={"name": f"profile{i}", "scanners": {"semgrep": {}}},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 201, f"Failed creating profile{i}: {resp.text}"

        # 11th should fail
        resp = await auth_client.post(
            "/api/config/profiles",
            json={"name": "one_too_many", "scanners": {"semgrep": {}}},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400


class TestListProfiles:
    """GET /api/config/profiles"""

    async def test_list_profiles(self, auth_client):
        token = await get_admin_token(auth_client)
        resp = await auth_client.get(
            "/api/config/profiles",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "profiles" in data
        assert "quick_scan" in data["profiles"]


class TestGetProfile:
    """GET /api/config/profiles/{name}"""

    async def test_get_profile_success(self, auth_client):
        token = await get_admin_token(auth_client)
        resp = await auth_client.get(
            "/api/config/profiles/quick_scan",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "quick_scan"
        assert "scanners" in data

    async def test_get_profile_not_found(self, auth_client):
        token = await get_admin_token(auth_client)
        resp = await auth_client.get(
            "/api/config/profiles/nonexistent",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404


class TestUpdateProfile:
    """PUT /api/config/profiles/{name}"""

    async def test_update_profile_description(self, auth_client, config_path):
        token = await get_admin_token(auth_client)
        resp = await auth_client.put(
            "/api/config/profiles/quick_scan",
            json={"description": "Updated description"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

        # Verify persistence
        with open(config_path) as f:
            cfg = yaml.safe_load(f)
        assert cfg["profiles"]["quick_scan"]["description"] == "Updated description"

    async def test_update_profile_scanners(self, auth_client, config_path):
        token = await get_admin_token(auth_client)
        resp = await auth_client.put(
            "/api/config/profiles/quick_scan",
            json={"scanners": {"gitleaks": {}, "semgrep": {}}},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

        with open(config_path) as f:
            cfg = yaml.safe_load(f)
        assert "gitleaks" in cfg["profiles"]["quick_scan"]["scanners"]

    async def test_update_profile_empty_scanners_returns_422(self, auth_client):
        token = await get_admin_token(auth_client)
        resp = await auth_client.put(
            "/api/config/profiles/quick_scan",
            json={"scanners": {}},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    async def test_update_profile_not_found(self, auth_client):
        token = await get_admin_token(auth_client)
        resp = await auth_client.put(
            "/api/config/profiles/nonexistent",
            json={"description": "nope"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404


class TestDeleteProfile:
    """DELETE /api/config/profiles/{name}"""

    async def test_delete_profile_success(self, auth_client, config_path):
        token = await get_admin_token(auth_client)
        resp = await auth_client.delete(
            "/api/config/profiles/quick_scan",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

        with open(config_path) as f:
            cfg = yaml.safe_load(f)
        assert "quick_scan" not in cfg.get("profiles", {})

    async def test_delete_profile_not_found(self, auth_client):
        token = await get_admin_token(auth_client)
        resp = await auth_client.delete(
            "/api/config/profiles/nonexistent",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404


class TestProfileAuth:
    """Non-admin access returns 403."""

    async def test_viewer_cannot_create_profile(self, auth_client):
        viewer_token = await get_user_token(auth_client, "viewer1", role="viewer")
        resp = await auth_client.post(
            "/api/config/profiles",
            json={"name": "viewer_profile", "scanners": {"semgrep": {}}},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 403

    async def test_viewer_cannot_list_profiles(self, auth_client):
        viewer_token = await get_user_token(auth_client, "viewer2", role="viewer")
        resp = await auth_client.get(
            "/api/config/profiles",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 403

    async def test_viewer_cannot_delete_profile(self, auth_client):
        viewer_token = await get_user_token(auth_client, "viewer3", role="viewer")
        resp = await auth_client.delete(
            "/api/config/profiles/quick_scan",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 403
