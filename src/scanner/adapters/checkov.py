"""Checkov scanner adapter -- parses JSON output with severity by check_id prefix."""

import json

from scanner.adapters.base import ScannerAdapter
from scanner.core.exceptions import ScannerExecutionError
from scanner.core.fingerprint import compute_fingerprint
from scanner.schemas.finding import FindingSchema
from scanner.schemas.severity import Severity

# Severity mapping by check_id prefix (longest prefix first for matching).
CHECKOV_SEVERITY_PREFIX_MAP: dict[str, Severity] = {
    "CKV2_K8S": Severity.HIGH,
    "CKV2_DOCKER": Severity.HIGH,
    "CKV_K8S": Severity.MEDIUM,
    "CKV_DOCKER": Severity.MEDIUM,
    "CKV_HELM": Severity.MEDIUM,
}

# Sorted by prefix length descending so CKV2_ matches before CKV_.
_SORTED_PREFIXES = sorted(
    CHECKOV_SEVERITY_PREFIX_MAP.keys(), key=len, reverse=True
)


def _get_severity(check_id: str) -> Severity:
    """Determine severity from check_id prefix.

    Iterates longest prefixes first so CKV2_K8S matches before CKV_K8S.
    Falls back to MEDIUM for unrecognized prefixes.
    """
    for prefix in _SORTED_PREFIXES:
        if check_id.startswith(prefix):
            return CHECKOV_SEVERITY_PREFIX_MAP[prefix]
    return Severity.MEDIUM


class CheckovAdapter(ScannerAdapter):
    """Adapter for Checkov infrastructure-as-code scanner."""

    @property
    def tool_name(self) -> str:
        return "checkov"

    def _version_command(self) -> list[str]:
        return ["checkov", "--version"]

    async def run(
        self,
        target_path: str,
        timeout: int,
        extra_args: list[str] | None = None,
    ) -> list[FindingSchema]:
        cmd = [
            "checkov",
            "--directory",
            target_path,
            "--output",
            "json",
            "--quiet",
            "--compact",
        ]
        if extra_args:
            cmd.extend(extra_args)

        stdout, stderr, returncode = await self._execute(cmd, timeout)

        # Exit code 1 means failed checks found (not an error).
        if returncode not in (0, 1):
            raise ScannerExecutionError(
                self.tool_name, stderr or "unknown error", returncode
            )

        if not stdout.strip():
            return []

        parsed = json.loads(stdout)

        # Checkov output can be a single dict or a list of dicts.
        if isinstance(parsed, dict):
            parsed = [parsed]

        findings: list[FindingSchema] = []
        for check_type_result in parsed:
            results = check_type_result.get("results", {})
            failed_checks = results.get("failed_checks", [])

            for check in failed_checks:
                check_id = check.get("check_id", "")
                check_name = check.get("check_name", "")
                file_path = check.get("file_path", "")
                # Strip leading /
                file_path = file_path.lstrip("/")

                line_range = check.get("file_line_range", [])
                line_start = line_range[0] if len(line_range) > 0 else None
                line_end = line_range[1] if len(line_range) > 1 else None

                resource = check.get("resource", "")
                guideline = check.get("guideline")
                severity = _get_severity(check_id)

                fingerprint = compute_fingerprint(
                    file_path, check_id, resource
                )

                findings.append(
                    FindingSchema(
                        fingerprint=fingerprint,
                        tool=self.tool_name,
                        rule_id=check_id,
                        file_path=file_path,
                        line_start=line_start,
                        line_end=line_end,
                        snippet=resource,
                        severity=severity,
                        title=check_name,
                        description=f"Check {check_id}: {check_name}",
                        recommendation=guideline,
                    )
                )

        return findings
