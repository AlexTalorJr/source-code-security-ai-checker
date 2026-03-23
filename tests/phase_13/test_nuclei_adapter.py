"""Unit tests for NucleiAdapter -- Nuclei DAST scanner adapter."""

import pytest

from scanner.adapters.nuclei import NucleiAdapter, NUCLEI_SEVERITY_MAP
from scanner.core.exceptions import ScannerExecutionError
from scanner.core.fingerprint import compute_fingerprint
from scanner.schemas.severity import Severity


@pytest.mark.asyncio
async def test_parse_single_finding(nuclei_jsonl_fixture_path, mock_execute):
    """Single JSONL event is parsed into one FindingSchema with correct fields."""
    first_line = nuclei_jsonl_fixture_path.read_text().splitlines()[0]
    mock, patcher = mock_execute(first_line, "", 0)
    try:
        adapter = NucleiAdapter()
        results = await adapter.run("http://example.com", timeout=60)

        assert len(results) == 1
        f = results[0]
        assert f.tool == "nuclei"
        assert f.rule_id == "nginx-version"
        assert f.file_path == "http://example.com/"
        assert f.severity == Severity.INFO
        assert f.title == "nginx version detect"
        assert f.snippet == "nginx/1.19.0"
    finally:
        patcher.stop()


@pytest.mark.asyncio
async def test_parse_multiple_findings(nuclei_jsonl_fixture_path, mock_execute):
    """Three JSONL events produce three FindingSchema objects."""
    content = nuclei_jsonl_fixture_path.read_text()
    mock, patcher = mock_execute(content, "", 0)
    try:
        adapter = NucleiAdapter()
        results = await adapter.run("http://example.com", timeout=60)

        assert len(results) == 3
        severities = {r.severity for r in results}
        assert Severity.INFO in severities
        assert Severity.CRITICAL in severities
        assert Severity.MEDIUM in severities
    finally:
        patcher.stop()


@pytest.mark.asyncio
async def test_severity_mapping():
    """Each Nuclei severity string maps to the correct Severity enum value."""
    expected = {
        "critical": Severity.CRITICAL,
        "high": Severity.HIGH,
        "medium": Severity.MEDIUM,
        "low": Severity.LOW,
        "info": Severity.INFO,
    }
    for sev_str, sev_enum in expected.items():
        assert NUCLEI_SEVERITY_MAP[sev_str] == sev_enum


@pytest.mark.asyncio
async def test_unknown_severity_defaults_to_info(mock_execute):
    """Unknown or missing severity string defaults to Severity.INFO."""
    import json

    event = {
        "template-id": "test-unknown",
        "info": {"name": "Test", "severity": "unknown"},
        "matched-at": "http://example.com/",
        "extracted-results": ["data"],
    }
    mock, patcher = mock_execute(json.dumps(event), "", 0)
    try:
        adapter = NucleiAdapter()
        results = await adapter.run("http://example.com", timeout=60)
        assert results[0].severity == Severity.INFO
    finally:
        patcher.stop()


@pytest.mark.asyncio
async def test_fingerprint(mock_execute):
    """Fingerprint matches compute_fingerprint(matched_at, template_id, snippet)."""
    import json

    event = {
        "template-id": "nginx-version",
        "info": {"name": "Test", "severity": "info"},
        "matched-at": "http://example.com/",
        "extracted-results": ["nginx/1.19.0"],
    }
    mock, patcher = mock_execute(json.dumps(event), "", 0)
    try:
        adapter = NucleiAdapter()
        results = await adapter.run("http://example.com", timeout=60)
        expected_fp = compute_fingerprint(
            "http://example.com/", "nginx-version", "nginx/1.19.0"
        )
        assert results[0].fingerprint == expected_fp
    finally:
        patcher.stop()


@pytest.mark.asyncio
async def test_empty_output(mock_execute):
    """Empty stdout returns an empty list without error."""
    mock, patcher = mock_execute("", "", 0)
    try:
        adapter = NucleiAdapter()
        results = await adapter.run("http://example.com", timeout=60)
        assert results == []
    finally:
        patcher.stop()


@pytest.mark.asyncio
async def test_execution_error(mock_execute):
    """Non-zero exit code raises ScannerExecutionError."""
    mock, patcher = mock_execute("", "fatal error", 1)
    try:
        adapter = NucleiAdapter()
        with pytest.raises(ScannerExecutionError):
            await adapter.run("http://example.com", timeout=60)
    finally:
        patcher.stop()


@pytest.mark.asyncio
async def test_extra_args_passed(mock_execute):
    """Extra args are included in the command list passed to _execute."""
    mock, patcher = mock_execute("", "", 0)
    try:
        adapter = NucleiAdapter()
        await adapter.run(
            "http://example.com", timeout=60, extra_args=["-tags", "cve"]
        )
        called_cmd = mock.call_args[0][0]
        assert "-tags" in called_cmd
        assert "cve" in called_cmd
    finally:
        patcher.stop()


@pytest.mark.asyncio
async def test_missing_extracted_results(mock_execute):
    """When extracted-results is empty but matched-line exists, snippet uses matched-line."""
    import json

    event = {
        "template-id": "open-redirect",
        "info": {"name": "Open Redirect", "severity": "medium"},
        "matched-at": "http://example.com/redirect",
        "extracted-results": [],
        "matched-line": "Location: http://evil.com",
    }
    mock, patcher = mock_execute(json.dumps(event), "", 0)
    try:
        adapter = NucleiAdapter()
        results = await adapter.run("http://example.com", timeout=60)
        assert results[0].snippet == "Location: http://evil.com"
    finally:
        patcher.stop()


def test_tool_name():
    """adapter.tool_name returns 'nuclei'."""
    adapter = NucleiAdapter()
    assert adapter.tool_name == "nuclei"
