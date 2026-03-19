"""Shared fixtures for Phase 02 scanner adapter tests."""

import json
from pathlib import Path

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the path to the test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def semgrep_output(fixtures_dir: Path) -> dict:
    """Load and return the semgrep fixture output."""
    return json.loads((fixtures_dir / "semgrep_output.json").read_text())


@pytest.fixture
def cppcheck_output(fixtures_dir: Path) -> str:
    """Load and return the cppcheck fixture output as XML string."""
    return (fixtures_dir / "cppcheck_output.xml").read_text()


@pytest.fixture
def gitleaks_output(fixtures_dir: Path) -> list[dict]:
    """Load and return the gitleaks fixture output."""
    return json.loads((fixtures_dir / "gitleaks_output.json").read_text())


@pytest.fixture
def trivy_output(fixtures_dir: Path) -> dict:
    """Load and return the trivy fixture output."""
    return json.loads((fixtures_dir / "trivy_output.json").read_text())


@pytest.fixture
def checkov_output(fixtures_dir: Path) -> dict:
    """Load and return the checkov fixture output."""
    return json.loads((fixtures_dir / "checkov_output.json").read_text())


@pytest.fixture
def tmp_target_dir(tmp_path: Path) -> Path:
    """Create a temporary directory with a dummy file to simulate a scan target."""
    target = tmp_path / "target"
    target.mkdir()
    (target / "dummy.py").write_text("# dummy file for testing\n")
    return target
