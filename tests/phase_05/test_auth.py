"""Tests for API key authentication."""

import pytest


class TestAPIKeyAuth:
    @pytest.mark.asyncio
    async def test_api_requires_key(self, auth_client):
        """GET /api/scans without X-API-Key header returns 422 (missing required header)."""
        resp = await auth_client.get("/api/scans")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_api_rejects_bad_key(self, auth_client):
        """GET /api/scans with wrong API key returns 401."""
        resp = await auth_client.get(
            "/api/scans", headers={"X-API-Key": "wrong-key"}
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_api_accepts_valid_key(self, auth_client, api_headers):
        """GET /api/scans with valid API key returns 200."""
        resp = await auth_client.get("/api/scans", headers=api_headers)
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_health_no_auth(self, auth_client):
        """GET /api/health without any key returns 200."""
        resp = await auth_client.get("/api/health")
        assert resp.status_code == 200
