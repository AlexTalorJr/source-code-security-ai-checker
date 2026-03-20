"""cppcheck scanner adapter -- parses XML v2 output into FindingSchema."""

import defusedxml.ElementTree as ET
from pathlib import Path

from scanner.adapters.base import ScannerAdapter
from scanner.core.exceptions import ScannerExecutionError
from scanner.core.fingerprint import compute_fingerprint
from scanner.schemas.finding import FindingSchema
from scanner.schemas.severity import Severity

CPPCHECK_SEVERITY_MAP: dict[str, Severity] = {
    "error": Severity.HIGH,
    "warning": Severity.MEDIUM,
    "style": Severity.LOW,
    "performance": Severity.LOW,
    "portability": Severity.LOW,
    "information": Severity.INFO,
}

_CPP_EXTENSIONS = frozenset(
    {".c", ".cpp", ".cc", ".cxx", ".h", ".hpp", ".hxx"}
)

# Noisy check IDs to skip (not security-relevant).
_SKIP_IDS = frozenset({"missingIncludeSystem"})


class CppcheckAdapter(ScannerAdapter):
    """Adapter for cppcheck static analysis tool."""

    @property
    def tool_name(self) -> str:
        return "cppcheck"

    def _version_command(self) -> list[str]:
        return ["cppcheck", "--version"]

    _SKIP_DIRS = frozenset({".venv", "venv", "node_modules", ".git", "__pycache__"})

    @classmethod
    def _has_cpp_files(cls, target_path: str) -> bool:
        """Check whether the target directory contains any C/C++ files."""
        for p in Path(target_path).rglob("*"):
            if any(part in cls._SKIP_DIRS for part in p.parts):
                continue
            if p.suffix in _CPP_EXTENSIONS:
                return True
        return False

    async def run(
        self,
        target_path: str,
        timeout: int,
        extra_args: list[str] | None = None,
    ) -> list[FindingSchema]:
        if not self._has_cpp_files(target_path):
            return []

        cmd = [
            "cppcheck",
            "--xml",
            "--xml-version=2",
            "--enable=warning,style,performance,portability",
            "-i.venv",
            "-inode_modules",
            "-i.git",
            target_path,
        ]
        if extra_args:
            cmd.extend(extra_args)

        stdout, stderr, returncode = await self._execute(cmd, timeout)

        # cppcheck writes XML to stderr, not stdout.
        if not stderr or not stderr.strip():
            return []
        root = ET.fromstring(stderr)

        findings: list[FindingSchema] = []
        for error in root.iter("error"):
            error_id = error.get("id", "")
            if error_id in _SKIP_IDS:
                continue

            locations = error.findall("location")
            if not locations:
                continue

            loc = locations[0]
            raw_path = loc.get("file", "")
            rel_path = self._normalize_path(raw_path, target_path)
            line = int(loc.get("line", 0)) or None
            severity_str = error.get("severity", "information")
            severity = CPPCHECK_SEVERITY_MAP.get(severity_str, Severity.INFO)
            msg = error.get("msg", error_id)
            verbose = error.get("verbose", msg)

            fingerprint = compute_fingerprint(rel_path, error_id, msg)

            findings.append(
                FindingSchema(
                    fingerprint=fingerprint,
                    tool=self.tool_name,
                    rule_id=error_id,
                    file_path=rel_path,
                    line_start=line,
                    snippet=msg,
                    severity=severity,
                    title=msg,
                    description=verbose,
                )
            )

        return findings
