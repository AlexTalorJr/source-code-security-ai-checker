# Architecture

**Analysis Date:** 2026-03-20

## Pattern Overview

**Overall:** Layered async service with dual entry points (CLI + HTTP API) and background worker queue

**Key Characteristics:**
- Single Python package `scanner` under `src/scanner/` using the `src` layout
- FastAPI application with async SQLite (aiosqlite + SQLAlchemy 2.0) for persistence
- Background scan queue (`ScanQueue`) processes scans serially in a single async worker task
- Adapter pattern wraps five external CLI tools (semgrep, cppcheck, gitleaks, trivy, checkov), normalizing output to `FindingSchema`
- AI enrichment layer (Anthropic Claude) is optional and gracefully degrades — scans complete without it if the API key is absent or the call fails

## Layers

**Configuration Layer:**
- Purpose: Loads and validates all settings; single source of truth for the whole application
- Location: `src/scanner/config.py`
- Contains: `ScannerSettings` (pydantic-settings), `ScannersConfig`, `AIConfig`, `GateConfig`, `NotificationsConfig`
- Depends on: Nothing internal
- Used by: All layers; settings object is passed down explicitly (no globals)

**Schemas Layer:**
- Purpose: Pydantic data contracts for in-memory data transfer
- Location: `src/scanner/schemas/`
- Contains: `FindingSchema`, `ScanResultSchema`, `CompoundRiskSchema`, `Severity` (IntEnum)
- Depends on: Nothing internal
- Used by: Adapters, orchestrator, AI layer, API, CLI, reports

**Models Layer (ORM):**
- Purpose: SQLAlchemy ORM models mapping to SQLite tables
- Location: `src/scanner/models/`
- Contains: `ScanResult`, `Finding`, `CompoundRisk`, `Suppression`, `Base`
- Depends on: `src/scanner/models/base.py` (declarative base)
- Used by: Orchestrator, scan queue worker, API endpoints, dashboard

**Database Layer:**
- Purpose: Async engine and session factory creation; SQLite WAL mode setup
- Location: `src/scanner/db/session.py`
- Contains: `create_engine()`, `create_session_factory()`
- Depends on: aiosqlite, SQLAlchemy async extensions
- Used by: `main.py` lifespan, orchestrator (when persisting directly), scan queue worker

**Adapters Layer:**
- Purpose: Wrap external CLI security tools; normalize tool output into `FindingSchema` list
- Location: `src/scanner/adapters/`
- Contains: `ScannerAdapter` (abstract base), five concrete adapters (`SemgrepAdapter`, `CppcheckAdapter`, `GitleaksAdapter`, `TrivyAdapter`, `CheckovAdapter`)
- Depends on: Schemas layer, `core/fingerprint.py`, `core/exceptions.py`
- Used by: Orchestrator exclusively

**Core Layer:**
- Purpose: Central scan execution logic and cross-cutting utilities
- Location: `src/scanner/core/`
- Contains:
  - `orchestrator.py` — `run_scan()`, adapter dispatch, deduplication, AI enrichment call, persistence
  - `scan_queue.py` — `ScanQueue` async worker, crash recovery
  - `fingerprint.py` — deterministic SHA-256 fingerprint computation
  - `git.py` — `clone_repo()`, `cleanup_clone()` for remote repo targets
  - `suppression.py` — CRUD for suppressed fingerprints
  - `exceptions.py` — `ScannerError`, `ScannerTimeoutError`, `ScannerExecutionError`, `GitCloneError`
- Depends on: Adapters, AI, Schemas, Models, DB, Config layers
- Used by: CLI, API, Dashboard

**AI Layer:**
- Purpose: Claude API integration for enriching findings with business risk context and generating compound risks
- Location: `src/scanner/ai/`
- Contains: `AIAnalyzer`, `cost.py` (budget tracking), `prompts.py` (prompt builders), `schemas.py` (response schemas)
- Depends on: `anthropic` SDK, Schemas layer, Config layer
- Used by: Orchestrator only (`enrich_with_ai()` in `core/orchestrator.py`)

