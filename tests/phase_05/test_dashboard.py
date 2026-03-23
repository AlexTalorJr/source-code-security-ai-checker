"""Tests for dashboard page rendering and dashboard-triggered actions."""

from datetime import datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient

from scanner.dashboard.auth import create_session_jwt, COOKIE_NAME
from scanner.main import create_app
from scanner.models.finding import Finding
from scanner.models.scan import ScanResult
from scanner.models.suppression import Suppression
from scanner.models.user import User
from sqlalchemy import select
from tests.phase_05.conftest import _lifespan_client, seed_findings, seed_scan


async def _dashboard_client(test_env):
    """Create a lifespan client with dashboard session cookie set."""
    app = create_app()
    async with _lifespan_client(app) as client:
        # Get the bootstrapped admin user's ID for JWT creation
        async with app.state.session_factory() as session:
            result = await session.execute(
                select(User).where(User.username == "testadmin")
            )
            user = result.scalar_one()
            token = create_session_jwt(user.id, user.role, "test-secret-key-for-phase05")
        client.cookies.set(COOKIE_NAME, token)
        yield client, app


class TestHistoryPage:
    @pytest.mark.asyncio
    async def test_history_page_renders(self, test_env):
        """GET /dashboard/history returns 200 with 'Scan History'."""
        async for client, app in _dashboard_client(test_env):
            resp = await client.get("/dashboard/history")
            assert resp.status_code == 200
            assert "Scan History" in resp.text

    @pytest.mark.asyncio
    async def test_history_shows_empty_state(self, test_env):
        """With no scans, response contains 'No scans yet'."""
        async for client, app in _dashboard_client(test_env):
            resp = await client.get("/dashboard/history")
            assert "No scans yet" in resp.text

    @pytest.mark.asyncio
    async def test_history_shows_scans(self, test_env):
        """With seeded scans, response contains scan IDs."""
        async for client, app in _dashboard_client(test_env):
            async with app.state.session_factory() as session:
                await seed_scan(session, branch="main")
                await seed_scan(session, branch="develop")
                await session.commit()

            resp = await client.get("/dashboard/history")
            assert resp.status_code == 200
            assert "#1" in resp.text
            assert "#2" in resp.text


class TestDetailPage:
    @pytest.mark.asyncio
    async def test_detail_page_renders(self, test_env):
        """GET /dashboard/scans/{id} returns 200 with 'Quality Gate'."""
        async for client, app in _dashboard_client(test_env):
            async with app.state.session_factory() as session:
                scan_id = await seed_scan(
                    session, branch="main", gate_passed=1
                )
                await seed_findings(session, scan_id, count=2)
                await session.commit()

            resp = await client.get(f"/dashboard/scans/{scan_id}")
            assert resp.status_code == 200
            assert "Quality Gate" in resp.text

    @pytest.mark.asyncio
    async def test_detail_shows_findings(self, test_env):
        """Seeded findings appear in the detail page."""
        async for client, app in _dashboard_client(test_env):
            async with app.state.session_factory() as session:
                scan_id = await seed_scan(session, branch="main")
                await seed_findings(session, scan_id, count=2)
                await session.commit()

            resp = await client.get(f"/dashboard/scans/{scan_id}")
            assert "Test finding 0" in resp.text
            assert "Test finding 1" in resp.text

    @pytest.mark.asyncio
    async def test_detail_running_scan_has_refresh(self, test_env):
        """Running scan page includes JS polling for auto-refresh."""
        async for client, app in _dashboard_client(test_env):
            async with app.state.session_factory() as session:
                scan_id = await seed_scan(session, status="running")
                await session.commit()

            resp = await client.get(f"/dashboard/scans/{scan_id}")
            assert resp.status_code == 200
            assert "setInterval(poll" in resp.text


class TestTrendsPage:
    @pytest.mark.asyncio
    async def test_trends_page_renders(self, test_env):
        """GET /dashboard/trends returns 200 with 'Finding Trends'."""
        async for client, app in _dashboard_client(test_env):
            resp = await client.get("/dashboard/trends")
            assert resp.status_code == 200
            assert "Finding Trends" in resp.text

    @pytest.mark.asyncio
    async def test_trends_empty_state(self, test_env):
        """With fewer than 2 scans, shows 'Not enough data'."""
        async for client, app in _dashboard_client(test_env):
            resp = await client.get("/dashboard/trends")
            assert "Not enough data" in resp.text

    @pytest.mark.asyncio
    async def test_trends_shows_charts(self, test_env):
        """With 3 completed scans, charts are rendered as base64 PNG images."""
        async for client, app in _dashboard_client(test_env):
            async with app.state.session_factory() as session:
                for i in range(3):
                    await seed_scan(
                        session,
                        branch="main",
                        total_findings=5,
                        critical_count=1,
                        high_count=1,
                        medium_count=1,
                        low_count=1,
                        info_count=1,
                        created_at=datetime.utcnow() - timedelta(days=3 - i),
                    )
                await session.commit()

            resp = await client.get("/dashboard/trends")
            assert resp.status_code == 200
            assert "data:image/png;base64," in resp.text


class TestDashboardActions:
    @pytest.mark.asyncio
    async def test_start_scan_from_dashboard(self, test_env):
        """POST /dashboard/start-scan creates scan and redirects."""
        async for client, app in _dashboard_client(test_env):
            resp = await client.post(
                "/dashboard/start-scan",
                data={"path": "/tmp/test", "repo_url": "", "branch": ""},
                follow_redirects=False,
            )
            assert resp.status_code == 302
            assert "/dashboard/scans/" in resp.headers["location"]

    @pytest.mark.asyncio
    async def test_suppress_from_dashboard(self, test_env):
        """POST suppress moves finding to suppressed tab."""
        async for client, app in _dashboard_client(test_env):
            async with app.state.session_factory() as session:
                scan_id = await seed_scan(session, branch="main")
                fps = await seed_findings(session, scan_id, count=1)
                await session.commit()

            fp = fps[0]
            resp = await client.post(
                f"/dashboard/scans/{scan_id}/suppress/{fp}",
                follow_redirects=False,
            )
            assert resp.status_code == 302

            # Verify the finding is now in suppressed tab
            detail_resp = await client.get(f"/dashboard/scans/{scan_id}")
            assert detail_resp.status_code == 200
            # The fingerprint should appear in the suppressed section
            assert fp in detail_resp.text

    @pytest.mark.asyncio
    async def test_unsuppress_from_dashboard(self, test_env):
        """POST unsuppress restores finding to active list."""
        async for client, app in _dashboard_client(test_env):
            async with app.state.session_factory() as session:
                scan_id = await seed_scan(session, branch="main")
                fps = await seed_findings(session, scan_id, count=1)
                await session.commit()

            fp = fps[0]
            # Suppress first
            await client.post(
                f"/dashboard/scans/{scan_id}/suppress/{fp}",
                follow_redirects=False,
            )
            # Then unsuppress
            resp = await client.post(
                f"/dashboard/scans/{scan_id}/unsuppress/{fp}",
                follow_redirects=False,
            )
            assert resp.status_code == 302

            # Verify finding is back in active findings
            detail_resp = await client.get(f"/dashboard/scans/{scan_id}")
            assert detail_resp.status_code == 200
            # The Suppress button should be visible (not Restore)
            assert "Suppress" in detail_resp.text
