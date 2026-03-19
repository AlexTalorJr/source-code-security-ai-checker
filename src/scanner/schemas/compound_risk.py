"""Pydantic schema for compound risk data."""

from pydantic import BaseModel


class CompoundRiskSchema(BaseModel):
    """Schema for compound risk entries from AI cross-component correlation."""

    id: int | None = None
    scan_id: int | None = None
    title: str
    description: str
    severity: int  # Severity IntEnum value
    risk_category: str | None = None
    finding_fingerprints: list[str] = []
    recommendation: str | None = None
