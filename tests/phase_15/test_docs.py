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
    for lang in LANGUAGES:
        path = os.path.join(DOCS_DIR, lang, "admin-guide.md")
        content = open(path).read()
        for section in ["RBAC", "Token", "Scanner Configuration", "Scan Profile", "DAST"]:
            assert section.lower() in content.lower(), (
                f"docs/{lang}/admin-guide.md missing section about '{section}'"
            )


def test_user_guide_sections():
    for lang in LANGUAGES:
        path = os.path.join(DOCS_DIR, lang, "user-guide.md")
        content = open(path).read()
        for keyword in ["login", "profile", "DAST"]:
            assert keyword.lower() in content.lower(), (
                f"docs/{lang}/user-guide.md missing content about '{keyword}'"
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
