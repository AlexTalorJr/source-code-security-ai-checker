"""Tests for dashboard login flow (AUTH-02)."""

import pytest
from tests.phase_12.conftest import TEST_ADMIN_USER, TEST_ADMIN_PASSWORD


@pytest.mark.asyncio
async def test_login_with_credentials(auth_client):
    """User can log in with username and password (AUTH-02)."""
    resp = await auth_client.post(
        "/dashboard/login",
        data={"username": TEST_ADMIN_USER, "password": TEST_ADMIN_PASSWORD},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "/dashboard/history" in resp.headers.get("location", "")
    assert "scanner_session" in resp.headers.get("set-cookie", "")


@pytest.mark.asyncio
async def test_login_invalid_credentials_shows_error(auth_client):
    """Invalid credentials redirect back to login with error."""
    resp = await auth_client.post(
        "/dashboard/login",
        data={"username": "wrong", "password": "wrong"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "error=1" in resp.headers.get("location", "")


@pytest.mark.asyncio
async def test_login_page_renders(auth_client):
    """Login page renders without authentication."""
    resp = await auth_client.get("/dashboard/login")
    assert resp.status_code == 200
    assert "username" in resp.text.lower()
    assert "password" in resp.text.lower()


@pytest.mark.asyncio
async def test_logout_clears_cookie(auth_client):
    """Logout clears session cookie and redirects to login."""
    # Login first
    resp = await auth_client.post(
        "/dashboard/login",
        data={"username": TEST_ADMIN_USER, "password": TEST_ADMIN_PASSWORD},
        follow_redirects=False,
    )
    cookies = resp.cookies

    # Logout
    resp = await auth_client.get("/dashboard/logout", cookies=cookies, follow_redirects=False)
    assert resp.status_code == 302
    assert "/dashboard/login" in resp.headers.get("location", "")


@pytest.mark.asyncio
async def test_authenticated_user_sees_history(auth_client):
    """Authenticated user can access dashboard history page."""
    # Login
    resp = await auth_client.post(
        "/dashboard/login",
        data={"username": TEST_ADMIN_USER, "password": TEST_ADMIN_PASSWORD},
        follow_redirects=False,
    )
    cookies = resp.cookies

    # Access history
    resp = await auth_client.get("/dashboard/history", cookies=cookies)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_navbar_shows_username_and_role(auth_client):
    """Dashboard navbar displays username and role badge."""
    # Login
    resp = await auth_client.post(
        "/dashboard/login",
        data={"username": TEST_ADMIN_USER, "password": TEST_ADMIN_PASSWORD},
        follow_redirects=False,
    )
    cookies = resp.cookies

    # Access a page
    resp = await auth_client.get("/dashboard/history", cookies=cookies)
    assert resp.status_code == 200
    assert TEST_ADMIN_USER in resp.text
    assert "ADMIN" in resp.text.upper()
