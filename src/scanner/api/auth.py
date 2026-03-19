"""API key authentication dependency for FastAPI endpoints."""

import secrets

from fastapi import Header, HTTPException, Request


async def require_api_key(
    request: Request,
    x_api_key: str = Header(..., alias="X-API-Key"),
) -> str:
    """FastAPI dependency that validates the X-API-Key header.

    Uses timing-safe comparison to prevent timing attacks.

    Args:
        request: FastAPI request (provides access to app settings).
        x_api_key: Value of the X-API-Key header.

    Returns:
        The validated API key string.

    Raises:
        HTTPException: 503 if API key not configured, 401 if key is invalid.
    """
    configured_key = request.app.state.settings.api_key
    if not configured_key:
        raise HTTPException(
            status_code=503,
            detail="API key not configured on server",
        )
    if not secrets.compare_digest(x_api_key, configured_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key
