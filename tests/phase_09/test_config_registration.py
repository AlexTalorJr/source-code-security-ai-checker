"""Integration tests: all 4 new scanners register and load via config.yml."""

import pytest

from scanner.adapters.registry import ScannerRegistry, load_adapter_class
from scanner.config import ScannerToolConfig

NEW_SCANNERS = {
    "gosec": {
        "adapter_class": "scanner.adapters.gosec.GosecAdapter",
        "languages": ["go"],
        "tool_name": "gosec",
    },
    "bandit": {
        "adapter_class": "scanner.adapters.bandit.BanditAdapter",
        "languages": ["python"],
        "tool_name": "bandit",
    },
    "brakeman": {
        "adapter_class": "scanner.adapters.brakeman.BrakemanAdapter",
        "languages": ["ruby"],
        "tool_name": "brakeman",
    },
    "cargo_audit": {
        "adapter_class": "scanner.adapters.cargo_audit.CargoAuditAdapter",
        "languages": ["rust"],
        "tool_name": "cargo-audit",
    },
}


@pytest.mark.parametrize("scanner_name,info", NEW_SCANNERS.items())
def test_load_adapter_class(scanner_name, info):
    """Each adapter class can be dynamically loaded via importlib."""
    cls = load_adapter_class(scanner_name, info["adapter_class"])
    assert cls is not None, f"Failed to load {info['adapter_class']}"
    instance = cls()
    assert instance.tool_name == info["tool_name"]


def test_registry_loads_all_new_scanners():
    """ScannerRegistry loads all 4 new scanners without errors."""
    config = {
        name: ScannerToolConfig(
            adapter_class=info["adapter_class"],
            enabled="auto",
            timeout=120,
            languages=info["languages"],
        )
        for name, info in NEW_SCANNERS.items()
    }
    registry = ScannerRegistry(config)
    for name in NEW_SCANNERS:
        scanner = registry.get_scanner_config(name)
        assert scanner is not None
        assert scanner.load_error is None, f"{name}: {scanner.load_error}"
        assert scanner.adapter_class is not None


def test_registry_language_filtering():
    """New scanners are enabled for their respective languages."""
    config = {
        name: ScannerToolConfig(
            adapter_class=info["adapter_class"],
            enabled="auto",
            timeout=120,
            languages=info["languages"],
        )
        for name, info in NEW_SCANNERS.items()
    }
    registry = ScannerRegistry(config)

    go_adapters = registry.get_enabled_adapters({"go"})
    assert any(a.tool_name == "gosec" for a in go_adapters)

    python_adapters = registry.get_enabled_adapters({"python"})
    assert any(a.tool_name == "bandit" for a in python_adapters)

    ruby_adapters = registry.get_enabled_adapters({"ruby"})
    assert any(a.tool_name == "brakeman" for a in ruby_adapters)

    rust_adapters = registry.get_enabled_adapters({"rust"})
    assert any(a.tool_name == "cargo-audit" for a in rust_adapters)
