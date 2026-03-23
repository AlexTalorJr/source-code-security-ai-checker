"""Tests for authentication and authorization (AUTH-07)."""

import pytest


@pytest.mark.asyncio
async def test_unauthenticated_api_returns_401(auth_client):
    """Unauthenticated requests to protected API endpoints return 401."""
    endpoints = [
        ("GET", "/api/scans"),
        ("POST", "/api/scans"),
        ("GET", "/api/scanners"),
    ]
    for method, path in endpoints:
        resp = await auth_client.request(method, path)
        assert resp.status_code == 401, f"{method} {path} returned {resp.status_code}, expected 401"


@pytest.mark.asyncio
async def test_invalid_bearer_token_returns_401(auth_client):
    """Invalid Bearer token returns 401."""
    resp = await auth_client.get(
        "/api/scans",
        headers={"Authorization": "Bearer nvsec_invalid_token_here"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_page_does_not_require_auth(auth_client):
    """Login page is accessible without authentication."""
    resp = await auth_client.get("/dashboard/login")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_dashboard_without_cookie_redirects_to_login(auth_client):
    """Dashboard pages without valid session redirect to login."""
    resp = await auth_client.get("/dashboard/history", follow_redirects=False)
    assert resp.status_code == 302
    assert "/dashboard/login" in resp.headers.get("location", "")
