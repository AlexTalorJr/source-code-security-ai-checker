"""Tests for GitleaksAdapter."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from scanner.adapters.gitleaks import GitleaksAdapter
from scanner.schemas.severity import Severity


@pytest.fixture
def adapter():
    return GitleaksAdapter()


@pytest.fixture
def mock_report(gitleaks_output, tmp_path):
    """Write fixture data to a temporary report file and return its path."""
    report_path = str(tmp_path / "gitleaks-report.json")
    with open(report_path, "w") as f:
        json.dump(gitleaks_output, f)
    return report_path


@pytest.mark.asyncio
async def test_parse_gitleaks_findings(adapter, mock_report):
    """Parse fixture JSON report and return 2 findings."""
    adapter._execute = AsyncMock(return_value=("", "", 1))
    with (
        patch("scanner.adapters.gitleaks.os.path.join", return_value=mock_report),
        patch("scanner.adapters.gitleaks.os.remove"),
    ):
        findings = await adapter.run("/tmp/target", timeout=60)
    assert len(findings) == 2
    assert all(f.tool == "gitleaks" for f in findings)


@pytest.mark.asyncio
async def test_gitleaks_all_findings_high_severity(adapter, mock_report):
    """All gitleaks findings should be HIGH severity."""
    adapter._execute = AsyncMock(return_value=("", "", 1))
    with (
        patch("scanner.adapters.gitleaks.os.path.join", return_value=mock_report),
        patch("scanner.adapters.gitleaks.os.remove"),
    ):
        findings = await adapter.run("/tmp/target", timeout=60)
    assert all(f.severity == Severity.HIGH for f in findings)


@pytest.mark.asyncio
async def test_gitleaks_secret_redacted(adapter, mock_report):
    """Snippets must not contain actual secret values."""
    adapter._execute = AsyncMock(return_value=("", "", 1))
    with (
        patch("scanner.adapters.gitleaks.os.path.join", return_value=mock_report),
        patch("scanner.adapters.gitleaks.os.remove"),
    ):
        findings = await adapter.run("/tmp/target", timeout=60)
    for finding in findings:
        assert "AKIAIOSFODNN7EXAMPLE" not in finding.snippet
        assert "-----BEGIN RSA PRIVATE KEY-----" not in finding.snippet
        assert "***REDACTED***" in finding.snippet


@pytest.mark.asyncio
async def test_gitleaks_exit_code_1_is_not_error(adapter, tmp_path):
    """Exit code 1 means leaks found -- not an error."""
    report_path = str(tmp_path / "gitleaks-empty.json")
    with open(report_path, "w") as f:
        json.dump([], f)

    adapter._execute = AsyncMock(return_value=("", "", 1))
    with (
        patch("scanner.adapters.gitleaks.os.path.join", return_value=report_path),
        patch("scanner.adapters.gitleaks.os.remove"),
    ):
        findings = await adapter.run("/tmp/target", timeout=60)
    assert findings == []
