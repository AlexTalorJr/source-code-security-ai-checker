"""PHP Security Checker adapter -- CVE detection in composer dependencies."""

import json
import logging
from pathlib import Path

from scanner.adapters.base import ScannerAdapter

logger = logging.getLogger(__name__)
from scanner.core.fingerprint import compute_fingerprint
from scanner.schemas.finding import FindingSchema
from scanner.schemas.severity import Severity


class PhpSecurityCheckerAdapter(ScannerAdapter):
    """Adapter for local-php-security-checker (composer dependency CVEs)."""

    @property
    def tool_name(self) -> str:
        return "php_security_checker"

    def _version_command(self) -> list[str]:
        return ["local-php-security-checker", "--version"]

    @staticmethod
    def _has_composer_lock(target_path: str) -> bool:
        """Check whether composer.lock exists in the target."""
        return (Path(target_path) / "composer.lock").exists()

    async def run(
        self,
        target_path: str,
        timeout: int,
        extra_args: list[str] | None = None,
    ) -> list[FindingSchema]:
        if not self._has_composer_lock(target_path):
            return []

        lock_path = str(Path(target_path) / "composer.lock")

        cmd = [
            "local-php-security-checker",
            "--format=json",
            f"--path={lock_path}",
        ]
        if extra_args:
            cmd.extend(extra_args)

        try:
            stdout, stderr, returncode = await self._execute(cmd, timeout)
        except FileNotFoundError:
            logger.warning("local-php-security-checker not installed, skipping")
            return []

        if not stdout or not stdout.strip():
            return []

        try:
            data = json.loads(stdout)
        except json.JSONDecodeError:
            return []

        findings: list[FindingSchema] = []

        # Output format: {"package-name": {"version": "x.y", "advisories": [...]}}
        for package_name, package_data in data.items():
            version = package_data.get("version", "unknown")
            advisories = package_data.get("advisories", [])

            for advisory in advisories:
                cve = advisory.get("cve") or advisory.get("title", "unknown")
                title = advisory.get("title", cve)
                link = advisory.get("link", "")

                fingerprint = compute_fingerprint(
                    "composer.lock", cve, package_name
                )

                findings.append(
                    FindingSchema(
                        fingerprint=fingerprint,
                        tool=self.tool_name,
                        rule_id=cve,
                        file_path="composer.lock",
                        snippet=f"{package_name}:{version}",
                        severity=Severity.HIGH,
                        title=f"{package_name}:{version} — {title}",
                        description=f"{title}. {link}".strip(),
                    )
                )

        return findings
