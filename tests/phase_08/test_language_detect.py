"""Tests for config-driven language detection (no hard-coded SCANNER_LANGUAGES)."""

from pathlib import Path

from scanner.core.language_detect import detect_languages, should_enable_scanner


def test_universal_scanner_always_runs():
    """Scanner with empty languages list (universal) always runs."""
    assert should_enable_scanner("gitleaks", [], {"python"}) is True


def test_scanner_disabled_when_languages_dont_match():
    """Scanner whose languages don't intersect with detected should not run."""
    assert should_enable_scanner("psalm", ["php"], {"python"}) is False


def test_scanner_enabled_when_languages_match():
    """Scanner should run when its languages intersect with detected."""
    assert should_enable_scanner("semgrep", ["python", "php"], {"python"}) is True


def test_universal_scanner_with_no_detected_languages():
    """Universal scanner still runs even if no languages detected."""
    assert should_enable_scanner("test", [], set()) is True


def test_detect_languages_finds_python(tmp_path: Path):
    """detect_languages on a dir with a .py file returns 'python'."""
    (tmp_path / "app.py").write_text("print('hello')")
    langs = detect_languages(str(tmp_path))
    assert "python" in langs
