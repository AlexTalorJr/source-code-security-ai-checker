"""Tests for dashboard cookie-based authentication."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from scanner.dashboard.auth import create_session_jwt, COOKIE_NAME
from scanner.main import create_app
from scanner.models.user import User
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
        """POST /dashboard/login with correct credentials sets session cookie."""
        app = create_app()
        async with _lifespan_client(app) as client:
            resp = await client.post(
                "/dashboard/login",
                data={"username": "testadmin", "password": "testpass123"},
                follow_redirects=False,
            )
            assert resp.status_code == 302
            assert "/dashboard/history" in resp.headers["location"]
            assert COOKIE_NAME in resp.headers.get("set-cookie", "")

    @pytest.mark.asyncio
    async def test_login_failure_shows_error(self, test_env):
        """POST /dashboard/login with wrong credentials redirects with error."""
        app = create_app()
        async with _lifespan_client(app) as client:
            resp = await client.post(
                "/dashboard/login",
                data={"username": "testadmin", "password": "wrongpass"},
                follow_redirects=False,
            )
            assert resp.status_code == 302
            assert "error=1" in resp.headers["location"]

    @pytest.mark.asyncio
    async def test_dashboard_accessible_with_cookie(self, test_env):
        """GET /dashboard/history with valid session cookie returns 200."""
        app = create_app()
        async with _lifespan_client(app) as client:
            async with app.state.session_factory() as session:
                result = await session.execute(
                    select(User).where(User.username == "testadmin")
                )
                user = result.scalar_one()
                token = create_session_jwt(user.id, user.role, "test-secret-key-for-phase05")
            client.cookies.set(COOKIE_NAME, token)
            resp = await client.get("/dashboard/history")
            assert resp.status_code == 200
            assert "Scan History" in resp.text

    @pytest.mark.asyncio
    async def test_logout_clears_cookie(self, test_env):
        """GET /dashboard/logout returns 302 and clears cookie."""
        app = create_app()
        async with _lifespan_client(app) as client:
            async with app.state.session_factory() as session:
                result = await session.execute(
                    select(User).where(User.username == "testadmin")
                )
                user = result.scalar_one()
                token = create_session_jwt(user.id, user.role, "test-secret-key-for-phase05")
            client.cookies.set(COOKIE_NAME, token)
            resp = await client.get(
                "/dashboard/logout", follow_redirects=False
            )
            assert resp.status_code == 302
            assert "/dashboard/login" in resp.headers["location"]
            # Cookie should be cleared (max-age=0 or deleted)
            set_cookie = resp.headers.get("set-cookie", "")
            assert COOKIE_NAME in set_cookie
