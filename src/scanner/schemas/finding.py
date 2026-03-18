"""Finding schema for normalized security vulnerability data."""

from datetime import datetime

from pydantic import BaseModel

from scanner.schemas.severity import Severity


class FindingSchema(BaseModel):
    """Pydantic schema for a single security finding."""

    fingerprint: str  # SHA-256 hex, 64 chars
    tool: str  # semgrep, gitleaks, trivy, cppcheck, checkov
    rule_id: str
    file_path: str
    line_start: int | None = None
    line_end: int | None = None
    snippet: str | None = None
    severity: Severity
    title: str
    description: str | None = None
    recommendation: str | None = None
    ai_analysis: str | None = None
    ai_fix_suggestion: str | None = None
    false_positive: bool = False
    created_at: datetime | None = None
