"""Tests that scan_queue worker calls notify_scan_complete with correct args."""

from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from scanner.config import (
    NotificationSlackConfig,
    NotificationsConfig,
    ScannerSettings,
)
from scanner.main import create_app
from scanner.schemas.scan import ScanResultSchema
from tests.phase_05.conftest import seed_scan


@asynccontextmanager
async def _lifespan_client(app):
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


@pytest.mark.asyncio
async def test_worker_calls_notify_with_correct_arg_order(
    tmp_path, monkeypatch
):
    """The scan queue worker must call notify_scan_complete(scan_result, delta, settings).

    This test catches the bug where arguments were passed as (settings, scan_id, scan_result).
    """
    db_path = str(tmp_path / "test.db")
    monkeypatch.setenv("SCANNER_DB_PATH", db_path)
    monkeypatch.setenv("SCANNER_CONFIG_PATH", str(tmp_path / "nonexistent.yml"))
    monkeypatch.setenv("SCANNER_API_KEY", "test-key-notify")
    monkeypatch.setenv("SCANNER_SLACK_WEBHOOK_URL", "https://hooks.slack.com/test")

    app = create_app()

    # Configure notifications enabled
    async with _lifespan_client(app) as client:
        settings: ScannerSettings = app.state.settings
        settings.notifications = NotificationsConfig(
            slack=NotificationSlackConfig(enabled=True),
        )
        settings.slack_webhook_url = "https://hooks.slack.com/test"

        # Seed a queued scan
        async with app.state.session_factory() as session:
            async with session.begin():
                scan_id = await seed_scan(session, status="queued")

        # Mock run_scan to return immediately
        fake_result = ScanResultSchema(
            id=scan_id,
            branch="main",
            status="completed",
            duration_seconds=1.0,
            total_findings=0,
            critical_count=0,
            high_count=0,
            medium_count=0,
            low_count=0,
            info_count=0,
            gate_passed=True,
        )
        mock_run_scan = AsyncMock(return_value=(fake_result, [], []))

        mock_slack = AsyncMock()
        mock_email = AsyncMock()

        with (
            patch("scanner.core.orchestrator.run_scan", mock_run_scan),
            patch(
                "scanner.notifications.service.send_slack_notification",
                mock_slack,
            ),
            patch(
                "scanner.notifications.service.send_email_notification",
                mock_email,
            ),
        ):
            # Enqueue and let worker process one item
            await app.state.scan_queue.enqueue(scan_id)
            worker_task = asyncio.create_task(
                app.state.scan_queue.worker(app)
            )
            # Wait for the queue to drain (item processed)
            await asyncio.wait_for(
                app.state.scan_queue._queue.join(), timeout=5.0
            )
            worker_task.cancel()

            # Slack notification should have been called
            mock_slack.assert_awaited_once()

            # CRITICAL: verify first argument is ScanResultSchema, NOT ScannerSettings or int
            call_args = mock_slack.call_args
            first_arg = call_args[0][0]
            assert isinstance(
                first_arg, ScanResultSchema
            ), f"Expected ScanResultSchema as first arg, got {type(first_arg).__name__}"


@pytest.mark.asyncio
async def test_worker_notification_failure_does_not_crash_worker(
    tmp_path, monkeypatch
):
    """If notify_scan_complete raises, the worker logs a warning but does not crash."""
    db_path = str(tmp_path / "test.db")
    monkeypatch.setenv("SCANNER_DB_PATH", db_path)
    monkeypatch.setenv("SCANNER_CONFIG_PATH", str(tmp_path / "nonexistent.yml"))
    monkeypatch.setenv("SCANNER_API_KEY", "test-key-notify2")

    app = create_app()

    async with _lifespan_client(app) as client:
        async with app.state.session_factory() as session:
            async with session.begin():
                scan_id = await seed_scan(session, status="queued")

        fake_result = ScanResultSchema(
            id=scan_id, status="completed", gate_passed=True,
            total_findings=0, critical_count=0, high_count=0,
            medium_count=0, low_count=0, info_count=0,
        )
        mock_run_scan = AsyncMock(return_value=(fake_result, [], []))

        with (
            patch("scanner.core.orchestrator.run_scan", mock_run_scan),
            patch(
                "scanner.notifications.service.send_slack_notification",
                AsyncMock(side_effect=Exception("Slack down")),
            ),
            patch(
                "scanner.notifications.service.send_email_notification",
                AsyncMock(),
            ),
        ):
            await app.state.scan_queue.enqueue(scan_id)
            worker_task = asyncio.create_task(
                app.state.scan_queue.worker(app)
            )
            await asyncio.wait_for(
                app.state.scan_queue._queue.join(), timeout=5.0
            )
            worker_task.cancel()
            # No exception raised -- worker handled it gracefully
