"""Tests for finding suppression API endpoints."""

import pytest

from tests.phase_05.conftest import seed_findings, seed_scan


class TestSuppression:
    @pytest.mark.asyncio
    async def test_suppress_fingerprint(self, auth_client, api_headers):
        """PUT /api/findings/{fp}/suppress returns 200 with suppressed=True."""
        resp = await auth_client.put(
            "/api/findings/abc123/suppress", headers=api_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["fingerprint"] == "abc123"
        assert data["suppressed"] is True

    @pytest.mark.asyncio
    async def test_suppress_with_reason(self, auth_client, api_headers):
        """PUT with reason body stores the reason."""
        resp = await auth_client.put(
            "/api/findings/def456/suppress",
            json={"reason": "False alarm"},
            headers=api_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["reason"] == "False alarm"

    @pytest.mark.asyncio
    async def test_unsuppress_fingerprint(self, auth_client, api_headers):
        """After suppressing, DELETE returns 200 with suppressed=False."""
        # Suppress first
        await auth_client.put(
            "/api/findings/ghi789/suppress", headers=api_headers
        )
        # Unsuppress
        resp = await auth_client.delete(
            "/api/findings/ghi789/suppress", headers=api_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["fingerprint"] == "ghi789"
        assert data["suppressed"] is False

    @pytest.mark.asyncio
    async def test_unsuppress_not_found(self, auth_client, api_headers):
        """DELETE on non-suppressed fingerprint returns 404."""
        resp = await auth_client.delete(
            "/api/findings/nonexistent/suppress", headers=api_headers
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_suppressed_findings_shown_in_listing(
        self, auth_client, api_headers
    ):
        """After suppressing a fingerprint, GET findings shows suppressed=true."""
        # Seed scan with findings
        async with auth_client._transport.app.state.session_factory() as session:
            async with session.begin():
                scan_id = await seed_scan(session, total_findings=2)
                fps = await seed_findings(session, scan_id, count=2)

        # Suppress the first fingerprint
        await auth_client.put(
            f"/api/findings/{fps[0]}/suppress", headers=api_headers
        )

        # Get findings
        resp = await auth_client.get(
            f"/api/scans/{scan_id}/findings", headers=api_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        items = data["items"]

        suppressed_items = [i for i in items if i["suppressed"] is True]
        unsuppressed_items = [i for i in items if i["suppressed"] is False]
        assert len(suppressed_items) == 1
        assert len(unsuppressed_items) == 1
        assert suppressed_items[0]["fingerprint"] == fps[0]
