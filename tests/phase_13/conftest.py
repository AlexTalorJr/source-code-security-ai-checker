"""Shared fixtures for phase 13 NucleiAdapter tests."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def nuclei_jsonl_fixture_path() -> Path:
    """Return path to the sample Nuclei JSONL fixture file."""
    return FIXTURES_DIR / "nuclei_output.jsonl"


@pytest.fixture
def sample_nuclei_event() -> dict:
    """Return the first parsed event from the JSONL fixture."""
    first_line = (FIXTURES_DIR / "nuclei_output.jsonl").read_text().splitlines()[0]
    return json.loads(first_line)


@pytest.fixture
def mock_execute():
    """Patch ScannerAdapter._execute to return configurable output.

    Usage:
        async def test_something(mock_execute):
            mock_execute("stdout content", "", 0)
            adapter = NucleiAdapter()
            result = await adapter.run(...)
    """

    def _configure(stdout: str = "", stderr: str = "", returncode: int = 0):
        patcher = patch(
            "scanner.adapters.base.ScannerAdapter._execute",
            new_callable=AsyncMock,
            return_value=(stdout, stderr, returncode),
        )
        mock = patcher.start()
        return mock, patcher

    return _configure
