"""Tests validating Jenkinsfile.security structure and content."""

from __future__ import annotations

from pathlib import Path

import pytest

JENKINSFILE = Path(__file__).resolve().parents[2] / "Jenkinsfile.security"


@pytest.fixture
def jenkinsfile_content() -> str:
    """Read Jenkinsfile.security content."""
    return JENKINSFILE.read_text()


def test_jenkinsfile_exists() -> None:
    """Jenkinsfile.security exists at project root."""
    assert JENKINSFILE.exists(), f"Expected {JENKINSFILE} to exist"


def test_jenkinsfile_contains_pipeline(jenkinsfile_content: str) -> None:
    """Jenkinsfile uses declarative pipeline syntax."""
    assert "pipeline {" in jenkinsfile_content


def test_jenkinsfile_contains_api_key_header(jenkinsfile_content: str) -> None:
    """Jenkinsfile sends X-API-Key header for authentication."""
    assert "X-API-Key" in jenkinsfile_content


def test_jenkinsfile_contains_workspace_path(jenkinsfile_content: str) -> None:
    """Jenkinsfile passes Jenkins WORKSPACE path to scanner."""
    assert "${WORKSPACE}" in jenkinsfile_content


def test_jenkinsfile_contains_gate_check(jenkinsfile_content: str) -> None:
    """Jenkinsfile checks quality gate result."""
    assert "gate_passed" in jenkinsfile_content


def test_jenkinsfile_contains_poll_loop(jenkinsfile_content: str) -> None:
    """Jenkinsfile polls for scan completion with sleep."""
    assert "while" in jenkinsfile_content
    assert "sleep" in jenkinsfile_content
