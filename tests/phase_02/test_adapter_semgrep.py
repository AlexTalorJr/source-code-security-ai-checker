"""Tests for SemgrepAdapter."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from scanner.adapters.semgrep import SemgrepAdapter
from scanner.core.exceptions import ScannerExecutionError
from scanner.schemas.severity import Severity


@pytest.fixture
def adapter():
    return SemgrepAdapter()


@pytest.mark.asyncio
async def test_parse_semgrep_findings(adapter, semgrep_output):
    """Parse fixture JSON and return 3 findings."""
    adapter._execute = AsyncMock(
        return_value=(json.dumps(semgrep_output), "", 0)
    )
    findings = await adapter.run("/tmp/target", timeout=60)
    assert len(findings) == 3
    assert all(f.tool == "semgrep" for f in findings)


@pytest.mark.asyncio
async def test_semgrep_severity_mapping(adapter, semgrep_output):
    """ERROR -> HIGH, WARNING -> MEDIUM, INFO -> INFO."""
    adapter._execute = AsyncMock(
        return_value=(json.dumps(semgrep_output), "", 0)
    )
    findings = await adapter.run("/tmp/target", timeout=60)
    severity_map = {f.rule_id: f.severity for f in findings}
    assert severity_map["python.lang.security.audit.exec-used"] == Severity.HIGH
    assert severity_map["python.lang.security.audit.eval-used"] == Severity.MEDIUM


@pytest.mark.asyncio
async def test_semgrep_path_normalization(adapter, semgrep_output):
    """File paths should have target prefix stripped."""
    adapter._execute = AsyncMock(
        return_value=(json.dumps(semgrep_output), "", 0)
    )
    findings = await adapter.run("/tmp/target", timeout=60)
    for f in findings:
        assert not f.file_path.startswith("/tmp/target")
        assert not f.file_path.startswith("/")


@pytest.mark.asyncio
async def test_semgrep_exit_code_1_is_not_error(adapter, semgrep_output):
    """Exit code 1 means findings found -- not an error."""
    adapter._execute = AsyncMock(
        return_value=(json.dumps(semgrep_output), "", 1)
    )
    findings = await adapter.run("/tmp/target", timeout=60)
    assert len(findings) == 3


@pytest.mark.asyncio
async def test_semgrep_exit_code_2_raises_error(adapter):
    """Exit code >= 2 is a real error."""
    adapter._execute = AsyncMock(return_value=("", "fatal error", 2))
    with pytest.raises(ScannerExecutionError):
        await adapter.run("/tmp/target", timeout=60)


@pytest.mark.asyncio
async def test_semgrep_fingerprint_populated(adapter, semgrep_output):
    """Each finding should have a 64-char hex fingerprint."""
    adapter._execute = AsyncMock(
        return_value=(json.dumps(semgrep_output), "", 0)
    )
    findings = await adapter.run("/tmp/target", timeout=60)
    for f in findings:
        assert len(f.fingerprint) == 64
        assert all(c in "0123456789abcdef" for c in f.fingerprint)
