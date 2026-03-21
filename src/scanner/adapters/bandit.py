"""Bandit scanner adapter -- parses JSON output into FindingSchema."""

import json

from scanner.adapters.base import ScannerAdapter
from scanner.core.exceptions import ScannerExecutionError
from scanner.core.fingerprint import compute_fingerprint
from scanner.schemas.finding import FindingSchema
from scanner.schemas.severity import Severity

# Confidence x severity matrix per CONTEXT.md decision
BANDIT_SEVERITY_MATRIX: dict[tuple[str, str], Severity] = {
    ("HIGH", "HIGH"): Severity.CRITICAL,
    ("HIGH", "MEDIUM"): Severity.HIGH,
    ("HIGH", "LOW"): Severity.MEDIUM,
    ("MEDIUM", "HIGH"): Severity.MEDIUM,
    ("MEDIUM", "MEDIUM"): Severity.MEDIUM,
    ("MEDIUM", "LOW"): Severity.LOW,
    ("LOW", "HIGH"): Severity.LOW,
    ("LOW", "MEDIUM"): Severity.LOW,
    ("LOW", "LOW"): Severity.INFO,
}


def _bandit_severity(issue_severity: str, issue_confidence: str) -> Severity:
    """Map Bandit severity using confidence x severity matrix."""
    key = (issue_severity.upper(), issue_confidence.upper())
    return BANDIT_SEVERITY_MATRIX.get(key, Severity.INFO)


class BanditAdapter(ScannerAdapter):
    """Adapter for Bandit Python security analysis tool."""

    @property
    def tool_name(self) -> str:
        return "bandit"

    def _version_command(self) -> list[str]:
        return ["bandit", "--version"]

    async def run(
        self,
        target_path: str,
        timeout: int,
        extra_args: list[str] | None = None,
    ) -> list[FindingSchema]:
        cmd = [
            "bandit", "-r", target_path, "-f", "json",
        ]
        if extra_args:
            cmd.extend(extra_args)

        stdout, stderr, returncode = await self._execute(cmd, timeout)

        # Exit code 1 = findings found (not error). Only >= 2 is error.
        if returncode >= 2:
            raise ScannerExecutionError(
                self.tool_name, stderr or "unknown error", returncode
            )

        if not stdout.strip():
            return []

        data = json.loads(stdout)
        results = data.get("results", [])

        findings: list[FindingSchema] = []
        for result in results:
            test_id = result.get("test_id", "unknown")
            raw_path = result.get("filename", "")
            rel_path = self._normalize_path(raw_path, target_path)
            snippet = result.get("code", "")
            severity = _bandit_severity(
                result.get("issue_severity", "LOW"),
                result.get("issue_confidence", "LOW"),
            )
            line_start = result.get("line_number")
            line_range = result.get("line_range", [])
            line_end = line_range[-1] if line_range else line_start

            fingerprint = compute_fingerprint(rel_path, test_id, snippet)

            findings.append(
                FindingSchema(
                    fingerprint=fingerprint,
                    tool=self.tool_name,
                    rule_id=test_id,
                    file_path=rel_path,
                    line_start=line_start,
                    line_end=line_end,
                    snippet=snippet,
                    severity=severity,
                    title=result.get("issue_text", test_id),
                    description=result.get("issue_text"),
                )
            )

        return findings
