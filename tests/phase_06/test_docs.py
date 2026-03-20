"""Documentation structure and content validation tests."""

from pathlib import Path

import pytest

# Find project root by traversing up from this file to find pyproject.toml
_current = Path(__file__).resolve()
PROJECT_ROOT = _current
while PROJECT_ROOT != PROJECT_ROOT.parent:
    if (PROJECT_ROOT / "pyproject.toml").exists():
        break
    PROJECT_ROOT = PROJECT_ROOT.parent

DOCS_EN = PROJECT_ROOT / "docs" / "en"
DOCS_RU = PROJECT_ROOT / "docs" / "ru"
README = PROJECT_ROOT / "README.md"
README_RU = PROJECT_ROOT / "README.ru.md"

ALL_EN_DOCS = [
    "architecture.md",
    "database-schema.md",
    "user-guide.md",
    "admin-guide.md",
    "devops-guide.md",
    "api.md",
    "transfer-guide.md",
    "custom-rules.md",
]

RUSSIAN_TEXT_MARKERS = [
    "\u0411\u044b\u0441\u0442\u0440\u044b\u0439 \u0441\u0442\u0430\u0440\u0442",
    "\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435",
    "\u0414\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430\u0446\u0438\u044f",
]

RUSSIAN_SECTION_MARKERS = [
    "/ \u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435",
    "/ \u0410\u0440\u0445\u0438\u0442\u0435\u043a\u0442\u0443\u0440\u0430",
    "/ \u041e\u0431\u0437\u043e\u0440",
]


# --- README tests ---


def test_readme_exists():
    assert README.is_file(), f"README.md not found at {README}"


def test_readme_is_english_only():
    content = README.read_text(encoding="utf-8")
    for marker in RUSSIAN_TEXT_MARKERS:
        assert marker not in content, (
            f"README.md contains Russian text marker: {marker}"
        )


def test_readme_has_quick_start():
    content = README.read_text(encoding="utf-8")
    assert "## Quick Start" in content, "README.md missing '## Quick Start' section"


def test_readme_links_to_docs_en():
    content = README.read_text(encoding="utf-8")
    assert "docs/en/" in content, "README.md should link to docs/en/ paths"


@pytest.mark.xfail(reason="Created in Plan 04")
def test_readme_ru_exists():
    assert README_RU.is_file(), f"README.ru.md not found at {README_RU}"


# --- docs/en/ structure tests ---


def test_docs_en_directory_exists():
    assert DOCS_EN.is_dir(), f"docs/en/ directory not found at {DOCS_EN}"


@pytest.mark.parametrize("filename", ALL_EN_DOCS)
def test_docs_en_has_all_files(filename):
    filepath = DOCS_EN / filename
    assert filepath.is_file(), f"Missing docs/en/{filename}"


@pytest.mark.parametrize("filename", ALL_EN_DOCS)
def test_docs_en_are_english_only(filename):
    filepath = DOCS_EN / filename
    if not filepath.is_file():
        pytest.skip(f"docs/en/{filename} does not exist yet")
    content = filepath.read_text(encoding="utf-8")
    for marker in RUSSIAN_SECTION_MARKERS:
        assert marker not in content, (
            f"docs/en/{filename} contains Russian section marker: {marker}"
        )


@pytest.mark.parametrize("filename", ALL_EN_DOCS)
def test_docs_structure(filename):
    filepath = DOCS_EN / filename
    if not filepath.is_file():
        pytest.skip(f"docs/en/{filename} does not exist yet")
    content = filepath.read_text(encoding="utf-8")
    assert content.startswith("# "), (
        f"docs/en/{filename} should start with '# ' title line"
    )


# --- docs/ru/ tests (xfail, created in Plan 04) ---


@pytest.mark.xfail(reason="Created in Plan 04")
def test_russian_docs():
    assert DOCS_RU.is_dir(), f"docs/ru/ directory not found at {DOCS_RU}"
    for filename in ALL_EN_DOCS:
        filepath = DOCS_RU / filename
        assert filepath.is_file(), f"Missing docs/ru/{filename}"


# --- Meta files tests ---


@pytest.mark.xfail(reason="Created in Plan 03")
def test_meta_files_license():
    license_file = PROJECT_ROOT / "LICENSE"
    assert license_file.is_file(), "LICENSE file not found"
    content = license_file.read_text(encoding="utf-8")
    assert "Apache License" in content, "LICENSE should contain 'Apache License'"


@pytest.mark.xfail(reason="Created in Plan 03")
def test_meta_files_contributing():
    contributing = PROJECT_ROOT / "CONTRIBUTING.md"
    assert contributing.is_file(), "CONTRIBUTING.md not found"


@pytest.mark.xfail(reason="Created in Plan 03")
def test_meta_files_changelog():
    changelog = PROJECT_ROOT / "CHANGELOG.md"
    assert changelog.is_file(), "CHANGELOG.md not found"
    content = changelog.read_text(encoding="utf-8")
    assert "Phase 5" in content, "CHANGELOG.md should contain 'Phase 5'"


def test_meta_files_env_example():
    env_example = PROJECT_ROOT / ".env.example"
    assert env_example.is_file(), ".env.example not found"
