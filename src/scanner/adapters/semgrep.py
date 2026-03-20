"""Semgrep scanner adapter -- parses JSON output into FindingSchema."""

import json

from scanner.adapters.base import ScannerAdapter
from scanner.core.exceptions import ScannerExecutionError
from scanner.core.fingerprint import compute_fingerprint
from scanner.schemas.finding import FindingSchema
from scanner.schemas.severity import Severity

SEMGREP_SEVERITY_MAP: dict[str, Severity] = {
    "ERROR": Severity.HIGH,
    "WARNING": Severity.MEDIUM,
    "INFO": Severity.INFO,
}


class SemgrepAdapter(ScannerAdapter):
    """Adapter for Semgrep static analysis tool."""

    @property
    def tool_name(self) -> str:
        return "semgrep"

    def _version_command(self) -> list[str]:
        return ["semgrep", "--version"]

    async def run(
        self,
        target_path: str,
        timeout: int,
        extra_args: list[str] | None = None,
    ) -> list[FindingSchema]:
        cmd = [
            "semgrep",
            "--json",
            "--config",
            "p/security-audit",
            "--config",
            "p/secrets",
            "--exclude", ".venv",
            "--exclude", "node_modules",
            "--exclude", ".git",
            target_path,
        ]
        if extra_args:
            cmd.extend(extra_args)

        stdout, stderr, returncode = await self._execute(cmd, timeout)

        # Exit code 1 means findings found (not an error).
        # Only returncode >= 2 indicates a real error.
        if returncode >= 2:
            raise ScannerExecutionError(
                self.tool_name, stderr or "unknown error", returncode
            )

        data = json.loads(stdout)
        results = data.get("results", [])

        findings: list[FindingSchema] = []
        for result in results:
            check_id = result["check_id"]
            raw_path = result["path"]
            rel_path = self._normalize_path(raw_path, target_path)
            snippet = result["extra"].get("lines", "")
            severity_str = result["extra"].get("severity", "INFO")
            severity = SEMGREP_SEVERITY_MAP.get(severity_str, Severity.INFO)

            fingerprint = compute_fingerprint(rel_path, check_id, snippet)

            findings.append(
                FindingSchema(
                    fingerprint=fingerprint,
                    tool=self.tool_name,
                    rule_id=check_id,
                    file_path=rel_path,
                    line_start=result["start"]["line"],
                    line_end=result["end"]["line"],
                    snippet=snippet,
                    severity=severity,
                    title=result["extra"].get("message", check_id),
                    description=result["extra"].get("message"),
                )
            )

        return findings
