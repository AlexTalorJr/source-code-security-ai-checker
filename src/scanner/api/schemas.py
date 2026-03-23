"""API request and response schemas for the security scanner REST API."""

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, model_validator

T = TypeVar("T")


class ScanRequest(BaseModel):
    """Request body for triggering a new scan."""

    path: str | None = None
    repo_url: str | None = None
    branch: str | None = None
    target_url: str | None = None  # DAST target URL
    skip_ai: bool = False

    @model_validator(mode="after")
    def validate_target(self) -> "ScanRequest":
        if self.target_url:
            # DAST mode -- path and repo_url must be absent
            if self.path or self.repo_url:
                raise ValueError(
                    'target_url cannot be combined with "path" or "repo_url".'
                )
            return self
        # Existing SAST validation
        if self.path and self.repo_url:
            raise ValueError('Provide either "path" or "repo_url", not both.')
        if not self.path and not self.repo_url:
            raise ValueError(
                'Provide "path", "repo_url", or "target_url".'
            )
        return self


class ScanResponse(BaseModel):
    """Response after triggering a scan."""

    id: int
    status: str


class ScanDetailResponse(BaseModel):
    """Detailed scan information."""

    id: int
    status: str
    target_path: str | None = None
    repo_url: str | None = None
    branch: str | None = None
    target_url: str | None = None
    commit_hash: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_seconds: float | None = None
    total_findings: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0
    gate_passed: bool | None = None
    error_message: str | None = None
    ai_cost_usd: float | None = None


class FindingResponse(BaseModel):
    """Single finding in API responses."""

    fingerprint: str
    tool: str
    rule_id: str
    file_path: str
    line_start: int | None = None
    line_end: int | None = None
    snippet: str | None = None
    severity: str  # String name (CRITICAL, HIGH, etc.), not int
    title: str
    description: str | None = None
    recommendation: str | None = None
    ai_analysis: str | None = None
    ai_fix_suggestion: str | None = None
    suppressed: bool = False


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int


class SuppressionRequest(BaseModel):
    """Request body for suppressing a finding."""

    reason: str | None = None
