"""Notification dispatcher -- fires on scan completion."""

from __future__ import annotations

import logging

from scanner.config import ScannerSettings
from scanner.notifications.email_sender import send_email_notification
from scanner.notifications.slack import send_slack_notification
from scanner.reports.models import DeltaResult
from scanner.schemas.scan import ScanResultSchema

logger = logging.getLogger(__name__)


async def notify_scan_complete(
    scan_result: ScanResultSchema,
    delta: DeltaResult | None,
    settings: ScannerSettings,
) -> None:
    """Dispatch notifications to all enabled channels.

    Each channel is called independently -- a failure in one channel
    does not prevent the other from firing.
    """
    # Derive dashboard URL
    if settings.dashboard_url:
        dashboard_url = settings.dashboard_url.rstrip("/")
    else:
        dashboard_url = f"http://{settings.host}:{settings.port}/dashboard"

    # Slack
    if settings.notifications.slack.enabled and settings.slack_webhook_url:
        try:
            await send_slack_notification(
                scan_result, delta, dashboard_url, settings.slack_webhook_url
            )
        except Exception:
            logger.warning(
                "Slack notification failed for scan %s",
                scan_result.id,
                exc_info=True,
            )

    # Email
    if (
        settings.notifications.email.enabled
        and settings.email_smtp_host
        and settings.notifications.email.recipients
    ):
        try:
            await send_email_notification(
                scan_result, delta, dashboard_url, settings
            )
        except Exception:
            logger.warning(
                "Email notification failed for scan %s",
                scan_result.id,
                exc_info=True,
            )
