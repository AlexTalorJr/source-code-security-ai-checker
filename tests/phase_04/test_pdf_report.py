"""Tests for PDF report generation."""

import pytest
from jinja2 import Environment, PackageLoader, select_autoescape

from scanner.reports.models import DeltaResult, ReportData
from scanner.reports.pdf_report import generate_pdf_report


def _render_template(data: ReportData) -> str:
    """Render PDF template to HTML string for inspection (no WeasyPrint needed)."""
    from collections import Counter
    from datetime import datetime

    from scanner.reports.charts import generate_severity_pie_chart, generate_tool_bar_chart
    from scanner.schemas.severity import Severity

    env = Environment(
        loader=PackageLoader("scanner.reports", "templates"),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("report_pdf.html.j2")
    scan = data.scan_result

    pie_chart = generate_severity_pie_chart(
        critical=scan.critical_count, high=scan.high_count,
        medium=scan.medium_count, low=scan.low_count, info=scan.info_count,
    )
    tool_counts = Counter(f.tool for f in data.findings)
    bar_chart = generate_tool_bar_chart(dict(tool_counts))
    sorted_findings = sorted(data.findings, key=lambda f: -f.severity.value)
    target = scan.branch or scan.target_path or scan.repo_url or "unknown"
    tool_count = len(scan.tool_versions) if scan.tool_versions else 0
    executive_summary = (
        f"This scan analyzed {target} and identified {scan.total_findings} finding(s) "
        f"across {tool_count} security tools. "
        f"{scan.critical_count} Critical and {scan.high_count} High severity issues were found. "
        f"{len(data.compound_risks)} compound risk(s) were identified through AI correlation."
    )
    delta_summary = None
    if data.delta:
        delta_summary = (
            f"{len(data.delta.new_fingerprints)} new finding(s), "
            f"{len(data.delta.fixed_fingerprints)} fixed, "
            f"{len(data.delta.persisting_fingerprints)} persisting."
        )
    scan_date = scan.completed_at.strftime("%Y-%m-%d %H:%M") if scan.completed_at else datetime.utcnow().strftime("%Y-%m-%d %H:%M")

    return template.render(
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


def _make_report_data(scan_result, findings, compound_risks, **kwargs):
    return ReportData(
        scan_result=scan_result,
        findings=findings,
        compound_risks=compound_risks,
        **kwargs,
    )


class TestPdfGenerated:
    def test_pdf_generated(self, sample_scan_result, sample_findings, sample_compound_risks, tmp_path):
        """Integration test: generate actual PDF, verify magic bytes."""
        data = _make_report_data(sample_scan_result, sample_findings, sample_compound_risks, gate_passed=False, fail_reasons=["1 Critical finding"])
        output = tmp_path / "report.pdf"
        result = generate_pdf_report(data, str(output))
        assert result == str(output)
        assert output.exists()
        magic = output.read_bytes()[:4]
        assert magic == b"%PDF", f"Expected PDF magic bytes, got {magic!r}"


class TestPdfContents:
    def test_pdf_contains_gate_status(self, sample_scan_result, sample_findings, sample_compound_risks):
        data = _make_report_data(sample_scan_result, sample_findings, sample_compound_risks, gate_passed=False, fail_reasons=["1 Critical finding"])
        html = _render_template(data)
        assert "Quality Gate: FAILED" in html

    def test_pdf_contains_executive_summary(self, sample_scan_result, sample_findings, sample_compound_risks):
        data = _make_report_data(sample_scan_result, sample_findings, sample_compound_risks)
        html = _render_template(data)
        assert "Executive Summary" in html
        assert "5 finding(s)" in html
        assert "1 Critical" in html

    def test_pdf_contains_metadata(self, sample_scan_result, sample_findings, sample_compound_risks):
        data = _make_report_data(sample_scan_result, sample_findings, sample_compound_risks)
        html = _render_template(data)
        assert "release/v2.1" in html
        assert "45.2" in html

    def test_pdf_contains_delta(self, sample_scan_result, sample_findings, sample_compound_risks):
        delta = DeltaResult(
            new_fingerprints={"fp1", "fp2"},
            fixed_fingerprints={"fp3"},
            persisting_fingerprints={"fp4", "fp5", "fp6"},
        )
        data = _make_report_data(sample_scan_result, sample_findings, sample_compound_risks, delta=delta)
        html = _render_template(data)
        assert "2 new finding(s)" in html
        assert "1 fixed" in html
        assert "3 persisting" in html

    def test_pdf_no_delta(self, sample_scan_result, sample_findings, sample_compound_risks):
        data = _make_report_data(sample_scan_result, sample_findings, sample_compound_risks, delta=None)
        html = _render_template(data)
        assert "No previous scan available" in html

    def test_pdf_compound_risks(self, sample_scan_result, sample_findings, sample_compound_risks):
        data = _make_report_data(sample_scan_result, sample_findings, sample_compound_risks)
        html = _render_template(data)
        assert "Compound Risks" in html
        assert "Auth bypass via session fixation" in html

    def test_pdf_findings_table(self, sample_scan_result, sample_findings, sample_compound_risks):
        data = _make_report_data(sample_scan_result, sample_findings, sample_compound_risks)
        html = _render_template(data)
        assert "src/auth/login.py" in html
        assert "php.lang.security.injection.sql-injection" in html
        assert "Finding Details" in html
