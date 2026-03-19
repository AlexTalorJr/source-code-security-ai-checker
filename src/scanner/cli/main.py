"""Typer CLI for the security scanner."""

import asyncio
import os
import sys
from datetime import datetime
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from scanner.config import ScannerSettings
from scanner.core.orchestrator import run_scan
from scanner.reports import generate_html_report, generate_pdf_report
from scanner.reports.models import ReportData
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


async def _compute_delta_for_cli(settings, findings, scan_result):
    """Compute delta comparison against previous scan of the same branch."""
    from scanner.db.session import create_engine, create_session_factory
    from scanner.reports.delta import compute_delta

    engine = create_engine(settings.db_path)
    session_factory = create_session_factory(engine)
    async with session_factory() as session:
        delta = await compute_delta(
            findings, scan_result.branch, scan_result.id, session
        )
    await engine.dispose()
    return delta


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
    output_dir: str = typer.Option(
        "reports", "--output-dir", help="Directory for HTML/PDF report output"
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
        scan_result, findings, compound_risks = asyncio.run(
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
    if scan_result.error_message:
        warning_lines = scan_result.error_message.strip().split("\n")
        warning_text = "\n".join(f"  {line}" for line in warning_lines)
        err_console.print(
            Panel(
                warning_text,
                title="WARNINGS",
                style="bold yellow",
            )
        )

    # Compute gate fail reasons for display
    gate_config = settings.gate
    severity_counts = {s: 0 for s in Severity}
    for f in findings:
        severity_counts[f.severity] += 1
    _, fail_reasons = gate_config.evaluate(severity_counts, compound_risks)

    # Compute delta comparison
    delta = None
    if scan_result.id is not None and scan_result.branch is not None:
        try:
            delta = asyncio.run(
                _compute_delta_for_cli(settings, findings, scan_result)
            )
        except Exception as exc:
            err_console.print(
                f"[yellow]Delta comparison failed: {exc}[/yellow]"
            )

    # Generate reports
    os.makedirs(output_dir, exist_ok=True)

    branch_slug = (scan_result.branch or "local").replace("/", "-")
    date_slug = datetime.now().strftime("%Y%m%d-%H%M%S")
    scan_id = scan_result.id or 0
    base_name = f"scan-{scan_id}-{branch_slug}-{date_slug}"

    report_data = ReportData(
        scan_result=scan_result,
        findings=findings,
        compound_risks=compound_risks,
        delta=delta,
        gate_passed=scan_result.gate_passed or False,
        fail_reasons=fail_reasons,
    )

    html_path = os.path.join(output_dir, f"{base_name}.html")
    pdf_path = os.path.join(output_dir, f"{base_name}.pdf")

    generate_html_report(report_data, html_path)
    try:
        generate_pdf_report(report_data, pdf_path)
    except Exception as exc:
        err_console.print(f"[yellow]PDF generation failed: {exc}[/yellow]")
        pdf_path = None

    if json_output:
        import json

        data = json.loads(scan_result.model_dump_json())
        data["fail_reasons"] = fail_reasons
        if delta:
            data["delta"] = {
                "new": len(delta.new_fingerprints),
                "fixed": len(delta.fixed_fingerprints),
                "persisting": len(delta.persisting_fingerprints),
                "previous_scan_id": delta.previous_scan_id,
            }
        else:
            data["delta"] = None
        data["reports"] = {"html": html_path, "pdf": pdf_path}
        console.print(json.dumps(data, indent=2, default=str))
    else:
        # Build rich table
        table = Table(title="Scan Results")
        table.add_column("Severity", style="bold")
        table.add_column("Count", justify="right")

        severity_display = [
            (Severity.CRITICAL, scan_result.critical_count),
            (Severity.HIGH, scan_result.high_count),
            (Severity.MEDIUM, scan_result.medium_count),
            (Severity.LOW, scan_result.low_count),
            (Severity.INFO, scan_result.info_count),
        ]

        for severity, count in severity_display:
            style = _SEVERITY_STYLES[severity]
            table.add_row(f"[{style}]{severity.name}[/{style}]", str(count))

        console.print(table)
        console.print()
        console.print(f"Total findings: {scan_result.total_findings}")

        if scan_result.duration_seconds is not None:
            console.print(f"Duration: {scan_result.duration_seconds:.1f}s")

        # Delta summary
        if delta:
            delta_line = (
                f"Delta: +{len(delta.new_fingerprints)} new, "
                f"-{len(delta.fixed_fingerprints)} fixed, "
                f"{len(delta.persisting_fingerprints)} persisting"
            )
            console.print(delta_line)
        else:
            console.print("[dim]Delta: first scan on this branch[/dim]")

        # Gate status with fail reasons
        if scan_result.gate_passed:
            console.print("[bold green]Quality gate: PASSED[/bold green]")
        else:
            console.print("[bold red]Quality gate: FAILED[/bold red]")
            for reason in fail_reasons:
                console.print(f"  [red]- {reason}[/red]")

        # AI analysis info
        if scan_result.ai_skipped:
            console.print(
                f"[dim]AI analysis: skipped ({scan_result.ai_skip_reason})[/dim]"
            )
        elif scan_result.ai_cost_usd is not None:
            console.print(f"AI cost: ${scan_result.ai_cost_usd:.4f}")

        # Report paths
        console.print(f"Reports: {html_path}")
        if pdf_path:
            console.print(f"         {pdf_path}")

    # Exit code based on gate
    if not scan_result.gate_passed:
        sys.exit(1)
    else:
        sys.exit(0)
