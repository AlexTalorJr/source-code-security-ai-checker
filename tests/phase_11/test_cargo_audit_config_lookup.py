"""Integration test: CargoAuditAdapter.tool_name matches config.yml key for orchestrator lookup."""

from scanner.adapters.cargo_audit import CargoAuditAdapter
from scanner.config import ScannerToolConfig


def test_cargo_audit_config_lookup_no_key_error():
    """Orchestrator uses settings.scanners[adapter.tool_name] -- must not raise KeyError."""
    adapter = CargoAuditAdapter()

    # Simulate the settings.scanners dict as it appears from config.yml
    settings = {
        "cargo_audit": ScannerToolConfig(
            adapter_class="scanner.adapters.cargo_audit.CargoAuditAdapter",
            enabled="auto",
            timeout=60,
            languages=["rust"],
        ),
    }

    # This is the exact lookup the orchestrator performs (line 196 of orchestrator.py)
    assert adapter.tool_name == "cargo_audit"
    assert settings[adapter.tool_name] is not None  # no KeyError
    assert settings[adapter.tool_name].timeout == 60
