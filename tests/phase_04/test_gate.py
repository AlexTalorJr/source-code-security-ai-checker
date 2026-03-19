"""Tests for configurable quality gate (GateConfig)."""

from unittest.mock import AsyncMock, patch

import pytest

from scanner.config import GateConfig, ScannerSettings
from scanner.schemas.compound_risk import CompoundRiskSchema
from scanner.schemas.severity import Severity


def _zero_counts() -> dict[Severity, int]:
    """Severity counts with all zeros."""
    return {s: 0 for s in Severity}


def test_default_gate_fails_on_critical():
    """GateConfig().evaluate with CRITICAL > 0 returns (False, reasons with 'CRITICAL')."""
    gate = GateConfig()
    counts = _zero_counts()
    counts[Severity.CRITICAL] = 2

    passed, reasons = gate.evaluate(counts, [])

    assert passed is False
    assert len(reasons) == 1
    assert "2 CRITICAL finding(s)" in reasons[0]


def test_default_gate_fails_on_high():
    """GateConfig().evaluate with HIGH > 0 returns (False, reasons with 'HIGH')."""
    gate = GateConfig()
    counts = _zero_counts()
    counts[Severity.HIGH] = 3

    passed, reasons = gate.evaluate(counts, [])

    assert passed is False
    assert "3 HIGH finding(s)" in reasons[0]


def test_default_gate_passes_medium_only():
    """GateConfig().evaluate with only MEDIUM > 0 returns (True, [])."""
    gate = GateConfig()
    counts = _zero_counts()
    counts[Severity.MEDIUM] = 5

    passed, reasons = gate.evaluate(counts, [])

    assert passed is True
    assert reasons == []


def test_custom_gate_medium_threshold():
    """GateConfig(fail_on=['medium']).evaluate with MEDIUM > 0 returns (False, ...)."""
    gate = GateConfig(fail_on=["medium"])
    counts = _zero_counts()
    counts[Severity.MEDIUM] = 2

    passed, reasons = gate.evaluate(counts, [])

    assert passed is False
    assert "2 MEDIUM finding(s)" in reasons[0]


def test_compound_risk_fails_gate():
    """GateConfig().evaluate with zero individual findings but HIGH compound risk returns (False, ...)."""
    gate = GateConfig()
    counts = _zero_counts()
    compound_risk = CompoundRiskSchema(
        title="Auth bypass chain",
        description="Combined attack path",
        severity=Severity.HIGH.value,
        finding_fingerprints=["a" * 64],
    )

    passed, reasons = gate.evaluate(counts, [compound_risk])

    assert passed is False
    assert any("Compound risk" in r and "HIGH" in r for r in reasons)


def test_compound_risk_disabled():
    """GateConfig(include_compound_risks=False).evaluate with HIGH compound risk returns (True, [])."""
    gate = GateConfig(include_compound_risks=False)
    counts = _zero_counts()
    compound_risk = CompoundRiskSchema(
        title="Auth bypass chain",
        description="Combined attack path",
        severity=Severity.HIGH.value,
        finding_fingerprints=["a" * 64],
    )

    passed, reasons = gate.evaluate(counts, [compound_risk])

    assert passed is True
    assert reasons == []


def test_exit_code(sample_scan_result):
    """CLI exits with 1 when gate fails (mock run_scan to return gate_passed=False)."""
    from typer.testing import CliRunner
    from scanner.cli.main import app

    runner = CliRunner()
    # run_scan now returns a tuple
    mock_result = (sample_scan_result, [], [])

    with patch("scanner.cli.main.run_scan", new_callable=AsyncMock, return_value=mock_result):
        result = runner.invoke(app, ["scan", "--path", "/tmp/test"])

    assert result.exit_code == 1


def test_configurable_thresholds():
    """GateConfig loads from dict matching YAML structure."""
    gate = GateConfig(**{"fail_on": ["critical", "medium"], "include_compound_risks": False})

    assert gate.fail_on == ["critical", "medium"]
    assert gate.include_compound_risks is False


def test_gate_in_report():
    """Fail_reasons list is non-empty string list when gate fails."""
    gate = GateConfig()
    counts = _zero_counts()
    counts[Severity.CRITICAL] = 1
    counts[Severity.HIGH] = 2

    passed, reasons = gate.evaluate(counts, [])

    assert passed is False
    assert len(reasons) == 2
    assert all(isinstance(r, str) for r in reasons)
    assert any("CRITICAL" in r for r in reasons)
    assert any("HIGH" in r for r in reasons)


def test_default_gate_config_values():
    """Default GateConfig() has fail_on=['critical', 'high'] and include_compound_risks=True."""
    gate = GateConfig()
    assert gate.fail_on == ["critical", "high"]
    assert gate.include_compound_risks is True


def test_scanner_settings_has_gate():
    """ScannerSettings includes gate field with default GateConfig."""
    import os
    os.environ["SCANNER_CONFIG_PATH"] = "/dev/null"
    settings = ScannerSettings()
    assert hasattr(settings, "gate")
    assert isinstance(settings.gate, GateConfig)
    assert settings.gate.fail_on == ["critical", "high"]
