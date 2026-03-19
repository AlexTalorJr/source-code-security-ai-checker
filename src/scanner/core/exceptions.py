"""Scanner-specific exception classes."""


class ScannerError(Exception):
    """Base exception for scanner errors."""


class ScannerTimeoutError(ScannerError):
    """Raised when a scanner tool exceeds its timeout."""

    def __init__(self, tool_name: str, timeout: int):
        self.tool_name = tool_name
        self.timeout = timeout
        super().__init__(f"{tool_name} timed out after {timeout}s")


class ScannerExecutionError(ScannerError):
    """Raised when a scanner tool fails to execute."""

    def __init__(
        self, tool_name: str, message: str, returncode: int | None = None
    ):
        self.tool_name = tool_name
        self.returncode = returncode
        super().__init__(f"{tool_name} failed: {message}")


class GitCloneError(ScannerError):
    """Raised when git clone fails."""
