"""Tests for Makefile structure and targets."""

import re
from pathlib import Path

import pytest


def _project_root() -> Path:
    """Find project root by traversing up from test file to find pyproject.toml."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find project root (no pyproject.toml)")


@pytest.fixture
def makefile_path() -> Path:
    return _project_root() / "Makefile"


@pytest.fixture
def makefile_content(makefile_path: Path) -> str:
    return makefile_path.read_text()


def test_makefile_exists(makefile_path: Path) -> None:
    assert makefile_path.exists(), "Makefile must exist at project root"


def test_makefile_has_phony(makefile_content: str) -> None:
    assert ".PHONY" in makefile_content, "Makefile must declare .PHONY targets"


REQUIRED_TARGETS = [
    "install",
    "run",
    "stop",
    "test",
    "migrate",
    "backup",
    "restore",
    "package",
    "clean",
    "docker-multiarch",
    "docker-push",
    "help",
]


def test_makefile_has_required_targets(makefile_content: str) -> None:
    for target in REQUIRED_TARGETS:
        assert f"{target}:" in makefile_content, (
            f"Makefile must contain target '{target}:'"
        )


def test_makefile_has_help_comments(makefile_content: str) -> None:
    for target in REQUIRED_TARGETS:
        pattern = rf"^{re.escape(target)}:.*##"
        assert re.search(pattern, makefile_content, re.MULTILINE), (
            f"Target '{target}' must have a '## description' comment for self-documenting help"
        )


def test_makefile_uses_tabs(makefile_path: Path) -> None:
    raw = makefile_path.read_bytes()
    lines = raw.split(b"\n")
    found_recipe = False
    for i, line in enumerate(lines):
        # A recipe line follows a target line and starts with a tab
        if b":" in line and not line.startswith(b"\t") and not line.startswith(b"#"):
            # This might be a target line; check next lines for tab-indented recipes
            for j in range(i + 1, min(i + 5, len(lines))):
                if lines[j].startswith(b"\t"):
                    found_recipe = True
                    break
                if lines[j].strip() and not lines[j].startswith(b"\t"):
                    break
    assert found_recipe, "Makefile recipe lines must use tab characters (not spaces)"


def test_makefile_version_from_pyproject(makefile_content: str) -> None:
    assert "pyproject.toml" in makefile_content, (
        "Makefile must source version from pyproject.toml"
    )
