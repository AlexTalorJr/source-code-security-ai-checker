"""Tests for AI graceful degradation in the orchestrator wrapper."""

import pytest

from scanner.ai.schemas import AIAnalysisResult
from scanner.config import ScannerSettings
from scanner.core.orchestrator import enrich_with_ai
from scanner.schemas.compound_risk import CompoundRiskSchema
from scanner.schemas.finding import FindingSchema
from scanner.schemas.severity import Severity


def _make_settings(**overrides) -> ScannerSettings:
    """Create ScannerSettings with test defaults."""
    defaults = {
        "db_path": ":memory:",
        "claude_api_key": "",
    }
    defaults.update(overrides)
    return ScannerSettings(**defaults)


def _make_finding(fingerprint: str = "a" * 64) -> FindingSchema:
    return FindingSchema(
        fingerprint=fingerprint,
        tool="semgrep",
        rule_id="test-rule",
        file_path="src/app.py",
        line_start=1,
        severity=Severity.HIGH,
        title="Test finding",
    )


@pytest.mark.asyncio
async def test_no_api_key():
    """When claude_api_key is empty, AI is skipped with reason."""
    settings = _make_settings(claude_api_key="")
    findings = [_make_finding()]

    enriched, compound_risks, result = await enrich_with_ai(findings, settings)

    assert enriched is findings  # original list returned
    assert compound_risks == []
    assert result.skipped is True
    assert result.skip_reason == "Claude API key not configured"
    assert result.cost_usd == 0.0


@pytest.mark.asyncio
async def test_api_unavailable(monkeypatch):
    """When AIAnalyzer.analyze raises Exception, AI degrades gracefully."""
    settings = _make_settings(claude_api_key="sk-test-key")
    findings = [_make_finding()]

    async def mock_analyze(self, findings_arg):
        raise Exception("Connection refused")

    monkeypatch.setattr(
        "scanner.ai.analyzer.AIAnalyzer.analyze", mock_analyze
    )

    enriched, compound_risks, result = await enrich_with_ai(findings, settings)

    assert enriched is findings
    assert compound_risks == []
    assert result.skipped is True
    assert "AI analysis failed:" in result.skip_reason
    assert "Connection refused" in result.skip_reason


@pytest.mark.asyncio
async def test_api_error_degradation(monkeypatch):
    """When anthropic.APIError is raised, scan still completes."""
    settings = _make_settings(claude_api_key="sk-test-key")
    findings = [_make_finding()]

    async def mock_analyze(self, findings_arg):
        from anthropic import APIError

        raise APIError(
            message="Rate limit exceeded",
            request=None,
            body=None,
        )

    monkeypatch.setattr(
        "scanner.ai.analyzer.AIAnalyzer.analyze", mock_analyze
    )

    enriched, compound_risks, result = await enrich_with_ai(findings, settings)

    assert enriched is findings
    assert compound_risks == []
    assert result.skipped is True
    assert "AI analysis failed:" in result.skip_reason


@pytest.mark.asyncio
async def test_success_returns_enriched(monkeypatch):
    """On success, enrich_with_ai returns enriched findings and compound risks."""
    settings = _make_settings(claude_api_key="sk-test-key")
    original = _make_finding()
    enriched_finding = _make_finding()
    enriched_finding.ai_analysis = "This is a real risk"

    compound_risk = CompoundRiskSchema(
        title="Combined risk",
        description="Two findings together",
        severity=Severity.HIGH.value,
        finding_fingerprints=["a" * 64],
    )

    async def mock_analyze(self, findings_arg):
        self.analyzed_components = ["src"]
        self.skipped_components = []
        return [enriched_finding], [compound_risk], 0.0042

    monkeypatch.setattr(
        "scanner.ai.analyzer.AIAnalyzer.analyze", mock_analyze
    )

    result_findings, result_crs, result = await enrich_with_ai(
        [original], settings
    )

    assert result.skipped is False
    assert result.cost_usd == 0.0042
    assert result.analyzed_components == ["src"]
    assert result.skipped_components == []
    assert len(result_crs) == 1
    assert result_crs[0].title == "Combined risk"


@pytest.mark.asyncio
async def test_components_populated(monkeypatch):
    """enrich_with_ai populates analyzed and skipped components from analyzer."""
    settings = _make_settings(claude_api_key="sk-test-key")
    findings = [_make_finding()]

    async def mock_analyze(self, findings_arg):
        self.analyzed_components = ["vms", "infra"]
        self.skipped_components = ["mediaserver"]
        return findings_arg, [], 0.001

    monkeypatch.setattr(
        "scanner.ai.analyzer.AIAnalyzer.analyze", mock_analyze
    )

    _, _, result = await enrich_with_ai(findings, settings)

    assert result.analyzed_components == ["vms", "infra"]
    assert result.skipped_components == ["mediaserver"]


@pytest.mark.asyncio
async def test_skip_reason_recorded():
    """ai_skip_reason is properly set in result when key is missing."""
    settings = _make_settings(claude_api_key="")
    _, _, result = await enrich_with_ai([_make_finding()], settings)

    assert isinstance(result, AIAnalysisResult)
    assert result.skip_reason == "Claude API key not configured"
