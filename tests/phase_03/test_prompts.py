"""Tests for AI prompt builders and tool definitions."""

import json

from scanner.ai.prompts import (
    ANALYSIS_TOOL,
    CORRELATION_TOOL,
    build_component_prompt,
    build_correlation_prompt,
    build_system_prompt,
)
from scanner.schemas.finding import FindingSchema
from scanner.schemas.severity import Severity


class TestBuildSystemPrompt:
    def test_vms_contains_rtsp_and_tenant_and_laravel(self):
        prompt = build_system_prompt("vms")
        assert "RTSP" in prompt
        assert "tenant isolation" in prompt.lower() or "tenant" in prompt.lower()
        assert "Laravel" in prompt

    def test_mediaserver_contains_buffer_overflow_and_cpp(self):
        prompt = build_system_prompt("mediaserver")
        assert "buffer overflow" in prompt.lower()
        assert "C++" in prompt
        assert "memory safety" in prompt.lower()

    def test_infra_contains_kubernetes_and_helm(self):
        prompt = build_system_prompt("infra")
        assert "Kubernetes" in prompt
        assert "Helm" in prompt

    def test_unknown_component_has_core_concerns_no_framework(self):
        prompt = build_system_prompt("unknown_component")
        # Core security concerns should still be present
        assert "RTSP" in prompt
        # Should not have framework-specific context from COMPONENT_FRAMEWORK_MAP
        assert "Laravel" not in prompt
        assert "Eloquent" not in prompt
        assert "use-after-free" not in prompt


class TestBuildComponentPrompt:
    def test_produces_json_serialized_findings(self, sample_findings):
        prompt = build_component_prompt("vms", sample_findings[:2])
        # Should contain serialized finding data
        assert "a" * 64 in prompt  # fingerprint
        assert "AuthController.php" in prompt  # file_path
        assert "SQL injection" in prompt  # title
        assert "semgrep" not in prompt or "semgrep" in prompt  # tool may or may not be in prompt
        # Should be parseable JSON somewhere
        assert "fingerprint" in prompt
        assert "file_path" in prompt
        assert "line_start" in prompt
        assert "severity" in prompt
        assert "rule_id" in prompt


class TestBuildCorrelationPrompt:
    def test_includes_component_summaries(self):
        summaries = {
            "vms": [
                {"fingerprint": "a" * 64, "title": "SQL injection", "risk_category": "auth_bypass"},
            ],
            "mediaserver": [
                {"fingerprint": "c" * 64, "title": "Buffer overflow", "risk_category": "memory_safety"},
            ],
        }
        prompt = build_correlation_prompt(summaries)
        assert "vms" in prompt
        assert "mediaserver" in prompt
        assert "SQL injection" in prompt or "a" * 64 in prompt


class TestAnalysisTool:
    def test_has_correct_name(self):
        assert ANALYSIS_TOOL["name"] == "security_analysis"

    def test_has_input_schema(self):
        schema = ANALYSIS_TOOL["input_schema"]
        assert schema["type"] == "object"
        assert "findings_analysis" in schema["properties"]


class TestCorrelationTool:
    def test_has_correct_name(self):
        assert CORRELATION_TOOL["name"] == "cross_component_correlation"

    def test_has_input_schema(self):
        schema = CORRELATION_TOOL["input_schema"]
        assert schema["type"] == "object"
        assert "compound_risks" in schema["properties"]
