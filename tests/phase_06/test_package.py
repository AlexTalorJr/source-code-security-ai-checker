"""Tests for Makefile package target contents."""

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
def makefile_content() -> str:
    return (_project_root() / "Makefile").read_text()


REQUIRED_PACKAGE_FILES = [
    "Dockerfile",
    "docker-compose.yml",
    "config.yml.example",
    ".env.example",
    "README.md",
    "LICENSE",
    "src/",
    "pyproject.toml",
    "alembic/",
    "alembic.ini",
    "docs/",
]


def test_package_target_includes_required_files(makefile_content: str) -> None:
    # Extract the package recipe block (lines after "package:" until next target)
    in_package = False
    recipe_lines: list[str] = []
    for line in makefile_content.splitlines():
        if line.startswith("package:"):
            in_package = True
            recipe_lines.append(line)
            continue
        if in_package:
            if line.startswith("\t") or (line.startswith(" ") and line.strip()):
                recipe_lines.append(line)
            elif line.strip() and not line.startswith("\t"):
                break
    recipe_text = "\n".join(recipe_lines)

    for required_file in REQUIRED_PACKAGE_FILES:
        assert required_file in recipe_text, (
            f"Package target must include '{required_file}'"
        )


def test_package_name_uses_version(makefile_content: str) -> None:
    assert "security-ai-scanner-$(VERSION)" in makefile_content, (
        "Package name must use VERSION variable: security-ai-scanner-$(VERSION)"
    )
