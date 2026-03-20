# Codebase Concerns

**Analysis Date:** 2026-03-20

## Tech Debt

**Deprecated datetime API:**
- Issue: `datetime.utcnow()` is deprecated since Python 3.12. Used in 8 places across model defaults and orchestrator timestamps.
- Files: `src/scanner/models/scan.py:47`, `src/scanner/models/finding.py:40`, `src/scanner/models/suppression.py:19`, `src/scanner/core/orchestrator.py:141,261`, `src/scanner/core/scan_queue.py:63,180`, `src/scanner/dashboard/router.py:591`
- Impact: Deprecation warnings in Python 3.12+; will break in a future Python version.
- Fix approach: Replace all `datetime.utcnow()` with `datetime.now(datetime.UTC)` (or `datetime.now(timezone.utc)`).

**Dual schema migration strategy (ad-hoc + Alembic):**
- Issue: `src/scanner/main.py` uses `_apply_schema_updates()` with raw `ALTER TABLE` SQL as a parallel migration system alongside Alembic. This means schema evolution is tracked in two places.
- Files: `src/scanner/main.py:16-37`, `alembic/versions/001_add_skip_ai_to_scans.py`
- Impact: Alembic and the inline migration function can diverge; `_apply_schema_updates` was a workaround for pre-Alembic databases and was never removed.
- Fix approach: Migrate remaining ad-hoc columns to proper Alembic migration files and remove `_apply_schema_updates`.

**Compound risks not returned in `_build_report_data`:**
- Issue: In `src/scanner/dashboard/router.py:237`, `compound_risks=[]` is hardcoded when building `ReportData` for dashboard-served HTML/PDF reports. Compound risks are persisted to the DB during scanning but never loaded back for report display.
- Files: `src/scanner/dashboard/router.py:237`
- Impact: Quality gate in report re-evaluation (`fail_reasons`) also passes `[]` for compound risks, potentially showing "PASSED" on a scan that actually failed due to compound risks.
- Fix approach: Load `CompoundRisk` records from the database in `_build_report_data` and populate `compound_risks` correctly.

**API `GET /scans/{scan_id}/report` returns stub HTML:**
- Issue: `src/scanner/api/scans.py:192-200` generates a minimal inline HTML string, not the full Jinja2-templated report. The dashboard has the real implementation but the REST API endpoint is incomplete.
- Files: `src/scanner/api/scans.py:192-200`
- Impact: API consumers expecting a full report get summary-only output without findings, delta, or AI analysis.
- Fix approach: Reuse `_build_report_data` + `generate_html_report` from the dashboard, or deduplicate into a shared service function.

**Hardcoded client-specific platform context in AI prompts:**
- Issue: `src/scanner/ai/prompts.py` and `src/scanner/ai/analyzer.py` contain hardcoded references to "aipix video surveillance platform," `AIPIX_SECURITY_CONCERNS`, and `COMPONENT_FRAMEWORK_MAP` with component names (`vms`, `mediaserver`, `infra`, `client`, `mobile`). This makes the tool client-specific rather than generic.
- Files: `src/scanner/ai/prompts.py:8-42,62`, `src/scanner/ai/analyzer.py:228`
- Impact: Any user of this scanner not running the aipix platform receives misleading AI analysis framing; the tool is not truly reusable as a generic scanner.
- Fix approach: Make platform context configurable via `config.yml` (e.g., `ai.platform_name`, `ai.platform_description`, `ai.component_frameworks` map) and load from settings.

**`false_positive` column unused:**
- Issue: `src/scanner/models/finding.py:39` defines a `false_positive` column with a comment "Phase 5" that was never wired up. The suppression mechanism uses a separate `Suppression` table; `false_positive` is always 0.
- Files: `src/scanner/models/finding.py:39`
- Impact: Dead schema column that adds confusion; never read or written by application code.
- Fix approach: Remove the column via Alembic migration, or wire it up as a per-scan override (vs. global suppression).

## Known Bugs

**Temporary HTML file leaked on dashboard HTML report:**
- Symptoms: When serving the HTML report via the dashboard, a temporary file is written then read, but unlike the PDF path the HTML temp file is never deleted.
- Files: `src/scanner/dashboard/router.py:264-267`
- Trigger: Any request to `GET /dashboard/scans/{scan_id}/report`
- Workaround: None; temp files accumulate in `/tmp` over time.

