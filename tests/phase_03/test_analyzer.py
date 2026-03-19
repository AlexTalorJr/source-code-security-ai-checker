"""Tests for AIAnalyzer component analysis, fix suggestions, and correlation."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scanner.ai.analyzer import AIAnalyzer, group_by_component, sort_batches_by_severity
from scanner.ai.schemas import ComponentAnalysisResponse, CorrelationResponse
from scanner.config import ScannerSettings
from scanner.schemas.finding import FindingSchema
from scanner.schemas.severity import Severity


@pytest.fixture
def settings() -> ScannerSettings:
    """Settings with test API key."""
    return ScannerSettings(claude_api_key="test-key", ai={"max_cost_per_scan": 5.0})


def _make_finding(
    fingerprint: str,
    file_path: str,
    severity: Severity = Severity.HIGH,
    title: str = "Test finding",
) -> FindingSchema:
    return FindingSchema(
        fingerprint=fingerprint,
        tool="semgrep",
        rule_id="test-rule",
        file_path=file_path,
        severity=severity,
        title=title,
    )


def _mock_create_response(analysis_data: dict, input_tokens: int = 500, output_tokens: int = 150):
    """Create a mock messages.create response with tool_use block."""
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.input = analysis_data

    text_block = MagicMock()
    text_block.type = "text"

    response = MagicMock()
    response.content = [text_block, tool_block]  # tool_use NOT at index 0
    response.usage = MagicMock(input_tokens=input_tokens, output_tokens=output_tokens)
    return response


# --- group_by_component tests ---


class TestGroupByComponent:
    def test_groups_by_top_level_directory(self, sample_findings):
        groups = group_by_component(sample_findings)
        assert "vms" in groups
        assert "mediaserver" in groups
        assert "infra" in groups
        # vms has 3 findings (auth, camera, services)
        assert len(groups["vms"]) == 3
        assert len(groups["mediaserver"]) == 1
        assert len(groups["infra"]) == 1

    def test_files_without_slash_go_to_root(self):
        findings = [_make_finding("f" * 64, "Makefile")]
        groups = group_by_component(findings)
        assert "root" in groups
        assert len(groups["root"]) == 1


# --- sort_batches_by_severity tests ---


class TestSortBatchesBySeverity:
    def test_returns_batches_ordered_by_max_severity(self):
        batches = {
            "low_comp": [_make_finding("a" * 64, "low_comp/f.py", Severity.LOW)],
            "crit_comp": [_make_finding("b" * 64, "crit_comp/f.py", Severity.CRITICAL)],
            "med_comp": [_make_finding("c" * 64, "med_comp/f.py", Severity.MEDIUM)],
        }
        sorted_b = sort_batches_by_severity(batches)
        assert sorted_b[0][0] == "crit_comp"
        assert sorted_b[1][0] == "med_comp"
        assert sorted_b[2][0] == "low_comp"


# --- AIAnalyzer.analyze() tests ---


class TestAnalyzeComponentCalls:
    @pytest.mark.asyncio
    async def test_calls_create_once_per_component(
        self, settings, sample_findings, mock_analysis_response, mock_correlation_response
    ):
        """2 components with eligible findings -> 2 analysis calls + 1 correlation."""
        mock_client = AsyncMock()
        mock_client.messages.count_tokens.return_value = MagicMock(input_tokens=500)

        # vms response (2 findings analyzed)
        vms_response = _mock_create_response(mock_analysis_response)
        # mediaserver response (1 finding)
        ms_analysis = {
            "findings_analysis": [{
                "fingerprint": "c" * 64,
                "business_logic_risk": "Buffer overflow risk",
                "risk_category": "memory_safety",
                "fix_suggestion": None,
                "recommendation": "Add bounds checking",
            }]
        }
        ms_response = _mock_create_response(ms_analysis)
        # infra response (1 finding)
        infra_analysis = {
            "findings_analysis": [{
                "fingerprint": "d" * 64,
                "business_logic_risk": "Privileged container risk",
                "risk_category": "k8s_misconfig",
                "fix_suggestion": None,
                "recommendation": "Remove privileged flag",
            }]
        }
        infra_response = _mock_create_response(infra_analysis)
        # correlation response
        corr_response = _mock_create_response(mock_correlation_response)

        mock_client.messages.create.side_effect = [
            vms_response,   # vms batch (has CRITICAL, processed first)
            ms_response,    # mediaserver batch (has CRITICAL)
            infra_response, # infra batch (has HIGH)
            corr_response,  # correlation
        ]

        with patch("scanner.ai.analyzer.AsyncAnthropic", return_value=mock_client):
            analyzer = AIAnalyzer(settings)
            findings, compound_risks, cost = await analyzer.analyze(sample_findings)

        # 3 component calls + 1 correlation = 4 total
        assert mock_client.messages.create.call_count == 4

    @pytest.mark.asyncio
    async def test_applies_ai_analysis_to_findings(
        self, settings, sample_findings, mock_analysis_response, mock_correlation_response
    ):
        mock_client = AsyncMock()
        mock_client.messages.count_tokens.return_value = MagicMock(input_tokens=500)

        vms_response = _mock_create_response(mock_analysis_response)
        ms_analysis = {
            "findings_analysis": [{
                "fingerprint": "c" * 64,
                "business_logic_risk": "Buffer overflow risk",
                "risk_category": "memory_safety",
                "fix_suggestion": None,
                "recommendation": "Add bounds checking",
            }]
        }
        ms_response = _mock_create_response(ms_analysis)
        infra_analysis = {
            "findings_analysis": [{
                "fingerprint": "d" * 64,
                "business_logic_risk": "Privileged container risk",
                "risk_category": "k8s_misconfig",
                "fix_suggestion": None,
                "recommendation": "Remove privileged flag",
            }]
        }
        infra_response = _mock_create_response(infra_analysis)
        corr_response = _mock_create_response(mock_correlation_response)

        mock_client.messages.create.side_effect = [
            vms_response, ms_response, infra_response, corr_response,
        ]

        with patch("scanner.ai.analyzer.AsyncAnthropic", return_value=mock_client):
            analyzer = AIAnalyzer(settings)
            findings, _, _ = await analyzer.analyze(sample_findings)

        fp_a = next(f for f in findings if f.fingerprint == "a" * 64)
        assert fp_a.ai_analysis == "Authentication bypass via SQL injection allows unauthorized access to any tenant account"

    @pytest.mark.asyncio
    async def test_fix_suggestion_format(
        self, settings, sample_findings, mock_analysis_response, mock_correlation_response
    ):
        """fix_suggestion is serialized JSON on ai_fix_suggestion field."""
        mock_client = AsyncMock()
        mock_client.messages.count_tokens.return_value = MagicMock(input_tokens=500)

        vms_response = _mock_create_response(mock_analysis_response)
        ms_analysis = {
            "findings_analysis": [{
                "fingerprint": "c" * 64,
                "business_logic_risk": "Buffer overflow",
                "risk_category": "memory_safety",
                "fix_suggestion": None,
                "recommendation": "Add bounds checking",
            }]
        }
        infra_analysis = {
            "findings_analysis": [{
                "fingerprint": "d" * 64,
                "business_logic_risk": "Priv container",
                "risk_category": "k8s_misconfig",
                "fix_suggestion": None,
                "recommendation": "Remove flag",
            }]
        }
        corr_response = _mock_create_response(mock_correlation_response)

        mock_client.messages.create.side_effect = [
            vms_response,
            _mock_create_response(ms_analysis),
            _mock_create_response(infra_analysis),
            corr_response,
        ]

        with patch("scanner.ai.analyzer.AsyncAnthropic", return_value=mock_client):
            analyzer = AIAnalyzer(settings)
            findings, _, _ = await analyzer.analyze(sample_findings)

        import json
        fp_a = next(f for f in findings if f.fingerprint == "a" * 64)
        assert fp_a.ai_fix_suggestion is not None
        fix_data = json.loads(fp_a.ai_fix_suggestion)
        assert "before" in fix_data
        assert "after" in fix_data
        assert "explanation" in fix_data

    @pytest.mark.asyncio
    async def test_null_fix_with_recommendation(
        self, settings, sample_findings, mock_analysis_response, mock_correlation_response
    ):
        """When fix_suggestion is null, recommendation text goes into ai_analysis."""
        mock_client = AsyncMock()
        mock_client.messages.count_tokens.return_value = MagicMock(input_tokens=500)

        vms_response = _mock_create_response(mock_analysis_response)
        ms_analysis = {
            "findings_analysis": [{
                "fingerprint": "c" * 64,
                "business_logic_risk": "Buffer overflow",
                "risk_category": "memory_safety",
                "fix_suggestion": None,
                "recommendation": "Add bounds checking",
            }]
        }
        infra_analysis = {
            "findings_analysis": [{
                "fingerprint": "d" * 64,
                "business_logic_risk": "Priv container",
                "risk_category": "k8s_misconfig",
                "fix_suggestion": None,
                "recommendation": "Remove flag",
            }]
        }
        corr_response = _mock_create_response(mock_correlation_response)

        mock_client.messages.create.side_effect = [
            vms_response,
            _mock_create_response(ms_analysis),
            _mock_create_response(infra_analysis),
            corr_response,
        ]

        with patch("scanner.ai.analyzer.AsyncAnthropic", return_value=mock_client):
            analyzer = AIAnalyzer(settings)
            findings, _, _ = await analyzer.analyze(sample_findings)

        fp_b = next(f for f in findings if f.fingerprint == "b" * 64)
        assert fp_b.ai_fix_suggestion is None
        assert "Recommendation:" in fp_b.ai_analysis
        assert "Define explicit $fillable" in fp_b.ai_analysis

    @pytest.mark.asyncio
    async def test_correlation_produces_compound_risks(
        self, settings, sample_findings, mock_analysis_response, mock_correlation_response
    ):
        mock_client = AsyncMock()
        mock_client.messages.count_tokens.return_value = MagicMock(input_tokens=500)

        vms_response = _mock_create_response(mock_analysis_response)
        ms_analysis = {
            "findings_analysis": [{
                "fingerprint": "c" * 64,
                "business_logic_risk": "Buffer overflow",
                "risk_category": "memory_safety",
                "fix_suggestion": None,
                "recommendation": "Check bounds",
            }]
        }
        infra_analysis = {
            "findings_analysis": [{
                "fingerprint": "d" * 64,
                "business_logic_risk": "Priv container",
                "risk_category": "k8s_misconfig",
                "fix_suggestion": None,
                "recommendation": "Remove flag",
            }]
        }
        corr_response = _mock_create_response(mock_correlation_response)

        mock_client.messages.create.side_effect = [
            vms_response,
            _mock_create_response(ms_analysis),
            _mock_create_response(infra_analysis),
            corr_response,
        ]

        with patch("scanner.ai.analyzer.AsyncAnthropic", return_value=mock_client):
            analyzer = AIAnalyzer(settings)
            _, compound_risks, _ = await analyzer.analyze(sample_findings)

        assert len(compound_risks) == 1
        cr = compound_risks[0]
        assert cr.title == "Authentication bypass + privilege escalation chain"
        assert cr.severity == Severity.CRITICAL.value
        assert len(cr.finding_fingerprints) == 2

    @pytest.mark.asyncio
    async def test_returns_tuple_findings_risks_cost(
        self, settings, sample_findings, mock_analysis_response, mock_correlation_response
    ):
        mock_client = AsyncMock()
        mock_client.messages.count_tokens.return_value = MagicMock(input_tokens=500)

        vms_response = _mock_create_response(mock_analysis_response)
        ms_analysis = {
            "findings_analysis": [{
                "fingerprint": "c" * 64,
                "business_logic_risk": "Test",
                "risk_category": "memory_safety",
                "fix_suggestion": None,
                "recommendation": "Test",
            }]
        }
        infra_analysis = {
            "findings_analysis": [{
                "fingerprint": "d" * 64,
                "business_logic_risk": "Test",
                "risk_category": "k8s_misconfig",
                "fix_suggestion": None,
                "recommendation": "Test",
            }]
        }
        corr_response = _mock_create_response(mock_correlation_response)

        mock_client.messages.create.side_effect = [
            vms_response,
            _mock_create_response(ms_analysis),
            _mock_create_response(infra_analysis),
            corr_response,
        ]

        with patch("scanner.ai.analyzer.AsyncAnthropic", return_value=mock_client):
            analyzer = AIAnalyzer(settings)
            result = await analyzer.analyze(sample_findings)

        assert isinstance(result, tuple)
        assert len(result) == 3
        findings, risks, cost = result
        assert isinstance(cost, float)
        assert cost > 0

    @pytest.mark.asyncio
    async def test_empty_findings_returns_immediately(self, settings):
        mock_client = AsyncMock()

        with patch("scanner.ai.analyzer.AsyncAnthropic", return_value=mock_client):
            analyzer = AIAnalyzer(settings)
            findings, risks, cost = await analyzer.analyze([])

        assert findings == []
        assert risks == []
        assert cost == 0.0
        mock_client.messages.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_only_low_info_findings_no_api_calls(self, settings):
        low_findings = [
            _make_finding("x" * 64, "vms/low.php", Severity.LOW),
            _make_finding("y" * 64, "vms/info.php", Severity.INFO),
        ]
        mock_client = AsyncMock()

        with patch("scanner.ai.analyzer.AsyncAnthropic", return_value=mock_client):
            analyzer = AIAnalyzer(settings)
            findings, risks, cost = await analyzer.analyze(low_findings)

        assert len(findings) == 2
        assert cost == 0.0
        mock_client.messages.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_splits_large_batch(self, settings):
        """Batch with >50 findings splits into sub-batches."""
        # Create 60 HIGH findings in same component
        many_findings = [
            _make_finding(f"{i:064d}", f"vms/file{i}.php", Severity.HIGH)
            for i in range(60)
        ]

        mock_client = AsyncMock()
        mock_client.messages.count_tokens.return_value = MagicMock(input_tokens=500)

        # Need 2 sub-batch responses + 1 correlation
        batch1_analysis = {
            "findings_analysis": [
                {"fingerprint": f"{i:064d}", "business_logic_risk": "risk", "risk_category": "other"}
                for i in range(50)
            ]
        }
        batch2_analysis = {
            "findings_analysis": [
                {"fingerprint": f"{i:064d}", "business_logic_risk": "risk", "risk_category": "other"}
                for i in range(50, 60)
            ]
        }
        corr = {"compound_risks": []}

        mock_client.messages.create.side_effect = [
            _mock_create_response(batch1_analysis),
            _mock_create_response(batch2_analysis),
            _mock_create_response(corr),
        ]

        with patch("scanner.ai.analyzer.AsyncAnthropic", return_value=mock_client):
            analyzer = AIAnalyzer(settings)
            await analyzer.analyze(many_findings)

        # 2 sub-batch calls + 1 correlation = 3
        assert mock_client.messages.create.call_count == 3

    @pytest.mark.asyncio
    async def test_tool_use_response_parsing_iterates_blocks(self, settings):
        """Parser iterates content blocks; tool_use is NOT at index 0."""
        mock_client = AsyncMock()
        mock_client.messages.count_tokens.return_value = MagicMock(input_tokens=500)

        finding = _make_finding("z" * 64, "vms/test.php", Severity.HIGH)
        analysis = {
            "findings_analysis": [{
                "fingerprint": "z" * 64,
                "business_logic_risk": "Test risk",
                "risk_category": "other",
                "fix_suggestion": None,
                "recommendation": "Test",
            }]
        }
        # text block first, then tool_use
        response = _mock_create_response(analysis)
        corr_response = _mock_create_response({"compound_risks": []})

        mock_client.messages.create.side_effect = [response, corr_response]

        with patch("scanner.ai.analyzer.AsyncAnthropic", return_value=mock_client):
            analyzer = AIAnalyzer(settings)
            findings, _, _ = await analyzer.analyze([finding])

        fp_z = next(f for f in findings if f.fingerprint == "z" * 64)
        # fix_suggestion is null but recommendation exists, so ai_analysis includes it
        assert "Test risk" in fp_z.ai_analysis
        assert fp_z.ai_analysis is not None
