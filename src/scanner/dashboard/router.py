"""Dashboard route handlers for server-rendered Jinja2 pages."""

import base64
import io
import secrets
from collections import defaultdict
from datetime import datetime

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Environment, PackageLoader
from sqlalchemy import desc, select

from scanner.core.suppression import (
    get_suppressed_fingerprints,
    suppress_fingerprint,
    unsuppress_fingerprint,
)
from scanner.dashboard.auth import make_session_token, require_dashboard_auth
from scanner.models.finding import Finding
from scanner.models.scan import ScanResult
from scanner.reports.delta import compute_delta
from scanner.schemas.finding import FindingSchema
from scanner.schemas.severity import Severity

router = APIRouter()

_jinja_env = Environment(
    loader=PackageLoader("scanner.dashboard", "templates"),
    autoescape=True,
)

SEVERITY_COLORS = {
    "Critical": "#dc3545",
    "High": "#fd7e14",
    "Medium": "#ffc107",
    "Low": "#28a745",
    "Info": "#6c757d",
}

STATUS_COLORS = {
    "queued": "#0d6efd",
    "running": "#fd7e14",
    "completed": "#28a745",
    "failed": "#dc3545",
    "pending": "#6c757d",
}


def _severity_name(value: int) -> str:
    """Convert severity int to name."""
    try:
        return Severity(value).name.capitalize()
    except ValueError:
        return "Info"


def _gate_display(gate_passed) -> tuple[str | None, bool]:
    """Convert gate_passed int to (label, passed_bool) or (None, False)."""
    if gate_passed is None:
        return None, False
    return ("PASSED" if gate_passed else "FAILED"), bool(gate_passed)


# ---------- Login / Logout ----------


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str | None = None):
    """Render login page."""
    template = _jinja_env.get_template("login.html.j2")
    return HTMLResponse(template.render(error=error))


@router.post("/login")
async def login_submit(request: Request, api_key: str = Form(...)):
    """Validate API key and set session cookie."""
    expected = request.app.state.settings.api_key
    if expected and secrets.compare_digest(api_key, expected):
        token = make_session_token(api_key)
        response = RedirectResponse(url="/dashboard/history", status_code=302)
        response.set_cookie(
            key="scanner_session",
            value=token,
            httponly=True,
            path="/",
        )
        return response
    return RedirectResponse(url="/dashboard/login?error=1", status_code=302)


@router.get("/logout")
async def logout(request: Request):
    """Clear session cookie and redirect to login."""
    response = RedirectResponse(url="/dashboard/login", status_code=302)
    response.delete_cookie(key="scanner_session", path="/")
    return response


# ---------- History ----------


@router.get("/history", response_class=HTMLResponse)
async def history_page(request: Request):
    """Render scan history page."""
    redirect = await require_dashboard_auth(request)
    if redirect:
        return redirect

    async with request.app.state.session_factory() as session:
        result = await session.execute(
            select(ScanResult).order_by(desc(ScanResult.created_at))
        )
        scans = result.scalars().all()

    scan_list = []
    for s in scans:
        gate_label, gate_passed = _gate_display(s.gate_passed)
        scan_list.append({
            "id": s.id,
            "branch": s.branch or s.target_path or "-",
            "status": s.status,
            "status_color": STATUS_COLORS.get(s.status, "#6c757d"),
            "total_findings": s.total_findings or 0,
            "gate_label": gate_label,
            "gate_passed": gate_passed,
            "duration": f"{s.duration_seconds:.0f}s" if s.duration_seconds else "-",
            "date": s.created_at.strftime("%Y-%m-%d %H:%M") if s.created_at else "-",
        })

    template = _jinja_env.get_template("history.html.j2")
    return HTMLResponse(template.render(scans=scan_list))


# ---------- Scan Detail ----------


