import os

import pytest

LANGUAGES = ["en", "ru", "fr", "es", "it"]
DOC_FILES = ["admin-guide.md", "user-guide.md", "api.md"]
DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "docs")


def test_all_doc_files_exist():
    for lang in LANGUAGES:
        for doc in DOC_FILES:
            path = os.path.join(DOCS_DIR, lang, doc)
            assert os.path.exists(path), f"Missing: docs/{lang}/{doc}"


def test_admin_guide_sections():
    """Verify admin guides contain RBAC, tokens, scanner config, scan profiles, DAST content.

    For non-English docs, we check for universal markers (URLs, code terms)
    rather than English prose headings.
    """
    for lang in LANGUAGES:
        path = os.path.join(DOCS_DIR, lang, "admin-guide.md")
        content = open(path).read()
        # RBAC - universal term used in all languages
        assert "rbac" in content.lower(), (
            f"docs/{lang}/admin-guide.md missing RBAC content"
        )
        # Tokens - check for nvsec_ prefix (universal) or "token" (universal term)
        assert "token" in content.lower(), (
            f"docs/{lang}/admin-guide.md missing token content"
        )
        # Scanner Configuration UI - check for dashboard URL
        assert "/dashboard/scanners" in content, (
            f"docs/{lang}/admin-guide.md missing scanner configuration UI content"
        )
        # Scan Profiles - check for profiles YAML example (present in all languages)
        assert "profiles:" in content or "quick_scan" in content, (
            f"docs/{lang}/admin-guide.md missing scan profiles content"
        )
        # DAST - universal term
        assert "dast" in content.lower(), (
            f"docs/{lang}/admin-guide.md missing DAST content"
        )


def test_user_guide_sections():
    """Verify user guides contain login, profiles, and DAST content."""
    for lang in LANGUAGES:
        path = os.path.join(DOCS_DIR, lang, "user-guide.md")
        content = open(path).read()
        # Login - check for dashboard URL
        assert "/dashboard/login" in content or "login" in content.lower(), (
            f"docs/{lang}/user-guide.md missing login content"
        )
        # Profiles - check for profile API example
        assert "profile" in content.lower(), (
            f"docs/{lang}/user-guide.md missing profile content"
        )
        # DAST - universal term
        assert "dast" in content.lower(), (
            f"docs/{lang}/user-guide.md missing DAST content"
        )


def test_api_uses_bearer_auth():
    for lang in LANGUAGES:
        path = os.path.join(DOCS_DIR, lang, "api.md")
        content = open(path).read()
        assert "Bearer" in content, f"docs/{lang}/api.md missing Bearer auth"
        assert "X-API-Key" not in content, (
            f"docs/{lang}/api.md still references deprecated X-API-Key"
        )


def test_api_has_profile_endpoints():
    for lang in LANGUAGES:
        path = os.path.join(DOCS_DIR, lang, "api.md")
        content = open(path).read()
        assert "profiles" in content.lower(), (
            f"docs/{lang}/api.md missing profile endpoints"
        )


def test_api_has_config_endpoints():
    for lang in LANGUAGES:
        path = os.path.join(DOCS_DIR, lang, "api.md")
        content = open(path).read()
        assert "/api/config" in content, (
            f"docs/{lang}/api.md missing config endpoints"
        )
