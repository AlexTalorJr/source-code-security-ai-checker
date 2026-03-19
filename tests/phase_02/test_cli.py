"""Tests for the CLI scan command."""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from typer.testing import CliRunner

from scanner.cli.main import app
from scanner.schemas.scan import ScanResultSchema

runner = CliRunner()

# Common patches for report generation (called by every scan command now)
_REPORT_PATCHES = [
    patch("scanner.cli.main.generate_html_report", return_value="/tmp/reports/test.html"),
    patch("scanner.cli.main.generate_pdf_report", return_value="/tmp/reports/test.pdf"),
]


def _make_scan_result(**overrides) -> ScanResultSchema:
    """Create a minimal ScanResultSchema for testing."""
    defaults = dict(
        id=1,
        status="completed",
        target_path="/tmp/test",
        started_at=datetime(2026, 1, 1, 0, 0, 0),
        completed_at=datetime(2026, 1, 1, 0, 0, 10),
        duration_seconds=10.0,
        total_findings=0,
        critical_count=0,
        high_count=0,
        medium_count=0,
        low_count=0,
        info_count=0,
        gate_passed=True,
        tool_versions={"semgrep": "1.0"},
        error_message=None,
    )
    defaults.update(overrides)
    return ScanResultSchema(**defaults)


@patch("scanner.cli.main.generate_pdf_report", return_value="/tmp/r.pdf")
@patch("scanner.cli.main.generate_html_report", return_value="/tmp/r.html")
@patch("scanner.cli.main.run_scan", new_callable=AsyncMock)
def test_scan_local_path_flag(mock_run_scan, _mock_html, _mock_pdf):
    """Scan with --path flag runs and exits 0."""
    mock_run_scan.return_value = (_make_scan_result(), [], [])

    result = runner.invoke(app, ["scan", "--path", "/tmp/test"])

    assert result.exit_code == 0
    mock_run_scan.assert_awaited_once()


def test_scan_repo_url_requires_branch():
    """--repo-url without --branch should fail."""
    result = runner.invoke(
        app, ["scan", "--repo-url", "https://example.com/repo.git"]
    )
    assert result.exit_code != 0


@patch("scanner.cli.main.generate_pdf_report", return_value="/tmp/r.pdf")
@patch("scanner.cli.main.generate_html_report", return_value="/tmp/r.html")
@patch("scanner.cli.main.run_scan", new_callable=AsyncMock)
def test_scan_json_output(mock_run_scan, _mock_html, _mock_pdf):
    """--json flag outputs valid JSON with status field."""
    mock_run_scan.return_value = (_make_scan_result(), [], [])

    result = runner.invoke(app, ["scan", "--path", "/tmp/test", "--json"])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["status"] == "completed"
    assert "fail_reasons" in data
    assert "delta" in data
    assert "reports" in data


@patch("scanner.cli.main.generate_pdf_report", return_value="/tmp/r.pdf")
@patch("scanner.cli.main.generate_html_report", return_value="/tmp/r.html")
@patch("scanner.cli.main.run_scan", new_callable=AsyncMock)
def test_scan_exit_code_1_on_critical(mock_run_scan, _mock_html, _mock_pdf):
    """Exit code 1 when gate_passed is False (Critical/High found)."""
    mock_run_scan.return_value = (_make_scan_result(
        gate_passed=False,
        critical_count=1,
        total_findings=1,
    ), [], [])

    result = runner.invoke(app, ["scan", "--path", "/tmp/test"])

    assert result.exit_code == 1


@patch("scanner.cli.main.generate_pdf_report", return_value="/tmp/r.pdf")
@patch("scanner.cli.main.generate_html_report", return_value="/tmp/r.html")
@patch("scanner.cli.main.run_scan", new_callable=AsyncMock)
def test_scan_exit_code_0_on_clean(mock_run_scan, _mock_html, _mock_pdf):
    """Exit code 0 when gate_passed is True."""
    mock_run_scan.return_value = (_make_scan_result(gate_passed=True), [], [])

    result = runner.invoke(app, ["scan", "--path", "/tmp/test"])

    assert result.exit_code == 0


