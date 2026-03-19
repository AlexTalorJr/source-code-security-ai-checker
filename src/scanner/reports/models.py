"""Data contracts for report generation."""

from dataclasses import dataclass, field

from scanner.schemas.compound_risk import CompoundRiskSchema
from scanner.schemas.finding import FindingSchema
from scanner.schemas.scan import ScanResultSchema


@dataclass
class DeltaResult:
    """Result of comparing current scan findings against a previous scan."""

    new_fingerprints: set[str]
    fixed_fingerprints: set[str]
    persisting_fingerprints: set[str]
    previous_scan_id: int | None = None


@dataclass
class ReportData:
    """All data needed to render a scan report."""

    scan_result: ScanResultSchema
    findings: list[FindingSchema]
    compound_risks: list[CompoundRiskSchema]
    delta: DeltaResult | None = None
    gate_passed: bool = True
    fail_reasons: list[str] = field(default_factory=list)
