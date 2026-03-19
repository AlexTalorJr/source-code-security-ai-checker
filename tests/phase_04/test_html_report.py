"""Tests for HTML report generator."""

import json
from pathlib import Path

import pytest

from scanner.reports.html_report import generate_html_report
from scanner.reports.models import DeltaResult, ReportData
from scanner.schemas.finding import FindingSchema
from scanner.schemas.severity import Severity


@pytest.fixture
def report_data_failed(sample_scan_result, sample_findings, sample_compound_risks):
    """ReportData with gate_passed=False."""
    return ReportData(
        scan_result=sample_scan_result,
        findings=sample_findings,
        compound_risks=sample_compound_risks,
        gate_passed=False,
        fail_reasons=["2 CRITICAL finding(s)", "1 HIGH compound risk"],
    )


@pytest.fixture
def report_data_passed(sample_scan_result, sample_findings, sample_compound_risks):
    """ReportData with gate_passed=True."""
    return ReportData(
        scan_result=sample_scan_result,
        findings=sample_findings,
        compound_risks=sample_compound_risks,
        gate_passed=True,
    )


@pytest.fixture
def report_data_with_delta(sample_scan_result, sample_findings, sample_compound_risks):
    """ReportData with delta comparison."""
    fp_critical = sample_findings[0].fingerprint
    fp_high = sample_findings[1].fingerprint
    fp_medium = sample_findings[2].fingerprint
    delta = DeltaResult(
        new_fingerprints={fp_critical},
        fixed_fingerprints={fp_high},
        persisting_fingerprints={fp_medium},
    )
    return ReportData(
        scan_result=sample_scan_result,
        findings=sample_findings,
        compound_risks=sample_compound_risks,
        delta=delta,
        gate_passed=False,
        fail_reasons=["2 CRITICAL finding(s)"],
    )


class TestHtmlReportGenerated:
    def test_html_report_generated(self, report_data_failed, tmp_path):
        out = tmp_path / "report.html"
        result = generate_html_report(report_data_failed, str(out))
        assert Path(result).exists()
        assert out.stat().st_size > 0


class TestGateBanner:
    def test_gate_banner_failed(self, report_data_failed, tmp_path):
        out = tmp_path / "report.html"
        generate_html_report(report_data_failed, str(out))
        html = out.read_text()
        assert "QUALITY GATE: FAILED" in html
        assert "Blocked by:" in html
        assert "2 CRITICAL" in html

    def test_gate_banner_passed(self, report_data_passed, tmp_path):
        out = tmp_path / "report.html"
        generate_html_report(report_data_passed, str(out))
        html = out.read_text()
        assert "QUALITY GATE: PASSED" in html


class TestSeverityGrouping:
    def test_severity_grouping(self, report_data_failed, tmp_path):
        out = tmp_path / "report.html"
        generate_html_report(report_data_failed, str(out))
        html = out.read_text()
        # All 5 severities have 1 finding each
        assert "CRITICAL (1)" in html
        assert "HIGH (1)" in html
        assert "MEDIUM (1)" in html
        assert "LOW (1)" in html
        assert "INFO (1)" in html


class TestFindingCardAttributes:
    def test_finding_card_attributes(self, report_data_failed, tmp_path):
        out = tmp_path / "report.html"
        generate_html_report(report_data_failed, str(out))
        html = out.read_text()
        assert 'data-severity="CRITICAL"' in html
        assert 'data-tool="semgrep"' in html
        assert 'data-component="src"' in html


class TestCodeContext:
    def test_code_context(self, report_data_failed, tmp_path):
        out = tmp_path / "report.html"
        generate_html_report(report_data_failed, str(out))
        html = out.read_text()
        assert "Code Context" in html
        # Check that the snippet text is present (HTML-escaped)
        assert "SELECT * FROM users" in html


class TestAiFixSuggestion:
    def test_ai_fix_suggestion(self, tmp_path, sample_scan_result):
        """Finding with ai_fix_suggestion shows before/after diff."""
        finding = FindingSchema(
            fingerprint="test_fix_fp",
            tool="semgrep",
            rule_id="test-rule",
            file_path="app/main.py",
            severity=Severity.HIGH,
            title="Test finding with fix",
            ai_fix_suggestion=json.dumps({
                "before": "old()",
                "after": "new()",
                "explanation": "fix it",
            }),
        )
        data = ReportData(
            scan_result=sample_scan_result,
            findings=[finding],
            compound_risks=[],
            gate_passed=True,
        )
        out = tmp_path / "report.html"
        generate_html_report(data, str(out))
        html = out.read_text()
        assert "AI Fix Suggestion" in html
        assert "old()" in html
        assert "new()" in html

    def test_no_ai_fix(self, tmp_path, sample_scan_result):
        """Finding without ai_fix_suggestion shows unavailable message."""
        finding = FindingSchema(
            fingerprint="test_nofix_fp",
            tool="trivy",
            rule_id="no-fix-rule",
            file_path="lib/util.py",
            severity=Severity.MEDIUM,
            title="No fix finding",
        )
        data = ReportData(
            scan_result=sample_scan_result,
            findings=[finding],
            compound_risks=[],
            gate_passed=True,
        )
        out = tmp_path / "report.html"
        generate_html_report(data, str(out))
        html = out.read_text()
        assert "AI analysis not available for this finding." in html


class TestMetadata:
    def test_metadata(self, report_data_failed, tmp_path):
        out = tmp_path / "report.html"
        generate_html_report(report_data_failed, str(out))
        html = out.read_text()
        assert "release/v2.1" in html
        assert "semgrep" in html
        assert "45.2" in html
        assert "Scan Details" in html


class TestDelta:
    def test_delta_badges(self, report_data_with_delta, tmp_path):
        out = tmp_path / "report.html"
        generate_html_report(report_data_with_delta, str(out))
        html = out.read_text()
        assert "1 new" in html
        assert "1 fixed" in html
        assert "1 persisting" in html

    def test_delta_first_scan(self, report_data_passed, tmp_path):
        """When delta is None, show first scan message."""
        out = tmp_path / "report.html"
        generate_html_report(report_data_passed, str(out))
        html = out.read_text()
        assert "First scan on this branch" in html


class TestNewFindingHighlight:
    def test_new_finding_highlight(self, report_data_with_delta, tmp_path):
        out = tmp_path / "report.html"
        generate_html_report(report_data_with_delta, str(out))
        html = out.read_text()
        assert "finding-card--new" in html


class TestSelfContained:
    def test_self_contained(self, report_data_failed, tmp_path):
        out = tmp_path / "report.html"
        generate_html_report(report_data_failed, str(out))
        html = out.read_text()
        assert '<link rel="stylesheet" href=' not in html
        assert "<script src=" not in html


class TestCompoundRisks:
    def test_compound_risks_section(self, report_data_failed, tmp_path):
        out = tmp_path / "report.html"
        generate_html_report(report_data_failed, str(out))
        html = out.read_text()
        assert "Compound Risks" in html
        assert "Auth bypass via session fixation" in html


class TestSidebarFilters:
    def test_sidebar_filters(self, report_data_failed, tmp_path):
        out = tmp_path / "report.html"
        generate_html_report(report_data_failed, str(out))
        html = out.read_text()
        assert "Filters" in html
        assert "Severity" in html
        assert "Tool" in html
        assert "Component" in html
        assert "filter-checkbox" in html