@patch("scanner.cli.main.generate_pdf_report", return_value="/tmp/r.pdf")
@patch("scanner.cli.main.generate_html_report", return_value="/tmp/r.html")
@patch("scanner.cli.main.run_scan", new_callable=AsyncMock)
def test_scan_shows_warning_banner(mock_run_scan, _mock_html, _mock_pdf):
    """Warning banner appears in stderr when error_message present."""
    mock_run_scan.return_value = (_make_scan_result(
        error_message="cppcheck: timed out after 120s"
    ), [], [])

    result = runner.invoke(app, ["scan", "--path", "/tmp/test"])

    # CliRunner mixes stdout and stderr by default
    assert "cppcheck" in result.output


@patch("scanner.cli.main.generate_pdf_report", return_value="/tmp/r.pdf")
@patch("scanner.cli.main.generate_html_report", return_value="/tmp/r.html")
@patch("scanner.cli.main.run_scan", new_callable=AsyncMock)
def test_scan_shows_delta_line(mock_run_scan, _mock_html, _mock_pdf):
    """Delta summary line appears in output."""
    mock_run_scan.return_value = (_make_scan_result(), [], [])

    result = runner.invoke(app, ["scan", "--path", "/tmp/test"])

    assert result.exit_code == 0
    # First scan on branch (id=1, no branch set) => "first scan"
    assert "Delta:" in result.output


@patch("scanner.cli.main.generate_pdf_report", return_value="/tmp/r.pdf")
@patch("scanner.cli.main.generate_html_report", return_value="/tmp/r.html")
@patch("scanner.cli.main.run_scan", new_callable=AsyncMock)
def test_scan_shows_gate_fail_reasons(mock_run_scan, _mock_html, _mock_pdf):
    """Gate fail reasons displayed when gate fails."""
    from scanner.schemas.finding import FindingSchema
    from scanner.schemas.severity import Severity

    critical_finding = FindingSchema(
        fingerprint="fp1",
        tool="semgrep",
        rule_id="test-rule",
        file_path="/test.py",
        line_start=1,
        severity=Severity.CRITICAL,
        title="Test Critical",
        description="Test",
    )

    mock_run_scan.return_value = (_make_scan_result(
        gate_passed=False,
        critical_count=1,
        total_findings=1,
    ), [critical_finding], [])

    result = runner.invoke(app, ["scan", "--path", "/tmp/test"])

    assert result.exit_code == 1
    assert "Quality gate: FAILED" in result.output
    assert "CRITICAL finding" in result.output


@patch("scanner.cli.main.generate_pdf_report", return_value="/tmp/r.pdf")
@patch("scanner.cli.main.generate_html_report", return_value="/tmp/r.html")
@patch("scanner.cli.main.run_scan", new_callable=AsyncMock)
def test_scan_shows_report_paths(mock_run_scan, mock_html, _mock_pdf):
    """Report file paths displayed in output."""
    mock_run_scan.return_value = (_make_scan_result(), [], [])

    result = runner.invoke(app, ["scan", "--path", "/tmp/test"])

    assert result.exit_code == 0
    assert "Reports:" in result.output


@patch("scanner.cli.main.generate_pdf_report", return_value="/tmp/r.pdf")
@patch("scanner.cli.main.generate_html_report", return_value="/tmp/r.html")
@patch("scanner.cli.main.run_scan", new_callable=AsyncMock)
def test_scan_quality_gate_passed(mock_run_scan, _mock_html, _mock_pdf):
    """Quality gate PASSED label displayed."""
    mock_run_scan.return_value = (_make_scan_result(gate_passed=True), [], [])

    result = runner.invoke(app, ["scan", "--path", "/tmp/test"])

    assert result.exit_code == 0
    assert "Quality gate: PASSED" in result.output
