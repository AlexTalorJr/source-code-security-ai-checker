# Phase 4: Reports and Quality Gate - Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Every scan produces professional reports (interactive HTML and formal PDF) and an automated pass/fail decision that can block deployment. Scan results are stored with delta comparison showing new, fixed, and persisting findings relative to the previous scan of the same branch.

</domain>

<decisions>
## Implementation Decisions

### HTML report layout
- Severity-first grouping: Critical > High > Medium > Low > Info sections
- Each finding shows component/tool tags within its severity section
- AI fix suggestions rendered as side-by-side diff (before/after code blocks with syntax highlighting, GitHub PR diff style)
- Single self-contained HTML file — all CSS/JS inlined for portability (email, share, archive)
- Left sidebar with checkbox filters for severity, tool, and component — findings update instantly, count badges per filter option

### PDF report structure
- Primary audience: management and telecom operators — non-technical language, focus on risk level and business impact
- Executive summary first, then severity breakdown
- Charts: pie chart for severity distribution + bar chart for findings per tool (generated server-side)
- Individual findings shown as summary table only (severity, file, rule, one-line description) — full details in HTML report
- PDF stays concise: 3-5 pages for typical scans
- English only for now — bilingual is v2 scope (ADV-02)

### Quality gate configurability
- Severity threshold configuration: `gate.fail_on: [critical, high]` — simple list of severities that trigger failure
- Compound risk gate: separate toggle `gate.include_compound_risks: true/false` — defaults to true, teams can disable while building trust in AI correlation
- Gate decision (PASSED/FAILED) prominently displayed at top of both HTML and PDF reports, showing which thresholds triggered failure

### Delta comparison
- Compare current scan to most recent previous scan of the same branch — automatic, no user input needed
- Finding matching by fingerprint (existing SHA-256: file + rule + snippet hash)
- HTML report: dedicated delta section at top — "N new, M fixed, K persisting" with colored badges. New findings highlighted in main list
- CLI output: brief one-line delta summary after severity table — "+3 new, -2 fixed, 5 persisting"

### Claude's Discretion
- HTML template framework choice (Jinja2 assumed from PROJECT.md tech stack)
- PDF generation library (WeasyPrint assumed from PROJECT.md tech stack)
- Chart generation library (matplotlib, plotly, or SVG generation)
- CSS styling, color scheme, typography for HTML report
- Exact sidebar filter implementation (vanilla JS vs lightweight library)
- PDF page layout, margins, fonts
- Delta section visual design

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — Phase 4 covers RPT-01, RPT-02, RPT-03, RPT-04, GATE-01, GATE-02, GATE-03, HIST-01, HIST-02
- `.planning/PROJECT.md` — Scanner tech stack (Jinja2 + WeasyPrint for reports), architecture layers, constraints

### Phase scope
- `.planning/ROADMAP.md` — Phase 4 goal and success criteria (5 criteria that must be TRUE)

### Existing code (integration points)
- `src/scanner/schemas/finding.py` — FindingSchema with ai_analysis and ai_fix_suggestion fields (source data for reports)
- `src/scanner/schemas/scan.py` — ScanResultSchema with gate_passed, severity counts, duration
- `src/scanner/schemas/compound_risk.py` — CompoundRiskSchema for compound risk report section
- `src/scanner/models/scan.py` — ScanResult ORM model with gate_passed, ai_cost_usd columns
- `src/scanner/models/finding.py` — Finding ORM model with fingerprint for delta matching
- `src/scanner/core/orchestrator.py` — run_scan returns ScanResultSchema, quality gate logic at lines 205-210
- `src/scanner/cli/main.py` — CLI entry point where report generation will be triggered
- `src/scanner/config.py` — ScannerSettings where gate config will be added

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ScanResultSchema` — contains all data needed for reports (findings, severity counts, gate result, duration, tool warnings)
- `FindingSchema` — has ai_analysis, ai_fix_suggestion (JSON with before/after/explanation), fingerprint
- `CompoundRiskSchema` — compound risk data for dedicated report section
- `ScanResult` / `Finding` ORM models — SQLite persistence already working, query by scan_id, indexed by fingerprint
- `Rich` library — already used for CLI formatting, Typer for CLI commands

### Established Patterns
- Pydantic schemas for data contracts, SQLAlchemy ORM for persistence
- Async throughout (aiosqlite, async orchestrator)
- Config via `ScannerSettings` with `SCANNER_` env prefix
- Quality gate: `gate_passed` field on ScanResult, exit code logic in CLI

### Integration Points
- Report generation plugs in after `run_scan()` returns `ScanResultSchema` — before or after DB persistence
- CLI `scan` command triggers report generation and writes files to output directory
- Gate config extends `ScannerSettings` (new `GateConfig` section alongside existing `AIConfig`)
- Delta comparison queries SQLite for previous scan of same branch via `ScanResult.target_ref`

</code_context>

<specifics>
## Specific Ideas

- HTML report should feel like a modern security dashboard — clean, not cluttered
- PDF is for people who don't read code — keep it executive-level
- Gate PASSED/FAILED should be the first thing visible in both report types
- Delta section placement at top of HTML mirrors how security teams triage: "what changed since last time?"

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 04-reports-and-quality-gate*
*Context gathered: 2026-03-19*
