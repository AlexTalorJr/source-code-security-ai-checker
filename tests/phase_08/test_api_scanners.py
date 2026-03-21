"""Tests for GET /api/scanners endpoint."""

from unittest.mock import MagicMock

import httpx
import pytest
from fastapi import FastAPI

from scanner.api.scanners import router
from scanner.config import ScannerToolConfig


def _create_test_app(scanners: dict[str, ScannerToolConfig]) -> FastAPI:
    """Create a minimal FastAPI app with mocked settings for testing."""
    app = FastAPI()
    app.include_router(router)

    mock_settings = MagicMock()
    mock_settings.scanners = scanners
    app.state.settings = mock_settings

    return app


@pytest.fixture
def scanners_config():
    """Provide a test scanner config with various states."""
    return {
        "semgrep": ScannerToolConfig(
            adapter_class="scanner.adapters.semgrep.SemgrepAdapter",
            enabled=True,
            languages=["python", "javascript"],
        ),
        "bad_scanner": ScannerToolConfig(
            adapter_class="scanner.adapters.nonexistent.BadAdapter",
            enabled=True,
        ),
        "disabled_tool": ScannerToolConfig(
            adapter_class="scanner.adapters.semgrep.SemgrepAdapter",
            enabled=False,
        ),
    }


async def test_list_scanners_returns_200(scanners_config):
    """GET /api/scanners returns 200 with a JSON list."""
    app = _create_test_app(scanners_config)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/scanners")

    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 3


async def test_enabled_scanner_status(scanners_config):
    """An enabled scanner with no errors shows status='enabled'."""
    app = _create_test_app(scanners_config)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/scanners")

    data = resp.json()
    semgrep = next(s for s in data if s["name"] == "semgrep")
    assert semgrep["status"] == "enabled"
    assert semgrep["enabled"] is True
    assert semgrep["languages"] == ["python", "javascript"]
    assert semgrep["load_error"] is None


async def test_load_error_in_api(scanners_config):
    """A scanner with a load error shows status='load_error' and error message."""
    app = _create_test_app(scanners_config)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/scanners")

    data = resp.json()
    bad = next(s for s in data if s["name"] == "bad_scanner")
    assert bad["status"] == "load_error"
    assert bad["load_error"] is not None
    assert "nonexistent" in bad["load_error"].lower() or "import" in bad["load_error"].lower() or "failed" in bad["load_error"].lower()


async def test_disabled_scanner_status(scanners_config):
    """A disabled scanner shows status='disabled'."""
    app = _create_test_app(scanners_config)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/scanners")

    data = resp.json()
    disabled = next(s for s in data if s["name"] == "disabled_tool")
    assert disabled["status"] == "disabled"
    assert disabled["enabled"] is False


async def test_scanner_response_keys(scanners_config):
    """Each scanner object has the required keys."""
    app = _create_test_app(scanners_config)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/scanners")

    data = resp.json()
    required_keys = {"name", "status", "enabled", "languages", "load_error"}
    for scanner in data:
        assert required_keys <= set(scanner.keys())
