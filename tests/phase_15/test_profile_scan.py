"""Tests for profile-aware scan triggering and orchestrator override."""

import pytest
import yaml

from tests.phase_15.conftest import get_admin_token


pytestmark = pytest.mark.anyio


class TestProfileScanTrigger:
    """POST /api/scans with profile field."""

    async def test_trigger_scan_with_valid_profile(self, auth_client, config_path):
        """ScanRequest with valid profile name creates scan with profile_name set."""
        token = await get_admin_token(auth_client)

        resp = await auth_client.post(
            "/api/scans",
            json={"path": "/tmp/test-project", "profile": "quick_scan"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 202
        scan_id = resp.json()["id"]

        # Check the DB record has profile_name
        resp = await auth_client.get(
            f"/api/scans/{scan_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["profile_name"] == "quick_scan"

    async def test_trigger_scan_with_unknown_profile_returns_400(self, auth_client):
        """ScanRequest with unknown profile name returns 400."""
        token = await get_admin_token(auth_client)

        resp = await auth_client.post(
            "/api/scans",
            json={"path": "/tmp/test-project", "profile": "nonexistent_profile"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400
        assert "nonexistent_profile" in resp.json()["detail"]

    async def test_trigger_scan_without_profile(self, auth_client):
        """ScanRequest without profile sets profile_name to None."""
        token = await get_admin_token(auth_client)

        resp = await auth_client.post(
            "/api/scans",
            json={"path": "/tmp/test-project"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 202
        scan_id = resp.json()["id"]

        resp = await auth_client.get(
            f"/api/scans/{scan_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["profile_name"] is None


class TestOrchestratorProfileOverride:
    """Unit tests for profile override in run_scan."""

    async def test_profile_filters_scanners(self):
        """Profile override builds filtered settings with only profile's scanners."""
        from scanner.config import (
            ScannerSettings,
            ScannerToolConfig,
            ScanProfileConfig,
            ScanProfileScannerConfig,
        )

        settings = ScannerSettings(
            scanners={
                "semgrep": ScannerToolConfig(
                    enabled="auto",
                    timeout=180,
                    adapter_class="scanner.adapters.semgrep.SemgrepAdapter",
                    languages=["python"],
                ),
                "gitleaks": ScannerToolConfig(
                    enabled=True,
                    timeout=120,
                    adapter_class="scanner.adapters.gitleaks.GitleaksAdapter",
                    languages=[],
                ),
            },
            profiles={
                "quick": ScanProfileConfig(
                    description="Quick scan",
                    scanners={
                        "semgrep": ScanProfileScannerConfig(timeout=60),
                    },
                ),
            },
        )

        # Apply profile override manually (same logic as orchestrator)
        profile = settings.profiles["quick"]
        filtered = {}
        for scanner_name, profile_scanner in profile.scanners.items():
            base = settings.scanners.get(scanner_name)
            if base is None:
                continue
            merged = ScannerToolConfig(
                adapter_class=base.adapter_class,
                languages=base.languages,
                enabled=True,
                timeout=profile_scanner.timeout if profile_scanner.timeout is not None else base.timeout,
                extra_args=profile_scanner.extra_args if profile_scanner.extra_args is not None else base.extra_args,
            )
            filtered[scanner_name] = merged

        new_settings = settings.model_copy(update={"scanners": filtered})

        # Only semgrep should be in filtered settings
        assert "semgrep" in new_settings.scanners
        assert "gitleaks" not in new_settings.scanners
        # Timeout overridden from profile
        assert new_settings.scanners["semgrep"].timeout == 60

    async def test_profile_timeout_fallback(self):
        """Profile with timeout=None falls back to base scanner timeout."""
        from scanner.config import (
            ScannerToolConfig,
            ScanProfileScannerConfig,
        )

        base = ScannerToolConfig(
            enabled="auto",
            timeout=180,
            adapter_class="scanner.adapters.semgrep.SemgrepAdapter",
            languages=["python"],
        )
        profile_scanner = ScanProfileScannerConfig()  # timeout=None

        merged_timeout = profile_scanner.timeout if profile_scanner.timeout is not None else base.timeout
        assert merged_timeout == 180

    async def test_unknown_profile_raises_valueerror(self):
        """run_scan with unknown profile_name raises ValueError."""
        from scanner.config import ScannerSettings, ScannerToolConfig
        from scanner.core.orchestrator import run_scan

        settings = ScannerSettings(
            scanners={
                "semgrep": ScannerToolConfig(
                    enabled="auto",
                    timeout=180,
                    adapter_class="scanner.adapters.semgrep.SemgrepAdapter",
                ),
            },
            profiles={},
        )

        with pytest.raises(ValueError, match="not found"):
            await run_scan(
                settings,
                target_path="/tmp/test",
                profile_name="nonexistent",
                persist=False,
                skip_ai=True,
            )

    async def test_dast_profile_without_nuclei_raises_error(self):
        """DAST scan with profile that lacks nuclei raises ValueError."""
        from scanner.config import (
            ScannerSettings,
            ScannerToolConfig,
            ScanProfileConfig,
            ScanProfileScannerConfig,
        )
        from scanner.core.orchestrator import run_scan

        settings = ScannerSettings(
            scanners={
                "semgrep": ScannerToolConfig(
                    enabled="auto",
                    timeout=180,
                    adapter_class="scanner.adapters.semgrep.SemgrepAdapter",
                ),
                "nuclei": ScannerToolConfig(
                    enabled=True,
                    timeout=300,
                    adapter_class="scanner.adapters.nuclei.NucleiAdapter",
                ),
            },
            profiles={
                "sast_only": ScanProfileConfig(
                    description="No nuclei",
                    scanners={
                        "semgrep": ScanProfileScannerConfig(),
                    },
                ),
            },
        )

        with pytest.raises(ValueError, match="nuclei"):
            await run_scan(
                settings,
                target_url="http://example.com",
                profile_name="sast_only",
                persist=False,
                skip_ai=True,
            )
