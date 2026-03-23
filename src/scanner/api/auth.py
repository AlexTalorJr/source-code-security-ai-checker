"""Unified authentication and authorization dependencies for API and dashboard."""

import hashlib
import logging
from datetime import datetime, timezone
from enum import Enum

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select

from scanner.dashboard.auth import COOKIE_NAME, verify_session_jwt
from scanner.models.user import APIToken, User

logger = logging.getLogger(__name__)


class Role(str, Enum):
    """User roles for authorization."""

    ADMIN = "admin"
    SCANNER = "scanner"
    VIEWER = "viewer"


async def get_current_user(request: Request) -> User:
    """Resolve current user from Bearer token or session cookie.

    Checks in order:
    1. Authorization: Bearer <token> header -- hash token, look up in api_tokens
    2. scanner_session cookie -- decode JWT, look up user by ID

    Args:
        request: FastAPI request object.

    Returns:
        Authenticated User object.

    Raises:
        HTTPException: 401 if no valid authentication found.
        HTTPException: 401 if user is inactive.
    """
    session_factory = request.app.state.session_factory
    settings = request.app.state.settings

    # Path 1: Bearer token
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        raw_token = auth_header[7:]
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        async with session_factory() as session:
            result = await session.execute(
                select(APIToken).where(APIToken.token_hash == token_hash)
            )
            api_token = result.scalar_one_or_none()

            if api_token is None:
                raise HTTPException(status_code=401, detail="Invalid API token")

            if api_token.revoked_at is not None:
                raise HTTPException(status_code=401, detail="Token has been revoked")

            if api_token.expires_at and api_token.expires_at < datetime.now(timezone.utc):
                raise HTTPException(status_code=401, detail="Token has expired")

            # Update last_used_at
            api_token.last_used_at = datetime.now(timezone.utc)
            await session.commit()

            # Load user
            user_result = await session.execute(
                select(User).where(User.id == api_token.user_id)
            )
            user = user_result.scalar_one_or_none()

            if user is None or not user.is_active:
                raise HTTPException(status_code=401, detail="User account is inactive")

            return user

    # Path 2: JWT session cookie
    cookie_token = request.cookies.get(COOKIE_NAME)
    if cookie_token:
        payload = verify_session_jwt(cookie_token, settings.secret_key)
        if payload:
            user_id = int(payload["sub"])
            async with session_factory() as session:
                result = await session.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()

                if user is None or not user.is_active:
                    raise HTTPException(status_code=401, detail="User account is inactive")

                return user

    raise HTTPException(status_code=401, detail="Authentication required")


def require_role(*roles: Role):
    """Dependency factory: require one of the specified roles.

    Args:
        *roles: Allowed Role enum values.

    Returns:
        FastAPI dependency that validates user role.
    """
    async def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in [r.value for r in roles]:
            raise HTTPException(
                status_code=403,
                detail=f"Requires role: {', '.join(r.value for r in roles)}",
            )
        return user

    return checker
