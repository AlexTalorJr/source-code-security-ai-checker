"""Tests for deterministic fingerprint computation."""

import pytest


class TestFingerprint:
    """Fingerprint module tests for deduplication hashing."""

    def test_basic_fingerprint(self):
        from scanner.core.fingerprint import compute_fingerprint

        result = compute_fingerprint(
            "src/auth.py",
            "sql-injection",
            "query = f'SELECT * FROM users WHERE id={user_id}'",
        )
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 hex digest

    def test_deterministic(self):
        from scanner.core.fingerprint import compute_fingerprint

        fp1 = compute_fingerprint("src/auth.py", "sql-injection", "query = 'SELECT 1'")
        fp2 = compute_fingerprint("src/auth.py", "sql-injection", "query = 'SELECT 1'")
        assert fp1 == fp2

    def test_path_normalization(self):
        from scanner.core.fingerprint import compute_fingerprint

        fp1 = compute_fingerprint(".\\src\\auth.py", "sql-injection", "code")
        fp2 = compute_fingerprint("src/auth.py", "sql-injection", "code")
        assert fp1 == fp2

    def test_whitespace_normalization(self):
        from scanner.core.fingerprint import compute_fingerprint

        fp1 = compute_fingerprint("file.py", "rule-1", "x  =  1")
        fp2 = compute_fingerprint("file.py", "rule-1", "x = 1")
        assert fp1 == fp2

    def test_rule_case_normalization(self):
        from scanner.core.fingerprint import compute_fingerprint

        fp1 = compute_fingerprint("file.py", "SQL-Injection", "code")
        fp2 = compute_fingerprint("file.py", "sql-injection", "code")
        assert fp1 == fp2

    def test_different_rules_differ(self):
        from scanner.core.fingerprint import compute_fingerprint

        fp1 = compute_fingerprint("file.py", "rule-a", "code")
        fp2 = compute_fingerprint("file.py", "rule-b", "code")
        assert fp1 != fp2

    def test_different_files_differ(self):
        from scanner.core.fingerprint import compute_fingerprint

        fp1 = compute_fingerprint("file1.py", "rule-1", "code")
        fp2 = compute_fingerprint("file2.py", "rule-1", "code")
        assert fp1 != fp2

    def test_different_snippets_differ(self):
        from scanner.core.fingerprint import compute_fingerprint

        fp1 = compute_fingerprint("file.py", "rule-1", "snippet_a")
        fp2 = compute_fingerprint("file.py", "rule-1", "snippet_b")
        assert fp1 != fp2

    def test_empty_snippet(self):
        from scanner.core.fingerprint import compute_fingerprint

        result = compute_fingerprint("file.py", "rule-1", "")
        assert isinstance(result, str)
        assert len(result) == 64

    def test_unicode_snippet(self):
        from scanner.core.fingerprint import compute_fingerprint

        result = compute_fingerprint("file.py", "rule-1", "var x = '\u2603\u2764\ufe0f\U0001f600'")
        assert isinstance(result, str)
        assert len(result) == 64
