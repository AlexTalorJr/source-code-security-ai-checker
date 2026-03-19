"""Tests for the CLI scan command."""

import json
from datetime import datetime
from unittest.mock import AsyncMock, patch

from typer.testing import CliRunner

from scanner.cli.main import app
from scanner.schemas.scan import ScanResultSchema

runner = CliRunner()


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


@patch("scanner.cli.main.run_scan", new_callable=AsyncMock)
def test_scan_local_path_flag(mock_run_scan):
    """Scan with --path flag runs and exits 0."""
    mock_run_scan.return_value = _make_scan_result()

    result = runner.invoke(app, ["scan", "--path", "/tmp/test"])

    assert result.exit_code == 0
    mock_run_scan.assert_awaited_once()


def test_scan_repo_url_requires_branch():
    """--repo-url without --branch should fail."""
    result = runner.invoke(
        app, ["scan", "--repo-url", "https://example.com/repo.git"]
    )
    assert result.exit_code != 0


@patch("scanner.cli.main.run_scan", new_callable=AsyncMock)
def test_scan_json_output(mock_run_scan):
    """--json flag outputs valid JSON with status field."""
    mock_run_scan.return_value = _make_scan_result()

    result = runner.invoke(app, ["scan", "--path", "/tmp/test", "--json"])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["status"] == "completed"


@patch("scanner.cli.main.run_scan", new_callable=AsyncMock)
def test_scan_exit_code_1_on_critical(mock_run_scan):
    """Exit code 1 when gate_passed is False (Critical/High found)."""
    mock_run_scan.return_value = _make_scan_result(
        gate_passed=False,
        critical_count=1,
        total_findings=1,
    )

    result = runner.invoke(app, ["scan", "--path", "/tmp/test"])

    assert result.exit_code == 1


@patch("scanner.cli.main.run_scan", new_callable=AsyncMock)
def test_scan_exit_code_0_on_clean(mock_run_scan):
    """Exit code 0 when gate_passed is True."""
    mock_run_scan.return_value = _make_scan_result(gate_passed=True)

    result = runner.invoke(app, ["scan", "--path", "/tmp/test"])

    assert result.exit_code == 0


@patch("scanner.cli.main.run_scan", new_callable=AsyncMock)
def test_scan_shows_warning_banner(mock_run_scan):
    """Warning banner appears in stderr when error_message present."""
    mock_run_scan.return_value = _make_scan_result(
        error_message="cppcheck: timed out after 120s"
    )

    result = runner.invoke(app, ["scan", "--path", "/tmp/test"])

    # CliRunner mixes stdout and stderr by default
    assert "cppcheck" in result.output
