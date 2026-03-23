"""Tests for config system, severity enum, and Pydantic schemas."""

import os
import pytest
from enum import IntEnum


class TestSeverity:
    """Severity enum tests."""

    def test_severity_values(self):
        from scanner.schemas.severity import Severity

        assert Severity.CRITICAL == 5
        assert Severity.HIGH == 4
        assert Severity.MEDIUM == 3
        assert Severity.LOW == 2
        assert Severity.INFO == 1

    def test_severity_ordering(self):
        from scanner.schemas.severity import Severity

        assert Severity.CRITICAL > Severity.HIGH
        assert Severity.HIGH > Severity.MEDIUM
        assert Severity.MEDIUM > Severity.LOW
        assert Severity.LOW > Severity.INFO

    def test_severity_from_int(self):
        from scanner.schemas.severity import Severity

        assert Severity(5) == Severity.CRITICAL
        assert Severity(1) == Severity.INFO

    def test_severity_is_intenum(self):
        from scanner.schemas.severity import Severity

        assert issubclass(Severity, IntEnum)


class TestScannerSettings:
    """Config loading tests."""

    def test_default_values(self):
        from scanner.config import ScannerSettings

        settings = ScannerSettings()
        assert settings.host == "0.0.0.0"
        assert settings.port == 8000
        assert settings.db_path == "/data/scanner.db"

    def test_yaml_loading(self, tmp_config_file, monkeypatch):
        from scanner.config import ScannerSettings

        monkeypatch.setenv("SCANNER_CONFIG_PATH", tmp_config_file)
        settings = ScannerSettings()
        assert settings.host == "127.0.0.1"
        assert settings.port == 9000
        assert settings.db_path == "/tmp/test.db"

    def test_env_override(self, tmp_config_file, monkeypatch):
        from scanner.config import ScannerSettings

        monkeypatch.setenv("SCANNER_CONFIG_PATH", tmp_config_file)
        monkeypatch.setenv("SCANNER_PORT", "9999")
        settings = ScannerSettings()
        # Env var should override YAML value of 9000
        assert settings.port == 9999

    def test_no_hardcoded_secrets(self):
        from scanner.config import ScannerSettings

        settings = ScannerSettings()
        assert settings.claude_api_key == ""

    def test_config_path_env(self, tmp_path, monkeypatch):
        from scanner.config import ScannerSettings

        custom_config = tmp_path / "custom.yml"
        custom_config.write_text('host: "custom-host"\nport: 7777\n')
        monkeypatch.setenv("SCANNER_CONFIG_PATH", str(custom_config))
        settings = ScannerSettings()
        assert settings.host == "custom-host"
        assert settings.port == 7777


class TestFindingSchema:
    """Finding schema validation tests."""

    def test_finding_schema(self):
        from scanner.schemas.finding import FindingSchema
        from scanner.schemas.severity import Severity

        finding = FindingSchema(
            fingerprint="a" * 64,
            tool="semgrep",
            rule_id="sql-injection",
            file_path="src/auth.py",
            severity=Severity.HIGH,
            title="SQL Injection found",
        )
        assert finding.tool == "semgrep"
        assert finding.severity == Severity.HIGH
        assert finding.fingerprint == "a" * 64

    def test_finding_schema_severity_validation(self):
        from scanner.schemas.finding import FindingSchema

        with pytest.raises(Exception):
            FindingSchema(
                fingerprint="a" * 64,
                tool="semgrep",
                rule_id="test",
                file_path="test.py",
                severity=99,  # Invalid severity
                title="Test",
            )

    def test_finding_schema_optional_fields(self):
        from scanner.schemas.finding import FindingSchema
        from scanner.schemas.severity import Severity

        finding = FindingSchema(
            fingerprint="b" * 64,
            tool="gitleaks",
            rule_id="hardcoded-secret",
            file_path="config.py",
            severity=Severity.CRITICAL,
            title="Hardcoded secret",
        )
        assert finding.line_start is None
        assert finding.snippet is None
        assert finding.description is None
        assert finding.ai_analysis is None
        assert finding.false_positive is False


class TestScanResultSchema:
    """ScanResult schema validation tests."""

    def test_scan_result_schema(self):
        from scanner.schemas.scan import ScanResultSchema
        from datetime import datetime

        scan = ScanResultSchema(
            status="completed",
            started_at=datetime(2026, 1, 1, 12, 0, 0),
            completed_at=datetime(2026, 1, 1, 12, 5, 0),
            total_findings=10,
            critical_count=2,
            high_count=3,
            medium_count=5,
        )
        assert scan.status == "completed"
        assert scan.total_findings == 10
        assert scan.critical_count == 2

    def test_scan_result_defaults(self):
        from scanner.schemas.scan import ScanResultSchema

        scan = ScanResultSchema()
        assert scan.status == "pending"
        assert scan.total_findings == 0
        assert scan.critical_count == 0
        assert scan.gate_passed is None
        assert scan.id is None
