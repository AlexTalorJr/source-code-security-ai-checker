"""Background scan queue for processing scan requests serially."""

import asyncio
import logging
from datetime import datetime

from fastapi import FastAPI
from sqlalchemy import select, update

from scanner.models.finding import Finding
from scanner.models.scan import ScanResult
from scanner.schemas.scan import ScanResultSchema

logger = logging.getLogger(__name__)


class ScanQueue:
    """Async queue that processes scans one at a time in the background.

    Usage:
        queue = ScanQueue()
        await queue.enqueue(scan_id)
        task = asyncio.create_task(queue.worker(app))
    """

    def __init__(self) -> None:
        self._queue: asyncio.Queue[int] = asyncio.Queue()
        self._current_scan_id: int | None = None
        self._progress: dict = {}  # {scan_id: {"stage": ..., "details": ...}}

    async def enqueue(self, scan_id: int) -> None:
        """Add a scan ID to the processing queue."""
        await self._queue.put(scan_id)

    @property
    def current_scan_id(self) -> int | None:
        """Return the scan ID currently being processed, or None."""
        return self._current_scan_id

    def get_progress(self, scan_id: int) -> dict | None:
        """Return current progress for a scan, or None if not tracking."""
        return self._progress.get(scan_id)

    async def worker(self, app: FastAPI) -> None:
        """Infinite loop that processes scans from the queue.

        Each scan is run via the orchestrator's run_scan function.
        On success, results are persisted. On failure, the scan is
        marked as failed with the error message.
        """
        from scanner.core.orchestrator import run_scan

        while True:
            scan_id = await self._queue.get()
            self._current_scan_id = scan_id
            try:
                async with app.state.session_factory() as session:
                    # Mark as running
                    await session.execute(
                        update(ScanResult)
                        .where(ScanResult.id == scan_id)
                        .values(
                            status="running", started_at=datetime.utcnow()
                        )
                    )
                    await session.commit()

                    # Read scan parameters
                    result = await session.execute(
                        select(ScanResult).where(ScanResult.id == scan_id)
                    )
                    db_scan = result.scalar_one()
                    target_path = db_scan.target_path
                    repo_url = db_scan.repo_url
                    branch = db_scan.branch
                    skip_ai = db_scan.skip_ai
                    target_url = db_scan.target_url
                    profile_name = db_scan.profile_name

                # Progress callback
                def _progress_cb(stage, details):
                    self._progress[scan_id] = {
                        "stage": stage,
                        "details": details,
                    }

                self._progress[scan_id] = {"stage": "starting", "details": {}}

                # Run scan (worker persists results itself, skip run_scan's persist)
                scan_result, findings, compound_risks = await run_scan(
                    app.state.settings,
                    target_path=target_path if not target_url else None,
                    repo_url=repo_url if not target_url else None,
                    branch=branch if not target_url else None,
                    target_url=target_url,
                    persist=False,
                    progress_callback=_progress_cb,
                    skip_ai=skip_ai,
                    profile_name=profile_name,
                )

                # Update DB record with results and persist findings
                async with app.state.session_factory() as session:
                    await session.execute(
                        update(ScanResult)
                        .where(ScanResult.id == scan_id)
                        .values(
                            status="completed",
                            completed_at=scan_result.completed_at,
                            started_at=scan_result.started_at,
                            duration_seconds=scan_result.duration_seconds,
                            total_findings=scan_result.total_findings,
                            critical_count=scan_result.critical_count,
                            high_count=scan_result.high_count,
                            medium_count=scan_result.medium_count,
                            low_count=scan_result.low_count,
                            info_count=scan_result.info_count,
                            gate_passed=(
                                1 if scan_result.gate_passed else 0
                            )
                            if scan_result.gate_passed is not None
                            else None,
                            error_message=scan_result.error_message,
                            ai_cost_usd=scan_result.ai_cost_usd,
                        )
                    )

                    # Persist individual findings (with AI enrichment if available)
                    for f in findings:
                        session.add(Finding(
                            scan_id=scan_id,
                            fingerprint=f.fingerprint,
                            tool=f.tool,
                            rule_id=f.rule_id,
                            file_path=f.file_path,
                            line_start=f.line_start,
                            line_end=f.line_end,
                            snippet=getattr(f, "snippet", None),
                            severity=f.severity.value if hasattr(f.severity, "value") else f.severity,
                            title=f.title,
                            description=f.description,
                            recommendation=getattr(f, "recommendation", None),
                            ai_analysis=getattr(f, "ai_analysis", None),
                            ai_fix_suggestion=getattr(f, "ai_fix_suggestion", None),
                        ))

                    await session.commit()

                # Ensure scan_result has id and target info for notifications
                scan_result.id = scan_id

                logger.info("Scan %d completed successfully", scan_id)

                # Notify (graceful -- module may not exist yet)
                try:
                    from scanner.notifications.service import (
                        notify_scan_complete,
                    )

                    await notify_scan_complete(
                        scan_result, None, app.state.settings
                    )
                except ImportError:
                    pass
                except Exception as notify_exc:
                    logger.warning(
                        "Notification failed for scan %d: %s",
                        scan_id,
                        notify_exc,
                    )

            except Exception as exc:
                logger.error(
                    "Scan %d failed: %s", scan_id, exc, exc_info=True
                )
                try:
                    async with app.state.session_factory() as session:
                        await session.execute(
                            update(ScanResult)
                            .where(ScanResult.id == scan_id)
                            .values(
                                status="failed",
                                error_message=str(exc),
                                completed_at=datetime.utcnow(),
                            )
                        )
                        await session.commit()
                except Exception as db_exc:
                    logger.error(
                        "Failed to update scan %d status: %s",
                        scan_id,
                        db_exc,
                    )
            finally:
                self._progress.pop(scan_id, None)
                self._current_scan_id = None
                self._queue.task_done()

    async def recover_stuck_scans(self, app: FastAPI) -> None:
        """Re-enqueue scans that were running or queued before a restart.

        Scans with status 'running' are reset to 'queued' and re-enqueued.
        Scans with status 'queued' are re-enqueued as-is.
        """
        async with app.state.session_factory() as session:
            # Reset running scans to queued
            await session.execute(
                update(ScanResult)
                .where(ScanResult.status == "running")
                .values(status="queued")
            )
            await session.commit()

            # Find all queued scans and re-enqueue
            result = await session.execute(
                select(ScanResult.id).where(ScanResult.status == "queued")
            )
            for (scan_id,) in result.fetchall():
                await self._queue.put(scan_id)
                logger.info("Recovered stuck scan %d", scan_id)