**API Layer:**
- Purpose: JSON REST API with API key authentication
- Location: `src/scanner/api/`
- Contains: `router.py` (aggregator), `scans.py`, `findings.py`, `health.py`, `auth.py`, `schemas.py` (request/response models)
- Depends on: Core, Models, DB, Config layers
- Used by: FastAPI app, external HTTP clients, CI/CD pipelines

**Dashboard Layer:**
- Purpose: Server-rendered HTML web UI using Jinja2 templates, cookie-based session auth
- Location: `src/scanner/dashboard/`
- Contains: `router.py` (all page and action handlers), `auth.py` (cookie session), `templates/` (Jinja2 `.html.j2` files)
- Depends on: Core, Models, Reports layers
- Used by: FastAPI app; browser-facing

**Reports Layer:**
- Purpose: Generate HTML and PDF scan reports with charts and delta comparison
- Location: `src/scanner/reports/`
- Contains: `html_report.py`, `pdf_report.py`, `charts.py`, `delta.py`, `models.py` (`ReportData`, `DeltaResult`), `templates/`
- Depends on: Schemas layer, matplotlib, weasyprint, Jinja2
- Used by: CLI (generates files to disk), Dashboard (generates in-memory for HTTP response)

**Notifications Layer:**
- Purpose: Post-scan dispatch to Slack and email channels
- Location: `src/scanner/notifications/`
- Contains: `service.py` (dispatcher), `slack.py`, `email_sender.py`, `templates/email.html.j2`
- Depends on: Schemas, Config layers
- Used by: Scan queue worker after scan completion

**CLI Layer:**
- Purpose: Typer CLI for triggering scans directly without the HTTP server
- Location: `src/scanner/cli/main.py`
- Contains: `scan` command; renders rich tables and generates HTML/PDF reports
- Depends on: Core orchestrator, Reports layer, Config, Schemas
- Used by: `python -m scanner` via `src/scanner/__main__.py`

## Data Flow

**HTTP API Scan Flow:**

1. Client sends `POST /api/scans` with `{path, repo_url, branch, skip_ai}` + API key header
2. `api/scans.py` creates a `ScanResult` record with status `queued`, flushes to DB, returns scan ID
3. `ScanQueue.enqueue(scan_id)` adds ID to the async queue
4. Background `ScanQueue.worker()` picks up the scan ID, marks it `running`
5. Worker calls `core/orchestrator.run_scan()` with `persist=False`
6. Orchestrator clones repo if needed via `core/git.clone_repo()`
7. All enabled adapters run in parallel via `asyncio.gather()`
8. Results are collected, warnings separated; per-tool versions captured
9. `deduplicate_findings()` removes duplicates by SHA-256 fingerprint
10. `enrich_with_ai()` calls `AIAnalyzer.analyze()` — skipped gracefully if no API key
11. `GateConfig.evaluate()` checks severity thresholds and compound risks
12. Worker persists `ScanResult`, `Finding` records, `CompoundRisk` records to SQLite
13. `notifications/service.notify_scan_complete()` fires to Slack and/or email
14. Client polls `GET /api/scans/{id}/progress` until `stage: completed`

**CLI Scan Flow:**

1. `scanner scan --path /code` or `--repo-url ... --branch ...`
2. `ScannerSettings` loaded from `config.yml` + env vars
3. `asyncio.run(run_scan(..., persist=True))` — orchestrator handles its own DB session
4. Reports generated to `reports/` directory as HTML and PDF files
5. Rich table printed to stdout; exits with code 1 if gate fails

**State Management:**
- All persistent state lives in SQLite at `db_path` (default `/data/scanner.db`)
- In-flight state (current scan ID, progress) lives in `ScanQueue._progress` dict in memory
- Application state (engine, session factory, settings, scan queue) stored on `app.state` in FastAPI lifespan

