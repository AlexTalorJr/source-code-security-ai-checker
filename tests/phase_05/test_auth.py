"""Tests for Bearer token API authentication."""

import pytest


class TestBearerTokenAuth:
    @pytest.mark.asyncio
    async def test_api_requires_auth(self, auth_client):
        """GET /api/scans without Authorization header returns 401."""
        resp = await auth_client.get("/api/scans")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_api_rejects_bad_token(self, auth_client):
        """GET /api/scans with invalid Bearer token returns 401."""
        resp = await auth_client.get(
            "/api/scans",
            headers={"Authorization": "Bearer nvsec_invalid_token"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_api_accepts_valid_token(self, auth_client, api_headers):
        """GET /api/scans with valid Bearer token returns 200."""
        resp = await auth_client.get("/api/scans", headers=api_headers)
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_health_no_auth(self, auth_client):
        """GET /api/health without any auth returns 200."""
        resp = await auth_client.get("/api/health")
        assert resp.status_code == 200
