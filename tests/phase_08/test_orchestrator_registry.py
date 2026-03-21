"""Tests for orchestrator using ScannerRegistry instead of ALL_ADAPTERS."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scanner.config import ScannerSettings, ScannerToolConfig
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
    """Create ScannerSettings with dict-based scanners config."""
    db_path = str(tmp_path / "test.db")
    os.environ["SCANNER_CONFIG_PATH"] = "/dev/null"
    if scanners is None:
        scanners = {
            "semgrep": ScannerToolConfig(
                adapter_class="scanner.adapters.semgrep.SemgrepAdapter",
                enabled=True,
                timeout=180,
                languages=["python"],
            ),
        }
    return ScannerSettings(db_path=db_path, scanners=scanners)


def _mock_adapter(tool_name: str, findings: list[FindingSchema] | None = None):
    """Create a mock ScannerAdapter instance."""
    instance = MagicMock()
    instance.tool_name = tool_name
    instance.run = AsyncMock(return_value=findings or [])
    instance.get_version = AsyncMock(return_value=f"{tool_name}-1.0")
    return instance


@pytest.fixture(autouse=True)
def _mock_language_detect():
    """Auto-detect returns all languages so registry can filter."""
    all_langs = {"python", "php", "javascript", "typescript",
                 "go", "rust", "java", "docker", "terraform", "yaml", "ci"}
    with patch("scanner.core.language_detect.detect_languages", return_value=all_langs):
        yield


async def test_orchestrator_uses_registry(tmp_path):
    """run_scan creates ScannerRegistry from settings.scanners and uses get_enabled_adapters."""
    mock_adapter = _mock_adapter("semgrep", [_make_finding()])
    settings = _make_settings(tmp_path)

    with patch("scanner.core.orchestrator.ScannerRegistry") as MockRegistry:
        MockRegistry.return_value.get_enabled_adapters.return_value = [mock_adapter]
        result, findings, _ = await run_scan(settings, target_path="/tmp/test")

    MockRegistry.assert_called_once_with(settings.scanners)
    assert result.status == "completed"
    assert result.total_findings == 1


async def test_per_tool_config_dict_access(tmp_path):
    """Orchestrator accesses settings.scanners[tool_name].timeout via dict syntax."""
    mock_adapter = _mock_adapter("semgrep", [])
    settings = _make_settings(tmp_path, scanners={
        "semgrep": ScannerToolConfig(
            adapter_class="scanner.adapters.semgrep.SemgrepAdapter",
            enabled=True,
            timeout=300,
            extra_args=["--verbose"],
        ),
    })

    with patch("scanner.core.orchestrator.ScannerRegistry") as MockRegistry:
        MockRegistry.return_value.get_enabled_adapters.return_value = [mock_adapter]
        await run_scan(settings, target_path="/tmp/test")

    # Verify the adapter was called with timeout=300 and extra_args
    mock_adapter.run.assert_awaited_once()
    call_args = mock_adapter.run.call_args
    assert call_args[0][1] == 300  # timeout
    assert call_args[0][2] == ["--verbose"]  # extra_args


async def test_gitleaks_shallow_clone_with_gitleaks_enabled(tmp_path):
    """When gitleaks is in config and enabled, clone should use shallow=False."""
    settings = _make_settings(tmp_path, scanners={
        "gitleaks": ScannerToolConfig(
            adapter_class="scanner.adapters.gitleaks.GitleaksAdapter",
            enabled=True,
        ),
    })

    with (
        patch("scanner.core.orchestrator.ScannerRegistry") as MockRegistry,
        patch("scanner.core.orchestrator.clone_repo", new_callable=AsyncMock, return_value="/tmp/clone") as mock_clone,
        patch("scanner.core.orchestrator.cleanup_clone"),
    ):
        mock_adapter = _mock_adapter("gitleaks")
        MockRegistry.return_value.get_enabled_adapters.return_value = [mock_adapter]
        await run_scan(settings, repo_url="https://example.com/repo.git", branch="main")

    mock_clone.assert_called_once()
    assert mock_clone.call_args[1].get("shallow") is False or mock_clone.call_args.kwargs.get("shallow") is False


async def test_gitleaks_shallow_clone_when_not_in_config(tmp_path):
    """When gitleaks is not in config, clone should use shallow=True."""
    settings = _make_settings(tmp_path, scanners={
        "semgrep": ScannerToolConfig(
            adapter_class="scanner.adapters.semgrep.SemgrepAdapter",
            enabled=True,
        ),
    })

    with (
        patch("scanner.core.orchestrator.ScannerRegistry") as MockRegistry,
        patch("scanner.core.orchestrator.clone_repo", new_callable=AsyncMock, return_value="/tmp/clone") as mock_clone,
        patch("scanner.core.orchestrator.cleanup_clone"),
    ):
        mock_adapter = _mock_adapter("semgrep")
        MockRegistry.return_value.get_enabled_adapters.return_value = [mock_adapter]
        await run_scan(settings, repo_url="https://example.com/repo.git", branch="main")

    mock_clone.assert_called_once()
    assert mock_clone.call_args.kwargs.get("shallow") is True
