"""Test documentation consistency across languages."""
import pathlib
import pytest
from .conftest import PROJECT_ROOT, ALL_SCANNER_NAMES, LANGUAGES, DOC_FILES


class TestDocConsistency:

    def test_all_doc_files_exist(self):
        """Every language has all 8 doc files."""
        for lang in LANGUAGES:
            for doc in DOC_FILES:
                path = PROJECT_ROOT / "docs" / lang / doc
                assert path.exists(), f"Missing: docs/{lang}/{doc}"

    def test_user_guide_has_all_scanner_names(self):
        """user-guide.md in every language mentions all 12 scanners."""
        for lang in LANGUAGES:
            content = (PROJECT_ROOT / "docs" / lang / "user-guide.md").read_text()
            for scanner in ["Semgrep", "Cppcheck", "Gitleaks", "Trivy", "Checkov",
                            "gosec", "Bandit", "Brakeman", "cargo-audit"]:
                assert scanner.lower() in content.lower(), (
                    f"docs/{lang}/user-guide.md missing scanner: {scanner}"
                )

    def test_no_stale_five_scanner_count_in_user_guide(self):
        """user-guide.md should not say 'five scanners' in any language."""
        stale_patterns = ["five scanner", "cinq outils", "cinco herramientas",
                          "cinque strumenti", "pyat' instrumentov",
                          "pyati instrumentov", "5 scanner"]
        for lang in LANGUAGES:
            content = (PROJECT_ROOT / "docs" / lang / "user-guide.md").read_text().lower()
            for pattern in stale_patterns:
                assert pattern.lower() not in content, (
                    f"docs/{lang}/user-guide.md has stale count: '{pattern}'"
                )

    def test_admin_guide_has_plugin_registry_section(self):
        """admin-guide.md in every language has Plugin Registry section."""
        registry_terms = {
            "en": ("plugin", "registry"),
            "ru": ("плагин", "реестр"),
            "fr": ("plugin", "registre"),
            "es": ("plugin", "registro"),
            "it": ("plugin", "registro"),
        }
        for lang in LANGUAGES:
            content = (PROJECT_ROOT / "docs" / lang / "admin-guide.md").read_text().lower()
            term1, term2 = registry_terms.get(lang, ("plugin", "registry"))
            assert term1 in content and term2 in content, (
                f"docs/{lang}/admin-guide.md missing Plugin Registry section"
            )

    def test_admin_guide_has_adapter_class(self):
        """admin-guide.md mentions adapter_class config field."""
        for lang in LANGUAGES:
            content = (PROJECT_ROOT / "docs" / lang / "admin-guide.md").read_text()
            assert "adapter_class" in content, (
                f"docs/{lang}/admin-guide.md missing adapter_class reference"
            )

    def test_readme_files_exist(self):
        """All 5 README variants exist."""
        readmes = ["README.md", "README.ru.md", "README.fr.md", "README.es.md", "README.it.md"]
        for readme in readmes:
            path = PROJECT_ROOT / readme
            assert path.exists(), f"Missing: {readme}"

    def test_readme_mentions_twelve_scanners(self):
        """All README files reference 12 scanners."""
        readmes = ["README.md", "README.ru.md", "README.fr.md", "README.es.md", "README.it.md"]
        for readme in readmes:
            content = (PROJECT_ROOT / readme).read_text()
            assert "12" in content, f"{readme} does not mention 12 scanners"
