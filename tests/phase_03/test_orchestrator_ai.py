"""Tests for AI integration in the scan orchestrator."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scanner.ai.schemas import AIAnalysisResult
from scanner.config import ScannerSettings
from scanner.schemas.compound_risk import CompoundRiskSchema
from scanner.schemas.finding import FindingSchema
from scanner.schemas.severity import Severity

# Import CompoundRisk model so SQLAlchemy mapper can resolve the relationship
import scanner.models.compound_risk  # noqa: F401


def _make_settings(**overrides) -> ScannerSettings:
    defaults = {
        "db_path": ":memory:",
        "claude_api_key": "sk-test",
    }
    defaults.update(overrides)
    return ScannerSettings(**defaults)


def _make_finding(
    fingerprint: str = "a" * 64,
    severity: Severity = Severity.HIGH,
    ai_analysis: str | None = None,
    ai_fix_suggestion: str | None = None,
) -> FindingSchema:
    return FindingSchema(
        fingerprint=fingerprint,
        tool="semgrep",
        rule_id="test-rule",
        file_path="src/app.py",
        line_start=1,
        severity=severity,
        title="Test finding",
        ai_analysis=ai_analysis,
        ai_fix_suggestion=ai_fix_suggestion,
    )


def _setup_db_mocks(mock_engine, mock_sf):
    """Create and wire up DB mock objects. Returns (mock_db_scan,)."""
    mock_conn = AsyncMock()
    mock_engine_inst = MagicMock()
    mock_engine.return_value = mock_engine_inst
    mock_engine_inst.begin = MagicMock(return_value=mock_conn)
    mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_conn.__aexit__ = AsyncMock(return_value=False)
    mock_conn.run_sync = AsyncMock()

    mock_session = AsyncMock()
    mock_session_ctx = AsyncMock()
    mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_ctx.__aexit__ = AsyncMock(return_value=False)

    mock_begin_ctx = AsyncMock()
    mock_begin_ctx.__aenter__ = AsyncMock(return_value=None)
    mock_begin_ctx.__aexit__ = AsyncMock(return_value=False)
    mock_session.begin = MagicMock(return_value=mock_begin_ctx)

    mock_db_scan = MagicMock()
    mock_db_scan.id = 1
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.execute = AsyncMock()

    mock_sf.return_value = MagicMock(return_value=mock_session_ctx)
    mock_engine_inst.dispose = AsyncMock()

    return mock_db_scan


@pytest.mark.asyncio
async def test_ai_enrichment_in_orchestrator():
    """run_scan calls enrich_with_ai after deduplicate_findings."""
    settings = _make_settings()
    enriched_finding = _make_finding(ai_analysis="Risk analysis here")
    ai_result = AIAnalysisResult(cost_usd=0.005)

    with (
        patch(
            "scanner.core.orchestrator.enrich_with_ai",
            new_callable=AsyncMock,
            return_value=([enriched_finding], [], ai_result),
        ) as mock_enrich,
        patch(
            "scanner.core.orchestrator.asyncio.gather",
            new_callable=AsyncMock,
            return_value=[("semgrep", [_make_finding()])],
        ),
        patch("scanner.core.orchestrator.create_engine") as mock_engine,
        patch("scanner.core.orchestrator.create_session_factory") as mock_sf,
    ):
        mock_db_scan = _setup_db_mocks(mock_engine, mock_sf)

        from scanner.core.orchestrator import run_scan

        result = await run_scan(settings, target_path="/tmp/test")

        mock_enrich.assert_called_once()
        assert result.ai_cost_usd == 0.005
        assert result.ai_skipped is False


@pytest.mark.asyncio
async def test_ai_skipped_in_scan_result():
    """run_scan sets ai_skipped=True when AI degrades."""
    settings = _make_settings()
    ai_result = AIAnalysisResult(skipped=True, skip_reason="No API key")
    original = _make_finding()

    with (
        patch(
            "scanner.core.orchestrator.enrich_with_ai",
            new_callable=AsyncMock,
            return_value=([original], [], ai_result),
        ),
        patch(
            "scanner.core.orchestrator.asyncio.gather",
            new_callable=AsyncMock,
            return_value=[("semgrep", [original])],
        ),
        patch("scanner.core.orchestrator.create_engine") as mock_engine,
        patch("scanner.core.orchestrator.create_session_factory") as mock_sf,
    ):
        _setup_db_mocks(mock_engine, mock_sf)

        from scanner.core.orchestrator import run_scan

        result = await run_scan(settings, target_path="/tmp/test")

        assert result.ai_skipped is True
        assert result.ai_skip_reason == "No API key"


@pytest.mark.asyncio
async def test_compound_risk_gate_fails_on_critical():
    """Quality gate fails when compound risk has CRITICAL severity even if individual findings are MEDIUM."""
    settings = _make_settings()
    medium_finding = _make_finding(severity=Severity.MEDIUM)
    compound_risk = CompoundRiskSchema(
        title="Critical chain",
        description="Compound risk",
        severity=Severity.CRITICAL.value,
        finding_fingerprints=["a" * 64],
    )
    ai_result = AIAnalysisResult(cost_usd=0.01)

    with (
        patch(
            "scanner.core.orchestrator.enrich_with_ai",
            new_callable=AsyncMock,
            return_value=([medium_finding], [compound_risk], ai_result),
        ),
        patch(
            "scanner.core.orchestrator.asyncio.gather",
            new_callable=AsyncMock,
            return_value=[("semgrep", [medium_finding])],
        ),
        patch("scanner.core.orchestrator.create_engine") as mock_engine,
        patch("scanner.core.orchestrator.create_session_factory") as mock_sf,
    ):
        _setup_db_mocks(mock_engine, mock_sf)

        from scanner.core.orchestrator import run_scan

        result = await run_scan(settings, target_path="/tmp/test")

        assert result.gate_passed is False


@pytest.mark.asyncio
async def test_compound_risk_gate_passes_on_medium():
    """Quality gate passes when compound risks are only MEDIUM severity."""
    settings = _make_settings()
    medium_finding = _make_finding(severity=Severity.MEDIUM)
    compound_risk = CompoundRiskSchema(
        title="Medium chain",
        description="Not critical",
        severity=Severity.MEDIUM.value,
        finding_fingerprints=["a" * 64],
    )
    ai_result = AIAnalysisResult(cost_usd=0.01)

    with (
        patch(
            "scanner.core.orchestrator.enrich_with_ai",
            new_callable=AsyncMock,
            return_value=([medium_finding], [compound_risk], ai_result),
        ),
        patch(
            "scanner.core.orchestrator.asyncio.gather",
            new_callable=AsyncMock,
            return_value=[("semgrep", [medium_finding])],
        ),
        patch("scanner.core.orchestrator.create_engine") as mock_engine,
        patch("scanner.core.orchestrator.create_session_factory") as mock_sf,
    ):
        _setup_db_mocks(mock_engine, mock_sf)

        from scanner.core.orchestrator import run_scan

        result = await run_scan(settings, target_path="/tmp/test")

        assert result.gate_passed is True


@pytest.mark.asyncio
async def test_run_scan_succeeds_when_ai_unavailable():
    """run_scan completes without exception when AI module fails."""
    settings = _make_settings()
    finding = _make_finding()
    ai_result = AIAnalysisResult(
        skipped=True, skip_reason="AI analysis failed: import error"
    )

    with (
        patch(
            "scanner.core.orchestrator.enrich_with_ai",
            new_callable=AsyncMock,
            return_value=([finding], [], ai_result),
        ),
        patch(
            "scanner.core.orchestrator.asyncio.gather",
            new_callable=AsyncMock,
            return_value=[("semgrep", [finding])],
        ),
        patch("scanner.core.orchestrator.create_engine") as mock_engine,
        patch("scanner.core.orchestrator.create_session_factory") as mock_sf,
    ):
        _setup_db_mocks(mock_engine, mock_sf)

        from scanner.core.orchestrator import run_scan

        result = await run_scan(settings, target_path="/tmp/test")

        assert result.status == "completed"
        assert result.ai_skipped is True
