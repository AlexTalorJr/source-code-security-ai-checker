"""Gitleaks scanner adapter -- parses JSON report into FindingSchema."""

import json
import os
import tempfile

from scanner.adapters.base import ScannerAdapter
from scanner.core.exceptions import ScannerExecutionError
from scanner.core.fingerprint import compute_fingerprint
from scanner.schemas.finding import FindingSchema
from scanner.schemas.severity import Severity


class GitleaksAdapter(ScannerAdapter):
    """Adapter for Gitleaks secret detection tool."""

    @property
    def tool_name(self) -> str:
        return "gitleaks"

    def _version_command(self) -> list[str]:
        return ["gitleaks", "version"]

    async def run(
        self,
        target_path: str,
        timeout: int,
        extra_args: list[str] | None = None,
    ) -> list[FindingSchema]:
        report_path = os.path.join(
            tempfile.gettempdir(), f"gitleaks-{os.getpid()}.json"
        )
        cmd = [
            "gitleaks",
            "detect",
            "--source",
            target_path,
            "--report-format",
            "json",
            "--report-path",
            report_path,
            "--no-banner",
        ]
        if extra_args:
            cmd.extend(extra_args)

        try:
            _stdout, stderr, returncode = await self._execute(cmd, timeout)

            # Exit code 1 means leaks found (not an error).
            if returncode not in (0, 1):
                raise ScannerExecutionError(
                    self.tool_name, stderr or "unknown error", returncode
                )

            if not os.path.exists(report_path):
                return []

            raw = open(report_path).read().strip()  # noqa: SIM115
            if not raw:
                return []

            leaks: list[dict] = json.loads(raw)
        finally:
            if os.path.exists(report_path):
                os.remove(report_path)

        findings: list[FindingSchema] = []
        for leak in leaks:
            rule_id = leak.get("RuleID", "unknown")
            file_path = self._normalize_path(
                leak.get("File", ""), target_path
            )
            secret = leak.get("Secret", "")
            match_text = leak.get("Match", "")

            # Redact the actual secret value in the snippet.
            snippet = (
                match_text.replace(secret, "***REDACTED***")
                if secret
                else match_text
            )

            fingerprint = compute_fingerprint(file_path, rule_id, snippet)

            findings.append(
                FindingSchema(
                    fingerprint=fingerprint,
                    tool=self.tool_name,
                    rule_id=rule_id,
                    file_path=file_path,
                    line_start=leak.get("StartLine"),
                    line_end=leak.get("EndLine"),
                    snippet=snippet,
                    severity=Severity.HIGH,
                    title=leak.get("Description", rule_id),
                    description=leak.get("Description"),
                )
            )

        return findings
