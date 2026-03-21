"""Tests for BanditAdapter."""

import json
from unittest.mock import AsyncMock

import pytest

from scanner.adapters.bandit import BanditAdapter
from scanner.core.exceptions import ScannerExecutionError
from scanner.schemas.severity import Severity


@pytest.fixture
def adapter():
    return BanditAdapter()


@pytest.mark.asyncio
async def test_parse_bandit_findings(adapter, bandit_output):
    """Parse fixture JSON and return 4 findings."""
    adapter._execute = AsyncMock(
        return_value=(json.dumps(bandit_output), "", 1)
    )
    findings = await adapter.run("/tmp/target", timeout=60)
    assert len(findings) == 4
    assert all(f.tool == "bandit" for f in findings)


@pytest.mark.asyncio
async def test_bandit_severity_matrix(adapter, bandit_output):
    """HIGH/HIGH -> CRITICAL, HIGH/MEDIUM -> HIGH, MEDIUM/HIGH -> MEDIUM, LOW/LOW -> INFO."""
    adapter._execute = AsyncMock(
        return_value=(json.dumps(bandit_output), "", 1)
    )
    findings = await adapter.run("/tmp/target", timeout=60)
    severity_map = {f.rule_id: f.severity for f in findings}
    assert severity_map["B102"] == Severity.CRITICAL   # HIGH sev + HIGH conf
    assert severity_map["B105"] == Severity.HIGH        # HIGH sev + MEDIUM conf
    assert severity_map["B303"] == Severity.MEDIUM      # MEDIUM sev + HIGH conf
    assert severity_map["B103"] == Severity.INFO         # LOW sev + LOW conf


@pytest.mark.asyncio
async def test_bandit_path_normalization(adapter, bandit_output):
    """File paths should have target prefix stripped."""
    adapter._execute = AsyncMock(
        return_value=(json.dumps(bandit_output), "", 1)
    )
    findings = await adapter.run("/tmp/target", timeout=60)
    for f in findings:
        assert not f.file_path.startswith("/tmp/target")
        assert not f.file_path.startswith("/")


@pytest.mark.asyncio
async def test_bandit_exit_code_1_is_not_error(adapter, bandit_output):
    """Exit code 1 means findings found -- not an error."""
    adapter._execute = AsyncMock(
        return_value=(json.dumps(bandit_output), "", 1)
    )
    findings = await adapter.run("/tmp/target", timeout=60)
    assert len(findings) == 4


@pytest.mark.asyncio
async def test_bandit_exit_code_2_raises_error(adapter):
    """Exit code >= 2 is a real error."""
    adapter._execute = AsyncMock(return_value=("", "fatal error", 2))
    with pytest.raises(ScannerExecutionError):
        await adapter.run("/tmp/target", timeout=60)


@pytest.mark.asyncio
async def test_bandit_fingerprint_populated(adapter, bandit_output):
    """Each finding should have a 64-char hex fingerprint."""
    adapter._execute = AsyncMock(
        return_value=(json.dumps(bandit_output), "", 1)
    )
    findings = await adapter.run("/tmp/target", timeout=60)
    for f in findings:
        assert len(f.fingerprint) == 64
        assert all(c in "0123456789abcdef" for c in f.fingerprint)


@pytest.mark.asyncio
async def test_bandit_empty_results(adapter):
    """Empty results list returns empty findings list."""
    empty_output = json.dumps({"results": [], "errors": []})
    adapter._execute = AsyncMock(return_value=(empty_output, "", 0))
    findings = await adapter.run("/tmp/target", timeout=60)
    assert findings == []


@pytest.mark.asyncio
async def test_bandit_line_range(adapter, bandit_output):
    """line_start from line_number, line_end from last element of line_range."""
    adapter._execute = AsyncMock(
        return_value=(json.dumps(bandit_output), "", 1)
    )
    findings = await adapter.run("/tmp/target", timeout=60)
    for f in findings:
        assert isinstance(f.line_start, int)
        assert isinstance(f.line_end, int)
        assert f.line_end >= f.line_start
