"""Tests for the scan orchestrator."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scanner.config import ScannerSettings, ScannerToolConfig
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


def _make_settings(tmp_path, scanners: dict[str, ScannerToolConfig] | None = None) -> ScannerSettings:
    """Create ScannerSettings with a temporary DB path."""
    db_path = str(tmp_path / "test.db")
    # Avoid loading config.yml from disk
    os.environ["SCANNER_CONFIG_PATH"] = "/dev/null"
    if scanners is None:
        scanners = {
            name: ScannerToolConfig(
                adapter_class=f"scanner.adapters.{name}.{name.capitalize()}Adapter",
                enabled=True,
                timeout=180,
            )
            for name in ["semgrep", "cppcheck", "gitleaks", "trivy", "checkov"]
        }
    return ScannerSettings(db_path=db_path, scanners=scanners)


def _mock_registry_adapters(findings_map: dict | None = None):
    """Create a mock ScannerRegistry that returns configurable adapter mocks.

    Args:
        findings_map: dict of tool_name -> list[FindingSchema].
            If None, all adapters return empty lists.

    Returns:
        Tuple of (mock_registry_class, mock_adapters_list) where
        mock_registry_class can be used with patch for ScannerRegistry.
    """
    if findings_map is None:
        findings_map = {}

    mock_adapters = []
    for tool_name in ["semgrep", "cppcheck", "gitleaks", "trivy", "checkov"]:
        instance = MagicMock()
        instance.tool_name = tool_name
        instance.run = AsyncMock(
            return_value=findings_map.get(tool_name, [])
        )
        instance.get_version = AsyncMock(return_value=f"{tool_name}-1.0")
        mock_adapters.append(instance)

    mock_registry = MagicMock()
    mock_registry.get_enabled_adapters.return_value = mock_adapters

    MockRegistryClass = MagicMock(return_value=mock_registry)
    return MockRegistryClass, mock_adapters


@pytest.fixture
def settings(tmp_path):
    return _make_settings(tmp_path)


@pytest.fixture(autouse=True)
def _mock_language_detect():
    """Auto-detect returns all languages so all mocked adapters run."""
    all_langs = {"python", "php", "laravel", "cpp", "javascript", "typescript",
                 "go", "rust", "java", "docker", "terraform", "yaml", "ci"}
    with patch("scanner.core.language_detect.detect_languages", return_value=all_langs):
        yield


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
    MockRegistry, _ = _mock_registry_adapters({"semgrep": test_findings})
    with patch("scanner.core.orchestrator.ScannerRegistry", MockRegistry):
        result, findings, compound_risks = await run_scan(settings, target_path="/tmp/test")

    assert result.status == "completed"
    assert result.total_findings == 1
    assert result.id is not None


async def test_run_scan_with_repo_url(settings, tmp_path):
    """Scan with repo_url clones, scans, and cleans up."""
    clone_dir = str(tmp_path / "clone")
    MockRegistry, _ = _mock_registry_adapters()

    with (
        patch("scanner.core.orchestrator.ScannerRegistry", MockRegistry),
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
    MockRegistry, adapters = _mock_registry_adapters(
        {"cppcheck": [_make_finding(fingerprint="f1", tool="cppcheck")]}
    )
    # Make semgrep raise a timeout
    adapters[0].run = AsyncMock(
        side_effect=ScannerTimeoutError("semgrep", 180)
    )

    with patch("scanner.core.orchestrator.ScannerRegistry", MockRegistry):
        result, _, _ = await run_scan(settings, target_path="/tmp/test")

    assert result.status == "completed"
    assert result.error_message is not None
    assert "semgrep" in result.error_message
    assert result.total_findings == 1


async def test_adapter_crash_graceful_degradation(settings):
    """Adapter RuntimeError produces partial results with warning."""
    MockRegistry, adapters = _mock_registry_adapters(
        {"cppcheck": [_make_finding(fingerprint="f1", tool="cppcheck")]}
    )
    adapters[0].run = AsyncMock(
        side_effect=RuntimeError("segfault")
    )

    with patch("scanner.core.orchestrator.ScannerRegistry", MockRegistry):
        result, _, _ = await run_scan(settings, target_path="/tmp/test")

    assert result.status == "completed"
    assert "segfault" in result.error_message
    assert result.total_findings == 1


async def test_gate_fails_on_critical(settings):
    """Gate fails when CRITICAL findings present."""
    MockRegistry, _ = _mock_registry_adapters(
        {"semgrep": [_make_finding(severity=Severity.CRITICAL)]}
    )

    with patch("scanner.core.orchestrator.ScannerRegistry", MockRegistry):
        result, _, _ = await run_scan(settings, target_path="/tmp/test")

    assert result.gate_passed is False


async def test_gate_passes_on_medium_only(settings):
    """Gate passes when only MEDIUM findings present."""
    MockRegistry, _ = _mock_registry_adapters(
        {"semgrep": [_make_finding(severity=Severity.MEDIUM)]}
    )

    with patch("scanner.core.orchestrator.ScannerRegistry", MockRegistry):
        result, _, _ = await run_scan(settings, target_path="/tmp/test")

    assert result.gate_passed is True


async def test_disabled_adapter_not_run(tmp_path):
    """Disabled adapter should be excluded by registry."""
    settings = _make_settings(tmp_path, scanners={
        "semgrep": ScannerToolConfig(
            adapter_class="scanner.adapters.semgrep.SemgrepAdapter",
            enabled=False,
        ),
        "cppcheck": ScannerToolConfig(
            adapter_class="scanner.adapters.cppcheck.CppcheckAdapter",
            enabled=True,
        ),
    })

    mock_cppcheck = MagicMock()
    mock_cppcheck.tool_name = "cppcheck"
    mock_cppcheck.run = AsyncMock(return_value=[])
    mock_cppcheck.get_version = AsyncMock(return_value="cppcheck-1.0")

    mock_registry = MagicMock()
    # Registry excludes disabled semgrep, only returns cppcheck
    mock_registry.get_enabled_adapters.return_value = [mock_cppcheck]

    MockRegistryClass = MagicMock(return_value=mock_registry)

    with patch("scanner.core.orchestrator.ScannerRegistry", MockRegistryClass):
        result, _, _ = await run_scan(settings, target_path="/tmp/test")

    assert result.status == "completed"
    # Only cppcheck ran (semgrep was disabled via registry)
    mock_cppcheck.run.assert_awaited_once()
