"""Interactive HTML report generator."""

import html as html_mod
import json
import logging
import re
from collections import defaultdict
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape
from markupsafe import Markup

from scanner.reports.models import ReportData
from scanner.schemas.severity import Severity


def _format_ai_text(text):
    """Format AI analysis text into readable HTML."""
    if not text:
        return ""
    text = html_mod.escape(text)
    # Numbered items like (1), (2)... -> list
    text = re.sub(r'\((\d+)\)\s*', r'<br><strong>\1.</strong> ', text)
    # Double newlines -> paragraphs
    text = re.sub(r'\n{2,}', '</p><p>', text)
    # Single newlines -> br
    text = text.replace('\n', '<br>')
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Inline code
    text = re.sub(r'`(.+?)`', r'<code style="background:#e3f2fd;padding:1px 4px;border-radius:3px;font-size:12px;">\1</code>', text)
    return Markup(f'<p style="margin:0 0 8px 0;line-height:1.6;">{text}</p>')

logger = logging.getLogger(__name__)

SEVERITY_COLORS = {
    "CRITICAL": "#dc3545",
    "HIGH": "#fd7e14",
    "MEDIUM": "#ffc107",
    "LOW": "#28a745",
    "INFO": "#6c757d",
}

SEVERITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]


def _parse_ai_fix(ai_fix_suggestion: str | None) -> dict | None:
    """Parse AI fix suggestion JSON string into dict with before/after/explanation."""
    if not ai_fix_suggestion:
        return None
    try:
        return json.loads(ai_fix_suggestion)
    except (json.JSONDecodeError, TypeError):
        return None


def _extract_component(file_path: str) -> str:
    """Extract component name from file path (first directory segment)."""
    parts = file_path.split("/")
    return parts[0] if len(parts) > 1 else "root"


def generate_html_report(data: ReportData, output_path: str) -> str:
    """Generate self-contained HTML report.

    Args:
        data: Report data bundle with scan result, findings, delta, gate info.
        output_path: File path to write the HTML report.

    Returns:
        The output file path.
    """
    env = Environment(
        loader=PackageLoader("scanner.reports", "templates"),
        autoescape=select_autoescape(["html"]),
    )
    env.filters["ai_format"] = _format_ai_text
    template = env.get_template("report.html.j2")

    # Group findings by severity, exclude empty groups
    findings_by_severity: dict[str, list] = defaultdict(list)
    for finding in data.findings:
        findings_by_severity[finding.severity.name].append(finding)

    ordered_findings = {
        sev: findings_by_severity[sev]
        for sev in SEVERITY_ORDER
        if sev in findings_by_severity
    }

    # Collect unique tools and components
    all_tools = sorted({f.tool for f in data.findings})
    all_components = sorted({_extract_component(f.file_path) for f in data.findings})

    # Parse AI fix suggestions
    parsed_fixes = {
        f.fingerprint: _parse_ai_fix(f.ai_fix_suggestion)
        for f in data.findings
    }

    # Collect AI analysis text
    ai_analyses = {
        f.fingerprint: f.ai_analysis
        for f in data.findings
        if f.ai_analysis
    }

    # New fingerprints for highlighting
    new_fingerprints = data.delta.new_fingerprints if data.delta else set()

    html_content = template.render(
        scan=data.scan_result,
        findings_by_severity=ordered_findings,
        compound_risks=data.compound_risks,
        delta=data.delta,
        gate_passed=data.gate_passed,
        fail_reasons=data.fail_reasons,
        new_fingerprints=new_fingerprints,
        severity_colors=SEVERITY_COLORS,
        all_tools=all_tools,
        all_components=all_components,
        parsed_fixes=parsed_fixes,
        ai_analyses=ai_analyses,
        extract_component=_extract_component,
    )

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(html_content, encoding="utf-8")
    logger.info("HTML report written to %s", output_path)
    return output_path
