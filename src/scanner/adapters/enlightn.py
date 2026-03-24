"""Enlightn scanner adapter -- Laravel-specific security checks."""

import asyncio
import json
import logging
import re
from pathlib import Path

from scanner.adapters.base import ScannerAdapter
from scanner.core.exceptions import ScannerTimeoutError

logger = logging.getLogger(__name__)
from scanner.core.fingerprint import compute_fingerprint
from scanner.schemas.finding import FindingSchema
from scanner.schemas.severity import Severity

# Enlightn section headers mapped to severities
SECTION_SEVERITY_MAP: dict[str, Severity] = {
    "security": Severity.HIGH,
    "performance": Severity.LOW,
    "reliability": Severity.MEDIUM,
}

# Regex to parse check lines:
# "Check N/M: <title>. Failed" or "Check N/M: <title>. Exception"
CHECK_PATTERN = re.compile(
    r"Check\s+\d+/\d+:\s+(.+?)\.\s+(Failed|Exception|Passed|Not Applicable)"
)

# Section header pattern: "| Running <Category> Checks"
SECTION_PATTERN = re.compile(r"\|\s*Running\s+(\w+)\s+Checks")


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

    @staticmethod
    def _parse_text_output(stdout: str) -> list[dict]:
        """Parse Enlightn CI text output into structured check results."""
        results = []
        current_section = "security"

        for line in stdout.splitlines():
            # Detect section changes
            section_match = SECTION_PATTERN.search(line)
            if section_match:
                current_section = section_match.group(1).lower()
                continue

            # Parse check results
            check_match = CHECK_PATTERN.search(line)
            if check_match:
                title = check_match.group(1).strip()
                status = check_match.group(2)
                if status in ("Passed", "Not Applicable"):
                    continue
                results.append({
                    "title": title,
                    "status": status.lower(),  # "failed" or "exception"
                    "category": current_section,
                    "description": "",
                })
                continue

            # Capture description lines (text after a Failed/Exception check)
            if results and not line.startswith(("Check ", "|", "+", "Report Card")):
                desc_line = line.strip()
                if desc_line and not desc_line.startswith("="):
                    if results[-1]["description"]:
                        results[-1]["description"] += " " + desc_line
                    else:
                        results[-1]["description"] = desc_line

        return results

    async def run(
        self,
        target_path: str,
        timeout: int,
        extra_args: list[str] | None = None,
    ) -> list[FindingSchema]:
        if not self._is_laravel_project(target_path):
            return []

        # Check that enlightn package is installed in the project
        vendor_enlightn = Path(target_path) / "vendor" / "enlightn" / "enlightn"
        if not vendor_enlightn.exists():
            logger.info("Enlightn skipped: package not installed in %s", target_path)
            return []

        cmd = [
            "php",
            str(Path(target_path) / "artisan"),
            "enlightn",
            "--ci",
            "--details",
            "--no-interaction",
        ]
        if extra_args:
            cmd.extend(extra_args)

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=target_path,
            )
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
            stdout = stdout_bytes.decode()
            stderr = stderr_bytes.decode()
            returncode = proc.returncode
        except asyncio.TimeoutError:
            logger.warning("Enlightn timed out after %ds", timeout)
            return []
        except FileNotFoundError:
            logger.warning("PHP not installed, skipping Enlightn")
            return []

        if not stdout or not stdout.strip():
            return []

        # Parse text output (Enlightn does not support --json)
        checks = self._parse_text_output(stdout)

        if not checks:
            logger.info("Enlightn: no failed checks found in output")
            return []

        findings: list[FindingSchema] = []
        for check in checks:
            category = check["category"]
            severity = SECTION_SEVERITY_MAP.get(category, Severity.MEDIUM)

            # Security failures are always HIGH
            if category == "security" and check["status"] == "failed":
                severity = Severity.HIGH

            # Exceptions indicate runtime errors — treat as MEDIUM
            if check["status"] == "exception":
                severity = Severity.MEDIUM

            title = check["title"]
            description = check["description"]
            rule_id = re.sub(r"[^a-zA-Z0-9]", "_", title)[:80]

            fingerprint = compute_fingerprint("app", rule_id, title)

            findings.append(
                FindingSchema(
                    fingerprint=fingerprint,
                    tool=self.tool_name,
                    rule_id=rule_id,
                    file_path="app",
                    line_start=None,
                    snippet=description[:500] if description else "",
                    severity=severity,
                    title=title,
                    description=description,
                )
            )

        return findings
