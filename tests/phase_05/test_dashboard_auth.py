"""Tests for dashboard cookie-based authentication."""

import pytest
from httpx import ASGITransport, AsyncClient

from scanner.dashboard.auth import make_session_token
from scanner.main import create_app
from tests.phase_05.conftest import _lifespan_client


class TestDashboardAuth:
    @pytest.mark.asyncio
    async def test_dashboard_redirects_to_login(self, test_env):
        """GET /dashboard/history without cookie returns 302 redirect to login."""
        app = create_app()
        async with _lifespan_client(app) as client:
            resp = await client.get(
                "/dashboard/history", follow_redirects=False
            )
            assert resp.status_code == 302
            assert "/dashboard/login" in resp.headers["location"]

    @pytest.mark.asyncio
    async def test_login_page_renders(self, test_env):
        """GET /dashboard/login returns 200 with 'Security Scanner'."""
        app = create_app()
        async with _lifespan_client(app) as client:
            resp = await client.get("/dashboard/login")
            assert resp.status_code == 200
            assert "Security Scanner" in resp.text

    @pytest.mark.asyncio
    async def test_login_success_sets_cookie(self, test_env):
        """POST /dashboard/login with correct key sets session cookie."""
        app = create_app()
        async with _lifespan_client(app) as client:
            resp = await client.post(
                "/dashboard/login",
                data={"api_key": "test-api-key-12345"},
                follow_redirects=False,
            )
            assert resp.status_code == 302
            assert "/dashboard/history" in resp.headers["location"]
            assert "scanner_session" in resp.headers.get("set-cookie", "")

    @pytest.mark.asyncio
    async def test_login_failure_shows_error(self, test_env):
        """POST /dashboard/login with wrong key redirects with error."""
        app = create_app()
        async with _lifespan_client(app) as client:
            resp = await client.post(
                "/dashboard/login",
                data={"api_key": "wrong-key"},
                follow_redirects=False,
            )
            assert resp.status_code == 302
            assert "error=1" in resp.headers["location"]

    @pytest.mark.asyncio
    async def test_dashboard_accessible_with_cookie(self, test_env):
        """GET /dashboard/history with valid session cookie returns 200."""
        app = create_app()
        async with _lifespan_client(app) as client:
            token = make_session_token("test-api-key-12345")
            client.cookies.set("scanner_session", token)
            resp = await client.get("/dashboard/history")
            assert resp.status_code == 200
            assert "Scan History" in resp.text

    @pytest.mark.asyncio
    async def test_logout_clears_cookie(self, test_env):
        """GET /dashboard/logout returns 302 and clears cookie."""
        app = create_app()
        async with _lifespan_client(app) as client:
            token = make_session_token("test-api-key-12345")
            client.cookies.set("scanner_session", token)
            resp = await client.get(
                "/dashboard/logout", follow_redirects=False
            )
            assert resp.status_code == 302
            assert "/dashboard/login" in resp.headers["location"]
            # Cookie should be cleared (max-age=0 or deleted)
            set_cookie = resp.headers.get("set-cookie", "")
            assert "scanner_session" in set_cookie
