"""Server-side chart generation for PDF/HTML reports."""

import base64
import io
import logging

import matplotlib

matplotlib.use("Agg")  # MUST be before pyplot import
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

SEVERITY_COLORS = {
    "Critical": "#dc3545",
    "High": "#fd7e14",
    "Medium": "#ffc107",
    "Low": "#28a745",
    "Info": "#6c757d",
}


def generate_severity_pie_chart(
    critical: int = 0,
    high: int = 0,
    medium: int = 0,
    low: int = 0,
    info: int = 0,
) -> str:
    """Generate severity distribution pie chart as base64 PNG data URI.

    Only includes severities with count > 0. Returns empty string if all zero.
    """
    counts = {"Critical": critical, "High": high, "Medium": medium, "Low": low, "Info": info}
    labels = [k for k, v in counts.items() if v > 0]
    values = [v for k, v in counts.items() if v > 0]

    if not values:
        return ""

    colors = [SEVERITY_COLORS[label] for label in labels]

    fig, ax = plt.subplots(figsize=(4, 4))
    try:
        ax.pie(values, labels=labels, colors=colors, autopct="%1.0f%%",
               textprops={"fontsize": 10})
        ax.set_title("Severity Distribution", fontsize=14, fontweight="bold")

        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
        buf.seek(0)
        return f"data:image/png;base64,{base64.b64encode(buf.read()).decode()}"
    finally:
        plt.close(fig)


def generate_tool_bar_chart(tool_counts: dict[str, int]) -> str:
    """Generate findings-by-tool bar chart as base64 PNG data URI.

    Args:
        tool_counts: Mapping of tool name to finding count.

    Returns empty string if no tools.
    """
    if not tool_counts:
        return ""

    tools = list(tool_counts.keys())
    counts = list(tool_counts.values())

    fig, ax = plt.subplots(figsize=(4, 4))
    try:
        bars = ax.bar(tools, counts, color="#0d6efd")
        ax.set_title("Findings by Tool", fontsize=14, fontweight="bold")
        ax.set_ylabel("Count")
        ax.set_xlabel("Tool")
        # Add count labels on bars
        for bar, count in zip(bars, counts):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                    str(count), ha="center", va="bottom", fontsize=10)
        plt.xticks(rotation=45, ha="right")

        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
        buf.seek(0)
        return f"data:image/png;base64,{base64.b64encode(buf.read()).decode()}"
    finally:
        plt.close(fig)