## Key Abstractions

**ScannerAdapter:**
- Purpose: Uniform interface for all external scanner CLI tools
- Examples: `src/scanner/adapters/semgrep.py`, `src/scanner/adapters/trivy.py`
- Pattern: Abstract base with `tool_name` property, `run()` async method, and `_execute()` subprocess helper; all adapters call `compute_fingerprint()` to assign deterministic IDs to findings

**FindingSchema:**
- Purpose: Normalized in-memory representation of any security finding from any tool
- Examples: `src/scanner/schemas/finding.py`
- Pattern: Pydantic BaseModel; fingerprint, tool name, severity (IntEnum), file path, line range, AI-enrichable fields (`ai_analysis`, `ai_fix_suggestion`)

**ScannerSettings:**
- Purpose: Single hierarchical configuration object passed throughout the system
- Examples: `src/scanner/config.py`
- Pattern: pydantic-settings `BaseSettings` with YAML as lowest priority source and `SCANNER_*` env vars overriding; nested sub-models for `scanners`, `ai`, `gate`, `notifications`

**ScanQueue:**
- Purpose: Decouple scan triggering from scan execution; serialize scan runs
- Examples: `src/scanner/core/scan_queue.py`
- Pattern: `asyncio.Queue[int]` holding scan IDs; single persistent worker coroutine started in FastAPI lifespan; crash recovery re-enqueues `running`/`queued` scans on startup

**AIAnalyzer:**
- Purpose: Batch Claude API calls per component, enforce cost budget, produce compound risks
- Examples: `src/scanner/ai/analyzer.py`
- Pattern: Groups findings by top-level directory; sorted batches by max severity; pre-estimates token cost before each call; retry on empty responses; separate correlation pass for cross-component compound risks

## Entry Points

**FastAPI Server:**
- Location: `src/scanner/main.py` (`app = create_app()`)
- Triggers: `uvicorn scanner.main:app` or `fastapi run`; Dockerfile exposes port 8000
- Responsibilities: Lifespan startup (DB init, schema migrations, scan queue worker), API router at `/api`, dashboard router at `/dashboard`

**CLI:**
- Location: `src/scanner/cli/main.py` (Typer app), `src/scanner/__main__.py` (entry dispatch)
- Triggers: `python -m scanner scan --path ...` or `scanner scan ...`
- Responsibilities: Load settings, call `run_scan()`, render results, generate reports, exit with gate-appropriate exit code

## Error Handling

**Strategy:** Graceful degradation — individual adapter failures never abort a scan; AI enrichment failures are caught and logged; notification failures are caught and logged

**Patterns:**
- Each adapter runs inside `_run_adapter()` which catches all exceptions and returns `(tool_name, exception)` — failures become warnings in the scan result `error_message`
- AI enrichment: `enrich_with_ai()` wraps `AIAnalyzer.analyze()` in a try/except returning the original findings unchanged on any failure
- Notification dispatch: each channel wrapped in individual try/except with `logger.warning`
- `ScannerTimeoutError` raised by `ScannerAdapter._execute()` when asyncio timeout fires
- CLI exits with code 1 on gate failure, code 2 on argument errors

## Cross-Cutting Concerns

**Logging:** `logging.getLogger(__name__)` per module; log level from `ScannerSettings.log_level`; no third-party logging framework

**Validation:** Pydantic v2 for all API request/response models (`src/scanner/api/schemas.py`) and internal data contracts (`src/scanner/schemas/`); settings validated by pydantic-settings

**Authentication:**
- API: Bearer API key via `Authorization: Bearer <key>` header; enforced with `Depends(require_api_key)` in `src/scanner/api/auth.py`
- Dashboard: Cookie-based session token set on login; `require_dashboard_auth()` in `src/scanner/dashboard/auth.py` checks cookie on every protected route

---

*Architecture analysis: 2026-03-20*
