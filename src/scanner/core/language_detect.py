"""Auto-detect project languages to determine which scanners to enable."""

from pathlib import Path

_SKIP_DIRS = frozenset({
    ".venv", "venv", "node_modules", ".git", "__pycache__",
    "vendor", "dist", "build", ".tox", ".mypy_cache",
})

# Map file extensions to language tags
_EXT_TO_LANG: dict[str, str] = {
    # Python
    ".py": "python",
    # PHP
    ".php": "php",
    # C/C++
    ".c": "cpp", ".cpp": "cpp", ".cc": "cpp", ".cxx": "cpp",
    ".h": "cpp", ".hpp": "cpp", ".hxx": "cpp",
    # JavaScript/TypeScript
    ".js": "javascript", ".jsx": "javascript",
    ".ts": "typescript", ".tsx": "typescript",
    # Go
    ".go": "go",
    # Rust
    ".rs": "rust",
    # Java/Kotlin
    ".java": "java", ".kt": "kotlin",
    # C#
    ".cs": "csharp",
    # Ruby
    ".rb": "ruby",
    # Infrastructure
    ".yml": "yaml", ".yaml": "yaml",
    ".tf": "terraform",
    ".dockerfile": "docker",
}

# Special file markers
_MARKER_FILES: dict[str, set[str]] = {
    "artisan": {"laravel"},
    "composer.json": {"php"},
    "composer.lock": {"php"},
    "package.json": {"javascript"},
    "Cargo.toml": {"rust"},
    "go.mod": {"go"},
    "Gemfile": {"ruby"},
    "Dockerfile": {"docker"},
    "docker-compose.yml": {"docker"},
    "docker-compose.yaml": {"docker"},
    "Jenkinsfile": {"ci"},
    ".gitlab-ci.yml": {"ci"},
    "Makefile": {"make"},
}


def detect_languages(target_path: str, max_files: int = 5000) -> set[str]:
    """Scan target directory and return a set of detected language tags.

    Skips common non-source directories (.venv, node_modules, vendor, etc.).
    Stops after max_files to avoid hanging on huge repos.
    """
    languages: set[str] = set()
    count = 0

    root = Path(target_path)

    # Check marker files first (fast)
    for marker, langs in _MARKER_FILES.items():
        if (root / marker).exists():
            languages.update(langs)

    # Check for Laravel specifically
    if (root / "artisan").exists() and (root / "composer.json").exists():
        languages.add("laravel")

    # Scan file extensions
    for p in root.rglob("*"):
        if count >= max_files:
            break
        if any(part in _SKIP_DIRS for part in p.parts):
            continue
        if p.is_file():
            count += 1
            lang = _EXT_TO_LANG.get(p.suffix.lower())
            if lang:
                languages.add(lang)

    # Dockerfile special case (no extension)
    if (root / "Dockerfile").exists():
        languages.add("docker")

    return languages


def should_enable_scanner(
    tool_name: str,
    scanner_languages: list[str],
    detected_languages: set[str],
) -> bool:
    """Determine if a scanner should run based on detected languages.

    Universal scanners (empty languages list) always run.
    """
    if not scanner_languages:
        return True
    return bool(set(scanner_languages) & detected_languages)
