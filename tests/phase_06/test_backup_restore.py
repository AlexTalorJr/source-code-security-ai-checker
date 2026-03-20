"""Tests for Makefile backup and restore targets."""

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


def _extract_recipe(makefile_content: str, target: str) -> str:
    """Extract recipe lines for a given target from Makefile content."""
    in_target = False
    recipe_lines: list[str] = []
    for line in makefile_content.splitlines():
        if line.startswith(f"{target}:"):
            in_target = True
            recipe_lines.append(line)
            continue
        if in_target:
            if line.startswith("\t") or line.strip() == "":
                recipe_lines.append(line)
            else:
                break
    return "\n".join(recipe_lines)


def test_backup_target_exists(makefile_content: str) -> None:
    assert "backup:" in makefile_content, "Makefile must contain 'backup:' target"


def test_restore_target_exists(makefile_content: str) -> None:
    assert "restore:" in makefile_content, "Makefile must contain 'restore:' target"


def test_backup_creates_archive(makefile_content: str) -> None:
    recipe = _extract_recipe(makefile_content, "backup")
    assert "tar" in recipe, "Backup recipe must use tar"
    assert ".tar.gz" in recipe, "Backup recipe must create .tar.gz archive"


def test_backup_includes_reports(makefile_content: str) -> None:
    recipe = _extract_recipe(makefile_content, "backup")
    assert "reports" in recipe, (
        "Backup recipe must include 'reports' directory (per user decision)"
    )


def test_restore_uses_backup_var(makefile_content: str) -> None:
    recipe = _extract_recipe(makefile_content, "restore")
    assert "BACKUP" in recipe, (
        "Restore recipe must use BACKUP variable for archive path"
    )


def test_restore_includes_reports(makefile_content: str) -> None:
    recipe = _extract_recipe(makefile_content, "restore")
    assert "reports" in recipe, (
        "Restore recipe must include 'reports' directory (per user decision)"
    )
