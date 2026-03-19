"""Shared fixtures for phase 03 AI analysis tests."""

import pytest

from scanner.schemas.finding import FindingSchema
from scanner.schemas.severity import Severity


@pytest.fixture
def sample_findings() -> list[FindingSchema]:
    """Five findings spanning different components and severities."""
    return [
        FindingSchema(
            fingerprint="a" * 64,
            tool="semgrep",
            rule_id="php.lang.security.injection.sql-injection",
            file_path="vms/app/Http/Controllers/AuthController.php",
            line_start=42,
            snippet='$user = DB::select("SELECT * FROM users WHERE email = \'$email\'");',
            severity=Severity.CRITICAL,
            title="SQL injection in authentication",
            description="Raw SQL query with user-controlled input",
        ),
        FindingSchema(
            fingerprint="b" * 64,
            tool="semgrep",
            rule_id="php.laravel.security.mass-assignment",
            file_path="vms/app/Models/Camera.php",
            line_start=15,
            snippet="protected $guarded = [];",
            severity=Severity.HIGH,
            title="Mass assignment vulnerability",
            description="Empty guarded array allows mass assignment",
        ),
        FindingSchema(
            fingerprint="c" * 64,
            tool="cppcheck",
            rule_id="bufferAccessOutOfBounds",
            file_path="mediaserver/src/rtsp/stream_handler.cpp",
            line_start=128,
            snippet="memcpy(buffer, data, len);",
            severity=Severity.CRITICAL,
            title="Buffer overflow in RTSP handler",
            description="Unchecked memcpy may overflow buffer",
        ),
        FindingSchema(
            fingerprint="d" * 64,
            tool="checkov",
            rule_id="CKV_K8S_8",
            file_path="infra/helm/templates/deployment.yaml",
            line_start=22,
            snippet="privileged: true",
            severity=Severity.HIGH,
            title="Privileged container",
            description="Container running with privileged flag",
        ),
        FindingSchema(
            fingerprint="e" * 64,
            tool="gitleaks",
            rule_id="generic-api-key",
            file_path="vms/config/services.php",
            line_start=8,
            snippet="'api_key' => 'sk-live-abc123def456'",
            severity=Severity.MEDIUM,
            title="Hardcoded API key",
            description="API key found in configuration file",
        ),
    ]


@pytest.fixture
def mock_analysis_response() -> dict:
    """Dict mimicking Claude tool_use response with findings_analysis."""
    return {
        "findings_analysis": [
            {
                "fingerprint": "a" * 64,
                "business_logic_risk": "Authentication bypass via SQL injection allows unauthorized access to any tenant account",
                "risk_category": "auth_bypass",
                "fix_suggestion": {
                    "before": '$user = DB::select("SELECT * FROM users WHERE email = \'$email\'");',
                    "after": "$user = User::where('email', $email)->first();",
                    "explanation": "Use Eloquent query builder with parameterized binding instead of raw SQL",
                },
                "recommendation": None,
            },
            {
                "fingerprint": "b" * 64,
                "business_logic_risk": "Mass assignment could allow privilege escalation by setting is_admin field",
                "risk_category": "idor",
                "fix_suggestion": None,
                "recommendation": "Define explicit $fillable array with only user-editable fields",
            },
        ]
    }


@pytest.fixture
def mock_correlation_response() -> dict:
    """Dict mimicking correlation tool_use response with compound_risks."""
    return {
        "compound_risks": [
            {
                "title": "Authentication bypass + privilege escalation chain",
                "description": "SQL injection in auth combined with mass assignment creates full admin takeover path",
                "severity": "CRITICAL",
                "risk_category": "auth_bypass",
                "finding_fingerprints": ["a" * 64, "b" * 64],
                "recommendation": "Fix SQL injection first, then lock down mass assignment",
            }
        ]
    }
