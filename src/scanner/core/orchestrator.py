"""Scan orchestrator: parallel adapter execution, deduplication, and persistence."""

import asyncio
import json
import logging
from datetime import datetime

from scanner.adapters import ALL_ADAPTERS
from scanner.adapters.base import ScannerAdapter
from scanner.ai.schemas import AIAnalysisResult
from scanner.config import ScannerSettings
from scanner.core.git import cleanup_clone, clone_repo
from scanner.db.session import create_engine, create_session_factory
from scanner.models.base import Base
from scanner.models.finding import Finding
from scanner.models.scan import ScanResult
from scanner.schemas.compound_risk import CompoundRiskSchema
from scanner.schemas.finding import FindingSchema
from scanner.schemas.scan import ScanResultSchema
from scanner.schemas.severity import Severity

logger = logging.getLogger(__name__)


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
    on_complete=None,
) -> tuple[str, list[FindingSchema] | Exception]:
    """Run a single adapter with error isolation.

    Returns:
        Tuple of (tool_name, findings_list) on success,
        or (tool_name, exception) on any failure.
    """
    try:
        findings = await adapter.run(target_path, timeout, extra_args)
        if on_complete:
            on_complete(adapter.tool_name, len(findings), None)
        return (adapter.tool_name, findings)
    except Exception as exc:
        if on_complete:
            on_complete(adapter.tool_name, 0, str(exc))
        return (adapter.tool_name, exc)


async def enrich_with_ai(
    findings: list[FindingSchema],
    settings: ScannerSettings,
) -> tuple[list[FindingSchema], list[CompoundRiskSchema], AIAnalysisResult]:
    """Enrich findings with AI analysis. Returns originals on any failure."""
    result = AIAnalysisResult()

    if not settings.claude_api_key:
        result.skipped = True
        result.skip_reason = "Claude API key not configured"
        logger.info("AI analysis skipped: %s", result.skip_reason)
        return findings, [], result

    try:
        from scanner.ai.analyzer import AIAnalyzer

        analyzer = AIAnalyzer(settings)
        enriched, compound_risks, cost = await analyzer.analyze(findings)
        result.cost_usd = cost
        result.analyzed_components = analyzer.analyzed_components
        result.skipped_components = analyzer.skipped_components
        logger.info(
            "AI analysis complete: cost=$%.4f, analyzed=%s, skipped=%s",
            cost,
            analyzer.analyzed_components,
            analyzer.skipped_components,
        )
        return enriched, compound_risks, result
    except Exception as exc:
        result.skipped = True
        result.skip_reason = f"AI analysis failed: {exc}"
        logger.warning("AI analysis failed: %s", exc)
        return findings, [], result