@router.get("/scans/{scan_id}", response_class=HTMLResponse)
async def detail_page(request: Request, scan_id: int):
    """Render scan detail page with findings, delta, and suppressed tabs."""
    redirect = await require_dashboard_auth(request)
    if redirect:
        return redirect

    async with request.app.state.session_factory() as session:
        result = await session.execute(
            select(ScanResult).where(ScanResult.id == scan_id)
        )
        scan = result.scalar_one_or_none()
        if not scan:
            return HTMLResponse("<h1>Scan not found</h1>", status_code=404)

        # Load findings
        findings_result = await session.execute(
            select(Finding).where(Finding.scan_id == scan_id)
        )
        all_findings = findings_result.scalars().all()

        # Suppressed fingerprints
        suppressed_fps = await get_suppressed_fingerprints(session)

        # Separate active vs suppressed
        active_findings = []
        suppressed_findings = []
        for f in all_findings:
            entry = {
                "id": f.id,
                "fingerprint": f.fingerprint,
                "tool": f.tool,
                "rule_id": f.rule_id,
                "file_path": f.file_path,
                "line_start": f.line_start,
                "severity": _severity_name(f.severity),
                "severity_color": SEVERITY_COLORS.get(
                    _severity_name(f.severity), "#6c757d"
                ),
                "title": f.title,
                "description": f.description,
            }
            if f.fingerprint in suppressed_fps:
                suppressed_findings.append(entry)
            else:
                active_findings.append(entry)

        # Compute delta
        finding_schemas = [
            FindingSchema(
                fingerprint=f.fingerprint,
                tool=f.tool,
                rule_id=f.rule_id,
                file_path=f.file_path,
                line_start=f.line_start,
                line_end=f.line_end,
                severity=f.severity,
                title=f.title,
                description=f.description,
                recommendation=f.recommendation,
            )
            for f in all_findings
        ]
        delta = await compute_delta(
            finding_schemas, scan.branch, scan.id, session
        )

    gate_label, gate_passed_bool = _gate_display(scan.gate_passed)
    is_running = scan.status in ("running", "queued")

    template = _jinja_env.get_template("detail.html.j2")
    return HTMLResponse(
        template.render(
            scan=scan,
            findings=active_findings,
            suppressed_findings=suppressed_findings,
            delta=delta,
            gate_label=gate_label,
            gate_passed=gate_passed_bool,
            is_running=is_running,
        )
    )


# ---------- Trends ----------


def _generate_severity_over_time(scans) -> str:
    """Generate severity-over-time line chart as base64 PNG data URI."""
    dates = []
    critical_counts = []
    high_counts = []
    medium_counts = []
    low_counts = []

    for s in scans:
        dates.append(s.created_at.strftime("%m/%d") if s.created_at else "?")
        critical_counts.append(s.critical_count or 0)
        high_counts.append(s.high_count or 0)
        medium_counts.append(s.medium_count or 0)
        low_counts.append(s.low_count or 0)

    fig, ax = plt.subplots(figsize=(8, 4))
    try:
        ax.plot(dates, critical_counts, color="#dc3545", label="Critical", marker="o")
        ax.plot(dates, high_counts, color="#fd7e14", label="High", marker="o")
        ax.plot(dates, medium_counts, color="#ffc107", label="Medium", marker="o")
        ax.plot(dates, low_counts, color="#28a745", label="Low", marker="o")
        ax.set_title("Severity Over Time", fontsize=14, fontweight="bold")
        ax.set_xlabel("Scan Date")
        ax.set_ylabel("Count")
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45, ha="right")

        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
        buf.seek(0)
        return f"data:image/png;base64,{base64.b64encode(buf.read()).decode()}"
    finally:
        plt.close(fig)


