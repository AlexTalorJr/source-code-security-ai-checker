"""Typer CLI for the security scanner."""

import asyncio
import os
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from scanner.config import ScannerSettings
from scanner.core.orchestrator import run_scan
from scanner.schemas.severity import Severity

app = typer.Typer(
    name="scanner",
    help="aipix-security-scanner CLI",
    invoke_without_command=True,
)
console = Console()
err_console = Console(stderr=True)


@app.callback()
def main() -> None:
    """aipix-security-scanner: scan code for security vulnerabilities."""

_SEVERITY_STYLES = {
    Severity.CRITICAL: "bold red",
    Severity.HIGH: "yellow",
    Severity.MEDIUM: "blue",
    Severity.LOW: "green",
    Severity.INFO: "dim",
}


@app.command()
def scan(
    path: Optional[str] = typer.Option(
        None, "--path", help="Local filesystem path to scan"
    ),
    repo_url: Optional[str] = typer.Option(
        None, "--repo-url", help="Git repository URL to clone and scan"
    ),
    branch: Optional[str] = typer.Option(
        None, "--branch", help="Git branch to scan (required with --repo-url)"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output results as JSON"
    ),
    config: Optional[str] = typer.Option(
        None, "--config", help="Path to config.yml"
    ),
) -> None:
    """Run security scanners against a target path or git repository."""
    # Validate: repo_url requires branch
    if repo_url and not branch:
        raise typer.BadParameter(
            "--branch is required when --repo-url is provided"
        )

    if config:
        os.environ["SCANNER_CONFIG_PATH"] = config

    settings = ScannerSettings()

    try:
        result, findings, compound_risks = asyncio.run(
            run_scan(
                settings,
                target_path=path,
                repo_url=repo_url,
                branch=branch,
            )
        )
    except ValueError as exc:
        err_console.print(f"[bold red]Error:[/bold red] {exc}")
        raise SystemExit(2) from exc

    # Handle warnings
    if result.error_message:
        warning_lines = result.error_message.strip().split("\n")
        warning_text = "\n".join(f"  {line}" for line in warning_lines)
        err_console.print(
            Panel(
                warning_text,
                title="WARNINGS",
                style="bold yellow",
            )
        )

    if json_output:
        console.print(result.model_dump_json(indent=2))
    else:
        # Build rich table
        table = Table(title="Scan Results")
        table.add_column("Severity", style="bold")
        table.add_column("Count", justify="right")

        severity_counts = [
            (Severity.CRITICAL, result.critical_count),
            (Severity.HIGH, result.high_count),
            (Severity.MEDIUM, result.medium_count),
            (Severity.LOW, result.low_count),
            (Severity.INFO, result.info_count),
        ]

        for severity, count in severity_counts:
            style = _SEVERITY_STYLES[severity]
            table.add_row(f"[{style}]{severity.name}[/{style}]", str(count))

        console.print(table)
        console.print()
        console.print(f"Total findings: {result.total_findings}")

        if result.duration_seconds is not None:
            console.print(f"Duration: {result.duration_seconds:.1f}s")

        if result.gate_passed:
            console.print("[bold green]Gate: PASSED[/bold green]")
        else:
            console.print("[bold red]Gate: FAILED[/bold red]")

        # AI analysis info
        if result.ai_skipped:
            console.print(
                f"[dim]AI analysis: skipped ({result.ai_skip_reason})[/dim]"
            )
        elif result.ai_cost_usd is not None:
            console.print(f"AI cost: ${result.ai_cost_usd:.4f}")

    # Exit code based on gate
    if not result.gate_passed:
        sys.exit(1)
    else:
        sys.exit(0)
