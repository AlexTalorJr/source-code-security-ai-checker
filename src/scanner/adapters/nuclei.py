"""Nuclei DAST scanner adapter -- parses JSONL output into FindingSchema."""

import json

from scanner.adapters.base import ScannerAdapter
from scanner.core.exceptions import ScannerExecutionError
from scanner.core.fingerprint import compute_fingerprint
from scanner.schemas.finding import FindingSchema
from scanner.schemas.severity import Severity

NUCLEI_SEVERITY_MAP: dict[str, Severity] = {
    "critical": Severity.CRITICAL,
    "high": Severity.HIGH,
    "medium": Severity.MEDIUM,
    "low": Severity.LOW,
    "info": Severity.INFO,
}


class NucleiAdapter(ScannerAdapter):
    """Adapter for Nuclei template-based vulnerability scanner (DAST)."""

    @property
    def tool_name(self) -> str:
        return "nuclei"

    def _version_command(self) -> list[str]:
        return ["nuclei", "-version"]

    async def run(
        self,
        target_path: str,
        timeout: int,
        extra_args: list[str] | None = None,
    ) -> list[FindingSchema]:
        # target_path is the URL for DAST scans
        cmd = [
            "nuclei", "-u", target_path, "-jsonl", "-silent",
            "-omit-raw", "-omit-template",
        ]
        if extra_args:
            cmd.extend(extra_args)

        stdout, stderr, returncode = await self._execute(cmd, timeout)

        # Nuclei exit code 0 = success (with or without findings)
        # Non-zero = actual error (NOT "findings found" like gosec)
        if returncode != 0:
            raise ScannerExecutionError(
                self.tool_name, stderr or "unknown error", returncode
            )

        findings: list[FindingSchema] = []
        for line in stdout.strip().splitlines():
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            finding = self._parse_event(event)
            findings.append(finding)
        return findings

    def _parse_event(self, event: dict) -> FindingSchema:
        template_id = event.get("template-id", "unknown")
        info = event.get("info", {})
        matched_at = event.get("matched-at", event.get("host", ""))
        severity_str = info.get("severity", "info").lower()
        severity = NUCLEI_SEVERITY_MAP.get(severity_str, Severity.INFO)

        # Snippet: extracted results or matched line
        extracted = event.get("extracted-results") or []
        matched_line = event.get("matched-line")
        snippet = "\n".join(extracted) if extracted else (matched_line or "")

        fingerprint = compute_fingerprint(matched_at, template_id, snippet)

        return FindingSchema(
            fingerprint=fingerprint,
            tool=self.tool_name,
            rule_id=template_id,
            file_path=matched_at,
            line_start=None,
            line_end=None,
            snippet=snippet or None,
            severity=severity,
            title=info.get("name", template_id),
            description=info.get("description"),
        )
