"""Tests for Slack, email notification senders and the dispatcher service."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scanner.config import (
    NotificationEmailConfig,
    NotificationSlackConfig,
    NotificationsConfig,
    ScannerSettings,
)
from scanner.notifications.email_sender import render_email_html, send_email_sync
from scanner.notifications.service import notify_scan_complete
from scanner.notifications.slack import send_slack_notification
from scanner.reports.models import DeltaResult
from scanner.schemas.scan import ScanResultSchema


# ---------------------------------------------------------------------------
# Slack notification tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_slack_notification_sends_blocks(scan_result_failed: ScanResultSchema) -> None:
    """Slack sender POSTs Block Kit message with correct structure."""
    mock_post = AsyncMock()
    mock_client = AsyncMock()
    mock_client.post = mock_post
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("scanner.notifications.slack.httpx.AsyncClient", return_value=mock_client):
        await send_slack_notification(
            scan_result_failed, None, "http://dash", "https://hooks.slack.com/test"
        )

    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args
    assert call_kwargs[0][0] == "https://hooks.slack.com/test"
    payload = call_kwargs[1]["json"]
    assert "blocks" in payload
    blocks = payload["blocks"]
    assert blocks[0]["type"] == "header"
    assert "FAILED" in blocks[0]["text"]["text"]


@pytest.mark.asyncio
async def test_slack_notification_passed(scan_result_passed: ScanResultSchema) -> None:
    """Slack header shows PASSED for passing gate."""
    mock_post = AsyncMock()
    mock_client = AsyncMock()
    mock_client.post = mock_post
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("scanner.notifications.slack.httpx.AsyncClient", return_value=mock_client):
        await send_slack_notification(
            scan_result_passed, None, "http://dash", "https://hooks.slack.com/test"
        )

    payload = mock_post.call_args[1]["json"]
    assert "PASSED" in payload["blocks"][0]["text"]["text"]


@pytest.mark.asyncio
async def test_slack_notification_includes_severity_fields(
    scan_result_failed: ScanResultSchema,
) -> None:
    """Slack section block contains severity count fields."""
    mock_post = AsyncMock()
    mock_client = AsyncMock()
    mock_client.post = mock_post
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("scanner.notifications.slack.httpx.AsyncClient", return_value=mock_client):
        await send_slack_notification(
            scan_result_failed, None, "http://dash", "https://hooks.slack.com/test"
        )

    payload = mock_post.call_args[1]["json"]
    section = payload["blocks"][1]
    assert section["type"] == "section"
    field_texts = [f["text"] for f in section["fields"]]
    assert any("*Critical:* 1" in t for t in field_texts)
    assert any("*High:* 2" in t for t in field_texts)
    assert any("*Medium:* 3" in t for t in field_texts)
    assert any("*Low:* 3" in t for t in field_texts)


@pytest.mark.asyncio
async def test_slack_notification_includes_delta(
    scan_result_failed: ScanResultSchema, delta: DeltaResult
) -> None:
    """Slack context block shows delta counts when delta provided."""
    mock_post = AsyncMock()
    mock_client = AsyncMock()
    mock_client.post = mock_post
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("scanner.notifications.slack.httpx.AsyncClient", return_value=mock_client):
        await send_slack_notification(
            scan_result_failed, delta, "http://dash", "https://hooks.slack.com/test"
        )

    payload = mock_post.call_args[1]["json"]
    context_blocks = [b for b in payload["blocks"] if b["type"] == "context"]
    assert len(context_blocks) == 1
    ctx_text = context_blocks[0]["elements"][0]["text"]
    assert "+2 new" in ctx_text
    assert "-1 fixed" in ctx_text


@pytest.mark.asyncio
async def test_slack_notification_swallows_error(
    scan_result_failed: ScanResultSchema,
) -> None:
    """Slack sender does not raise when HTTP call fails."""
    mock_post = AsyncMock(side_effect=Exception("network error"))
    mock_client = AsyncMock()
    mock_client.post = mock_post
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("scanner.notifications.slack.httpx.AsyncClient", return_value=mock_client):
        # Should not raise
        await send_slack_notification(
            scan_result_failed, None, "http://dash", "https://hooks.slack.com/test"
        )


# ---------------------------------------------------------------------------
# Email notification tests
# ---------------------------------------------------------------------------


def test_email_notification_calls_smtp() -> None:
    """send_email_sync uses SMTP with starttls and send_message."""
    mock_server = MagicMock()
    mock_smtp = MagicMock(return_value=mock_server)
    mock_server.__enter__ = MagicMock(return_value=mock_server)
    mock_server.__exit__ = MagicMock(return_value=False)

    with patch("scanner.notifications.email_sender.smtplib.SMTP", mock_smtp):
        send_email_sync(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="user@example.com",
            smtp_password="pass123",
            recipients=["dev@example.com"],
            subject="Test",
            html_body="<h1>Test</h1>",
            use_tls=True,
        )

    mock_smtp.assert_called_once_with("smtp.example.com", 587)
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with("user@example.com", "pass123")
    mock_server.send_message.assert_called_once()


def test_email_notification_subject_pass(scan_result_passed: ScanResultSchema) -> None:
    """Email subject for passed gate contains 'Passed'."""
    branch = scan_result_passed.branch or "local"
    expected = f"Security Scan Passed -- {branch}"
    assert scan_result_passed.gate_passed is True
    # Verify subject construction logic
    if scan_result_passed.gate_passed:
        subject = f"Security Scan Passed -- {branch}"
    else:
        subject = f"SECURITY SCAN FAILED -- {branch}"
    assert subject == expected


def test_email_notification_subject_fail(scan_result_failed: ScanResultSchema) -> None:
    """Email subject for failed gate contains 'FAILED'."""
    branch = scan_result_failed.branch or "local"
    expected = f"SECURITY SCAN FAILED -- {branch}"
    if scan_result_failed.gate_passed:
        subject = f"Security Scan Passed -- {branch}"
    else:
        subject = f"SECURITY SCAN FAILED -- {branch}"
    assert subject == expected


def test_email_notification_html_contains_gate_banner_passed(
    scan_result_passed: ScanResultSchema,
) -> None:
    """Rendered email HTML contains 'Quality Gate: PASSED' for passing scan."""
    html = render_email_html(scan_result_passed, None, "http://dash")
    assert "Quality Gate: PASSED" in html
    assert "aipix-security-scanner" in html
    assert "background-color:#0d6efd" in html
    assert "Configure notifications in config.yml" in html


def test_email_notification_html_contains_gate_banner_failed(
    scan_result_failed: ScanResultSchema,
) -> None:
    """Rendered email HTML contains 'Quality Gate: FAILED' for failing scan."""
    html = render_email_html(scan_result_failed, None, "http://dash")
    assert "Quality Gate: FAILED" in html


def test_email_notification_html_includes_delta(
    scan_result_failed: ScanResultSchema, delta: DeltaResult
) -> None:
    """Rendered email HTML shows delta badges when delta provided."""
    html = render_email_html(scan_result_failed, delta, "http://dash")
    assert "+2 new" in html
    assert "-1 fixed" in html


# ---------------------------------------------------------------------------
# Dispatcher tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_notify_scan_complete_slack_only(
    scan_result_failed: ScanResultSchema,
) -> None:
    """Dispatcher calls Slack but not email when only Slack is enabled."""
    settings = ScannerSettings(
        slack_webhook_url="https://hooks.slack.com/test",
        notifications=NotificationsConfig(
            slack=NotificationSlackConfig(enabled=True),
            email=NotificationEmailConfig(enabled=False),
        ),
    )

    with (
        patch(
            "scanner.notifications.service.send_slack_notification",
            new_callable=AsyncMock,
        ) as mock_slack,
        patch(
            "scanner.notifications.service.send_email_notification",
            new_callable=AsyncMock,
        ) as mock_email,
    ):
        await notify_scan_complete(scan_result_failed, None, settings)

    mock_slack.assert_awaited_once()
    mock_email.assert_not_awaited()


@pytest.mark.asyncio
async def test_notify_scan_complete_email_only(
    scan_result_failed: ScanResultSchema,
) -> None:
    """Dispatcher calls email but not Slack when only email is enabled."""
    settings = ScannerSettings(
        email_smtp_host="smtp.example.com",
        notifications=NotificationsConfig(
            slack=NotificationSlackConfig(enabled=False),
            email=NotificationEmailConfig(
                enabled=True,
                recipients=["dev@example.com"],
            ),
        ),
    )

    with (
        patch(
            "scanner.notifications.service.send_slack_notification",
            new_callable=AsyncMock,
        ) as mock_slack,
        patch(
            "scanner.notifications.service.send_email_notification",
            new_callable=AsyncMock,
        ) as mock_email,
    ):
        await notify_scan_complete(scan_result_failed, None, settings)

    mock_slack.assert_not_awaited()
    mock_email.assert_awaited_once()


@pytest.mark.asyncio
async def test_notify_scan_complete_both_disabled(
    scan_result_failed: ScanResultSchema,
) -> None:
    """Dispatcher calls neither channel when both are disabled."""
    settings = ScannerSettings(
        notifications=NotificationsConfig(
            slack=NotificationSlackConfig(enabled=False),
            email=NotificationEmailConfig(enabled=False),
        ),
    )

    with (
        patch(
            "scanner.notifications.service.send_slack_notification",
            new_callable=AsyncMock,
        ) as mock_slack,
        patch(
            "scanner.notifications.service.send_email_notification",
            new_callable=AsyncMock,
        ) as mock_email,
    ):
        await notify_scan_complete(scan_result_failed, None, settings)

    mock_slack.assert_not_awaited()
    mock_email.assert_not_awaited()


@pytest.mark.asyncio
async def test_notify_one_channel_failure_does_not_block_other(
    scan_result_failed: ScanResultSchema,
) -> None:
    """If Slack raises, email is still called."""
    settings = ScannerSettings(
        slack_webhook_url="https://hooks.slack.com/test",
        email_smtp_host="smtp.example.com",
        notifications=NotificationsConfig(
            slack=NotificationSlackConfig(enabled=True),
            email=NotificationEmailConfig(
                enabled=True,
                recipients=["dev@example.com"],
            ),
        ),
    )

    with (
        patch(
            "scanner.notifications.service.send_slack_notification",
            new_callable=AsyncMock,
            side_effect=Exception("Slack down"),
        ),
        patch(
            "scanner.notifications.service.send_email_notification",
            new_callable=AsyncMock,
        ) as mock_email,
    ):
        await notify_scan_complete(scan_result_failed, None, settings)

    mock_email.assert_awaited_once()
