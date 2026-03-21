"""Tests for ScannerRegistry: importlib loading, validation, error handling, filtering."""

import logging

import pytest

from scanner.adapters.base import ScannerAdapter
from scanner.config import ScannerToolConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(**overrides) -> ScannerToolConfig:
    defaults = {
        "adapter_class": "",
        "enabled": True,
        "timeout": 120,
        "extra_args": [],
        "languages": [],
    }
    defaults.update(overrides)
    return ScannerToolConfig(**defaults)


# ---------------------------------------------------------------------------
# load_adapter_class tests
# ---------------------------------------------------------------------------


class TestLoadAdapterClass:
    def test_load_adapter_from_config(self):
        from scanner.adapters.registry import load_adapter_class

        cls = load_adapter_class("semgrep", "scanner.adapters.semgrep.SemgrepAdapter")
        assert cls is not None
        assert issubclass(cls, ScannerAdapter)

    def test_missing_module_warns(self, caplog):
        from scanner.adapters.registry import load_adapter_class

        with caplog.at_level(logging.WARNING):
            result = load_adapter_class("bad", "scanner.adapters.nonexistent.Foo")
        assert result is None
        assert "failed to load adapter_class" in caplog.text

    def test_missing_class_warns(self, caplog):
        from scanner.adapters.registry import load_adapter_class

        with caplog.at_level(logging.WARNING):
            result = load_adapter_class(
                "bad", "scanner.adapters.semgrep.NonExistentClass"
            )
        assert result is None
        assert "failed to load adapter_class" in caplog.text

    def test_invalid_adapter_class_warns(self, caplog):
        """A dotted path with no dot should also fail gracefully."""
        from scanner.adapters.registry import load_adapter_class

        with caplog.at_level(logging.WARNING):
            result = load_adapter_class("bad", "nodots")
        assert result is None


# ---------------------------------------------------------------------------
# ScannerRegistry tests
# ---------------------------------------------------------------------------


class TestScannerRegistry:
    def test_non_subclass_rejected(self, caplog):
        """A class that is not a ScannerAdapter subclass is rejected."""
        from scanner.adapters.registry import ScannerRegistry

        # Use a real class that exists but is NOT a ScannerAdapter subclass
        config = {
            "fake": _make_config(
                adapter_class="scanner.config.ScannerToolConfig",
            ),
        }
        with caplog.at_level(logging.WARNING):
            reg = ScannerRegistry(config)
        entry = reg.get_scanner_config("fake")
        assert entry is not None
        assert entry.load_error is not None
        assert "not a ScannerAdapter subclass" in entry.load_error

    def test_missing_adapter_class_sets_error(self, caplog):
        from scanner.adapters.registry import ScannerRegistry

        config = {"empty": _make_config(adapter_class="")}
        with caplog.at_level(logging.WARNING):
            reg = ScannerRegistry(config)
        entry = reg.get_scanner_config("empty")
        assert entry.load_error == "adapter_class is required"

    def test_language_filtering(self):
        """get_enabled_adapters filters by detected languages."""
        from scanner.adapters.registry import ScannerRegistry

        config = {
            "semgrep": _make_config(
                adapter_class="scanner.adapters.semgrep.SemgrepAdapter",
                languages=["python", "php"],
                enabled="auto",
            ),
            "cppcheck": _make_config(
                adapter_class="scanner.adapters.cppcheck.CppcheckAdapter",
                languages=["cpp"],
                enabled="auto",
            ),
        }
        reg = ScannerRegistry(config)
        adapters = reg.get_enabled_adapters(detected_languages={"python"})
        names = [a.tool_name for a in adapters]
        assert "semgrep" in names
        assert "cppcheck" not in names

    def test_universal_scanner(self):
        """Scanners with languages=[] are universal -- always included."""
        from scanner.adapters.registry import ScannerRegistry

        config = {
            "gitleaks": _make_config(
                adapter_class="scanner.adapters.gitleaks.GitleaksAdapter",
                languages=[],
                enabled="auto",
            ),
        }
        reg = ScannerRegistry(config)
        adapters = reg.get_enabled_adapters(detected_languages={"python"})
        names = [a.tool_name for a in adapters]
        assert "gitleaks" in names

    def test_disabled_scanner_skipped(self):
        from scanner.adapters.registry import ScannerRegistry

        config = {
            "semgrep": _make_config(
                adapter_class="scanner.adapters.semgrep.SemgrepAdapter",
                enabled=False,
            ),
        }
        reg = ScannerRegistry(config)
        adapters = reg.get_enabled_adapters(detected_languages={"python"})
        assert len(adapters) == 0

    def test_all_scanners_info(self):
        from scanner.adapters.registry import ScannerRegistry

        config = {
            "semgrep": _make_config(
                adapter_class="scanner.adapters.semgrep.SemgrepAdapter",
                languages=["python"],
            ),
        }
        reg = ScannerRegistry(config)
        info = reg.all_scanners_info()
        assert len(info) == 1
        entry = info[0]
        assert entry["name"] == "semgrep"
        assert entry["status"] == "enabled"
        assert entry["enabled"] is True
        assert entry["languages"] == ["python"]
        assert entry["load_error"] is None

    def test_failed_scanner_info(self, caplog):
        from scanner.adapters.registry import ScannerRegistry

        config = {
            "broken": _make_config(
                adapter_class="scanner.adapters.nonexistent.Broken",
            ),
        }
        with caplog.at_level(logging.WARNING):
            reg = ScannerRegistry(config)
        info = reg.all_scanners_info()
        assert info[0]["status"] == "load_error"
        assert info[0]["load_error"] is not None
