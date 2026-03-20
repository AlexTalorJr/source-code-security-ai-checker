"""Psalm scanner adapter -- taint analysis for PHP/Laravel projects."""

import json
import logging
from pathlib import Path

from scanner.adapters.base import ScannerAdapter
from scanner.core.fingerprint import compute_fingerprint
from scanner.schemas.finding import FindingSchema
from scanner.schemas.severity import Severity

logger = logging.getLogger(__name__)

PSALM_SEVERITY_MAP: dict[str, Severity] = {
    "error": Severity.HIGH,
    "info": Severity.MEDIUM,
}

_PHP_EXTENSIONS = frozenset({".php"})
_SKIP_DIRS = frozenset({".venv", "venv", "node_modules", ".git", "vendor"})


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
        for p in Path(target_path).rglob("*"):
            if any(part in _SKIP_DIRS for part in p.parts):
                continue
            if p.suffix in _PHP_EXTENSIONS:
                return True
        return False

    @staticmethod
    def _has_psalm_config(target_path: str) -> bool:
        """Check if psalm.xml or psalm.xml.dist exists."""
        root = Path(target_path)
        return (root / "psalm.xml").exists() or (root / "psalm.xml.dist").exists()

    async def run(
        self,
        target_path: str,
        timeout: int,
        extra_args: list[str] | None = None,
    ) -> list[FindingSchema]:
        if not self._has_php_files(target_path):
            return []

        # Psalm requires a config file for taint analysis
        if not self._has_psalm_config(target_path):
            logger.info("Psalm skipped: no psalm.xml in %s", target_path)
            return []

        cmd = [
            "psalm",
            "--output-format=json",
            "--taint-analysis",
            "--no-cache",
            f"--root={target_path}",
        ]
        if extra_args:
            cmd.extend(extra_args)

        try:
            stdout, stderr, returncode = await self._execute(cmd, timeout)
        except FileNotFoundError:
            logger.warning("Psalm not installed, skipping")
            return []

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
