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

import re
from markupsafe import Markup


def _format_ai_text(text):
    """Format AI analysis text into readable HTML paragraphs."""
    if not text:
        return Markup("")
    import html as html_mod
    text = html_mod.escape(text)
    # Numbered items (1), (2)... -> line breaks with bold numbers
    text = re.sub(r'\((\d+)\)\s*', r'<br><strong>\1.</strong> ', text)
    # Split on double newlines
    text = re.sub(r'\n{2,}', '</p><p>', text)
    # Convert single newlines to <br>
    text = text.replace('\n', '<br>')
    # Bold markdown **text**
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Inline code `text`
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    # Bullet points
    text = re.sub(r'(?:^|<br>)\s*[-•]\s+', '<br>• ', text)
    return Markup(f'<p>{text}</p>')


def _format_ai_fix(json_str):
    """Parse ai_fix_suggestion JSON and render as HTML."""
    if not json_str:
        return Markup("")
    import html as html_mod
    import json
    try:
        fix = json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return Markup(f"<pre>{html_mod.escape(str(json_str))}</pre>")

    parts = []
    if fix.get("explanation"):
        parts.append(f'<div style="margin-bottom:10px;line-height:1.6;">{html_mod.escape(fix["explanation"])}</div>')
    if fix.get("before"):
        parts.append(
            f'<div style="margin-bottom:8px;">'
            f'<div style="font-size:11px;font-weight:600;color:#dc3545;margin-bottom:4px;">Before</div>'
            f'<pre style="background:#fff5f5;padding:8px;border-radius:4px;font-size:12px;white-space:pre-wrap;line-height:1.5;overflow-x:auto;">{html_mod.escape(fix["before"])}</pre>'
            f'</div>'
        )
    if fix.get("after"):
        parts.append(
            f'<div>'
            f'<div style="font-size:11px;font-weight:600;color:#28a745;margin-bottom:4px;">After</div>'
            f'<pre style="background:#f0fff0;padding:8px;border-radius:4px;font-size:12px;white-space:pre-wrap;line-height:1.5;overflow-x:auto;">{html_mod.escape(fix["after"])}</pre>'
            f'</div>'
        )
    return Markup("".join(parts))


_jinja_env = Environment(
    loader=PackageLoader("scanner.dashboard", "templates"),
    autoescape=True,
)
_jinja_env.filters["ai_format"] = _format_ai_text
_jinja_env.filters["ai_fix_format"] = _format_ai_fix

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


# ---------- Reports (proxied from API with cookie auth) ----------


async def _build_report_data(scan_id: int, session, settings):
    """Load scan, findings, and build ReportData for report generation."""
    from scanner.reports.models import ReportData

    result = await session.execute(
        select(ScanResult).where(ScanResult.id == scan_id)
    )
    scan = result.scalar_one_or_none()
    if not scan:
        return None, "Scan not found"
    if scan.status != "completed":
        return None, f"Scan is not completed (status: {scan.status})"

    findings_result = await session.execute(
        select(Finding).where(Finding.scan_id == scan_id)
    )
    all_findings = findings_result.scalars().all()

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
            ai_analysis=f.ai_analysis,
            ai_fix_suggestion=f.ai_fix_suggestion,
        )
        for f in all_findings
    ]

    from scanner.schemas.scan import ScanResultSchema
    scan_schema = ScanResultSchema(
        id=scan.id,
        status=scan.status,
        target_path=scan.target_path,
        repo_url=scan.repo_url,
        branch=scan.branch,
        commit_hash=scan.commit_hash,
        started_at=scan.started_at,
        completed_at=scan.completed_at,
        duration_seconds=scan.duration_seconds,
        total_findings=scan.total_findings,
        critical_count=scan.critical_count,
        high_count=scan.high_count,
        medium_count=scan.medium_count,
        low_count=scan.low_count,
        info_count=scan.info_count,
        gate_passed=bool(scan.gate_passed) if scan.gate_passed is not None else None,
        error_message=scan.error_message,
        ai_cost_usd=scan.ai_cost_usd,
    )

    delta = await compute_delta(
        finding_schemas, scan.branch, scan.id, session
    )

    gate_config = settings.gate
    severity_counts = {s: 0 for s in Severity}
    for f in finding_schemas:
        severity_counts[f.severity] += 1
    _, fail_reasons = gate_config.evaluate(severity_counts, [])

    return ReportData(
        scan_result=scan_schema,
        findings=finding_schemas,
        compound_risks=[],
        delta=delta,
        gate_passed=bool(scan.gate_passed) if scan.gate_passed is not None else True,
        fail_reasons=fail_reasons,
    ), None


@router.get("/scans/{scan_id}/report")
async def dashboard_html_report(scan_id: int, request: Request):
    """Generate and serve full HTML report with cookie auth."""
    from fastapi import HTTPException
    from fastapi.responses import HTMLResponse
    from scanner.reports.html_report import generate_html_report
    import tempfile

    redirect = await require_dashboard_auth(request)
    if redirect:
        return redirect

    async with request.app.state.session_factory() as session:
        report_data, error = await _build_report_data(
            scan_id, session, request.app.state.settings
        )

    if error:
        raise HTTPException(status_code=404 if "not found" in error else 409, detail=error)

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
        generate_html_report(report_data, tmp.name)
        html_content = open(tmp.name).read()

    return HTMLResponse(content=html_content)


@router.get("/scans/{scan_id}/report/pdf")
async def dashboard_pdf_report(scan_id: int, request: Request):
    """Generate and serve PDF report with cookie auth."""
    from fastapi import HTTPException
    from fastapi.responses import Response
    from scanner.reports.pdf_report import generate_pdf_report
    import tempfile
    import os

    redirect = await require_dashboard_auth(request)
    if redirect:
        return redirect

    async with request.app.state.session_factory() as session:
        report_data, error = await _build_report_data(
            scan_id, session, request.app.state.settings
        )

    if error:
        raise HTTPException(status_code=404 if "not found" in error else 409, detail=error)

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        try:
            generate_pdf_report(report_data, tmp.name)
            pdf_content = open(tmp.name, "rb").read()
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"PDF generation failed: {exc}")
        finally:
            os.unlink(tmp.name)

    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=scan-{scan_id}-report.pdf"},
    )


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
                "severity_order": f.severity,
                "severity_color": SEVERITY_COLORS.get(
                    _severity_name(f.severity), "#6c757d"
                ),
                "title": f.title,
                "description": f.description,
                "recommendation": f.recommendation,
                "ai_analysis": f.ai_analysis,
                "ai_fix_suggestion": f.ai_fix_suggestion,
            }
            if f.fingerprint in suppressed_fps:
                suppressed_findings.append(entry)
            else:
                active_findings.append(entry)

        # Sort by severity: Critical first, Info last
        active_findings.sort(key=lambda x: x["severity_order"], reverse=True)
        suppressed_findings.sort(key=lambda x: x["severity_order"], reverse=True)

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

    # Compute gate fail reasons
    fail_reasons = []
    if not gate_passed_bool and gate_label is not None:
        settings = request.app.state.settings
        severity_counts = {s: 0 for s in Severity}
        for f in all_findings:
            try:
                severity_counts[Severity(f.severity)] += 1
            except ValueError:
                pass
        _, fail_reasons = settings.gate.evaluate(severity_counts, [])

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
            fail_reasons=fail_reasons,
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
