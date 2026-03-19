"""SMTP email notification sender with HTML templates."""

from __future__ import annotations

import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from jinja2 import Environment, PackageLoader

from scanner.config import ScannerSettings
from scanner.reports.models import DeltaResult
from scanner.schemas.scan import ScanResultSchema

logger = logging.getLogger(__name__)


def send_email_sync(
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    recipients: list[str],
    subject: str,
    html_body: str,
    use_tls: bool = True,
) -> None:
    """Send an HTML email via SMTP (synchronous).

    Designed to be called from an async context via ``asyncio.to_thread``.
    """
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        if use_tls:
            server.starttls()
        if smtp_user and smtp_password:
            server.login(smtp_user, smtp_password)
        server.send_message(msg)


def render_email_html(
    scan_result: ScanResultSchema,
    delta: DeltaResult | None,
    dashboard_url: str,
) -> str:
    """Render the HTML email body from the Jinja2 template."""
    env = Environment(
        loader=PackageLoader("scanner.notifications", "templates"),
        autoescape=True,
    )
    template = env.get_template("email.html.j2")
    return template.render(
        scan_result=scan_result,
        delta=delta,
        dashboard_url=dashboard_url,
        gate_passed=scan_result.gate_passed,
    )


async def send_email_notification(
    scan_result: ScanResultSchema,
    delta: DeltaResult | None,
    dashboard_url: str,
    settings: ScannerSettings,
) -> None:
    """Send an HTML email notification for a completed scan.

    SMTP operations run in a thread pool to avoid blocking the async
    event loop. Errors are swallowed and logged as warnings.
    """
    try:
        branch = scan_result.branch or "local"
        if scan_result.gate_passed:
            subject = f"Security Scan Passed -- {branch}"
        else:
            subject = f"SECURITY SCAN FAILED -- {branch}"

        html_body = render_email_html(scan_result, delta, dashboard_url)

        await asyncio.to_thread(
            send_email_sync,
            settings.email_smtp_host,
            settings.notifications.email.smtp_port,
            settings.notifications.email.smtp_user,
            settings.notifications.email.smtp_password,
            settings.notifications.email.recipients,
            subject,
            html_body,
            settings.notifications.email.use_tls,
        )

        logger.info("Email notification sent for scan %s", scan_result.id)
    except Exception:
        logger.warning(
            "Failed to send email notification for scan %s",
            scan_result.id,
            exc_info=True,
        )
