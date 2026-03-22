"""Phase 10 test fixtures."""
import pathlib
import pytest

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent

ALL_SCANNER_NAMES = [
    "Semgrep", "Cppcheck", "Gitleaks", "Trivy", "Checkov",
    "Psalm", "Enlightn", "PHP Security Checker",
    "gosec", "Bandit", "Brakeman", "cargo-audit",
]

LANGUAGES = ["en", "ru", "fr", "es", "it"]

DOC_FILES = [
    "admin-guide.md", "api.md", "architecture.md", "custom-rules.md",
    "database-schema.md", "devops-guide.md", "transfer-guide.md", "user-guide.md",
]

@pytest.fixture
def docs_root():
    return PROJECT_ROOT / "docs"

@pytest.fixture
def all_doc_paths(docs_root):
    paths = []
    for lang in LANGUAGES:
        for doc in DOC_FILES:
            p = docs_root / lang / doc
            if p.exists():
                paths.append(p)
    return paths