**Gitleaks report file uses PID instead of a unique token:**
- Issue: `src/scanner/adapters/gitleaks.py:31` names the report file `gitleaks-{os.getpid()}.json`. Under asyncio all adapters share the same PID; two concurrent gitleaks scans (impossible with serial queue but possible if `persist=False` is called directly) would collide.
- Files: `src/scanner/adapters/gitleaks.py:31`
- Trigger: Calling `run_scan` with `persist=False` from multiple concurrent async tasks.
- Workaround: Scan queue is serial, so not triggered in practice.

## Security Considerations

**Session cookie missing `secure` and `samesite` attributes:**
- Risk: The dashboard session cookie (`scanner_session`) is set with `httponly=True` but without `secure=True` or `samesite` attribute.
- Files: `src/scanner/dashboard/router.py:145-151`
- Current mitigation: Cookie is httponly, preventing JS access.
- Recommendations: Add `secure=True` for production HTTPS deployments and `samesite="Lax"` to prevent CSRF on cookie-authenticated endpoints.

**Scan progress endpoint has no authentication:**
- Risk: `GET /api/scans/{scan_id}/progress` is explicitly documented "no auth required for polling" and is unauthenticated. Any unauthenticated caller can discover the existence of scan IDs and their current scan stage.
- Files: `src/scanner/api/scans.py:139-161`
- Current mitigation: Only stage name and generic details are returned; no finding data is exposed.
- Recommendations: Consider requiring API key for progress polling, or limit the response to avoid confirming scan ID existence to unauthenticated callers.

**No rate limiting on API or login endpoint:**
- Risk: The login endpoint `POST /dashboard/login` and all API key-protected endpoints have no rate limiting. Brute-force attacks against the API key or dashboard are unrestricted.
- Files: `src/scanner/dashboard/router.py:138-152`, `src/scanner/api/auth.py`
- Current mitigation: Timing-safe comparison (`secrets.compare_digest`) prevents timing attacks.
- Recommendations: Add rate limiting middleware (e.g., `slowapi` or nginx upstream limit) for production deployments.

**No CORS policy configured:**
- Risk: FastAPI defaults to no CORS headers; there is no `CORSMiddleware` configured. If the API is accessed from a browser-based integration, cross-origin requests will be blocked silently.
- Files: `src/scanner/main.py`
- Current mitigation: The API is primarily intended for CLI/CI use, not direct browser consumption.
- Recommendations: Explicitly configure CORS policy (even if restrictive) to document the intent.

**Git token written to filesystem via GIT_ASKPASS:**
- Risk: `src/scanner/core/git.py:36-39` writes the git token to a temporary shell script in the clone directory before deletion. The script is `chmod 700` but the token is briefly on disk in plaintext.
- Files: `src/scanner/core/git.py:36-39`
- Current mitigation: Token script is in the temp clone dir which is cleaned up in the `finally` block.
- Recommendations: Use the `GIT_CONFIG_COUNT`/`GIT_CONFIG_KEY_0`/`GIT_CONFIG_VALUE_0` env var approach to inject credentials without writing to disk, or use `git credential helper` via environment.

**No pagination upper bound on API:**
- Risk: `page_size` parameters in `GET /api/scans` and `GET /api/scans/{scan_id}/findings` accept arbitrary integers with no maximum cap. A caller can request all rows in a single query.
- Files: `src/scanner/api/scans.py:87`, `src/scanner/api/scans.py:211`
- Current mitigation: None.
- Recommendations: Add `page_size: int = Field(default=20, le=200)` to enforce an upper bound.

## Performance Bottlenecks

**Per-request suppressed fingerprints full-table scan:**
- Problem: Every request to `GET /api/scans/{scan_id}/findings` and every dashboard page load calls `get_suppressed_fingerprints()`, which selects all rows from the `suppressions` table.
- Files: `src/scanner/core/suppression.py:9-19`, `src/scanner/api/scans.py:228`, `src/scanner/dashboard/router.py:368`
- Cause: No caching; full `SELECT fingerprint FROM suppressions` on every request.
- Improvement path: In-memory LRU cache with invalidation on suppress/unsuppress, or add an `is_suppressed` index query per finding rather than bulk load when the suppression table grows large.

