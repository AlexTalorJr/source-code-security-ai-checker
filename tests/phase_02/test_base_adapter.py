"""Tests for the ScannerAdapter abstract base class."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from scanner.adapters.base import ScannerAdapter
from scanner.core.exceptions import ScannerTimeoutError
from scanner.schemas.finding import FindingSchema


class DummyAdapter(ScannerAdapter):
    """Concrete adapter subclass for testing the ABC."""

    @property
    def tool_name(self) -> str:
        return "dummy"

    async def run(
        self,
        target_path: str,
        timeout: int,
        extra_args: list[str] | None = None,
    ) -> list[FindingSchema]:
        return []

    def _version_command(self) -> list[str]:
        return ["dummy", "--version"]


class TestNormalizePath:
    """Tests for ScannerAdapter._normalize_path."""

    def test_normalize_path_strips_prefix(self):
        result = ScannerAdapter._normalize_path(
            "/tmp/target/src/file.py", "/tmp/target"
        )
        assert result == "src/file.py"

    def test_normalize_path_strips_leading_dot_slash(self):
        result = ScannerAdapter._normalize_path("./src/file.py", "")
        assert result == "src/file.py"

    def test_normalize_path_no_prefix_match(self):
        result = ScannerAdapter._normalize_path(
            "/other/path/file.py", "/tmp/target"
        )
        assert result == "other/path/file.py"

    def test_normalize_path_with_trailing_slash_prefix(self):
        result = ScannerAdapter._normalize_path(
            "/tmp/target/src/file.py", "/tmp/target/"
        )
        assert result == "src/file.py"


class TestExecute:
    """Tests for ScannerAdapter._execute."""

    @pytest.mark.asyncio
    @patch("scanner.adapters.base.asyncio.create_subprocess_exec")
    async def test_execute_timeout_raises_scanner_timeout_error(self, mock_exec):
        """Timeout during communicate raises ScannerTimeoutError."""
        proc = AsyncMock()
        proc.communicate.side_effect = asyncio.TimeoutError()
        proc.kill = AsyncMock()
        proc.wait = AsyncMock()
        mock_exec.return_value = proc

        adapter = DummyAdapter()
        with pytest.raises(ScannerTimeoutError) as exc_info:
            await adapter._execute(["dummy", "scan"], timeout=30)

        assert exc_info.value.tool_name == "dummy"
        assert exc_info.value.timeout == 30
        proc.kill.assert_called_once()
        proc.wait.assert_called_once()

    @pytest.mark.asyncio
    @patch("scanner.adapters.base.asyncio.create_subprocess_exec")
    async def test_execute_returns_stdout_stderr_returncode(self, mock_exec):
        """Successful execution returns (stdout, stderr, returncode) tuple."""
        proc = AsyncMock()
        proc.communicate.return_value = (b"output data", b"error data")
        proc.returncode = 0
        mock_exec.return_value = proc

        adapter = DummyAdapter()
        stdout, stderr, rc = await adapter._execute(["dummy", "scan"], timeout=30)

        assert stdout == "output data"
        assert stderr == "error data"
        assert rc == 0
