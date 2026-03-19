"""Tests for AI response schemas."""

import pytest
from pydantic import ValidationError

from scanner.ai.schemas import (
    AIAnalysisResult,
    ComponentAnalysisResponse,
    CorrelationResponse,
    FindingAnalysis,
    FixSuggestion,
)


class TestFindingAnalysis:
    def test_validates_with_all_fields(self):
        fa = FindingAnalysis(
            fingerprint="a" * 64,
            business_logic_risk="SQL injection enables auth bypass",
            risk_category="auth_bypass",
            fix_suggestion=FixSuggestion(
                before="raw sql",
                after="parameterized",
                explanation="Use query builder",
            ),
        )
        assert fa.fingerprint == "a" * 64
        assert fa.risk_category == "auth_bypass"
        assert fa.fix_suggestion is not None

    def test_risk_category_enum_values(self):
        valid_categories = [
            "auth_bypass",
            "tenant_isolation",
            "idor",
            "memory_safety",
            "secret_exposure",
            "k8s_misconfig",
            "webhook_validation",
            "other",
        ]
        for cat in valid_categories:
            fa = FindingAnalysis(
                fingerprint="x" * 64,
                business_logic_risk="test",
                risk_category=cat,
            )
            assert fa.risk_category == cat

    def test_invalid_risk_category_rejected(self):
        with pytest.raises(ValidationError):
            FindingAnalysis(
                fingerprint="x" * 64,
                business_logic_risk="test",
                risk_category="invalid_category",
            )

    def test_fix_suggestion_nullable(self):
        fa = FindingAnalysis(
            fingerprint="x" * 64,
            business_logic_risk="test",
            risk_category="other",
            fix_suggestion=None,
        )
        assert fa.fix_suggestion is None

    def test_null_fix_with_recommendation(self):
        fa = FindingAnalysis(
            fingerprint="x" * 64,
            business_logic_risk="test",
            risk_category="other",
            fix_suggestion=None,
            recommendation="Investigate configuration",
        )
        assert fa.fix_suggestion is None
        assert fa.recommendation == "Investigate configuration"


class TestComponentAnalysisResponse:
    def test_has_findings_analysis_list(self):
        resp = ComponentAnalysisResponse(
            findings_analysis=[
                FindingAnalysis(
                    fingerprint="a" * 64,
                    business_logic_risk="test",
                    risk_category="other",
                ),
            ]
        )
        assert len(resp.findings_analysis) == 1

    def test_from_mock_response(self, mock_analysis_response):
        resp = ComponentAnalysisResponse(**mock_analysis_response)
        assert len(resp.findings_analysis) == 2
        assert resp.findings_analysis[0].risk_category == "auth_bypass"


class TestCorrelationResponse:
    def test_has_compound_risks_list(self):
        resp = CorrelationResponse(
            compound_risks=[
                {
                    "title": "Test compound risk",
                    "description": "Description",
                    "severity": "HIGH",
                    "risk_category": "auth_bypass",
                    "finding_fingerprints": ["a" * 64],
                    "recommendation": "Fix it",
                }
            ]
        )
        assert len(resp.compound_risks) == 1
        assert resp.compound_risks[0].title == "Test compound risk"

    def test_from_mock_response(self, mock_correlation_response):
        resp = CorrelationResponse(**mock_correlation_response)
        assert len(resp.compound_risks) == 1
        assert resp.compound_risks[0].severity == "CRITICAL"
        assert len(resp.compound_risks[0].finding_fingerprints) == 2


class TestAIAnalysisResult:
    def test_defaults(self):
        result = AIAnalysisResult()
        assert result.skipped is False
        assert result.skip_reason is None
        assert result.cost_usd == 0.0
        assert result.analyzed_components == []
        assert result.skipped_components == []

    def test_skipped_result(self):
        result = AIAnalysisResult(
            skipped=True,
            skip_reason="API key not configured",
            cost_usd=0.0,
            analyzed_components=[],
            skipped_components=["vms", "mediaserver"],
        )
        assert result.skipped is True
        assert result.skip_reason == "API key not configured"
        assert len(result.skipped_components) == 2
