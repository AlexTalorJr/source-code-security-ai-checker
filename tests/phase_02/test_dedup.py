"""Tests for finding deduplication logic."""

from scanner.core.orchestrator import deduplicate_findings
from scanner.schemas.finding import FindingSchema
from scanner.schemas.severity import Severity


def _make_finding(
    fingerprint: str = "abc123",
    severity: Severity = Severity.MEDIUM,
    tool: str = "semgrep",
) -> FindingSchema:
    """Create a minimal FindingSchema for testing."""
    return FindingSchema(
        fingerprint=fingerprint,
        tool=tool,
        rule_id="test-rule",
        file_path="src/app.py",
        severity=severity,
        title="Test finding",
    )


def test_dedup_removes_duplicates():
    """Two findings with same fingerprint, different tools -> returns 1."""
    findings = [
        _make_finding(fingerprint="fp1", tool="semgrep"),
        _make_finding(fingerprint="fp1", tool="trivy"),
    ]
    result = deduplicate_findings(findings)
    assert len(result) == 1


def test_dedup_keeps_highest_severity():
    """Finding with higher severity wins when fingerprints match."""
    findings = [
        _make_finding(fingerprint="fp1", severity=Severity.MEDIUM, tool="semgrep"),
        _make_finding(fingerprint="fp1", severity=Severity.HIGH, tool="trivy"),
    ]
    result = deduplicate_findings(findings)
    assert len(result) == 1
    assert result[0].severity == Severity.HIGH


def test_dedup_preserves_unique():
    """Three findings with different fingerprints all survive."""
    findings = [
        _make_finding(fingerprint="fp1"),
        _make_finding(fingerprint="fp2"),
        _make_finding(fingerprint="fp3"),
    ]
    result = deduplicate_findings(findings)
    assert len(result) == 3


def test_dedup_empty_list():
    """Empty input returns empty list."""
    assert deduplicate_findings([]) == []


def test_dedup_preserves_order():
    """First-seen order is preserved in output."""
    findings = [
        _make_finding(fingerprint="A"),
        _make_finding(fingerprint="B"),
        _make_finding(fingerprint="C"),
    ]
    result = deduplicate_findings(findings)
    assert [f.fingerprint for f in result] == ["A", "B", "C"]
