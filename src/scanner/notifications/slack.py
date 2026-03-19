"""Slack webhook notification sender using Block Kit messages."""

from __future__ import annotations

import logging

import httpx

from scanner.reports.models import DeltaResult
from scanner.schemas.scan import ScanResultSchema

logger = logging.getLogger(__name__)


async def send_slack_notification(
    scan_result: ScanResultSchema,
    delta: DeltaResult | None,
    dashboard_url: str,
    webhook_url: str,
) -> None:
    """Send a Slack Block Kit notification for a completed scan.

    Errors are swallowed and logged as warnings -- notification failure
    must never break the scan pipeline.
    """
    try:
        gate_passed = bool(scan_result.gate_passed)
        emoji = "\u2705" if gate_passed else "\u274c"
        gate_text = "PASSED" if gate_passed else "FAILED"

        duration = (
            f"{scan_result.duration_seconds:.0f}s"
            if scan_result.duration_seconds is not None
            else "N/A"
        )

        blocks: list[dict] = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} Security Scan {gate_text}",
                },
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Branch:* {scan_result.branch or 'local'}",
                    },
                    {"type": "mrkdwn", "text": f"*Duration:* {duration}"},
                    {
                        "type": "mrkdwn",
                        "text": f"*Critical:* {scan_result.critical_count}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*High:* {scan_result.high_count}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Medium:* {scan_result.medium_count}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Low:* {scan_result.low_count}",
                    },
                ],
            },
        ]

        if delta is not None:
            delta_text = (
                f"+{len(delta.new_fingerprints)} new, "
                f"-{len(delta.fixed_fingerprints)} fixed"
            )
            blocks.append(
                {
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": f"Delta: {delta_text}"}
                    ],
                }
            )

        detail_url = f"{dashboard_url}/scans/{scan_result.id}"
        blocks.append(
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Details",
                        },
                        "url": detail_url,
                    }
                ],
            }
        )

        async with httpx.AsyncClient() as client:
            await client.post(webhook_url, json={"blocks": blocks})

        logger.info("Slack notification sent for scan %s", scan_result.id)
    except Exception:
        logger.warning(
            "Failed to send Slack notification for scan %s",
            scan_result.id,
            exc_info=True,
        )
