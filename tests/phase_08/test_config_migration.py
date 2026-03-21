"""Tests for ScannerToolConfig migration: adapter_class and languages fields."""

import os
import pathlib

import pytest

from scanner.config import ScannerToolConfig, ScannerSettings


# ---------------------------------------------------------------------------
# Unit tests for ScannerToolConfig fields
# ---------------------------------------------------------------------------


class TestScannerToolConfigFields:
    """ScannerToolConfig accepts adapter_class and languages."""

    def test_adapter_class_accepted(self):
        cfg = ScannerToolConfig(
            adapter_class="scanner.adapters.semgrep.SemgrepAdapter",
            languages=["python", "php"],
        )
        assert cfg.adapter_class == "scanner.adapters.semgrep.SemgrepAdapter"
        assert cfg.languages == ["python", "php"]

    def test_defaults(self):
        cfg = ScannerToolConfig()
        assert cfg.adapter_class == ""
        assert cfg.languages == []
        assert cfg.enabled == "auto"
        assert cfg.timeout == 180
        assert cfg.extra_args == []


# ---------------------------------------------------------------------------
# Integration tests: loading from real config.yml
# ---------------------------------------------------------------------------

_CONFIG_YML = pathlib.Path(__file__).resolve().parents[2] / "config.yml"


@pytest.fixture()
def settings():
    """Load ScannerSettings from the project's config.yml."""
    old = os.environ.get("SCANNER_CONFIG_PATH")
    os.environ["SCANNER_CONFIG_PATH"] = str(_CONFIG_YML)
    try:
        s = ScannerSettings()
        yield s
    finally:
        if old is None:
            os.environ.pop("SCANNER_CONFIG_PATH", None)
        else:
            os.environ["SCANNER_CONFIG_PATH"] = old


class TestConfigYmlMigration:
    """config.yml produces scanner entries with adapter_class and languages."""

    EXPECTED_SCANNERS = {
        "semgrep",
        "cppcheck",
        "gitleaks",
        "trivy",
        "checkov",
        "psalm",
        "enlightn",
        "php_security_checker",
        "gosec",
        "bandit",
        "brakeman",
        "cargo_audit",
    }

    def test_scanners_is_dict(self, settings):
        assert isinstance(settings.scanners, dict)

    def test_has_all_scanners(self, settings):
        assert set(settings.scanners.keys()) == self.EXPECTED_SCANNERS

    def test_each_scanner_has_adapter_class(self, settings):
        for name, cfg in settings.scanners.items():
            assert cfg.adapter_class, f"{name} missing adapter_class"
            assert cfg.adapter_class.startswith("scanner.adapters."), (
                f"{name} adapter_class has wrong prefix: {cfg.adapter_class}"
            )

    def test_semgrep_adapter_class(self, settings):
        assert (
            settings.scanners["semgrep"].adapter_class
            == "scanner.adapters.semgrep.SemgrepAdapter"
        )

    def test_gitleaks_universal(self, settings):
        assert settings.scanners["gitleaks"].languages == []

    def test_psalm_php(self, settings):
        assert settings.scanners["psalm"].languages == ["php"]

    def test_semgrep_languages(self, settings):
        langs = settings.scanners["semgrep"].languages
        assert len(langs) == 10
        for expected in ("python", "php", "javascript"):
            assert expected in langs, f"semgrep missing language: {expected}"
