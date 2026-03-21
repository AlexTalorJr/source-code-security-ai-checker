"""Tests for GosecAdapter."""

import json
from unittest.mock import AsyncMock

import pytest

from scanner.adapters.gosec import GosecAdapter
from scanner.core.exceptions import ScannerExecutionError
from scanner.schemas.severity import Severity


@pytest.fixture
def adapter():
    return GosecAdapter()


@pytest.mark.asyncio
async def test_parse_gosec_findings(adapter, gosec_output):
    """Parse fixture JSON and return 3 findings."""
    adapter._execute = AsyncMock(
        return_value=(json.dumps(gosec_output), "", 1)
    )
    findings = await adapter.run("/tmp/target", timeout=60)
    assert len(findings) == 3
    assert all(f.tool == "gosec" for f in findings)


@pytest.mark.asyncio
async def test_gosec_severity_mapping(adapter, gosec_output):
    """HIGH -> HIGH, MEDIUM -> MEDIUM, LOW -> LOW."""
    adapter._execute = AsyncMock(
        return_value=(json.dumps(gosec_output), "", 1)
    )
    findings = await adapter.run("/tmp/target", timeout=60)
    severity_map = {f.rule_id: f.severity for f in findings}
    assert severity_map["G101"] == Severity.HIGH
    assert severity_map["G304"] == Severity.MEDIUM
    assert severity_map["G104"] == Severity.LOW


@pytest.mark.asyncio
async def test_gosec_path_normalization(adapter, gosec_output):
    """File paths should have target prefix stripped."""
    adapter._execute = AsyncMock(
        return_value=(json.dumps(gosec_output), "", 1)
    )
    findings = await adapter.run("/tmp/target", timeout=60)
    for f in findings:
        assert not f.file_path.startswith("/tmp/target")
        assert not f.file_path.startswith("/")


@pytest.mark.asyncio
async def test_gosec_exit_code_1_is_not_error(adapter, gosec_output):
    """Exit code 1 means findings found -- not an error."""
    adapter._execute = AsyncMock(
        return_value=(json.dumps(gosec_output), "", 1)
    )
    findings = await adapter.run("/tmp/target", timeout=60)
    assert len(findings) == 3


@pytest.mark.asyncio
async def test_gosec_exit_code_2_raises_error(adapter):
    """Exit code >= 2 is a real error."""
    adapter._execute = AsyncMock(return_value=("", "fatal error", 2))
    with pytest.raises(ScannerExecutionError):
        await adapter.run("/tmp/target", timeout=60)


@pytest.mark.asyncio
async def test_gosec_fingerprint_populated(adapter, gosec_output):
    """Each finding should have a 64-char hex fingerprint."""
    adapter._execute = AsyncMock(
        return_value=(json.dumps(gosec_output), "", 1)
    )
    findings = await adapter.run("/tmp/target", timeout=60)
    for f in findings:
        assert len(f.fingerprint) == 64
        assert all(c in "0123456789abcdef" for c in f.fingerprint)


@pytest.mark.asyncio
async def test_gosec_empty_results(adapter):
    """Empty Issues list returns empty findings list."""
    empty_output = json.dumps({"Issues": [], "Stats": {}})
    adapter._execute = AsyncMock(return_value=(empty_output, "", 0))
    findings = await adapter.run("/tmp/target", timeout=60)
    assert findings == []


@pytest.mark.asyncio
async def test_gosec_string_line_numbers(adapter, gosec_output):
    """Line numbers should be converted from string to int; line_end == line_start."""
    adapter._execute = AsyncMock(
        return_value=(json.dumps(gosec_output), "", 1)
    )
    findings = await adapter.run("/tmp/target", timeout=60)
    for f in findings:
        assert isinstance(f.line_start, int)
        assert f.line_end == f.line_start
