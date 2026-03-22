"""Cargo-audit scanner adapter -- parses JSON output into FindingSchema."""

import asyncio
import json
import logging
from pathlib import Path

from scanner.adapters.base import ScannerAdapter
from scanner.core.exceptions import ScannerExecutionError
from scanner.core.fingerprint import compute_fingerprint
from scanner.schemas.finding import FindingSchema
from scanner.schemas.severity import Severity

logger = logging.getLogger(__name__)


def _cvss_to_severity(cvss_vector: str | None) -> Severity:
    """Convert CVSS vector string to Severity using score-based ranges.

    Ranges per CONTEXT.md:
      9.0+ -> CRITICAL, 7.0-8.9 -> HIGH, 4.0-6.9 -> MEDIUM,
      0.1-3.9 -> LOW, no CVSS -> MEDIUM (safe default).
    """
    if not cvss_vector:
        return Severity.MEDIUM
    try:
        from cvss import CVSS3

        score = CVSS3(cvss_vector).scores()[0]  # base score
    except Exception:
        return Severity.MEDIUM
    if score >= 9.0:
        return Severity.CRITICAL
    elif score >= 7.0:
        return Severity.HIGH
    elif score >= 4.0:
        return Severity.MEDIUM
    elif score > 0:
        return Severity.LOW
    return Severity.MEDIUM


async def _ensure_lockfile(target_path: str) -> bool:
    """Generate Cargo.lock if missing but Cargo.toml exists.

    Per user decision in CONTEXT.md: run `cargo generate-lockfile`
    if no Cargo.lock found, to generate it from Cargo.toml.

    Returns True if lockfile exists (or was generated), False if
    generation failed or cargo is not installed.
    """
    lockfile = Path(target_path) / "Cargo.lock"
    if lockfile.exists():
        return True

    cargo_toml = Path(target_path) / "Cargo.toml"
    if not cargo_toml.exists():
        logger.debug(
            "No Cargo.toml found in %s, skipping lockfile generation",
            target_path,
        )
        return False

    logger.info(
        "Cargo.lock not found in %s, running cargo generate-lockfile",
        target_path,
    )
    try:
        proc = await asyncio.create_subprocess_exec(
            "cargo",
            "generate-lockfile",
            cwd=target_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            logger.warning(
                "cargo generate-lockfile failed (rc=%d): %s",
                proc.returncode,
                stderr.decode(errors="replace").strip(),
            )
            return False
        return True
    except FileNotFoundError:
        logger.warning("cargo not found on PATH, cannot generate Cargo.lock")
        return False


class CargoAuditAdapter(ScannerAdapter):
    """Adapter for cargo-audit Rust dependency vulnerability scanner."""

    @property
    def tool_name(self) -> str:
        return "cargo_audit"

    def _version_command(self) -> list[str]:
        return ["cargo-audit", "--version"]

    async def run(
        self,
        target_path: str,
        timeout: int,
        extra_args: list[str] | None = None,
    ) -> list[FindingSchema]:
        # Per CONTEXT.md decision: generate Cargo.lock if missing
        lockfile_ready = await _ensure_lockfile(target_path)
        if not lockfile_ready:
            logger.debug(
                "No Cargo.lock available for %s (generation failed or no Cargo.toml), "
                "returning empty results",
                target_path,
            )
            return []

        cmd = [
            "cargo-audit",
            "audit",
            "--json",
            "--file",
            f"{target_path}/Cargo.lock",
        ]
        if extra_args:
            cmd.extend(extra_args)

        stdout, stderr, returncode = await self._execute(cmd, timeout)

        # Exit code 1 = vulnerabilities found (not error). Only >= 2 is error.
        if returncode >= 2:
            raise ScannerExecutionError(
                self.tool_name, stderr or "unknown error", returncode
            )

        if not stdout.strip():
            return []

        data = json.loads(stdout)
        # Only process vulnerabilities, NOT warnings (per CONTEXT.md)
        vuln_section = data.get("vulnerabilities", {})
        vuln_list = vuln_section.get("list", [])

        findings: list[FindingSchema] = []
        for vuln in vuln_list:
            advisory = vuln.get("advisory", {})
            package = vuln.get("package", {})

            advisory_id = advisory.get("id", "unknown")
            cvss_vector = advisory.get("cvss")
            severity = _cvss_to_severity(cvss_vector)

            title = advisory.get("title", advisory_id)
            description = advisory.get("description", "")
            pkg_name = package.get("name", "unknown")
            pkg_version = package.get("version", "unknown")

            # Enrich title and description with package info
            full_title = f"{title} ({pkg_name} {pkg_version})"
            full_description = (
                f"{description}\n\nAffected package: {pkg_name} {pkg_version}"
            )

            fingerprint = compute_fingerprint(
                "Cargo.lock", advisory_id, f"{pkg_name}:{pkg_version}"
            )

            findings.append(
                FindingSchema(
                    fingerprint=fingerprint,
                    tool=self.tool_name,
                    rule_id=advisory_id,
                    file_path="Cargo.lock",
                    line_start=None,  # dependency vulnerability, no source line
                    line_end=None,
                    snippet=f'{pkg_name} = "{pkg_version}"',
                    severity=severity,
                    title=full_title,
                    description=full_description,
                )
            )

        return findings
