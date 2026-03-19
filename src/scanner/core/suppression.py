"""Suppression query logic for managing false positive fingerprints."""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from scanner.models.suppression import Suppression


async def get_suppressed_fingerprints(session: AsyncSession) -> set[str]:
    """Return the set of all suppressed fingerprints.

    Args:
        session: Active async database session.

    Returns:
        Set of fingerprint strings that are currently suppressed.
    """
    result = await session.execute(select(Suppression.fingerprint))
    return {row[0] for row in result.fetchall()}


async def suppress_fingerprint(
    session: AsyncSession,
    fingerprint: str,
    reason: str | None = None,
) -> Suppression:
    """Suppress a fingerprint (mark as false positive).

    If the fingerprint is already suppressed, returns the existing record.

    Args:
        session: Active async database session.
        fingerprint: SHA-256 fingerprint to suppress.
        reason: Optional reason for suppression.

    Returns:
        The Suppression record (new or existing).
    """
    # Check if already suppressed
    result = await session.execute(
        select(Suppression).where(Suppression.fingerprint == fingerprint)
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        return existing

    suppression = Suppression(fingerprint=fingerprint, reason=reason)
    session.add(suppression)
    await session.flush()
    return suppression


async def unsuppress_fingerprint(
    session: AsyncSession, fingerprint: str
) -> bool:
    """Remove suppression for a fingerprint.

    Args:
        session: Active async database session.
        fingerprint: SHA-256 fingerprint to unsuppress.

    Returns:
        True if the fingerprint was suppressed and is now removed,
        False if it was not suppressed.
    """
    result = await session.execute(
        delete(Suppression).where(Suppression.fingerprint == fingerprint)
    )
    return result.rowcount > 0


async def is_suppressed(session: AsyncSession, fingerprint: str) -> bool:
    """Check if a fingerprint is currently suppressed.

    Args:
        session: Active async database session.
        fingerprint: SHA-256 fingerprint to check.

    Returns:
        True if suppressed, False otherwise.
    """
    result = await session.execute(
        select(Suppression.id).where(Suppression.fingerprint == fingerprint)
    )
    return result.scalar_one_or_none() is not None
