"""Brakeman scanner adapter -- parses JSON output into FindingSchema."""

import json
import logging

from scanner.adapters.base import ScannerAdapter
from scanner.core.exceptions import ScannerExecutionError
from scanner.core.fingerprint import compute_fingerprint
from scanner.schemas.finding import FindingSchema
from scanner.schemas.severity import Severity

logger = logging.getLogger(__name__)

# Brakeman uses confidence as a proxy for severity.
# Base severity maps confidence level to a starting severity.
BRAKEMAN_CONFIDENCE_SEVERITY: dict[str, Severity] = {
    "High": Severity.HIGH,
    "Medium": Severity.MEDIUM,
    "Weak": Severity.LOW,  # Weak confidence gets downgraded one level from MEDIUM -> LOW
}


class BrakemanAdapter(ScannerAdapter):
    """Adapter for Brakeman Ruby on Rails security analysis tool."""

    @property
    def tool_name(self) -> str:
        return "brakeman"

    def _version_command(self) -> list[str]:
        return ["brakeman", "--version"]

    async def run(
        self,
        target_path: str,
        timeout: int,
        extra_args: list[str] | None = None,
    ) -> list[FindingSchema]:
        cmd = [
            "brakeman", "--format", "json",
            "--no-exit-on-warn", "--quiet",
            target_path,
        ]
        if extra_args:
            cmd.extend(extra_args)

        stdout, stderr, returncode = await self._execute(cmd, timeout)

        # Brakeman with --no-exit-on-warn returns 0 for findings.
        # Non-zero means actual error (not a Rails app, config issue, etc.)
        if returncode != 0:
            # Graceful handling: non-Rails Ruby projects
            if "Please supply the path to a Rails application" in (stderr or ""):
                logger.debug(
                    "Brakeman: target is not a Rails application, returning empty results"
                )
                return []
            raise ScannerExecutionError(
                self.tool_name, stderr or "unknown error", returncode
            )

        if not stdout.strip():
            return []

        data = json.loads(stdout)
        warnings = data.get("warnings", [])

        findings: list[FindingSchema] = []
        for warning in warnings:
            check_name = warning.get("check_name", "unknown")
            warning_type = warning.get("warning_type", check_name)
            raw_path = warning.get("file", "")
            # Brakeman gives paths relative to Rails app root, normalize anyway
            rel_path = self._normalize_path(raw_path, target_path)
            snippet = warning.get("code", "")
            confidence = warning.get("confidence", "Medium")
            severity = BRAKEMAN_CONFIDENCE_SEVERITY.get(confidence, Severity.MEDIUM)
            line_num = warning.get("line")

            fingerprint = compute_fingerprint(rel_path, check_name, snippet or "")

            findings.append(
                FindingSchema(
                    fingerprint=fingerprint,
                    tool=self.tool_name,
                    rule_id=check_name,
                    file_path=rel_path,
                    line_start=line_num,
                    line_end=line_num,
                    snippet=snippet,
                    severity=severity,
                    title=f"{warning_type}: {warning.get('message', check_name)}",
                    description=warning.get("message"),
                )
            )

        return findings
