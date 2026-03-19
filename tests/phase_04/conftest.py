"""Shared fixtures for phase 04 reports and quality gate tests."""

import json

import pytest

from scanner.schemas.compound_risk import CompoundRiskSchema
from scanner.schemas.finding import FindingSchema
from scanner.schemas.scan import ScanResultSchema
from scanner.schemas.severity import Severity
from datetime import datetime


@pytest.fixture
def sample_findings() -> list[FindingSchema]:
    """Five findings: 1 CRITICAL, 1 HIGH, 1 MEDIUM, 1 LOW, 1 INFO with realistic data."""
    return [
        FindingSchema(
            fingerprint="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
            tool="semgrep",
            rule_id="php.lang.security.injection.sql-injection",
            file_path="src/auth/login.py",
            line_start=42,
            line_end=45,
            snippet='cursor.execute(f"SELECT * FROM users WHERE email = \'{email}\'")',
            severity=Severity.CRITICAL,
            title="SQL injection in authentication",
            description="Raw SQL query with user-controlled input in login handler",
            recommendation="Use parameterized queries",
            ai_analysis="This SQL injection in the authentication handler allows attackers to bypass login by injecting SQL into the email parameter.",
            ai_fix_suggestion=json.dumps({
                "before": 'cursor.execute(f"SELECT * FROM users WHERE email = \'{email}\'")',
                "after": 'cursor.execute("SELECT * FROM users WHERE email = %s", (email,))',
                "explanation": "Use parameterized query to prevent SQL injection",
            }),
        ),
        FindingSchema(
            fingerprint="b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3",
            tool="semgrep",
            rule_id="python.django.security.csrf-exempt",
            file_path="src/auth/login.py",
            line_start=10,
            snippet="@csrf_exempt\ndef login_view(request):",
            severity=Severity.HIGH,
            title="CSRF protection disabled on login endpoint",
            description="Login endpoint has CSRF protection explicitly disabled",
            ai_analysis="Disabling CSRF on login enables session fixation attacks when combined with other vulnerabilities.",
            ai_fix_suggestion=json.dumps({
                "before": "@csrf_exempt\ndef login_view(request):",
                "after": "def login_view(request):",
                "explanation": "Remove csrf_exempt decorator to enable CSRF protection",
            }),
        ),
        FindingSchema(
            fingerprint="c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
            tool="trivy",
            rule_id="CVE-2024-1234",
            file_path="requirements.txt",
            line_start=5,
            snippet="flask==2.0.1",
            severity=Severity.MEDIUM,
            title="Outdated Flask with known vulnerability",
            description="Flask 2.0.1 has a known security vulnerability",
        ),
        FindingSchema(
            fingerprint="d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5",
            tool="checkov",
            rule_id="CKV_K8S_22",
            file_path="infra/deployment.yaml",
            line_start=15,
            snippet="readOnlyRootFilesystem: false",
            severity=Severity.LOW,
            title="Container filesystem not read-only",
            description="Container root filesystem should be read-only",
        ),
        FindingSchema(
            fingerprint="e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6",
            tool="gitleaks",
            rule_id="generic-api-key",
            file_path="config/settings.py",
            line_start=3,
            snippet="API_KEY = 'test-key-not-production'",
            severity=Severity.INFO,
            title="Potential API key in config",
            description="API key pattern detected but appears to be test data",
        ),
    ]


@pytest.fixture
def sample_scan_result() -> ScanResultSchema:
    """ScanResultSchema with counts matching sample_findings (1C, 1H, 1M, 1L, 1I)."""
    return ScanResultSchema(
        id=1,
        target_path="/tmp/test-repo",
        repo_url="https://github.com/example/repo.git",
        branch="release/v2.1",
        status="completed",
        started_at=datetime(2026, 3, 1, 10, 0, 0),
        completed_at=datetime(2026, 3, 1, 10, 0, 45),
        duration_seconds=45.2,
        total_findings=5,
        critical_count=1,
        high_count=1,
        medium_count=1,
        low_count=1,
        info_count=1,
        gate_passed=False,
        tool_versions={"semgrep": "1.56.0", "trivy": "0.50.0"},
    )


@pytest.fixture
def sample_compound_risks() -> list[CompoundRiskSchema]:
    """One HIGH compound risk linking two sample findings."""
    return [
        CompoundRiskSchema(
            title="Auth bypass via session fixation",
            description="SQL injection in login combined with disabled CSRF protection enables session fixation attacks allowing full account takeover",
            severity=4,  # HIGH
            risk_category="authentication",
            finding_fingerprints=[
                "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
                "b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3",
            ],
            recommendation="Fix SQL injection first, then re-enable CSRF protection",
        ),
    ]
