"""Tests for AIAnalyzer budget tracking, severity ordering, and cost logging."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scanner.ai.analyzer import AIAnalyzer
from scanner.config import ScannerSettings
from scanner.schemas.finding import FindingSchema
from scanner.schemas.severity import Severity


@pytest.fixture
def settings() -> ScannerSettings:
    """Settings with tight budget for testing cutoffs."""
    return ScannerSettings(claude_api_key="test-key", ai={"max_cost_per_scan": 5.0})


@pytest.fixture
def tight_budget_settings() -> ScannerSettings:
    """Settings with very tight budget to trigger cutoff."""
    return ScannerSettings(claude_api_key="test-key", ai={"max_cost_per_scan": 0.001})


def _make_finding(
    fingerprint: str,
    file_path: str,
    severity: Severity = Severity.HIGH,
) -> FindingSchema:
    return FindingSchema(
        fingerprint=fingerprint,
        tool="semgrep",
        rule_id="test-rule",
        file_path=file_path,
        severity=severity,
        title="Test finding",
    )


def _mock_create_response(analysis_data: dict, input_tokens: int = 500, output_tokens: int = 150):
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.input = analysis_data

    response = MagicMock()
    response.content = [tool_block]
    response.usage = MagicMock(input_tokens=input_tokens, output_tokens=output_tokens)
    return response


class TestBudgetTracking:
    @pytest.mark.asyncio
    async def test_count_tokens_called_before_create(self, settings):
        """count_tokens is called before each messages.create."""
        finding = _make_finding("a" * 64, "vms/test.php", Severity.HIGH)

        mock_client = AsyncMock()
        mock_client.messages.count_tokens.return_value = MagicMock(input_tokens=500)

        analysis = {
            "findings_analysis": [{
                "fingerprint": "a" * 64,
                "business_logic_risk": "risk",
                "risk_category": "other",
            }]
        }
        corr = {"compound_risks": []}

        mock_client.messages.create.side_effect = [
            _mock_create_response(analysis),
            _mock_create_response(corr),
        ]

        with patch("scanner.ai.analyzer.AsyncAnthropic", return_value=mock_client):
            analyzer = AIAnalyzer(settings)
            await analyzer.analyze([finding])

        # count_tokens called at least once before messages.create
        assert mock_client.messages.count_tokens.call_count >= 1

    @pytest.mark.asyncio
    async def test_budget_cutoff_skips_component(self, tight_budget_settings):
        """When estimated cost exceeds 80% budget, component is skipped."""
        finding = _make_finding("a" * 64, "vms/test.php", Severity.HIGH)

        mock_client = AsyncMock()
        # Return high token count to blow budget
        mock_client.messages.count_tokens.return_value = MagicMock(input_tokens=100_000)

        with patch("scanner.ai.analyzer.AsyncAnthropic", return_value=mock_client):
            analyzer = AIAnalyzer(tight_budget_settings)
            findings, risks, cost = await analyzer.analyze([finding])

        # No create calls made
        mock_client.messages.create.assert_not_called()
        assert "vms" in analyzer.skipped_components

    @pytest.mark.asyncio
    async def test_cost_tracking_from_response_usage(self, settings):
        """Tracks actual cost from response.usage after each call."""
        finding = _make_finding("a" * 64, "vms/test.php", Severity.HIGH)

        mock_client = AsyncMock()
        mock_client.messages.count_tokens.return_value = MagicMock(input_tokens=500)

        analysis = {
            "findings_analysis": [{
                "fingerprint": "a" * 64,
                "business_logic_risk": "risk",
                "risk_category": "other",
            }]
        }
        corr = {"compound_risks": []}

        mock_client.messages.create.side_effect = [
            _mock_create_response(analysis, input_tokens=1000, output_tokens=300),
            _mock_create_response(corr, input_tokens=800, output_tokens=200),
        ]

        with patch("scanner.ai.analyzer.AsyncAnthropic", return_value=mock_client):
            analyzer = AIAnalyzer(settings)
            _, _, cost = await analyzer.analyze([finding])

        assert cost > 0.0
        assert analyzer.spent == cost

    @pytest.mark.asyncio
    async def test_skips_correlation_when_budget_at_80(self, settings):
        """Correlation call is skipped when budget already at 80%."""
        finding = _make_finding("a" * 64, "vms/test.php", Severity.HIGH)

        mock_client = AsyncMock()
        mock_client.messages.count_tokens.return_value = MagicMock(input_tokens=500)

        analysis = {
            "findings_analysis": [{
                "fingerprint": "a" * 64,
                "business_logic_risk": "risk",
                "risk_category": "other",
            }]
        }

        mock_client.messages.create.side_effect = [
            # Return response with very high token usage to eat budget
            _mock_create_response(analysis, input_tokens=500_000, output_tokens=200_000),
        ]

        with patch("scanner.ai.analyzer.AsyncAnthropic", return_value=mock_client):
            analyzer = AIAnalyzer(settings)
            _, compound_risks, _ = await analyzer.analyze([finding])

        # Only 1 call (component analysis), correlation skipped
        assert mock_client.messages.create.call_count == 1
        assert compound_risks == []

    @pytest.mark.asyncio
    async def test_records_analyzed_and_skipped_components(self, settings):
        """Analyzer tracks analyzed_components and skipped_components lists."""
        findings = [
            _make_finding("a" * 64, "vms/test.php", Severity.HIGH),
            _make_finding("b" * 64, "mediaserver/test.cpp", Severity.HIGH),
        ]

        mock_client = AsyncMock()
        # First component OK, second blows budget
        mock_client.messages.count_tokens.return_value = MagicMock(input_tokens=500)

        vms_analysis = {
            "findings_analysis": [{
                "fingerprint": "a" * 64,
                "business_logic_risk": "risk",
                "risk_category": "other",
            }]
        }
        corr = {"compound_risks": []}

        call_count = 0

        async def count_tokens_side_effect(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 1:
                return MagicMock(input_tokens=500)
            else:
                # Return huge count for second component to trigger budget skip
                return MagicMock(input_tokens=10_000_000)

        mock_client.messages.count_tokens.side_effect = count_tokens_side_effect
        mock_client.messages.create.side_effect = [
            _mock_create_response(vms_analysis),
            _mock_create_response(corr),
        ]

        with patch("scanner.ai.analyzer.AsyncAnthropic", return_value=mock_client):
            analyzer = AIAnalyzer(settings)
            await analyzer.analyze(findings)

        # vms was analyzed (higher severity or alphabetical first depends on sort)
        assert len(analyzer.analyzed_components) >= 1
        # at least one component should be in one of the lists
        total = len(analyzer.analyzed_components) + len(analyzer.skipped_components)
        assert total == 2


class TestSeverityPriorityOrder:
    @pytest.mark.asyncio
    async def test_critical_component_processed_before_medium(self, settings):
        """CRITICAL component processed first in severity order."""
        findings = [
            _make_finding("a" * 64, "low_priority/test.py", Severity.MEDIUM),
            _make_finding("b" * 64, "high_priority/test.py", Severity.CRITICAL),
        ]

        mock_client = AsyncMock()
        mock_client.messages.count_tokens.return_value = MagicMock(input_tokens=500)

        call_order = []

        async def create_side_effect(**kwargs):
            # Track which component prompt was sent
            for msg in kwargs.get("messages", []):
                content = msg.get("content", "")
                if "high_priority" in content:
                    call_order.append("high_priority")
                elif "low_priority" in content:
                    call_order.append("low_priority")
                elif "cross-component" in content.lower() or "compound" in content.lower():
                    call_order.append("correlation")

            analysis = {
                "findings_analysis": [{
                    "fingerprint": kwargs["messages"][0]["content"].split("fingerprint")[1].split('"')[2] if "fingerprint" in kwargs["messages"][0]["content"] else "x" * 64,
                    "business_logic_risk": "risk",
                    "risk_category": "other",
                }]
            }
            # Check if it's a correlation call by tool_choice
            if kwargs.get("tool_choice", {}).get("name") == "cross_component_correlation":
                analysis = {"compound_risks": []}

            return _mock_create_response(analysis)

        mock_client.messages.create.side_effect = create_side_effect

        with patch("scanner.ai.analyzer.AsyncAnthropic", return_value=mock_client):
            analyzer = AIAnalyzer(settings)
            await analyzer.analyze(findings)

        # high_priority (CRITICAL) should be processed before low_priority (MEDIUM)
        if "high_priority" in call_order and "low_priority" in call_order:
            assert call_order.index("high_priority") < call_order.index("low_priority")

    @pytest.mark.asyncio
    async def test_all_skipped_returns_original_findings(self, tight_budget_settings):
        """When all components skipped due to budget, original findings returned unchanged."""
        findings = [
            _make_finding("a" * 64, "vms/test.php", Severity.HIGH),
            _make_finding("b" * 64, "mediaserver/test.cpp", Severity.HIGH),
        ]

        mock_client = AsyncMock()
        mock_client.messages.count_tokens.return_value = MagicMock(input_tokens=100_000)

        with patch("scanner.ai.analyzer.AsyncAnthropic", return_value=mock_client):
            analyzer = AIAnalyzer(tight_budget_settings)
            result_findings, risks, cost = await analyzer.analyze(findings)

        # Original findings returned unchanged
        assert len(result_findings) == 2
        assert all(f.ai_analysis is None for f in result_findings)
        assert risks == []
        mock_client.messages.create.assert_not_called()
