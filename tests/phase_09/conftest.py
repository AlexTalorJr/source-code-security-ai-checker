"""Shared fixtures for Phase 09 scanner adapter tests."""

import json
from pathlib import Path

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the path to the test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def gosec_output(fixtures_dir: Path) -> dict:
    """Load and return the gosec fixture output."""
    return json.loads((fixtures_dir / "gosec_output.json").read_text())


@pytest.fixture
def bandit_output(fixtures_dir: Path) -> dict:
    """Load and return the Bandit fixture output."""
    return json.loads((fixtures_dir / "bandit_output.json").read_text())


@pytest.fixture
def brakeman_output(fixtures_dir: Path) -> dict:
    """Load and return the Brakeman fixture output."""
    return json.loads((fixtures_dir / "brakeman_output.json").read_text())


@pytest.fixture
def cargo_audit_output(fixtures_dir: Path) -> dict:
    """Load and return the cargo-audit fixture output."""
    return json.loads((fixtures_dir / "cargo_audit_output.json").read_text())
