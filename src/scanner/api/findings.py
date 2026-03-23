"""Findings management API endpoints: suppression and unsuppression."""

from fastapi import APIRouter, Depends, HTTPException, Request

from scanner.api.auth import get_current_user
from scanner.models.user import User
from scanner.api.schemas import SuppressionRequest
from scanner.core.suppression import suppress_fingerprint, unsuppress_fingerprint

router = APIRouter(prefix="/findings", tags=["findings"])


@router.put("/{fingerprint}/suppress", status_code=200)
async def suppress(
    fingerprint: str,
    request: Request,
    body: SuppressionRequest | None = None,
    current_user: User = Depends(get_current_user),
) -> dict:
    """Suppress a finding by fingerprint (mark as false positive).

    If the fingerprint is already suppressed, this is a no-op
    and returns the existing suppression.
    """
    reason = body.reason if body else None
    async with request.app.state.session_factory() as session:
        async with session.begin():
            suppression = await suppress_fingerprint(
                session, fingerprint, reason
            )
            return {
                "fingerprint": suppression.fingerprint,
                "suppressed": True,
                "reason": suppression.reason,
            }


@router.delete("/{fingerprint}/suppress", status_code=200)
async def unsuppress(
    fingerprint: str,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> dict:
    """Remove suppression for a finding by fingerprint.

    Returns 404 if the fingerprint was not suppressed.
    """
    async with request.app.state.session_factory() as session:
        async with session.begin():
            deleted = await unsuppress_fingerprint(session, fingerprint)
            if not deleted:
                raise HTTPException(
                    status_code=404,
                    detail="Fingerprint not suppressed",
                )
            return {"fingerprint": fingerprint, "suppressed": False}
