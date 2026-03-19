"""Dashboard cookie-based authentication."""

import hashlib
import secrets

from fastapi import Request
from fastapi.responses import RedirectResponse


def make_session_token(api_key: str) -> str:
    """Create a session token from the API key (SHA-256 hash)."""
    return hashlib.sha256(api_key.encode()).hexdigest()


async def require_dashboard_auth(request: Request):
    """Check session cookie. Returns None if valid, RedirectResponse if not."""
    token = request.cookies.get("scanner_session")
    expected = make_session_token(request.app.state.settings.api_key)
    if not token or not secrets.compare_digest(token, expected):
        return RedirectResponse(url="/dashboard/login", status_code=302)
    return None