**Synchronous matplotlib chart generation blocks async event loop:**
- Problem: `_generate_severity_over_time` and `_generate_branch_comparison` in `src/scanner/dashboard/router.py:454-532` call matplotlib synchronously inside an async route handler. For large scan history sets this blocks the event loop.
- Files: `src/scanner/dashboard/router.py:454-532`
- Cause: matplotlib operations are CPU-bound and not offloaded to a thread pool.
- Improvement path: Wrap chart generation calls in `await asyncio.to_thread(...)` as already done for SMTP.

**DB engine created and disposed per CLI scan:**
- Problem: `src/scanner/cli/main.py:46-53` creates a new SQLAlchemy async engine purely to query delta comparisons, then disposes it. The main `run_scan` call already creates and disposes another engine. Two engines are created per CLI scan.
- Files: `src/scanner/cli/main.py:42-54`, `src/scanner/core/orchestrator.py:286,361`
- Cause: Delta query was added as an afterthought in the CLI path without sharing the engine already used by `run_scan`.
- Improvement path: Pass the session or engine from `run_scan` to the delta function, or move delta computation inside `run_scan` itself.

## Fragile Areas

**`for...else` construct in AI analyzer's component loop:**
- Files: `src/scanner/ai/analyzer.py:96-127`
- Why fragile: Python's `for...else` (where `else` runs when the loop completes without `break`) is used to track whether all sub-batches completed. The `break` when `_analyze_component` returns `None` skips the `else` clause. This is a subtle control flow pattern that is easy to break when refactoring the retry/skip logic.
- Safe modification: Add an explicit `all_batches_ok` boolean flag instead of relying on `for...else`.
- Test coverage: Covered by `tests/phase_03/test_graceful_degradation.py` but the `for...else` branch is hard to test in isolation.

**`_on_tool_complete` closure captures mutable list:**
- Files: `src/scanner/core/orchestrator.py:176-186`
- Why fragile: The `_on_tool_complete` callback closes over `completed_tools` and `enabled_adapters`. Since adapters run concurrently via `asyncio.gather`, concurrent appends to `completed_tools` are safe (CPython GIL), but any refactor introducing true threading would create a race condition.
- Safe modification: Use a thread-safe structure if worker threads are ever introduced.
- Test coverage: Covered in `tests/phase_02/test_orchestrator.py`.

**Ad-hoc schema migration at startup:**
- Files: `src/scanner/main.py:16-37`
- Why fragile: `_apply_schema_updates` introspects the live database schema on every application startup and conditionally issues `ALTER TABLE`. If an Alembic migration adds the same column, the guard `if col not in scans_cols` prevents a duplicate, but any typo in the SQL or column name check produces a silent no-op or unhandled exception at startup.
- Safe modification: Remove this function and rely solely on Alembic.
- Test coverage: No direct test for `_apply_schema_updates`; indirectly tested via lifespan startup in phase 01 tests.

**Checkov severity is derived from rule prefix only:**
- Files: `src/scanner/adapters/checkov.py:12-36`
- Why fragile: Severity is mapped by `check_id` prefix (`CKV_DOCKER`, `CKV_K8S`, etc.) with a fallback to `MEDIUM`. New Checkov versions regularly add new framework checks with new prefixes; unknown prefixes silently default to MEDIUM regardless of actual severity.
- Safe modification: Check Checkov's JSON output for a native `severity` field (available in newer Checkov versions) before falling back to prefix-based mapping.
- Test coverage: `tests/phase_02/test_adapter_checkov.py`.

## Scaling Limits

**SQLite single-writer limit:**
- Current capacity: Handles all current workloads (single instance, serial scan queue).
- Limit: SQLite WAL mode allows concurrent reads but only one writer at a time. If multiple API server instances are deployed behind a load balancer, concurrent scan workers will serialize or fail on write contention.
- Scaling path: Migrate to PostgreSQL (SQLAlchemy async driver `asyncpg` already supportable) when multi-instance deployment is needed. The Alembic setup makes this migration easier.

