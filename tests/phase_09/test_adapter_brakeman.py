"""Tests for BrakemanAdapter."""

import json
from unittest.mock import AsyncMock

import pytest

from scanner.adapters.brakeman import BrakemanAdapter
from scanner.core.exceptions import ScannerExecutionError
from scanner.schemas.severity import Severity


@pytest.fixture
def adapter():
    return BrakemanAdapter()


@pytest.mark.asyncio
async def test_parse_brakeman_findings(adapter, brakeman_output):
    """Parse fixture JSON and return 3 findings."""
    adapter._execute = AsyncMock(
        return_value=(json.dumps(brakeman_output), "", 0)
    )
    findings = await adapter.run("/tmp/target", timeout=60)
    assert len(findings) == 3
    assert all(f.tool == "brakeman" for f in findings)


@pytest.mark.asyncio
async def test_brakeman_confidence_weighted_severity(adapter, brakeman_output):
    """High -> HIGH, Medium -> MEDIUM, Weak -> LOW."""
    adapter._execute = AsyncMock(
        return_value=(json.dumps(brakeman_output), "", 0)
    )
    findings = await adapter.run("/tmp/target", timeout=60)
    severity_map = {f.rule_id: f.severity for f in findings}
    assert severity_map["SQL"] == Severity.HIGH
    assert severity_map["CrossSiteScripting"] == Severity.MEDIUM
    assert severity_map["MassAssignment"] == Severity.LOW


@pytest.mark.asyncio
async def test_brakeman_weak_confidence_downgrade(adapter, brakeman_output):
    """Weak confidence warning gets downgraded: should be LOW."""
    adapter._execute = AsyncMock(
        return_value=(json.dumps(brakeman_output), "", 0)
    )
    findings = await adapter.run("/tmp/target", timeout=60)
    weak_finding = [f for f in findings if f.rule_id == "MassAssignment"][0]
    assert weak_finding.severity == Severity.LOW


@pytest.mark.asyncio
async def test_brakeman_path_normalization(adapter, brakeman_output):
    """File paths should be passed through as-is (relative to Rails app)."""
    adapter._execute = AsyncMock(
        return_value=(json.dumps(brakeman_output), "", 0)
    )
    findings = await adapter.run("/tmp/target", timeout=60)
    for f in findings:
        assert not f.file_path.startswith("/tmp/target")
        assert not f.file_path.startswith("/")


@pytest.mark.asyncio
async def test_brakeman_exit_code_0_normal(adapter, brakeman_output):
    """Exit code 0 (with --no-exit-on-warn) returns findings."""
    adapter._execute = AsyncMock(
        return_value=(json.dumps(brakeman_output), "", 0)
    )
    findings = await adapter.run("/tmp/target", timeout=60)
    assert len(findings) == 3


@pytest.mark.asyncio
async def test_brakeman_exit_code_nonzero_error(adapter):
    """Exit code >= 1 with stderr error text raises ScannerExecutionError."""
    adapter._execute = AsyncMock(
        return_value=("", "Error: something went wrong", 1)
    )
    with pytest.raises(ScannerExecutionError):
        await adapter.run("/tmp/target", timeout=60)


@pytest.mark.asyncio
async def test_brakeman_fingerprint_populated(adapter, brakeman_output):
    """Each finding should have a 64-char hex fingerprint."""
    adapter._execute = AsyncMock(
        return_value=(json.dumps(brakeman_output), "", 0)
    )
    findings = await adapter.run("/tmp/target", timeout=60)
    for f in findings:
        assert len(f.fingerprint) == 64
        assert all(c in "0123456789abcdef" for c in f.fingerprint)


@pytest.mark.asyncio
async def test_brakeman_empty_warnings(adapter):
    """Empty warnings list returns empty findings list."""
    empty_output = json.dumps({"warnings": [], "errors": []})
    adapter._execute = AsyncMock(return_value=(empty_output, "", 0))
    findings = await adapter.run("/tmp/target", timeout=60)
    assert findings == []


@pytest.mark.asyncio
async def test_brakeman_non_rails_graceful(adapter):
    """Non-Rails project returns empty list instead of raising."""
    adapter._execute = AsyncMock(
        return_value=(
            "",
            "Please supply the path to a Rails application",
            1,
        )
    )
    findings = await adapter.run("/tmp/target", timeout=60)
    assert findings == []
