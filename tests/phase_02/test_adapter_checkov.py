"""Tests for CheckovAdapter."""

import json
from unittest.mock import AsyncMock

import pytest

from scanner.adapters.checkov import CheckovAdapter, _get_severity
from scanner.schemas.severity import Severity


@pytest.fixture
def adapter():
    return CheckovAdapter()


@pytest.mark.asyncio
async def test_parse_checkov_failed_checks(adapter, checkov_output):
    """Only failed checks become findings (passed checks excluded)."""
    adapter._execute = AsyncMock(
        return_value=(json.dumps(checkov_output), "", 1)
    )
    findings = await adapter.run("/tmp/target", timeout=60)
    assert len(findings) == 2
    assert all(f.tool == "checkov" for f in findings)
    # Passed check CKV_DOCKER_1 should NOT appear
    rule_ids = {f.rule_id for f in findings}
    assert "CKV_DOCKER_1" not in rule_ids


@pytest.mark.asyncio
async def test_checkov_severity_by_prefix(adapter, checkov_output):
    """CKV_DOCKER -> MEDIUM, CKV2_K8S -> HIGH."""
    adapter._execute = AsyncMock(
        return_value=(json.dumps(checkov_output), "", 1)
    )
    findings = await adapter.run("/tmp/target", timeout=60)
    severity_map = {f.rule_id: f.severity for f in findings}
    assert severity_map["CKV_DOCKER_2"] == Severity.MEDIUM
    assert severity_map["CKV2_K8S_1"] == Severity.HIGH


@pytest.mark.asyncio
async def test_checkov_exit_code_1_is_not_error(adapter, checkov_output):
    """Exit code 1 means failed checks found -- not an error."""
    adapter._execute = AsyncMock(
        return_value=(json.dumps(checkov_output), "", 1)
    )
    # Should not raise
    findings = await adapter.run("/tmp/target", timeout=60)
    assert len(findings) == 2


@pytest.mark.asyncio
async def test_checkov_guideline_as_recommendation(adapter, checkov_output):
    """Recommendation field should contain guideline URL."""
    adapter._execute = AsyncMock(
        return_value=(json.dumps(checkov_output), "", 1)
    )
    findings = await adapter.run("/tmp/target", timeout=60)
    for f in findings:
        assert f.recommendation is not None
        assert "docs.bridgecrew.io" in f.recommendation


@pytest.mark.asyncio
async def test_checkov_single_dict_output(adapter):
    """Checkov can return a single dict (not list) -- should still parse."""
    single_dict = {
        "check_type": "dockerfile",
        "results": {
            "passed_checks": [],
            "failed_checks": [
                {
                    "check_id": "CKV_DOCKER_3",
                    "check_name": "Ensure no ADD",
                    "check_result": {"result": "FAILED"},
                    "file_path": "/Dockerfile",
                    "file_line_range": [5, 5],
                    "resource": "Dockerfile.",
                    "guideline": "https://docs.bridgecrew.io/docs/no-add",
                }
            ],
            "skipped_checks": [],
        },
    }
    adapter._execute = AsyncMock(
        return_value=(json.dumps(single_dict), "", 1)
    )
    findings = await adapter.run("/tmp/target", timeout=60)
    assert len(findings) == 1
    assert findings[0].rule_id == "CKV_DOCKER_3"


def test_get_severity_function():
    """Unit test the _get_severity helper directly."""
    assert _get_severity("CKV2_K8S_1") == Severity.HIGH
    assert _get_severity("CKV2_DOCKER_5") == Severity.HIGH
    assert _get_severity("CKV_DOCKER_2") == Severity.MEDIUM
    assert _get_severity("CKV_K8S_10") == Severity.MEDIUM
    assert _get_severity("CKV_HELM_1") == Severity.MEDIUM
    # Unknown prefix defaults to MEDIUM
    assert _get_severity("CKV_UNKNOWN_1") == Severity.MEDIUM