**In-memory progress tracking lost on restart:**
- Current capacity: `ScanQueue._progress` dict is in-process memory.
- Limit: Any restart during a running scan loses progress state; `recover_stuck_scans` re-queues the scan but progress polling returns `"queued"` until the next scan starts producing events.
- Scaling path: Persist progress to a Redis cache or a lightweight DB column if real-time progress needs to survive restarts.

**Trends page loads all completed scans into memory:**
- Current capacity: `GET /dashboard/trends` queries all completed scans with no pagination (`select(ScanResult).where(status == "completed")`).
- Limit: With thousands of scans this loads the full dataset into memory for chart generation.
- Scaling path: Add a `LIMIT` clause (e.g., last 100 scans) or use aggregated SQL queries for chart data instead of Python-side aggregation.

## Dependencies at Risk

**`weasyprint>=68.0` complex system dependency:**
- Risk: WeasyPrint requires `libpango`, `libharfbuzz`, and other system libs. Version incompatibilities between WeasyPrint and system libs surface as cryptic PDF generation failures.
- Impact: PDF report generation fails silently (caught by try/except in CLI and dashboard); users get no PDF output.
- Migration plan: Consider `reportlab` or `fpdf2` as alternatives with fewer system dependencies, or document the required system library versions explicitly.

**Pinned external tool versions in Dockerfile:**
- Risk: Gitleaks v8.30.0 and Trivy v0.69.3 are hardcoded in `Dockerfile`. Security fixes in those tools require a manual Dockerfile update and image rebuild.
- Files: `Dockerfile:19-27`
- Impact: Stale scanner versions may have unpatched vulnerabilities or miss new detection rules.
- Migration plan: Use a nightly build process or Dependabot to track and update tool versions.

**AI cost model hardcoded in source:**
- Risk: Claude API pricing (`INPUT_PRICE_PER_MTOK = 3.0`, `OUTPUT_PRICE_PER_MTOK = 15.0`) is hardcoded in `src/scanner/ai/cost.py`. If Anthropic changes pricing, budget enforcement silently miscalculates.
- Files: `src/scanner/ai/cost.py:1-6`
- Impact: Budget enforcement may over- or under-spend without any visible error.
- Migration plan: Move pricing constants to `config.yml` / `ScannerSettings.ai` so they can be updated without a code change.

## Missing Critical Features

**No compound risk display in dashboard scan detail:**
- Problem: The scan detail page (`GET /dashboard/scans/{scan_id}`) and related templates do not load or display compound risks from the database. They are stored after AI analysis but never shown in the UI.
- Blocks: Users cannot see AI-identified cross-component threats through the dashboard.

**No suppression audit trail:**
- Problem: `src/scanner/models/suppression.py` stores a `reason` field but no `suppressed_by` (user/API key), `suppressed_at` timestamp, or change history.
- Blocks: Security auditors cannot determine who suppressed a finding or when, which is a compliance gap.

## Test Coverage Gaps

**`_apply_schema_updates` migration logic:**
- What's not tested: The inline Alembic bypass in `src/scanner/main.py:16-37` has no direct test. Failure produces a silent no-op or startup crash.
- Files: `src/scanner/main.py:16-37`
- Risk: Columns silently not added on upgrade; runtime AttributeErrors on scan writes.
- Priority: Medium

**Dashboard compound_risks empty hardcode:**
- What's not tested: No test verifies that compound risks are loaded and rendered in `_build_report_data`; the hardcoded `compound_risks=[]` passes all current tests.
- Files: `src/scanner/dashboard/router.py:237`
- Risk: Compound risks are silently dropped from dashboard reports without any failing test.
- Priority: High

**Gitleaks concurrent scan collision:**
- What's not tested: The PID-based temp file name collision scenario has no test.
- Files: `src/scanner/adapters/gitleaks.py:31`
- Risk: Concurrent scans (if `persist=False` is used) could corrupt each other's gitleaks output.
- Priority: Low (serial queue prevents this in practice)

**HTML temp file cleanup (leak):**
- What's not tested: No test verifies that the temporary HTML file in `dashboard_html_report` is deleted after serving.
- Files: `src/scanner/dashboard/router.py:264-267`
- Risk: Disk space exhaustion under high report request volume.
- Priority: Medium

---

*Concerns audit: 2026-03-20*
