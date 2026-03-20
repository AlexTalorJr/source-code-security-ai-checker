"""Enlightn scanner adapter -- Laravel-specific security checks."""

import json
from pathlib import Path

from scanner.adapters.base import ScannerAdapter
from scanner.core.fingerprint import compute_fingerprint
from scanner.schemas.finding import FindingSchema
from scanner.schemas.severity import Severity

# Enlightn analyzer categories mapped to severities
ENLIGHTN_SEVERITY_MAP: dict[str, Severity] = {
    "security": Severity.HIGH,
    "performance": Severity.LOW,
    "reliability": Severity.MEDIUM,
}


class EnlightnAdapter(ScannerAdapter):
    """Adapter for Enlightn Laravel security analyzer."""

    @property
    def tool_name(self) -> str:
        return "enlightn"

    def _version_command(self) -> list[str]:
        return ["php", "artisan", "enlightn", "--version"]

    @staticmethod
    def _is_laravel_project(target_path: str) -> bool:
        """Check whether the target is a Laravel project."""
        artisan = Path(target_path) / "artisan"
        composer = Path(target_path) / "composer.json"
        if not artisan.exists() or not composer.exists():
            return False
        try:
            data = json.loads(composer.read_text())
            deps = {**data.get("require", {}), **data.get("require-dev", {})}
            return "laravel/framework" in deps or "enlightn/enlightn" in deps
        except (json.JSONDecodeError, OSError):
            return False

    async def run(
        self,
        target_path: str,
        timeout: int,
        extra_args: list[str] | None = None,
    ) -> list[FindingSchema]:
        if not self._is_laravel_project(target_path):
            return []

        cmd = [
            "php",
            "artisan",
            "enlightn",
            "--json",
            "--no-interaction",
        ]
        if extra_args:
            cmd.extend(extra_args)

        stdout, stderr, returncode = await self._execute(cmd, timeout)

        if not stdout or not stdout.strip():
            return []

        try:
            data = json.loads(stdout)
        except json.JSONDecodeError:
            return []

        findings: list[FindingSchema] = []
        analyzers = data if isinstance(data, list) else data.get("analyzers", [])

        for analyzer in analyzers:
            status = analyzer.get("status", "")
            if status == "passed":
                continue

            rule_id = analyzer.get("name", "unknown")
            title = analyzer.get("title", rule_id)
            description = analyzer.get("description", "")
            category = analyzer.get("category", "security").lower()
            severity = ENLIGHTN_SEVERITY_MAP.get(category, Severity.MEDIUM)

            # Security category findings with "fail" are high
            if category == "security" and status == "failed":
                severity = Severity.HIGH

            details = analyzer.get("details", "")
            file_path = analyzer.get("file", "app")
            line = analyzer.get("line")

            fingerprint = compute_fingerprint(file_path, rule_id, title)

            findings.append(
                FindingSchema(
                    fingerprint=fingerprint,
                    tool=self.tool_name,
                    rule_id=rule_id,
                    file_path=file_path,
                    line_start=line,
                    snippet=details[:500] if details else "",
                    severity=severity,
                    title=title,
                    description=description,
                )
            )

        return findings
