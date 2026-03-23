"""Tests for ScanRequest validation with target_url support."""

import pytest
from pydantic import ValidationError

from scanner.api.schemas import ScanRequest


class TestScanRequestTargetUrl:
    """ScanRequest validation for DAST target_url field."""

    def test_target_url_only(self):
        """ScanRequest(target_url="http://example.com") is valid."""
        req = ScanRequest(target_url="http://example.com")
        assert req.target_url == "http://example.com"
        assert req.path is None
        assert req.repo_url is None

    def test_target_url_with_path_rejected(self):
        """target_url + path raises ValueError containing 'target_url cannot be combined'."""
        with pytest.raises(ValidationError, match="target_url cannot be combined"):
            ScanRequest(target_url="http://example.com", path="/code")

    def test_target_url_with_repo_url_rejected(self):
        """target_url + repo_url raises ValueError containing 'target_url cannot be combined'."""
        with pytest.raises(ValidationError, match="target_url cannot be combined"):
            ScanRequest(target_url="http://x.com", repo_url="http://git.com/r")

    def test_path_only_still_works(self):
        """ScanRequest(path="/code") is valid (backward compat)."""
        req = ScanRequest(path="/code")
        assert req.path == "/code"
        assert req.target_url is None

    def test_repo_url_only_still_works(self):
        """ScanRequest(repo_url="http://git.com/r") is valid."""
        req = ScanRequest(repo_url="http://git.com/r")
        assert req.repo_url == "http://git.com/r"
        assert req.target_url is None

    def test_nothing_provided_error(self):
        """ScanRequest() raises ValueError containing 'target_url'."""
        with pytest.raises(ValidationError, match="target_url"):
            ScanRequest()

    def test_target_url_with_skip_ai(self):
        """ScanRequest(target_url="http://example.com", skip_ai=True) is valid."""
        req = ScanRequest(target_url="http://example.com", skip_ai=True)
        assert req.target_url == "http://example.com"
        assert req.skip_ai is True