async def run_scan(
    settings: ScannerSettings,
    target_path: str | None = None,
    repo_url: str | None = None,
    branch: str | None = None,
    persist: bool = True,
    progress_callback=None,
    skip_ai: bool = False,
) -> tuple[ScanResultSchema, list[FindingSchema], list[CompoundRiskSchema]]:
    """Run all enabled scanners against a target, deduplicate, and persist.

    Either ``target_path`` or ``repo_url`` (with ``branch``) must be provided,
    but not both.

    Args:
        settings: Application settings including per-tool config.
        target_path: Local filesystem path to scan.
        repo_url: Git repository URL to clone and scan.
        branch: Git branch (required when repo_url is provided).

    Returns:
        Tuple of (ScanResultSchema, list[FindingSchema], list[CompoundRiskSchema])
        populated with findings summary, gate result, and database ID.

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

        # Notify: scanning stage with tool list
        if progress_callback:
            progress_callback("scanning", {
                "tools": [a.tool_name for a in enabled_adapters],
                "completed": [],
            })

        # Track per-tool completion
        completed_tools = []

        def _on_tool_complete(tool_name, finding_count, error):
            completed_tools.append({
                "tool": tool_name,
                "findings": finding_count,
                "error": error,
            })
            if progress_callback:
                progress_callback("scanning", {
                    "tools": [a.tool_name for a in enabled_adapters],
                    "completed": completed_tools,
                })

        # Run all adapters in parallel
        tasks = [
            _run_adapter(
                adapter,
                target_path,
                getattr(settings.scanners, adapter.tool_name).timeout,
                getattr(settings.scanners, adapter.tool_name).extra_args
                or None,
                on_complete=_on_tool_complete,
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
        if progress_callback:
            progress_callback("deduplicating", {"total_raw": len(all_findings)})
        deduped_findings = deduplicate_findings(all_findings)

        # AI enrichment (graceful degradation)
        if skip_ai:
            enriched_findings = deduped_findings
            compound_risks: list[CompoundRiskSchema] = []
            ai_result = AIAnalysisResult(skipped=True, skip_reason="Skipped by user request")
            if progress_callback:
                progress_callback("ai_analysis", {
                    "total_findings": len(deduped_findings),
                    "skipped": True,
                })
            logger.info("AI analysis skipped by user request")
        else:
            if progress_callback:
                progress_callback("ai_analysis", {
                    "total_findings": len(deduped_findings),
                    "skipped": not settings.claude_api_key,
                })
            enriched_findings, compound_risks, ai_result = await enrich_with_ai(
                deduped_findings, settings
            )
        if progress_callback:
            progress_callback("finalizing", {})

        # Count by severity
        counts: dict[Severity, int] = {s: 0 for s in Severity}
        for f in enriched_findings:
            counts[f.severity] += 1

        # Quality gate: configurable via settings.gate
        gate_config = settings.gate
        gate_passed, fail_reasons = gate_config.evaluate(counts, compound_risks)

        # Build result schema
        completed_at = datetime.utcnow()
        scan_result = ScanResultSchema(
            status="completed",
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=(completed_at - started_at).total_seconds(),
            total_findings=len(enriched_findings),
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
            ai_cost_usd=ai_result.cost_usd if ai_result.cost_usd > 0 else None,
            ai_skipped=ai_result.skipped,
            ai_skip_reason=ai_result.skip_reason,
        )

        # Persist to SQLite (skip when called from scan_queue worker)
        if persist:
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
                    db_scan.ai_cost_usd = (
                        ai_result.cost_usd if ai_result.cost_usd > 0 else None
                    )
                    session.add(db_scan)
                    await session.flush()

                    for finding in enriched_findings:
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
                            ai_analysis=finding.ai_analysis,
                            ai_fix_suggestion=finding.ai_fix_suggestion,
                        )
                        session.add(db_finding)

                    # Persist compound risks
                    from scanner.models.compound_risk import CompoundRisk as CompoundRiskModel
                    from scanner.models.compound_risk import compound_risk_findings

                    for cr in compound_risks:
                        db_cr = CompoundRiskModel(
                            scan_id=db_scan.id,
                            title=cr.title,
                            description=cr.description,
                            severity=cr.severity,
                            risk_category=cr.risk_category,
                            recommendation=cr.recommendation,
                        )
                        session.add(db_cr)
                        await session.flush()
                        for fp in cr.finding_fingerprints:
                            await session.execute(
                                compound_risk_findings.insert().values(
                                    compound_risk_id=db_cr.id,
                                    finding_fingerprint=fp,
                                )
                            )

                scan_result.id = db_scan.id

            await engine.dispose()

        return (scan_result, enriched_findings, compound_risks)

    finally:
        if clone_path is not None:
            cleanup_clone(clone_path)


def format_summary_table(
    scan_result: ScanResultSchema,
    warnings: list[str],
    fail_reasons: list[str] | None = None,
) -> str:
    """Format a plain-text summary table for scan results.

    Args:
        scan_result: Completed scan result.
        warnings: List of warning messages from failed adapters.
        fail_reasons: Optional list of gate failure reasons.

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

    if fail_reasons:
        for reason in fail_reasons:
            lines.append(f"    - {reason}")

    return "\n".join(lines)
