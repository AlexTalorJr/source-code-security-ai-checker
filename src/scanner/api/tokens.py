"""API token management endpoints (per user)."""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, func

from scanner.api.auth import get_current_user
from scanner.models.user import APIToken, User
from scanner.schemas.auth import TokenCreate, TokenCreatedResponse, TokenResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tokens", tags=["tokens"])

SOFT_TOKEN_LIMIT = 10


def _generate_api_token() -> tuple[str, str]:
    """Generate a new API token and its hash.

    Returns:
        Tuple of (raw_token, token_hash). Raw token shown once;
        token_hash stored in database.
    """
    random_part = secrets.token_hex(32)
    raw_token = f"nvsec_{random_part}"
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    return raw_token, token_hash


@router.post("", response_model=TokenCreatedResponse, status_code=200)
async def create_token(
    body: TokenCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Generate a new personal API token.

    Args:
        body: Token creation data (name, optional expiration).
        request: FastAPI request.
        current_user: Authenticated user.

    Returns:
        Token created response with raw token (shown once).
    """
    async with request.app.state.session_factory() as session:
        # Check soft limit
        active_count = await session.scalar(
            select(func.count(APIToken.id)).where(
                APIToken.user_id == current_user.id,
                APIToken.revoked_at.is_(None),
            )
        )
        if active_count >= SOFT_TOKEN_LIMIT:
            raise HTTPException(
                status_code=400,
                detail=f"Maximum of {SOFT_TOKEN_LIMIT} active tokens reached. Revoke an existing token first.",
            )

        raw_token, token_hash = _generate_api_token()

        expires_at = None
        if body.expires_in_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=body.expires_in_days)

        token = APIToken(
            user_id=current_user.id,
            token_hash=token_hash,
            name=body.name,
            expires_at=expires_at,
        )
        session.add(token)
        await session.commit()
        await session.refresh(token)

        logger.info("Token created: %s for user %s", body.name, current_user.username)
        return TokenCreatedResponse(
            id=token.id,
            name=token.name,
            raw_token=raw_token,
            expires_at=token.expires_at,
        )


@router.get("", response_model=list[TokenResponse])
async def list_tokens(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """List current user's API tokens.

    Args:
        request: FastAPI request.
        current_user: Authenticated user.

    Returns:
        List of token responses (masked).
    """
    async with request.app.state.session_factory() as session:
        result = await session.execute(
            select(APIToken)
            .where(APIToken.user_id == current_user.id)
            .order_by(APIToken.created_at.desc())
        )
        tokens = result.scalars().all()
        return [
            TokenResponse(
                id=t.id,
                name=t.name,
                token_prefix=f"nvsec_{t.token_hash[:8]}...",
                created_at=t.created_at,
                expires_at=t.expires_at,
                revoked_at=t.revoked_at,
                last_used_at=t.last_used_at,
            )
            for t in tokens
        ]


@router.delete("/{token_id}", status_code=204)
async def revoke_token(
    token_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Revoke a personal API token.

    Args:
        token_id: ID of token to revoke.
        request: FastAPI request.
        current_user: Authenticated user.
    """
    async with request.app.state.session_factory() as session:
        result = await session.execute(
            select(APIToken).where(
                APIToken.id == token_id,
                APIToken.user_id == current_user.id,
            )
        )
        token = result.scalar_one_or_none()
        if not token:
            raise HTTPException(status_code=404, detail="Token not found")

        if token.revoked_at is not None:
            raise HTTPException(status_code=400, detail="Token already revoked")

        token.revoked_at = datetime.now(timezone.utc)
        await session.commit()
        logger.info("Token revoked: %s for user %s", token.name, current_user.username)
