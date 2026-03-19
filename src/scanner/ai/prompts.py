"""System prompt templates and tool definitions for AI analysis."""

import json

from scanner.schemas.finding import FindingSchema


AIPIX_SECURITY_CONCERNS = (
    "1. Unauthorized RTSP stream access (camera feed theft)\n"
    "2. API token exposure and hardcoded secrets\n"
    "3. Broken authorization in VMS multi-tenant user portal\n"
    "4. Webhook endpoint validation (no signature verification)\n"
    "5. Kubernetes misconfigurations (exposed services, weak RBAC)\n"
    "6. C++ Mediaserver memory safety (buffer overflows, format strings)\n"
    "7. Insecure direct object references on video archive endpoints"
)

COMPONENT_FRAMEWORK_MAP: dict[str, str] = {
    "vms": (
        "Laravel PHP framework. Watch for: Eloquent mass assignment, "
        "raw SQL in query scopes, missing CSRF on API routes, "
        "insecure session config."
    ),
    "mediaserver": (
        "C++ with STL. Watch for: buffer overflows, format string "
        "vulnerabilities, use-after-free, unchecked pointer dereferences, "
        "unsafe string functions (strcpy, sprintf)."
    ),
    "infra": (
        "Kubernetes + Helm + Docker Compose. Watch for: privileged "
        "containers, host network access, missing network policies, "
        "secrets in plaintext, weak RBAC."
    ),
    "client": (
        "C# Windows desktop. Watch for: insecure deserialization, "
        "hardcoded credentials, DLL injection paths."
    ),
    "mobile": (
        "Flutter/Dart. Watch for: insecure local storage, certificate "
        "pinning bypass, hardcoded API keys."
    ),
}


def build_system_prompt(component: str) -> str:
    """Build system prompt with aipix security concerns and framework context.

    Args:
        component: Component name (e.g., "vms", "mediaserver", "infra").

    Returns:
        System prompt string with domain context.
    """
    framework_context = None
    for prefix, context in COMPONENT_FRAMEWORK_MAP.items():
        if component.startswith(prefix):
            framework_context = context
            break

    lines = [
        "You are a security analysis expert reviewing findings from automated "
        "security scanners for the aipix video surveillance platform.",
        "",
        "## Known Security Concerns",
        "",
        AIPIX_SECURITY_CONCERNS,
        "",
    ]

    if framework_context:
        lines.extend([
            f"## Component: {component}",
            "",
            f"Framework context: {framework_context}",
            "",
        ])
    else:
        lines.extend([
            f"## Component: {component}",
            "",
            "Review for common security vulnerabilities including injection, "
            "authentication bypass, authorization flaws, and data exposure.",
            "",
        ])

    lines.extend([
        "## Instructions",
        "",
        "Analyze each finding for business logic risk specific to this platform. "
        "Categorize the risk and provide a structured fix suggestion where possible. "
        "If no concrete code fix is possible (architectural/config issues), set "
        "fix_suggestion to null and provide a textual recommendation instead.",
        "",
        "Return your analysis using the security_analysis tool.",
    ])

    return "\n".join(lines)


def build_component_prompt(component: str, findings: list[FindingSchema]) -> str:
    """Build user prompt with serialized findings for component analysis.

    Args:
        component: Component name.
        findings: List of findings to analyze.

    Returns:
        User prompt with JSON-serialized findings.
    """
    serialized = []
    for f in findings:
        serialized.append({
            "fingerprint": f.fingerprint,
            "file_path": f.file_path,
            "line_start": f.line_start,
            "snippet": f.snippet,
            "severity": f.severity.name,
            "title": f.title,
            "rule_id": f.rule_id,
        })

    findings_json = json.dumps(serialized, indent=2)

    return (
        f"Analyze these {len(findings)} security findings from the "
        f"'{component}' component.\n\n"
        f"Findings:\n```json\n{findings_json}\n```\n\n"
        "For each finding, assess the business logic risk in the context of "
        "a video surveillance platform, categorize it, and provide a fix "
        "suggestion if possible."
    )


def build_correlation_prompt(component_summaries: dict[str, list[dict]]) -> str:
    """Build prompt for cross-component correlation analysis.

    Args:
        component_summaries: Dict of component name -> list of finding analysis dicts.

    Returns:
        Prompt asking Claude to identify compound risks across components.
    """
    summaries_json = json.dumps(component_summaries, indent=2)

    return (
        "Review the following per-component security analysis results and "
        "identify compound risks that span multiple components or findings.\n\n"
        "A compound risk is a security threat that becomes more severe when "
        "multiple individual findings are considered together (e.g., SQL injection "
        "in auth + mass assignment = full account takeover).\n\n"
        f"Component analysis summaries:\n```json\n{summaries_json}\n```\n\n"
        "Identify any compound risks and return them using the "
        "cross_component_correlation tool."
    )


ANALYSIS_TOOL: dict = {
    "name": "security_analysis",
    "description": (
        "Return structured security analysis for each finding, including "
        "business logic risk assessment, risk categorization, and fix suggestions."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "findings_analysis": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "fingerprint": {"type": "string"},
                        "business_logic_risk": {"type": "string"},
                        "risk_category": {
                            "type": "string",
                            "enum": [
                                "auth_bypass",
                                "tenant_isolation",
                                "idor",
                                "memory_safety",
                                "secret_exposure",
                                "k8s_misconfig",
                                "webhook_validation",
                                "other",
                            ],
                        },
                        "fix_suggestion": {
                            "type": ["object", "null"],
                            "properties": {
                                "before": {"type": "string"},
                                "after": {"type": "string"},
                                "explanation": {"type": "string"},
                            },
                        },
                        "recommendation": {"type": ["string", "null"]},
                    },
                    "required": [
                        "fingerprint",
                        "business_logic_risk",
                        "risk_category",
                    ],
                },
            },
        },
        "required": ["findings_analysis"],
    },
}

CORRELATION_TOOL: dict = {
    "name": "cross_component_correlation",
    "description": (
        "Return compound risks identified across multiple components or "
        "findings that create elevated security threats when combined."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "compound_risks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "severity": {"type": "string"},
                        "risk_category": {"type": "string"},
                        "finding_fingerprints": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "recommendation": {"type": ["string", "null"]},
                    },
                    "required": [
                        "title",
                        "description",
                        "severity",
                        "risk_category",
                        "finding_fingerprints",
                    ],
                },
            },
        },
        "required": ["compound_risks"],
    },
}
