"""Shared test fixtures for Phase 01: Foundation and Data Models."""

import os
import pytest


@pytest.fixture()
def tmp_config_file(tmp_path):
    """Write a temporary config.yml and return its path."""
    config_content = """\
host: "127.0.0.1"
port: 9000
db_path: "/tmp/test.db"
api_key: ""
claude_api_key: ""
slack_webhook_url: ""
email_smtp_host: ""
log_level: "debug"
scan_timeout: 300
"""
    config_file = tmp_path / "config.yml"
    config_file.write_text(config_content)
    return str(config_file)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Clear all SCANNER_* environment variables before each test."""
    for key in list(os.environ.keys()):
        if key.startswith("SCANNER_"):
            monkeypatch.delenv(key, raising=False)
    # Point config path to a non-existent file so YAML loading is skipped
    # unless a test explicitly sets it
    monkeypatch.setenv("SCANNER_CONFIG_PATH", "/tmp/nonexistent_config.yml")