def _generate_branch_comparison(scans) -> str:
    """Generate branch comparison grouped bar chart as base64 PNG data URI."""
    # Get latest scan per branch
    latest_by_branch: dict[str, ScanResult] = {}
    for s in scans:
        branch = s.branch or "unknown"
        if branch not in latest_by_branch:
            latest_by_branch[branch] = s

    if not latest_by_branch:
        return ""

    branches = list(latest_by_branch.keys())
    critical = [latest_by_branch[b].critical_count or 0 for b in branches]
    high = [latest_by_branch[b].high_count or 0 for b in branches]
    medium = [latest_by_branch[b].medium_count or 0 for b in branches]
    low = [latest_by_branch[b].low_count or 0 for b in branches]

    import numpy as np

    x = np.arange(len(branches))
    width = 0.2

    fig, ax = plt.subplots(figsize=(8, 4))
    try:
        ax.bar(x - 1.5 * width, critical, width, label="Critical", color="#dc3545")
        ax.bar(x - 0.5 * width, high, width, label="High", color="#fd7e14")
        ax.bar(x + 0.5 * width, medium, width, label="Medium", color="#ffc107")
        ax.bar(x + 1.5 * width, low, width, label="Low", color="#28a745")
        ax.set_title("Branch Comparison", fontsize=14, fontweight="bold")
        ax.set_xlabel("Branch")
        ax.set_ylabel("Count")
        ax.set_xticks(x)
        ax.set_xticklabels(branches)
        ax.legend()
        ax.grid(True, alpha=0.3, axis="y")

        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
        buf.seek(0)
        return f"data:image/png;base64,{base64.b64encode(buf.read()).decode()}"
    finally:
        plt.close(fig)


@router.get("/trends", response_class=HTMLResponse)
async def trends_page(request: Request):
    """Render trends page with severity-over-time and branch comparison charts."""
    redirect = await require_dashboard_auth(request)
    if redirect:
        return redirect

    async with request.app.state.session_factory() as session:
        result = await session.execute(
            select(ScanResult)
            .where(ScanResult.status == "completed")
            .order_by(ScanResult.created_at)
        )
        scans = result.scalars().all()

    enough_data = len(scans) >= 2
    severity_chart = ""
    branch_chart = ""

    if enough_data:
        severity_chart = _generate_severity_over_time(scans)
        branch_chart = _generate_branch_comparison(scans)

    template = _jinja_env.get_template("trends.html.j2")
    return HTMLResponse(
        template.render(
            enough_data=enough_data,
            severity_chart=severity_chart,
            branch_chart=branch_chart,
        )
    )


# ---------- Dashboard Actions ----------


@router.post("/start-scan")
async def start_scan(
    request: Request,
    path: str = Form(default=""),
    repo_url: str = Form(default=""),
    branch: str = Form(default=""),
):
    """Create a new scan from the dashboard form."""
    redirect = await require_dashboard_auth(request)
    if redirect:
        return redirect

    async with request.app.state.session_factory() as session:
        scan = ScanResult(
            target_path=path or None,
            repo_url=repo_url or None,
            branch=branch or None,
            status="queued",
            created_at=datetime.utcnow(),
        )
        session.add(scan)
        await session.flush()
        scan_id = scan.id
        await session.commit()

    await request.app.state.scan_queue.enqueue(scan_id)
    return RedirectResponse(
        url=f"/dashboard/scans/{scan_id}", status_code=302
    )


@router.post("/scans/{scan_id}/suppress/{fingerprint}")
async def suppress_finding(request: Request, scan_id: int, fingerprint: str):
    """Suppress a finding fingerprint from the dashboard."""
    redirect = await require_dashboard_auth(request)
    if redirect:
        return redirect

    async with request.app.state.session_factory() as session:
        await suppress_fingerprint(session, fingerprint, reason="Dashboard suppression")
        await session.commit()

    return RedirectResponse(
        url=f"/dashboard/scans/{scan_id}", status_code=302
    )


@router.post("/scans/{scan_id}/unsuppress/{fingerprint}")
async def unsuppress_finding(request: Request, scan_id: int, fingerprint: str):
    """Restore a suppressed finding from the dashboard."""
    redirect = await require_dashboard_auth(request)
    if redirect:
        return redirect

    async with request.app.state.session_factory() as session:
        await unsuppress_fingerprint(session, fingerprint)
        await session.commit()

    return RedirectResponse(
        url=f"/dashboard/scans/{scan_id}", status_code=302
    )
