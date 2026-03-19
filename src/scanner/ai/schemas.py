"""Pydantic models for AI analysis response validation."""

from typing import Literal

from pydantic import BaseModel


class FixSuggestion(BaseModel):
    """Structured code fix with before/after and explanation."""

    before: str
    after: str
    explanation: str


class FindingAnalysis(BaseModel):
    """AI analysis of a single security finding."""

    fingerprint: str
    business_logic_risk: str
    risk_category: Literal[
        "auth_bypass",
        "tenant_isolation",
        "idor",
        "memory_safety",
        "secret_exposure",
        "k8s_misconfig",
        "webhook_validation",
        "other",
    ]
    fix_suggestion: FixSuggestion | None = None
    recommendation: str | None = None


class ComponentAnalysisResponse(BaseModel):
    """Response schema for per-component analysis."""

    findings_analysis: list[FindingAnalysis]


class CompoundRisk(BaseModel):
    """A compound risk identified across multiple findings."""

    title: str
    description: str
    severity: str
    risk_category: str
    finding_fingerprints: list[str]
    recommendation: str | None = None


class CorrelationResponse(BaseModel):
    """Response schema for cross-component correlation."""

    compound_risks: list[CompoundRisk]


class AIAnalysisResult(BaseModel):
    """Overall result of AI analysis for a scan."""

    skipped: bool = False
    skip_reason: str | None = None
    cost_usd: float = 0.0
    analyzed_components: list[str] = []
    skipped_components: list[str] = []
