"""Tests for the scan orchestrator."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scanner.config import ScannerSettings
from scanner.core.exceptions import ScannerTimeoutError
from scanner.core.orchestrator import run_scan
from scanner.schemas.finding import FindingSchema
from scanner.schemas.severity import Severity


def _make_finding(
    fingerprint: str = "abc123",
    severity: Severity = Severity.MEDIUM,
    tool: str = "semgrep",
) -> FindingSchema:
    return FindingSchema(
        fingerprint=fingerprint,
        tool=tool,
        rule_id="test-rule",
        file_path="src/app.py",
        severity=severity,
        title="Test finding",
    )


def _make_settings(tmp_path) -> ScannerSettings:
    """Create ScannerSettings with a temporary DB path."""
    db_path = str(tmp_path / "test.db")
    # Avoid loading config.yml from disk
    os.environ["SCANNER_CONFIG_PATH"] = "/dev/null"
    return ScannerSettings(db_path=db_path)


def _patch_all_adapters(findings_map: dict | None = None):
    """Create a mock for ALL_ADAPTERS that returns configurable findings.

    Args:
        findings_map: dict of tool_name -> list[FindingSchema].
            If None, all adapters return empty lists.
    """
    if findings_map is None:
        findings_map = {}

    mock_adapters = []
    for tool_name in ["semgrep", "cppcheck", "gitleaks", "trivy", "checkov"]:
        cls = MagicMock()
        instance = MagicMock()
        instance.tool_name = tool_name
        instance.run = AsyncMock(
            return_value=findings_map.get(tool_name, [])
        )
        instance.get_version = AsyncMock(return_value=f"{tool_name}-1.0")
        cls.return_value = instance
        mock_adapters.append(cls)

    return mock_adapters


@pytest.fixture
def settings(tmp_path):
    return _make_settings(tmp_path)


async def test_run_scan_requires_target_or_repo(settings):
    """Calling run_scan with neither path nor repo raises ValueError."""
    with pytest.raises(ValueError, match="either target_path or repo_url"):
        await run_scan(settings)


async def test_run_scan_rejects_both_target_and_repo(settings):
    """Calling run_scan with both path and repo raises ValueError."""
    with pytest.raises(ValueError, match="not both"):
        await run_scan(
            settings,
            target_path="/tmp/test",
            repo_url="https://example.com/repo.git",
            branch="main",
        )


async def test_run_scan_local_path(settings):
    """Scan with local path runs adapters and returns completed result."""
    test_findings = [_make_finding(fingerprint="f1", tool="semgrep")]
    adapters = _patch_all_adapters({"semgrep": test_findings})
    with patch("scanner.core.orchestrator.ALL_ADAPTERS", adapters):
        result, findings, compound_risks = await run_scan(settings, target_path="/tmp/test")

    assert result.status == "completed"
    assert result.total_findings == 1
    assert result.id is not None


async def test_run_scan_with_repo_url(settings, tmp_path):
    """Scan with repo_url clones, scans, and cleans up."""
    clone_dir = str(tmp_path / "clone")
    adapters = _patch_all_adapters()

    with (
        patch("scanner.core.orchestrator.ALL_ADAPTERS", adapters),
        patch(
            "scanner.core.orchestrator.clone_repo",
            new_callable=AsyncMock,
            return_value=clone_dir,
        ) as mock_clone,
        patch("scanner.core.orchestrator.cleanup_clone") as mock_cleanup,
    ):
        result, findings, compound_risks = await run_scan(
            settings, repo_url="https://example.com/repo.git", branch="main"
        )

    mock_clone.assert_called_once()
    mock_cleanup.assert_called_once_with(clone_dir)
    assert result.status == "completed"


async def test_timeout_graceful_degradation(settings):
    """Adapter timeout produces partial results with warning, not failure."""
    adapters = _patch_all_adapters(
        {"cppcheck": [_make_finding(fingerprint="f1", tool="cppcheck")]}
    )
    # Make semgrep raise a timeout
    adapters[0].return_value.run = AsyncMock(
        side_effect=ScannerTimeoutError("semgrep", 180)
    )

    with patch("scanner.core.orchestrator.ALL_ADAPTERS", adapters):
        result, _, _ = await run_scan(settings, target_path="/tmp/test")

    assert result.status == "completed"
    assert result.error_message is not None
    assert "semgrep" in result.error_message
    assert result.total_findings == 1


async def test_adapter_crash_graceful_degradation(settings):
    """Adapter RuntimeError produces partial results with warning."""
    adapters = _patch_all_adapters(
        {"cppcheck": [_make_finding(fingerprint="f1", tool="cppcheck")]}
    )
    adapters[0].return_value.run = AsyncMock(
        side_effect=RuntimeError("segfault")
    )

    with patch("scanner.core.orchestrator.ALL_ADAPTERS", adapters):
        result, _, _ = await run_scan(settings, target_path="/tmp/test")

    assert result.status == "completed"
    assert "segfault" in result.error_message
    assert result.total_findings == 1


async def test_gate_fails_on_critical(settings):
    """Gate fails when CRITICAL findings present."""
    adapters = _patch_all_adapters(
        {"semgrep": [_make_finding(severity=Severity.CRITICAL)]}
    )

    with patch("scanner.core.orchestrator.ALL_ADAPTERS", adapters):
        result, _, _ = await run_scan(settings, target_path="/tmp/test")

    assert result.gate_passed is False


async def test_gate_passes_on_medium_only(settings):
    """Gate passes when only MEDIUM findings present."""
    adapters = _patch_all_adapters(
        {"semgrep": [_make_finding(severity=Severity.MEDIUM)]}
    )

    with patch("scanner.core.orchestrator.ALL_ADAPTERS", adapters):
        result, _, _ = await run_scan(settings, target_path="/tmp/test")

    assert result.gate_passed is True


async def test_disabled_adapter_not_run(settings):
    """Disabled adapter should not have its run() called."""
    adapters = _patch_all_adapters()

    # Disable semgrep
    settings.scanners.semgrep.enabled = False

    with patch("scanner.core.orchestrator.ALL_ADAPTERS", adapters):
        result, _, _ = await run_scan(settings, target_path="/tmp/test")

    # semgrep adapter's run should never be called
    semgrep_instance = adapters[0].return_value
    semgrep_instance.run.assert_not_awaited()
    assert result.status == "completed"
