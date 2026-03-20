"""Scan lifecycle API endpoints: trigger, status, list, findings."""

import math

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select

from scanner.api.auth import require_api_key
from scanner.api.schemas import (
    FindingResponse,
    PaginatedResponse,
    ScanDetailResponse,
    ScanRequest,
    ScanResponse,
)
from scanner.core.suppression import get_suppressed_fingerprints
from scanner.models.finding import Finding
from scanner.models.scan import ScanResult
from scanner.schemas.severity import Severity

router = APIRouter(prefix="/scans", tags=["scans"])


def _gate_int_to_bool(value: int | None) -> bool | None:
    """Convert gate_passed integer (0/1/NULL) to bool/None."""
    if value is None:
        return None
    return bool(value)


def _scan_to_detail(scan: ScanResult) -> ScanDetailResponse:
    """Convert a ScanResult ORM object to ScanDetailResponse."""
    return ScanDetailResponse(
        id=scan.id,
        status=scan.status,
        target_path=scan.target_path,
        repo_url=scan.repo_url,
        branch=scan.branch,
        commit_hash=scan.commit_hash,
        started_at=scan.started_at,
        completed_at=scan.completed_at,
        duration_seconds=scan.duration_seconds,
        total_findings=scan.total_findings or 0,
        critical_count=scan.critical_count or 0,
        high_count=scan.high_count or 0,
        medium_count=scan.medium_count or 0,
        low_count=scan.low_count or 0,
        info_count=scan.info_count or 0,
        gate_passed=_gate_int_to_bool(scan.gate_passed),
        error_message=scan.error_message,
        ai_cost_usd=scan.ai_cost_usd,
    )


@router.post("", status_code=202, response_model=ScanResponse)
async def trigger_scan(
    body: ScanRequest,
    request: Request,
    _api_key: str = Depends(require_api_key),
) -> ScanResponse:
    """Trigger a new security scan.

    Creates a scan record with status 'queued' and enqueues it
    for background processing.
    """
    async with request.app.state.session_factory() as session:
        async with session.begin():
            db_scan = ScanResult(
                target_path=body.path,
                repo_url=body.repo_url,
                branch=body.branch,
                skip_ai=body.skip_ai,
                status="queued",
            )
            session.add(db_scan)
            await session.flush()
            scan_id = db_scan.id

    await request.app.state.scan_queue.enqueue(scan_id)
    return ScanResponse(id=scan_id, status="queued")


@router.get("", response_model=PaginatedResponse[ScanDetailResponse])
async def list_scans(
    request: Request,
    page: int = 1,
    page_size: int = 20,
    _api_key: str = Depends(require_api_key),
) -> PaginatedResponse[ScanDetailResponse]:
    """List scan history with pagination, most recent first."""
    async with request.app.state.session_factory() as session:
        # Total count
        count_result = await session.execute(
            select(func.count()).select_from(ScanResult)
        )
        total = count_result.scalar() or 0

        # Paginated results
        offset = (page - 1) * page_size
        result = await session.execute(
            select(ScanResult)
            .order_by(ScanResult.id.desc())
            .offset(offset)
            .limit(page_size)
        )
        scans = result.scalars().all()

    items = [_scan_to_detail(s) for s in scans]
    pages = math.ceil(total / page_size) if page_size > 0 else 0

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{scan_id}", response_model=ScanDetailResponse)
async def get_scan(
    scan_id: int,
    request: Request,
    _api_key: str = Depends(require_api_key),
) -> ScanDetailResponse:
    """Get detailed information about a specific scan."""
    async with request.app.state.session_factory() as session:
        result = await session.execute(
            select(ScanResult).where(ScanResult.id == scan_id)
        )
        scan = result.scalar_one_or_none()

    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")

    return _scan_to_detail(scan)


@router.get("/{scan_id}/progress")
async def get_scan_progress(
    scan_id: int,
    request: Request,
):
    """Get real-time scan progress (no auth required for polling)."""
    scan_queue = request.app.state.scan_queue
    progress = scan_queue.get_progress(scan_id)
    if progress is None:
        # Check if scan exists and is completed
        async with request.app.state.session_factory() as session:
            result = await session.execute(
                select(ScanResult.status).where(ScanResult.id == scan_id)
            )
            row = result.first()
        if row is None:
            raise HTTPException(status_code=404, detail="Scan not found")
        if row[0] == "completed":
            return {"stage": "completed", "details": {}}
        if row[0] == "failed":
            return {"stage": "failed", "details": {}}
        return {"stage": "queued", "details": {}}
    return progress


@router.get("/{scan_id}/report")
async def get_scan_report(
    scan_id: int,
    request: Request,
    _api_key: str = Depends(require_api_key),
):
    """Get the HTML report for a completed scan.

    Returns 409 if the scan is not yet completed.
    """
    from fastapi.responses import HTMLResponse

    async with request.app.state.session_factory() as session:
        result = await session.execute(
            select(ScanResult).where(ScanResult.id == scan_id)
        )
        scan = result.scalar_one_or_none()

    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")

    if scan.status != "completed":
        raise HTTPException(
            status_code=409,
            detail=f"Scan is not completed (status: {scan.status})",
        )

    # Simple HTML summary for now
    html = f"""<!DOCTYPE html>
<html><head><title>Scan {scan.id} Report</title></head>
<body>
<h1>Scan {scan.id} Report</h1>
<p>Status: {scan.status}</p>
<p>Total findings: {scan.total_findings}</p>
<p>Critical: {scan.critical_count} | High: {scan.high_count} | Medium: {scan.medium_count} | Low: {scan.low_count} | Info: {scan.info_count}</p>
</body></html>"""
    return HTMLResponse(content=html)


@router.get(
    "/{scan_id}/findings",
    response_model=PaginatedResponse[FindingResponse],
)
async def get_scan_findings(
    scan_id: int,
    request: Request,
    page: int = 1,
    page_size: int = 50,
    _api_key: str = Depends(require_api_key),
) -> PaginatedResponse[FindingResponse]:
    """Get paginated findings for a specific scan.

    Each finding includes a 'suppressed' flag based on the
    global suppressions table.
    """
    async with request.app.state.session_factory() as session:
        # Verify scan exists
        scan_result = await session.execute(
            select(ScanResult.id).where(ScanResult.id == scan_id)
        )
        if scan_result.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="Scan not found")

        # Get suppressed fingerprints
        suppressed_fps = await get_suppressed_fingerprints(session)

        # Total findings count
        count_result = await session.execute(
            select(func.count()).select_from(Finding).where(
                Finding.scan_id == scan_id
            )
        )
        total = count_result.scalar() or 0

        # Paginated findings
        offset = (page - 1) * page_size
        result = await session.execute(
            select(Finding)
            .where(Finding.scan_id == scan_id)
            .offset(offset)
            .limit(page_size)
        )
        findings = result.scalars().all()

    items = [
        FindingResponse(
            fingerprint=f.fingerprint,
            tool=f.tool,
            rule_id=f.rule_id,
            file_path=f.file_path,
            line_start=f.line_start,
            line_end=f.line_end,
            snippet=f.snippet,
            severity=Severity(f.severity).name,
            title=f.title,
            description=f.description,
            recommendation=f.recommendation,
            ai_analysis=f.ai_analysis,
            ai_fix_suggestion=f.ai_fix_suggestion,
            suppressed=f.fingerprint in suppressed_fps,
        )
        for f in findings
    ]

    pages = math.ceil(total / page_size) if page_size > 0 else 0

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )
