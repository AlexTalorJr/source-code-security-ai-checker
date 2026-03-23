"""Tests for orchestrator DAST routing via target_url."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scanner.core.orchestrator import run_scan


@pytest.fixture
def mock_settings():
    """Create mock ScannerSettings with nuclei configured."""
    settings = MagicMock()
    settings.claude_api_key = None
    settings.gate = MagicMock()
    settings.gate.evaluate = MagicMock(return_value=(True, []))
    settings.db_path = ":memory:"
    settings.scanners = {
        "nuclei": MagicMock(
            enabled=True,
            adapter_class="scanner.adapters.nuclei.NucleiAdapter",
            timeout=180,
            extra_args=[],
            languages=[],
        ),
    }
    return settings


class TestDastRouting:
    """Orchestrator routes to NucleiAdapter when target_url is provided."""

    @pytest.mark.asyncio
    async def test_dast_mode_runs_nuclei_only(self, mock_settings):
        """When target_url is provided, only NucleiAdapter runs."""
        mock_adapter = AsyncMock()
        mock_adapter.tool_name = "nuclei"
        mock_adapter.run = AsyncMock(return_value=[])
        mock_adapter.get_version = AsyncMock(return_value="3.0.0")

        mock_entry = MagicMock()
        mock_entry.adapter_class = MagicMock(return_value=mock_adapter)
        mock_entry.timeout = 180
        mock_entry.extra_args = []

        with patch(
            "scanner.core.orchestrator.ScannerRegistry"
        ) as MockRegistry:
            registry_instance = MockRegistry.return_value
            registry_instance.get_scanner_config.return_value = mock_entry
            # get_enabled_adapters should NOT be called in DAST mode
            registry_instance.get_enabled_adapters = MagicMock(
                side_effect=AssertionError("Should not call get_enabled_adapters in DAST mode")
            )

            scan_result, findings, risks = await run_scan(
                mock_settings,
                target_url="http://example.com",
                persist=False,
                skip_ai=True,
            )

        assert scan_result.status == "completed"
        registry_instance.get_scanner_config.assert_called_once_with("nuclei")
        registry_instance.get_enabled_adapters.assert_not_called()

    @pytest.mark.asyncio
    async def test_sast_mode_skips_nuclei(self, mock_settings):
        """When target_path provided (no target_url), standard SAST flow executes."""
        with patch(
            "scanner.core.orchestrator.detect_languages", return_value={"python"}
        ), patch(
            "scanner.core.orchestrator.ScannerRegistry"
        ) as MockRegistry:
            registry_instance = MockRegistry.return_value
            mock_adapter = AsyncMock()
            mock_adapter.tool_name = "bandit"
            mock_adapter.run = AsyncMock(return_value=[])
            mock_adapter.get_version = AsyncMock(return_value="1.0.0")
            registry_instance.get_enabled_adapters.return_value = [mock_adapter]
            mock_settings.scanners["bandit"] = MagicMock(timeout=180, extra_args=[])

            scan_result, findings, risks = await run_scan(
                mock_settings,
                target_path="/code",
                persist=False,
                skip_ai=True,
            )

        assert scan_result.status == "completed"
        registry_instance.get_enabled_adapters.assert_called_once()

    @pytest.mark.asyncio
    async def test_dast_mode_skips_git_clone(self, mock_settings):
        """When target_url provided, clone_repo is never called."""
        mock_adapter = AsyncMock()
        mock_adapter.tool_name = "nuclei"
        mock_adapter.run = AsyncMock(return_value=[])
        mock_adapter.get_version = AsyncMock(return_value="3.0.0")

        mock_entry = MagicMock()
        mock_entry.adapter_class = MagicMock(return_value=mock_adapter)
        mock_entry.timeout = 180
        mock_entry.extra_args = []

        with patch(
            "scanner.core.orchestrator.ScannerRegistry"
        ) as MockRegistry, patch(
            "scanner.core.orchestrator.clone_repo"
        ) as mock_clone:
            registry_instance = MockRegistry.return_value
            registry_instance.get_scanner_config.return_value = mock_entry

            await run_scan(
                mock_settings,
                target_url="http://example.com",
                persist=False,
                skip_ai=True,
            )

        mock_clone.assert_not_called()

    @pytest.mark.asyncio
    async def test_dast_mode_passes_url_to_adapter(self, mock_settings):
        """NucleiAdapter.run() receives the target_url as target_path parameter."""
        mock_adapter = AsyncMock()
        mock_adapter.tool_name = "nuclei"
        mock_adapter.run = AsyncMock(return_value=[])
        mock_adapter.get_version = AsyncMock(return_value="3.0.0")

        mock_entry = MagicMock()
        mock_entry.adapter_class = MagicMock(return_value=mock_adapter)
        mock_entry.timeout = 180
        mock_entry.extra_args = []

        with patch(
            "scanner.core.orchestrator.ScannerRegistry"
        ) as MockRegistry:
            registry_instance = MockRegistry.return_value
            registry_instance.get_scanner_config.return_value = mock_entry

            await run_scan(
                mock_settings,
                target_url="http://example.com",
                persist=False,
                skip_ai=True,
            )

        # _run_adapter passes target_url as target_path to adapter.run()
        mock_adapter.run.assert_called_once()
        call_args = mock_adapter.run.call_args
        assert call_args[0][0] == "http://example.com"
