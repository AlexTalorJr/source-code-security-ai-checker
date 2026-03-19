"""Tests for CppcheckAdapter."""

from unittest.mock import AsyncMock, patch

import pytest

from scanner.adapters.cppcheck import CppcheckAdapter
from scanner.schemas.severity import Severity


@pytest.fixture
def adapter():
    return CppcheckAdapter()


@pytest.mark.asyncio
async def test_parse_cppcheck_findings(adapter, cppcheck_output):
    """Parse fixture XML (from stderr) and return 2 findings."""
    adapter._execute = AsyncMock(return_value=("", cppcheck_output, 0))
    with patch.object(CppcheckAdapter, "_has_cpp_files", return_value=True):
        findings = await adapter.run("/tmp/target", timeout=60)
    assert len(findings) == 2
    assert all(f.tool == "cppcheck" for f in findings)


@pytest.mark.asyncio
async def test_cppcheck_severity_mapping(adapter, cppcheck_output):
    """error -> HIGH, warning -> MEDIUM."""
    adapter._execute = AsyncMock(return_value=("", cppcheck_output, 0))
    with patch.object(CppcheckAdapter, "_has_cpp_files", return_value=True):
        findings = await adapter.run("/tmp/target", timeout=60)
    severity_map = {f.rule_id: f.severity for f in findings}
    assert severity_map["bufferAccessOutOfBounds"] == Severity.HIGH
    assert severity_map["uninitvar"] == Severity.MEDIUM


@pytest.mark.asyncio
async def test_cppcheck_skips_no_cpp_files(adapter, tmp_path):
    """When no C/C++ files exist, return empty list without calling _execute."""
    spy = AsyncMock()
    adapter._execute = spy
    findings = await adapter.run(str(tmp_path), timeout=60)
    assert findings == []
    spy.assert_not_called()


@pytest.mark.asyncio
async def test_cppcheck_reads_stderr_not_stdout(adapter, cppcheck_output):
    """XML parsing must come from stderr (second tuple element)."""
    # Pass XML in stderr, empty stdout -- should work.
    adapter._execute = AsyncMock(return_value=("", cppcheck_output, 0))
    with patch.object(CppcheckAdapter, "_has_cpp_files", return_value=True):
        findings = await adapter.run("/tmp/target", timeout=60)
    assert len(findings) == 2

    # Pass XML in stdout, empty stderr -- should fail (no XML to parse).
    adapter._execute = AsyncMock(return_value=(cppcheck_output, "", 0))
    with patch.object(CppcheckAdapter, "_has_cpp_files", return_value=True):
        with pytest.raises(Exception):
            await adapter.run("/tmp/target", timeout=60)
