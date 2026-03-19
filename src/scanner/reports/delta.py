"""Delta comparison between current and previous scan of the same branch."""

import logging

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from scanner.models.finding import Finding
from scanner.models.scan import ScanResult
from scanner.reports.models import DeltaResult
from scanner.schemas.finding import FindingSchema

logger = logging.getLogger(__name__)


async def get_previous_scan_fingerprints(
    branch: str,
    current_scan_id: int,
    session: AsyncSession,
) -> tuple[set[str], int | None]:
    """Get fingerprints from the most recent previous completed scan of the same branch.

    Returns (fingerprint_set, previous_scan_id). If no previous scan, returns (set(), None).
    """
    prev_scan_stmt = (
        select(ScanResult.id)
        .where(ScanResult.branch == branch)
        .where(ScanResult.id != current_scan_id)
        .where(ScanResult.status == "completed")
        .order_by(desc(ScanResult.created_at))
        .limit(1)
    )
    prev_result = await session.execute(prev_scan_stmt)
    prev_scan_id = prev_result.scalar_one_or_none()

    if prev_scan_id is None:
        return set(), None

    fp_stmt = select(Finding.fingerprint).where(Finding.scan_id == prev_scan_id)
    fp_result = await session.execute(fp_stmt)
    return {row[0] for row in fp_result.fetchall()}, prev_scan_id


async def compute_delta(
    current_findings: list[FindingSchema],
    branch: str | None,
    current_scan_id: int,
    session: AsyncSession,
) -> DeltaResult | None:
    """Compare current findings against the previous scan of the same branch.

    Returns None if branch is None or no previous scan exists.
    """
    if not branch:
        return None

    previous_fps, prev_scan_id = await get_previous_scan_fingerprints(
        branch, current_scan_id, session
    )

    if prev_scan_id is None:
        return None  # First scan on this branch

    current_fps = {f.fingerprint for f in current_findings}

    return DeltaResult(
        new_fingerprints=current_fps - previous_fps,
        fixed_fingerprints=previous_fps - current_fps,
        persisting_fingerprints=current_fps & previous_fps,
        previous_scan_id=prev_scan_id,
    )
