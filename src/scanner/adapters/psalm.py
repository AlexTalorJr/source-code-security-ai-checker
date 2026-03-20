"""Psalm scanner adapter -- taint analysis for PHP/Laravel projects."""

import json
from pathlib import Path

from scanner.adapters.base import ScannerAdapter
from scanner.core.fingerprint import compute_fingerprint
from scanner.schemas.finding import FindingSchema
from scanner.schemas.severity import Severity

PSALM_SEVERITY_MAP: dict[str, Severity] = {
    "error": Severity.HIGH,
    "info": Severity.MEDIUM,
}

_PHP_EXTENSIONS = frozenset({".php"})


class PsalmAdapter(ScannerAdapter):
    """Adapter for Psalm static analysis with taint analysis (PHP/Laravel)."""

    @property
    def tool_name(self) -> str:
        return "psalm"

    def _version_command(self) -> list[str]:
        return ["psalm", "--version"]

    @staticmethod
    def _has_php_files(target_path: str) -> bool:
        """Check whether the target directory contains PHP files."""
        skip_dirs = {".venv", "venv", "node_modules", ".git", "vendor"}
        for p in Path(target_path).rglob("*"):
            if any(part in skip_dirs for part in p.parts):
                continue
            if p.suffix in _PHP_EXTENSIONS:
                return True
        return False

    async def run(
        self,
        target_path: str,
        timeout: int,
        extra_args: list[str] | None = None,
    ) -> list[FindingSchema]:
        if not self._has_php_files(target_path):
            return []

        cmd = [
            "psalm",
            "--output-format=json",
            "--taint-analysis",
            "--no-cache",
            target_path,
        ]
        if extra_args:
            cmd.extend(extra_args)

        stdout, stderr, returncode = await self._execute(cmd, timeout)

        # Psalm exit code 1 = issues found, 2 = error
        if not stdout or not stdout.strip():
            return []

        try:
            results = json.loads(stdout)
        except json.JSONDecodeError:
            return []

        findings: list[FindingSchema] = []
        for issue in results:
            rule_id = issue.get("type", "unknown")
            raw_path = issue.get("file_path", "")
            rel_path = self._normalize_path(raw_path, target_path)
            line = issue.get("line_from")
            snippet = issue.get("snippet", "")
            severity_str = issue.get("severity", "error")
            severity = PSALM_SEVERITY_MAP.get(severity_str, Severity.MEDIUM)
            message = issue.get("message", rule_id)

            # Taint findings are always high severity
            if "taint" in rule_id.lower() or "Taint" in message:
                severity = Severity.HIGH

            fingerprint = compute_fingerprint(rel_path, rule_id, snippet)

            findings.append(
                FindingSchema(
                    fingerprint=fingerprint,
                    tool=self.tool_name,
                    rule_id=rule_id,
                    file_path=rel_path,
                    line_start=line,
                    line_end=issue.get("line_to"),
                    snippet=snippet,
                    severity=severity,
                    title=message,
                    description=message,
                )
            )

        return findings
