"""Scan orchestrator: parallel adapter execution, deduplication, and persistence."""

import asyncio
import json
from datetime import datetime

from scanner.adapters import ALL_ADAPTERS
from scanner.adapters.base import ScannerAdapter
from scanner.config import ScannerSettings
from scanner.core.git import cleanup_clone, clone_repo
from scanner.db.session import create_engine, create_session_factory
from scanner.models.base import Base
from scanner.models.finding import Finding
from scanner.models.scan import ScanResult
from scanner.schemas.finding import FindingSchema
from scanner.schemas.scan import ScanResultSchema
from scanner.schemas.severity import Severity


def deduplicate_findings(
    findings: list[FindingSchema],
) -> list[FindingSchema]:
    """Deduplicate findings by fingerprint, keeping the highest severity.

    Args:
        findings: List of findings (may contain duplicates by fingerprint).

    Returns:
        Deduplicated list preserving insertion order of first occurrence.
    """
    seen: dict[str, FindingSchema] = {}
    for finding in findings:
        existing = seen.get(finding.fingerprint)
        if existing is None:
            seen[finding.fingerprint] = finding
        elif finding.severity > existing.severity:
            seen[finding.fingerprint] = finding
    return list(seen.values())


async def _run_adapter(
    adapter: ScannerAdapter,
    target_path: str,
    timeout: int,
    extra_args: list[str] | None,
) -> tuple[str, list[FindingSchema] | Exception]:
    """Run a single adapter with error isolation.

    Returns:
        Tuple of (tool_name, findings_list) on success,
        or (tool_name, exception) on any failure.
    """
    try:
        findings = await adapter.run(target_path, timeout, extra_args)
        return (adapter.tool_name, findings)
    except Exception as exc:
        return (adapter.tool_name, exc)


