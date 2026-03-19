"""PDF report generator using WeasyPrint."""

import logging
from collections import Counter
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape
from weasyprint import HTML

from scanner.reports.charts import generate_severity_pie_chart, generate_tool_bar_chart
from scanner.reports.models import ReportData
from scanner.schemas.severity import Severity

logger = logging.getLogger(__name__)

SEVERITY_ORDER = [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INFO]


def generate_pdf_report(data: ReportData, output_path: str) -> str:
    """Generate PDF report via WeasyPrint. Returns the file path."""
    env = Environment(
        loader=PackageLoader("scanner.reports", "templates"),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("report_pdf.html.j2")

    scan = data.scan_result

    # Generate charts
    pie_chart = generate_severity_pie_chart(
        critical=scan.critical_count,
        high=scan.high_count,
        medium=scan.medium_count,
        low=scan.low_count,
        info=scan.info_count,
    )

    tool_counts = Counter(f.tool for f in data.findings)
    bar_chart = generate_tool_bar_chart(dict(tool_counts))

    # Sort findings by severity (Critical first)
    sorted_findings = sorted(data.findings, key=lambda f: -f.severity.value)

    # Target display name
    target = scan.branch or scan.target_path or scan.repo_url or "unknown"

    # Tool count
    tool_count = len(scan.tool_versions) if scan.tool_versions else 0

    # Executive summary text
    executive_summary = (
        f"This scan analyzed {target} and identified {scan.total_findings} finding(s) "
        f"across {tool_count} security tools. "
        f"{scan.critical_count} Critical and {scan.high_count} High severity issues were found. "
        f"{len(data.compound_risks)} compound risk(s) were identified through AI correlation."
    )

    # Delta summary
    delta_summary = None
    if data.delta:
        delta_summary = (
            f"{len(data.delta.new_fingerprints)} new finding(s), "
            f"{len(data.delta.fixed_fingerprints)} fixed, "
            f"{len(data.delta.persisting_fingerprints)} persisting."
        )

    # Date for subtitle
    scan_date = (
        scan.completed_at.strftime("%Y-%m-%d %H:%M")
        if scan.completed_at
        else datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    )

    html_content = template.render(
        scan=scan,
        findings=sorted_findings,
        compound_risks=data.compound_risks,
        delta=data.delta,
        delta_summary=delta_summary,
        gate_passed=data.gate_passed,
        fail_reasons=data.fail_reasons,
        pie_chart=pie_chart,
        bar_chart=bar_chart,
        executive_summary=executive_summary,
        scan_date=scan_date,
        target=target,
    )

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html_content).write_pdf(output_path)
    logger.info("PDF report written to %s", output_path)
    return output_path
