"""Trivy scanner adapter -- parses JSON output with vulns and misconfigs."""

import json

from scanner.adapters.base import ScannerAdapter
from scanner.core.fingerprint import compute_fingerprint
from scanner.schemas.finding import FindingSchema
from scanner.schemas.severity import Severity

TRIVY_SEVERITY_MAP: dict[str, Severity] = {
    "CRITICAL": Severity.CRITICAL,
    "HIGH": Severity.HIGH,
    "MEDIUM": Severity.MEDIUM,
    "LOW": Severity.LOW,
    "UNKNOWN": Severity.INFO,
}


class TrivyAdapter(ScannerAdapter):
    """Adapter for Trivy vulnerability and misconfiguration scanner."""

    @property
    def tool_name(self) -> str:
        return "trivy"

    def _version_command(self) -> list[str]:
        return ["trivy", "--version"]

    async def run(
        self,
        target_path: str,
        timeout: int,
        extra_args: list[str] | None = None,
    ) -> list[FindingSchema]:
        cmd = [
            "trivy",
            "fs",
            "--format",
            "json",
            "--scanners",
            "vuln,misconfig,secret",
            target_path,
        ]
        if extra_args:
            cmd.extend(extra_args)

        stdout, _stderr, _returncode = await self._execute(cmd, timeout)
        data = json.loads(stdout)

        findings: list[FindingSchema] = []
        for result in data.get("Results", []):
            target = result.get("Target", "")

            # Process vulnerabilities
            for vuln in result.get("Vulnerabilities", []):
                severity_str = vuln.get("Severity", "UNKNOWN")
                severity = TRIVY_SEVERITY_MAP.get(severity_str, Severity.INFO)
                pkg_name = vuln.get("PkgName", "")
                installed = vuln.get("InstalledVersion", "")
                fixed = vuln.get("FixedVersion", "")
                snippet = f"{pkg_name} {installed} -> {fixed}"
                rule_id = vuln.get("VulnerabilityID", "")

                fingerprint = compute_fingerprint(target, rule_id, snippet)

                recommendation = None
                if fixed:
                    recommendation = f"Upgrade {pkg_name} to {fixed}"

                findings.append(
                    FindingSchema(
                        fingerprint=fingerprint,
                        tool=self.tool_name,
                        rule_id=rule_id,
                        file_path=target,
                        snippet=snippet,
                        severity=severity,
                        title=vuln.get("Title", rule_id),
                        description=vuln.get("Description"),
                        recommendation=recommendation,
                    )
                )

            # Process misconfigurations
            for misconfig in result.get("Misconfigurations", []):
                severity_str = misconfig.get("Severity", "UNKNOWN")
                severity = TRIVY_SEVERITY_MAP.get(severity_str, Severity.INFO)
                rule_id = misconfig.get("ID", "")
                message = misconfig.get("Message", "")

                fingerprint = compute_fingerprint(target, rule_id, message)

                findings.append(
                    FindingSchema(
                        fingerprint=fingerprint,
                        tool=self.tool_name,
                        rule_id=rule_id,
                        file_path=target,
                        snippet=message,
                        severity=severity,
                        title=misconfig.get("Title", rule_id),
                        description=message,
                        recommendation=misconfig.get("Resolution"),
                    )
                )

        return findings
