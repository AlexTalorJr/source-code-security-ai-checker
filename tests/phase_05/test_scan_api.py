"""Tests for scan lifecycle API endpoints."""

import pytest

from tests.phase_05.conftest import seed_findings, seed_scan


class TestTriggerScan:
    @pytest.mark.asyncio
    async def test_trigger_scan_returns_202(self, auth_client, api_headers):
        """POST /api/scans with valid body returns 202 with id and status."""
        resp = await auth_client.post(
            "/api/scans",
            json={"path": "/tmp/test"},
            headers=api_headers,
        )
        assert resp.status_code == 202
        data = resp.json()
        assert "id" in data
        assert data["status"] == "queued"

    @pytest.mark.asyncio
    async def test_trigger_scan_requires_path_or_repo(
        self, auth_client, api_headers
    ):
        """POST /api/scans with empty body returns 422."""
        resp = await auth_client.post(
            "/api/scans", json={}, headers=api_headers
        )
        assert resp.status_code == 422


class TestGetScan:
    @pytest.mark.asyncio
    async def test_get_scan_status(self, auth_client, api_headers):
        """GET /api/scans/{id} returns scan details for existing scan."""
        async with auth_client._transport.app.state.session_factory() as session:
            async with session.begin():
                scan_id = await seed_scan(session, status="completed")

        resp = await auth_client.get(
            f"/api/scans/{scan_id}", headers=api_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == scan_id
        assert data["status"] == "completed"

    @pytest.mark.asyncio
    async def test_get_scan_not_found(self, auth_client, api_headers):
        """GET /api/scans/99999 returns 404."""
        resp = await auth_client.get(
            "/api/scans/99999", headers=api_headers
        )
        assert resp.status_code == 404


class TestListScans:
    @pytest.mark.asyncio
    async def test_list_scans(self, auth_client, api_headers):
        """GET /api/scans returns paginated response with all seeded scans."""
        async with auth_client._transport.app.state.session_factory() as session:
            async with session.begin():
                for _ in range(3):
                    await seed_scan(session)

        resp = await auth_client.get("/api/scans", headers=api_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    @pytest.mark.asyncio
    async def test_list_scans_pagination(self, auth_client, api_headers):
        """GET /api/scans with page_size=2 returns correct pagination."""
        async with auth_client._transport.app.state.session_factory() as session:
            async with session.begin():
                for _ in range(5):
                    await seed_scan(session)

        resp = await auth_client.get(
            "/api/scans?page=1&page_size=2", headers=api_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["pages"] == 3


class TestGetFindings:
    @pytest.mark.asyncio
    async def test_get_findings(self, auth_client, api_headers):
        """GET /api/scans/{id}/findings returns paginated findings."""
        async with auth_client._transport.app.state.session_factory() as session:
            async with session.begin():
                scan_id = await seed_scan(session, total_findings=3)
                fps = await seed_findings(session, scan_id, count=3)

        resp = await auth_client.get(
            f"/api/scans/{scan_id}/findings", headers=api_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3
        # Check severity is string name, not int
        assert data["items"][0]["severity"] == "MEDIUM"
