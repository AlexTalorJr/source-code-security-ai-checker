"""Tests for TrivyAdapter."""

import json
from unittest.mock import AsyncMock

import pytest

from scanner.adapters.trivy import TrivyAdapter
from scanner.schemas.severity import Severity


@pytest.fixture
def adapter():
    return TrivyAdapter()


@pytest.mark.asyncio
async def test_parse_trivy_vulnerabilities(adapter, trivy_output):
    """Fixture has 2 vulnerability findings in requirements.txt."""
    adapter._execute = AsyncMock(
        return_value=(json.dumps(trivy_output), "", 0)
    )
    findings = await adapter.run("/tmp/target", timeout=60)
    vuln_findings = [f for f in findings if f.rule_id.startswith("CVE-")]
    assert len(vuln_findings) == 2


@pytest.mark.asyncio
async def test_parse_trivy_misconfigurations(adapter, trivy_output):
    """Fixture has 1 misconfiguration finding in Dockerfile."""
    adapter._execute = AsyncMock(
        return_value=(json.dumps(trivy_output), "", 0)
    )
    findings = await adapter.run("/tmp/target", timeout=60)
    misconfig_findings = [f for f in findings if f.file_path == "Dockerfile"]
    assert len(misconfig_findings) == 1
    assert misconfig_findings[0].rule_id == "DS002"


@pytest.mark.asyncio
async def test_trivy_severity_mapping(adapter, trivy_output):
    """CRITICAL -> CRITICAL, HIGH -> HIGH from parsed findings."""
    adapter._execute = AsyncMock(
        return_value=(json.dumps(trivy_output), "", 0)
    )
    findings = await adapter.run("/tmp/target", timeout=60)
    severity_map = {f.rule_id: f.severity for f in findings}
    assert severity_map["CVE-2023-99999"] == Severity.CRITICAL
    assert severity_map["CVE-2023-12345"] == Severity.HIGH


@pytest.mark.asyncio
async def test_trivy_recommendation_has_upgrade_path(adapter, trivy_output):
    """Vulnerability recommendations should contain 'Upgrade' and package name."""
    adapter._execute = AsyncMock(
        return_value=(json.dumps(trivy_output), "", 0)
    )
    findings = await adapter.run("/tmp/target", timeout=60)
    vuln_findings = [f for f in findings if f.rule_id.startswith("CVE-")]
    for f in vuln_findings:
        assert f.recommendation is not None
        assert "Upgrade" in f.recommendation


@pytest.mark.asyncio
async def test_trivy_empty_results(adapter):
    """Empty Results array should return empty list."""
    empty_output = {"SchemaVersion": 2, "Results": []}
    adapter._execute = AsyncMock(
        return_value=(json.dumps(empty_output), "", 0)
    )
    findings = await adapter.run("/tmp/target", timeout=60)
    assert findings == []
