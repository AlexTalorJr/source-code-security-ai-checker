"""Gosec scanner adapter -- parses JSON output into FindingSchema."""

import json

from scanner.adapters.base import ScannerAdapter
from scanner.core.exceptions import ScannerExecutionError
from scanner.core.fingerprint import compute_fingerprint
from scanner.schemas.finding import FindingSchema
from scanner.schemas.severity import Severity

GOSEC_SEVERITY_MAP: dict[str, Severity] = {
    "HIGH": Severity.HIGH,
    "MEDIUM": Severity.MEDIUM,
    "LOW": Severity.LOW,
}


class GosecAdapter(ScannerAdapter):
    """Adapter for gosec Go security analysis tool."""

    @property
    def tool_name(self) -> str:
        return "gosec"

    def _version_command(self) -> list[str]:
        return ["gosec", "--version"]

    async def run(
        self,
        target_path: str,
        timeout: int,
        extra_args: list[str] | None = None,
    ) -> list[FindingSchema]:
        cmd = ["gosec", "-fmt=json", "-stdout", f"{target_path}/..."]
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
        issues = data.get("Issues", [])

        findings: list[FindingSchema] = []
        for issue in issues:
            rule_id = issue.get("rule_id", "unknown")
            raw_path = issue.get("file", "")
            rel_path = self._normalize_path(raw_path, target_path)
            snippet = issue.get("code", "")
            severity_str = issue.get("severity", "MEDIUM")
            severity = GOSEC_SEVERITY_MAP.get(severity_str, Severity.MEDIUM)
            # gosec line is a string, convert to int
            line_num = int(issue.get("line", "0")) or None

            fingerprint = compute_fingerprint(rel_path, rule_id, snippet)

            findings.append(
                FindingSchema(
                    fingerprint=fingerprint,
                    tool=self.tool_name,
                    rule_id=rule_id,
                    file_path=rel_path,
                    line_start=line_num,
                    line_end=line_num,  # single-line per CONTEXT.md
                    snippet=snippet,
                    severity=severity,
                    title=issue.get("details", rule_id),
                    description=issue.get("details"),
                )
            )

        return findings
