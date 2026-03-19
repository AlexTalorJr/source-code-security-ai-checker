# Phase 5: API, Dashboard, CI, and Notifications - Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Phase Boundary

The scanner becomes a fully operational service: REST API for scan lifecycle (trigger, poll, query), a web dashboard for scan history and trends, Jenkins pipeline integration, Slack/email notifications, and false positive management. Users interact via API, dashboard, or Jenkins — not just CLI.

</domain>

<decisions>
## Implementation Decisions

### Dashboard approach
- Server-rendered Jinja2 templates — reuses existing Jinja2 stack from HTML reports, no JS framework, no build step
- Three pages: scan history list, scan detail (findings/delta/gate), trends (severity over time, branch comparison)
- Authentication via API key in session cookie — simple login page, same SCANNER_API_KEY for API and dashboard
- Charts rendered server-side with matplotlib (same approach as PDF reports) — no JS charting library

### Scan API lifecycle
- Background task model: POST /api/scans returns 202 with scan ID immediately, client polls GET /api/scans/{id} for status
- Scan status progression: queued → running → completed → failed
- One scan at a time — if a scan is running, new requests get queued status and wait
- Core endpoint set:
  - POST /api/scans — trigger scan (accepts path or repo_url+branch)
  - GET /api/scans — list scan history
  - GET /api/scans/{id} — status and results
  - GET /api/scans/{id}/report — download HTML report
  - GET /api/scans/{id}/findings — paginated findings list
- Authentication: X-API-Key header on all /api/* endpoints except /api/health
- FastAPI dependency injection for auth check

### Notification content and triggers
- Notifications fire on every scan completion (both pass and fail)
- Slack: Rich Block Kit message — gate status (green/red emoji), severity breakdown table, branch name, delta summary (+N new, -M fixed), link to dashboard scan detail page
- Email: Styled HTML email with gate status banner, severity table, delta summary, dashboard link
- Email recipients configured in config.yml: `notifications.email.recipients: [list]`
- SMTP credentials via env vars (SCANNER_EMAIL_SMTP_HOST, SCANNER_EMAIL_SMTP_PORT, etc.)
- Both channels independently enable/disable via config.yml toggles

### False positive workflow
- Suppression by fingerprint globally — marking a finding as FP suppresses that fingerprint across ALL future scans (any branch)
- Reversible via both API and dashboard:
  - PUT /api/findings/{fingerprint}/suppress — mark as FP
  - DELETE /api/findings/{fingerprint}/suppress — unsuppress
  - Dashboard shows suppressed findings in a separate tab with unsuppress button
- Suppressed findings excluded from quality gate entirely — a Critical FP won't fail the gate
- Optional comment/reason when marking FP (for audit trail, not required)

### Jenkins integration
- Jenkinsfile.security stage ready to drop into existing pipelines
- Jenkins passes local workspace path to scanner via API (POST /api/scans with path)
- Quality gate result (exit code from API response) determines Jenkins stage pass/fail
- X-API-Key passed via Jenkins credentials/environment variable

### Claude's Discretion
- Jinja2 template styling, CSS, dashboard layout details
- Background task implementation (asyncio.Task, or simple queue)
- Slack Block Kit exact block structure
- Email HTML template design
- Suppression table schema details
- Pagination strategy for findings endpoint
- Jenkins pipeline syntax details

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — Phase 5 covers API-01, API-02, API-03, API-05, API-06, CI-01, CI-02, CI-03, NOTF-01, NOTF-02, NOTF-03, HIST-03, HIST-04
- `.planning/PROJECT.md` — Scanner tech stack, architecture layers, constraints (API key auth, self-hosted, SQLite only)

### Phase scope
- `.planning/ROADMAP.md` — Phase 5 goal and 5 success criteria

### Prior phase context
- `.planning/phases/04-reports-and-quality-gate/04-CONTEXT.md` — HTML report layout decisions, quality gate config, delta comparison approach (reuse patterns for dashboard)

### Existing code (integration points)
- `src/scanner/main.py` — FastAPI app factory, lifespan, router mount (dashboard routes will be added here)
- `src/scanner/api/router.py` — API router aggregator (new scan/findings routers mount here)
- `src/scanner/api/health.py` — Health endpoint pattern (auth excluded from this)
- `src/scanner/config.py` — ScannerSettings with api_key, slack_webhook_url, email_smtp_host fields already defined
- `src/scanner/core/orchestrator.py` — run_scan() returns (ScanResultSchema, findings, compound_risks) — API will call this
- `src/scanner/cli/main.py` — CLI scan command showing report generation flow (API reuses same pattern)
- `src/scanner/models/scan.py` — ScanResult ORM model for history queries
- `src/scanner/models/finding.py` — Finding ORM model with fingerprint field (suppression will key on this)
- `src/scanner/reports/` — HTML/PDF report generators (dashboard scan detail can reuse or link to these)
- `src/scanner/reports/delta.py` — compute_delta() for delta comparison (dashboard trends will use similar queries)
- `src/scanner/schemas/scan.py` — ScanResultSchema (API response serialization)
- `src/scanner/schemas/finding.py` — FindingSchema with ai_analysis, ai_fix_suggestion fields

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ScannerSettings.api_key` — API key field already exists, just needs auth middleware
- `ScannerSettings.slack_webhook_url` / `email_smtp_host` — notification config fields already defined
- `GateConfig.evaluate()` — quality gate logic reusable for API gate checks
- `compute_delta()` — delta comparison reusable for dashboard trends
- `generate_html_report()` / `generate_pdf_report()` — report generators for download endpoints
- `ReportData` dataclass — packages all data needed for report generation
- Jinja2 `PackageLoader` pattern from `scanner.reports` — extend for dashboard templates
- Rich/Typer CLI patterns — consistent with adding API-triggered equivalents

### Established Patterns
- Pydantic schemas for request/response contracts (extend for API endpoints)
- Async SQLAlchemy sessions via lifespan-managed factory
- FastAPI dependency injection (use for auth middleware)
- Config via ScannerSettings with SCANNER_ env prefix and config.yml YAML source
- Error isolation pattern from orchestrator (_run_adapter wrapper)

### Integration Points
- Dashboard routes mount on FastAPI app alongside /api router (e.g., /dashboard prefix)
- Scan API triggers orchestrator.run_scan() as background task
- Auth dependency injected on all /api/* routes except /api/health
- Notification service called after scan completion (in background task flow)
- Suppression table checked during gate evaluation and finding serialization
- Jenkins calls POST /api/scans with X-API-Key header, polls for result

</code_context>

<specifics>
## Specific Ideas

- Dashboard should feel lightweight — server-rendered, no SPA overhead, fits the self-hosted Docker constraint
- Slack messages should be scannable at a glance — gate status is the first thing you see (green/red)
- FP management is about reducing noise over time — teams build up a suppression list as they triage findings
- Jenkins integration should be drop-in: copy Jenkinsfile.security, set env vars, done

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 05-api-dashboard-ci-and-notifications*
*Context gathered: 2026-03-19*
