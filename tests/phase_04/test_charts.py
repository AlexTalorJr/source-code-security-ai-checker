"""Tests for chart generation module (pie + bar charts as base64 PNG)."""

import base64

import matplotlib.pyplot as plt
import pytest

from scanner.reports.charts import generate_severity_pie_chart, generate_tool_bar_chart

PNG_MAGIC = b"\x89PNG"
DATA_URI_PREFIX = "data:image/png;base64,"


class TestSeverityPieChart:
    def test_severity_pie_chart(self):
        result = generate_severity_pie_chart(critical=3, high=5, medium=10)
        assert result.startswith(DATA_URI_PREFIX)
        raw = base64.b64decode(result.removeprefix(DATA_URI_PREFIX))
        assert raw[:4] == PNG_MAGIC

    def test_pie_chart_excludes_zero(self):
        result = generate_severity_pie_chart(critical=0, high=0, medium=5)
        assert result.startswith(DATA_URI_PREFIX)
        raw = base64.b64decode(result.removeprefix(DATA_URI_PREFIX))
        assert raw[:4] == PNG_MAGIC

    def test_pie_chart_all_zero(self):
        result = generate_severity_pie_chart()
        assert result == ""


class TestToolBarChart:
    def test_tool_bar_chart(self):
        result = generate_tool_bar_chart({"semgrep": 10, "trivy": 5, "gitleaks": 2})
        assert result.startswith(DATA_URI_PREFIX)
        raw = base64.b64decode(result.removeprefix(DATA_URI_PREFIX))
        assert raw[:4] == PNG_MAGIC

    def test_bar_chart_empty(self):
        result = generate_tool_bar_chart({})
        assert result == ""


class TestFigureClosed:
    def test_figure_closed(self):
        """Chart functions must close figures after saving (no memory leak)."""
        before = len(plt.get_fignums())
        generate_severity_pie_chart(critical=1, high=2)
        generate_tool_bar_chart({"semgrep": 3})
        after = len(plt.get_fignums())
        assert after == before, f"Figure leak: {after - before} unclosed figure(s)"
