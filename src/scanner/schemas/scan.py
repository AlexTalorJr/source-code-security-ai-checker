"""Scan result schema for tracking scan execution and results."""

from datetime import datetime

from pydantic import BaseModel


class ScanResultSchema(BaseModel):
    """Pydantic schema for a scan result."""

    id: int | None = None
    target_path: str | None = None
    repo_url: str | None = None
    target_url: str | None = None
    branch: str | None = None
    commit_hash: str | None = None
    status: str = "pending"  # pending/running/completed/failed
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
    scanner_version: str | None = None
    tool_versions: dict | None = None
    error_message: str | None = None
    ai_cost_usd: float | None = None
    ai_skipped: bool = False
    ai_skip_reason: str | None = None
    created_at: datetime | None = None
