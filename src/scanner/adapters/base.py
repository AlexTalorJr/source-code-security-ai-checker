"""Abstract base class for scanner tool adapters."""

import abc
import asyncio

from scanner.core.exceptions import ScannerTimeoutError
from scanner.schemas.finding import FindingSchema


class ScannerAdapter(abc.ABC):
    """Base class defining the contract all scanner adapters must implement.

    Each adapter wraps a specific security scanning tool (semgrep, cppcheck,
    gitleaks, trivy, checkov) and normalizes its output into FindingSchema.
    """

    @property
    @abc.abstractmethod
    def tool_name(self) -> str:
        """Return the name of the scanner tool (e.g. 'semgrep')."""
        ...

    @abc.abstractmethod
    async def run(
        self,
        target_path: str,
        timeout: int,
        extra_args: list[str] | None = None,
    ) -> list[FindingSchema]:
        """Run the scanner tool against the target path.

        Args:
            target_path: Path to the directory or file to scan.
            timeout: Maximum execution time in seconds.
            extra_args: Additional CLI arguments for the tool.

        Returns:
            List of normalized findings.
        """
        ...

    async def get_version(self) -> str:
        """Get the installed version of the scanner tool."""
        cmd = self._version_command()
        stdout, _stderr, _rc = await self._execute(cmd, timeout=10)
        return stdout.strip()

    @abc.abstractmethod
    def _version_command(self) -> list[str]:
        """Return the command list for checking tool version.

        Example: ["semgrep", "--version"]
        """
        ...

    async def _execute(
        self, cmd: list[str], timeout: int
    ) -> tuple[str, str, int]:
        """Execute a subprocess command with timeout.

        Args:
            cmd: Command and arguments to execute.
            timeout: Maximum execution time in seconds.

        Returns:
            Tuple of (stdout, stderr, returncode).

        Raises:
            ScannerTimeoutError: If the command exceeds the timeout.
        """
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise ScannerTimeoutError(self.tool_name, timeout)

        return (stdout.decode(), stderr.decode(), proc.returncode)

    @staticmethod
    def _normalize_path(file_path: str, target_prefix: str) -> str:
        """Strip the target directory prefix and leading ./ from a file path.

        Args:
            file_path: Absolute or relative path from tool output.
            target_prefix: The target directory path to strip.

        Returns:
            Relative path suitable for storage.
        """
        if target_prefix and file_path.startswith(target_prefix):
            file_path = file_path[len(target_prefix) :]
        file_path = file_path.lstrip("/")
        if file_path.startswith("./"):
            file_path = file_path[2:]
        return file_path
