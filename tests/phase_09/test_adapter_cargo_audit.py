"""Tests for CargoAuditAdapter."""

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scanner.adapters.cargo_audit import CargoAuditAdapter, _ensure_lockfile
from scanner.core.exceptions import ScannerExecutionError
from scanner.schemas.severity import Severity


@pytest.fixture
def adapter():
    return CargoAuditAdapter()


@pytest.mark.asyncio
async def test_parse_cargo_audit_findings(adapter, cargo_audit_output):
    """Parse fixture JSON and return 2 findings (warnings ignored)."""
    with patch(
        "scanner.adapters.cargo_audit._ensure_lockfile",
        new_callable=AsyncMock,
        return_value=True,
    ):
        adapter._execute = AsyncMock(
            return_value=(json.dumps(cargo_audit_output), "", 1)
        )
        findings = await adapter.run("/tmp/target", timeout=60)
    assert len(findings) == 2
    assert all(f.tool == "cargo-audit" for f in findings)


@pytest.mark.asyncio
async def test_cargo_audit_cvss_severity(adapter, cargo_audit_output):
    """RUSTSEC-2023-0001 CVSS 9.8 -> CRITICAL."""
    with patch(
        "scanner.adapters.cargo_audit._ensure_lockfile",
        new_callable=AsyncMock,
        return_value=True,
    ):
        adapter._execute = AsyncMock(
            return_value=(json.dumps(cargo_audit_output), "", 1)
        )
        findings = await adapter.run("/tmp/target", timeout=60)
    sev_map = {f.rule_id: f.severity for f in findings}
    assert sev_map["RUSTSEC-2023-0001"] == Severity.CRITICAL


@pytest.mark.asyncio
async def test_cargo_audit_null_cvss_defaults_medium(adapter, cargo_audit_output):
    """RUSTSEC-2023-0050 null CVSS -> MEDIUM."""
    with patch(
        "scanner.adapters.cargo_audit._ensure_lockfile",
        new_callable=AsyncMock,
        return_value=True,
    ):
        adapter._execute = AsyncMock(
            return_value=(json.dumps(cargo_audit_output), "", 1)
        )
        findings = await adapter.run("/tmp/target", timeout=60)
    sev_map = {f.rule_id: f.severity for f in findings}
    assert sev_map["RUSTSEC-2023-0050"] == Severity.MEDIUM


@pytest.mark.asyncio
async def test_cargo_audit_ignores_warnings(adapter, cargo_audit_output):
    """Only vulnerabilities.list items become findings, not warnings."""
    with patch(
        "scanner.adapters.cargo_audit._ensure_lockfile",
        new_callable=AsyncMock,
        return_value=True,
    ):
        adapter._execute = AsyncMock(
            return_value=(json.dumps(cargo_audit_output), "", 1)
        )
        findings = await adapter.run("/tmp/target", timeout=60)
    # Fixture has 2 vulns + 1 yanked warning; only 2 should appear
    assert len(findings) == 2
    rule_ids = {f.rule_id for f in findings}
    assert "old-crate" not in rule_ids


@pytest.mark.asyncio
async def test_cargo_audit_rule_id_is_advisory_id(adapter, cargo_audit_output):
    """rule_id should be the advisory ID."""
    with patch(
        "scanner.adapters.cargo_audit._ensure_lockfile",
        new_callable=AsyncMock,
        return_value=True,
    ):
        adapter._execute = AsyncMock(
            return_value=(json.dumps(cargo_audit_output), "", 1)
        )
        findings = await adapter.run("/tmp/target", timeout=60)
    rule_ids = {f.rule_id for f in findings}
    assert "RUSTSEC-2023-0001" in rule_ids
    assert "RUSTSEC-2023-0050" in rule_ids


@pytest.mark.asyncio
async def test_cargo_audit_file_path_is_cargo_lock(adapter, cargo_audit_output):
    """All findings have file_path == 'Cargo.lock'."""
    with patch(
        "scanner.adapters.cargo_audit._ensure_lockfile",
        new_callable=AsyncMock,
        return_value=True,
    ):
        adapter._execute = AsyncMock(
            return_value=(json.dumps(cargo_audit_output), "", 1)
        )
        findings = await adapter.run("/tmp/target", timeout=60)
    for f in findings:
        assert f.file_path == "Cargo.lock"


@pytest.mark.asyncio
async def test_cargo_audit_line_start_none(adapter, cargo_audit_output):
    """All findings have line_start == None and line_end == None."""
    with patch(
        "scanner.adapters.cargo_audit._ensure_lockfile",
        new_callable=AsyncMock,
        return_value=True,
    ):
        adapter._execute = AsyncMock(
            return_value=(json.dumps(cargo_audit_output), "", 1)
        )
        findings = await adapter.run("/tmp/target", timeout=60)
    for f in findings:
        assert f.line_start is None
        assert f.line_end is None