async def run_scan(
    settings: ScannerSettings,
    target_path: str | None = None,
    repo_url: str | None = None,
    branch: str | None = None,
) -> ScanResultSchema:
    """Run all enabled scanners against a target, deduplicate, and persist.

    Either ``target_path`` or ``repo_url`` (with ``branch``) must be provided,
    but not both.

    Args:
        settings: Application settings including per-tool config.
        target_path: Local filesystem path to scan.
        repo_url: Git repository URL to clone and scan.
        branch: Git branch (required when repo_url is provided).

    Returns:
        ScanResultSchema populated with findings summary, gate result,
        and database ID.

    Raises:
        ValueError: If arguments are invalid (both/neither target and repo).
    """
    if target_path and repo_url:
        raise ValueError(
            "Provide either target_path or repo_url, not both."
        )
    if not target_path and not repo_url:
        raise ValueError(
            "Provide either target_path or repo_url."
        )

    started_at = datetime.utcnow()
    clone_path: str | None = None

    try:
        # Clone repo if needed
        if repo_url:
            # Gitleaks needs full history, so shallow=False when it is enabled
            gitleaks_enabled = settings.scanners.gitleaks.enabled
            shallow = not gitleaks_enabled
            clone_path = await clone_repo(
                repo_url,
                branch,
                shallow=shallow,
                git_token=settings.git_token or None,
            )
            target_path = clone_path

        # Build enabled adapters
        enabled_adapters: list[ScannerAdapter] = []
        for adapter_cls in ALL_ADAPTERS:
            instance = adapter_cls()
            tool_config = getattr(settings.scanners, instance.tool_name)
            if tool_config.enabled:
                enabled_adapters.append(instance)

        # Run all adapters in parallel
        tasks = [
            _run_adapter(
                adapter,
                target_path,
                getattr(settings.scanners, adapter.tool_name).timeout,
                getattr(settings.scanners, adapter.tool_name).extra_args
                or None,
            )
            for adapter in enabled_adapters
        ]
        results = await asyncio.gather(*tasks)

        # Separate successes and warnings
        all_findings: list[FindingSchema] = []
        warnings: list[str] = []
        successful_adapters: list[ScannerAdapter] = []

        for i, (tool_name, result) in enumerate(results):
            if isinstance(result, Exception):
                warnings.append(f"{tool_name}: {result!s}")
            else:
                all_findings.extend(result)
                successful_adapters.append(enabled_adapters[i])

        # Collect tool versions
        tool_versions: dict[str, str] = {}
        for adapter in successful_adapters:
            try:
                version = await adapter.get_version()
                tool_versions[adapter.tool_name] = version
            except Exception:
                tool_versions[adapter.tool_name] = "unknown"

        # Deduplicate
        deduped_findings = deduplicate_findings(all_findings)

        # Count by severity
        counts: dict[Severity, int] = {s: 0 for s in Severity}
        for f in deduped_findings:
            counts[f.severity] += 1

        # Quality gate
        gate_passed = (counts[Severity.CRITICAL] + counts[Severity.HIGH]) == 0

        # Build result schema
        completed_at = datetime.utcnow()
        scan_result = ScanResultSchema(
            status="completed",
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=(completed_at - started_at).total_seconds(),
            total_findings=len(deduped_findings),
            critical_count=counts[Severity.CRITICAL],
            high_count=counts[Severity.HIGH],
            medium_count=counts[Severity.MEDIUM],
            low_count=counts[Severity.LOW],
            info_count=counts[Severity.INFO],
            gate_passed=gate_passed,
            tool_versions=tool_versions,
            error_message="\n".join(warnings) if warnings else None,
            target_path=target_path,
            repo_url=repo_url,
            branch=branch,
        )

        # Persist to SQLite
        engine = create_engine(settings.db_path)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_factory = create_session_factory(engine)
        async with session_factory() as session:
            async with session.begin():
                db_scan = ScanResult(
                    target_path=scan_result.target_path,
                    repo_url=scan_result.repo_url,
                    branch=scan_result.branch,
                    status=scan_result.status,
                    started_at=scan_result.started_at,
                    completed_at=scan_result.completed_at,
                    duration_seconds=scan_result.duration_seconds,
                    total_findings=scan_result.total_findings,
                    critical_count=scan_result.critical_count,
                    high_count=scan_result.high_count,
                    medium_count=scan_result.medium_count,
                    low_count=scan_result.low_count,
                    info_count=scan_result.info_count,
                    gate_passed=1 if scan_result.gate_passed else 0,
                    tool_versions=json.dumps(tool_versions),
                    error_message=scan_result.error_message,
                )
                session.add(db_scan)
                await session.flush()

                for finding in deduped_findings:
                    db_finding = Finding(
                        scan_id=db_scan.id,
                        fingerprint=finding.fingerprint,
                        tool=finding.tool,
                        rule_id=finding.rule_id,
                        file_path=finding.file_path,
                        line_start=finding.line_start,
                        line_end=finding.line_end,
                        snippet=finding.snippet,
                        severity=finding.severity.value,
                        title=finding.title,
                        description=finding.description,
                        recommendation=finding.recommendation,
                    )
                    session.add(db_finding)

            scan_result.id = db_scan.id

        await engine.dispose()

        return scan_result

    finally:
        if clone_path is not None:
            cleanup_clone(clone_path)


def format_summary_table(
    scan_result: ScanResultSchema, warnings: list[str]
) -> str:
    """Format a plain-text summary table for scan results.

    Args:
        scan_result: Completed scan result.
        warnings: List of warning messages from failed adapters.

    Returns:
        Formatted summary string.
    """
    lines: list[str] = []

    if warnings:
        lines.append("=" * 50)
        lines.append("WARNINGS:")
        for w in warnings:
            lines.append(f"  - {w}")
        lines.append("=" * 50)
        lines.append("")

    lines.append("Scan Results Summary")
    lines.append("-" * 40)
    lines.append(f"  CRITICAL: {scan_result.critical_count}")
    lines.append(f"  HIGH:     {scan_result.high_count}")
    lines.append(f"  MEDIUM:   {scan_result.medium_count}")
    lines.append(f"  LOW:      {scan_result.low_count}")
    lines.append(f"  INFO:     {scan_result.info_count}")
    lines.append("-" * 40)
    lines.append(f"  Total:    {scan_result.total_findings}")
    lines.append(
        f"  Duration: {scan_result.duration_seconds:.1f}s"
        if scan_result.duration_seconds is not None
        else "  Duration: N/A"
    )
    gate_label = "PASSED" if scan_result.gate_passed else "FAILED"
    lines.append(f"  Gate:     {gate_label}")

    return "\n".join(lines)