@pytest.mark.asyncio
async def test_cargo_audit_exit_code_1_is_not_error(adapter, cargo_audit_output):
    """Exit code 1 returns findings normally."""
    with patch(
        "scanner.adapters.cargo_audit._ensure_lockfile",
        new_callable=AsyncMock,
        return_value=True,
    ):
        adapter._execute = AsyncMock(
            return_value=(json.dumps(cargo_audit_output), "", 1)
        )
        findings = await adapter.run("/tmp/target", timeout=60)
    assert len(findings) == 2


@pytest.mark.asyncio
async def test_cargo_audit_exit_code_2_raises_error(adapter):
    """Exit code >= 2 raises ScannerExecutionError."""
    with patch(
        "scanner.adapters.cargo_audit._ensure_lockfile",
        new_callable=AsyncMock,
        return_value=True,
    ):
        adapter._execute = AsyncMock(return_value=("", "fatal error", 2))
        with pytest.raises(ScannerExecutionError):
            await adapter.run("/tmp/target", timeout=60)


@pytest.mark.asyncio
async def test_cargo_audit_fingerprint_populated(adapter, cargo_audit_output):
    """Each finding has a 64-char hex fingerprint."""
    with patch(
        "scanner.adapters.cargo_audit._ensure_lockfile",
        new_callable=AsyncMock,
        return_value=True,
    ):
        adapter._execute = AsyncMock(
            return_value=(json.dumps(cargo_audit_output), "", 1)
        )
        findings = await adapter.run("/tmp/target", timeout=60)
    for f in findings:
        assert len(f.fingerprint) == 64
        assert all(c in "0123456789abcdef" for c in f.fingerprint)


@pytest.mark.asyncio
async def test_cargo_audit_empty_vulnerabilities(adapter):
    """Empty vulnerabilities list returns empty findings list."""
    empty_output = json.dumps(
        {"vulnerabilities": {"found": False, "count": 0, "list": []}, "warnings": {}}
    )
    with patch(
        "scanner.adapters.cargo_audit._ensure_lockfile",
        new_callable=AsyncMock,
        return_value=True,
    ):
        adapter._execute = AsyncMock(return_value=(empty_output, "", 0))
        findings = await adapter.run("/tmp/target", timeout=60)
    assert findings == []


@pytest.mark.asyncio
async def test_cargo_audit_generates_lockfile_if_missing(adapter, cargo_audit_output):
    """Generate Cargo.lock via cargo generate-lockfile if missing."""
    mock_lockfile = MagicMock()
    mock_lockfile.exists.return_value = False

    mock_cargo_toml = MagicMock()
    mock_cargo_toml.exists.return_value = True

    def path_side_effect(p):
        result = MagicMock()
        if str(p).endswith("Cargo.lock"):
            result.exists.return_value = False
            result.__truediv__ = lambda s, x: path_side_effect(f"{p}/{x}")
            return result
        elif str(p).endswith("Cargo.toml"):
            result.exists.return_value = True
            return result
        # For Path(target_path) / "Cargo.lock" and Path(target_path) / "Cargo.toml"
        result.__truediv__ = lambda s, x: path_side_effect(f"{p}/{x}")
        return result

    # Mock the subprocess for cargo generate-lockfile
    mock_proc = AsyncMock()
    mock_proc.returncode = 0
    mock_proc.communicate = AsyncMock(return_value=(b"", b""))

    with patch("scanner.adapters.cargo_audit.Path") as mock_path_cls:
        # Path(target_path) / "Cargo.lock" -> not exists
        # Path(target_path) / "Cargo.toml" -> exists
        lock_path = MagicMock()
        lock_path.exists.return_value = False
        toml_path = MagicMock()
        toml_path.exists.return_value = True

        path_instance = MagicMock()
        path_instance.__truediv__ = lambda self, key: (
            lock_path if key == "Cargo.lock" else toml_path
        )
        mock_path_cls.return_value = path_instance

        with patch(
            "scanner.adapters.cargo_audit.asyncio.create_subprocess_exec",
            new_callable=AsyncMock,
            return_value=mock_proc,
        ) as mock_subprocess:
            result = await _ensure_lockfile("/tmp/target")

    assert result is True
    mock_subprocess.assert_called_once()
    call_args = mock_subprocess.call_args
    assert call_args[0] == ("cargo", "generate-lockfile")
    assert call_args[1]["cwd"] == "/tmp/target"


@pytest.mark.asyncio
async def test_cargo_audit_generates_lockfile_cargo_not_installed():
    """When cargo is not installed, _ensure_lockfile returns False gracefully."""
    lock_path = MagicMock()
    lock_path.exists.return_value = False
    toml_path = MagicMock()
    toml_path.exists.return_value = True

    path_instance = MagicMock()
    path_instance.__truediv__ = lambda self, key: (
        lock_path if key == "Cargo.lock" else toml_path
    )

    with patch("scanner.adapters.cargo_audit.Path", return_value=path_instance):
        with patch(
            "scanner.adapters.cargo_audit.asyncio.create_subprocess_exec",
            new_callable=AsyncMock,
            side_effect=FileNotFoundError("cargo not found"),
        ):
            result = await _ensure_lockfile("/tmp/target")

    assert result is False
