# Phase 3: AI Analysis - Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Enrich scan findings with Claude API-powered semantic analysis: business logic risk identification, framework-specific fix suggestions, and cross-tool correlation into compound risk entries. Token budgeting to stay under configurable cost limit. Graceful degradation when Claude API is unavailable. Reports and dashboard display are separate phases.

</domain>

<decisions>
## Implementation Decisions

### Prompt strategy
- Batch findings by component using directory-based grouping (top-level directory maps to component)
- Each component batch is a separate API call to Claude
- Final cross-component correlation call after all component batches complete
- System prompt embeds aipix-specific security concerns from PROJECT.md (RTSP access, API tokens, tenant isolation, webhooks, K8s misconfig, C++ memory safety, IDOR)
- System prompt includes framework context per component (Laravel for PHP, STL for C++, Helm for infra)
- Finding snippet only — no expanded source code context beyond what scanners captured (file_path, line, snippet, rule_id)
- Claude returns structured JSON responses (not free-form markdown)

### Token budgeting
- Severity-first priority: analyze Critical/High findings first, then Medium if budget remains, skip Low/Info
- Pre-estimate tokens per batch, sort batches by severity priority
- Stop sending batches when approaching ~80% of budget
- Budget limit configurable in config.yml (`ai.max_cost_per_scan`, default $5)
- Log actual cost from API response after each call
- Store per-scan AI cost in ScanResult DB record (new column) + show in CLI summary
- Cost also displayed in web dashboard (Phase 5 scope for UI, but DB column added now)
- Report which components were analyzed vs skipped due to budget

### Cross-tool correlation
- Separate final API call with per-component AI summaries as input
- Compound risk entries stored in dedicated DB table (`compound_risks`) with join table to findings
- Each compound risk has its own severity assigned by Claude
- Compound risk severity affects quality gate — Critical/High compound risks fail the gate even if individual findings were Medium
- Compound risks reference findings by fingerprint

### Fix suggestion format
- Structured JSON: `before` code, `after` code, `explanation` fields
- Framework-specific fixes (Eloquent for Laravel, smart pointers for C++, etc.)
- When no concrete fix possible (architectural/config issues): `fix_suggestion` is null, textual `recommendation` with investigation steps provided instead
- Reports will render before/after as visual diff (Phase 4 scope for rendering)

### Graceful degradation (AI-05)
- When Claude API is unavailable: scan completes without AI enrichment
- AI fields remain null on findings, compound_risks table empty for that scan
- Report clearly indicates "AI analysis was skipped" with reason
- No retry loop — single attempt per batch, fail fast on API errors

### Claude's Discretion
- Exact system prompt wording and few-shot examples
- JSON schema validation approach for Claude responses
- Token estimation algorithm (tiktoken vs character heuristic)
- Retry/backoff strategy for transient API errors (rate limits)
- Anthropic SDK version and async client setup
- Config.yml structure for AI section

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — Phase 3 covers AI-01, AI-02, AI-03, AI-04, AI-05
- `.planning/PROJECT.md` — Key security concerns (7 items), scanner tech stack, architecture layers, $5 cost constraint

### Phase scope
- `.planning/ROADMAP.md` — Phase 3 goal and success criteria (5 criteria that must be TRUE)

### Existing code
- `src/scanner/schemas/finding.py` — FindingSchema with `ai_analysis` and `ai_fix_suggestion` nullable fields already defined
- `src/scanner/models/finding.py` — Finding ORM model with `ai_analysis` and `ai_fix_suggestion` columns (nullable)
- `src/scanner/config.py` — ScannerSettings with `claude_api_key` field, extend with AI config section
- `src/scanner/core/orchestrator.py` — `run_scan()` function where AI analysis integrates after deduplication
- `src/scanner/schemas/scan.py` — ScanResultSchema, extend with AI cost tracking field

### Prior phase context
- `.planning/phases/02-scanner-adapters-and-orchestration/02-CONTEXT.md` — Orchestrator design, dedup strategy, partial failure handling

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `FindingSchema.ai_analysis` / `ai_fix_suggestion`: Already defined nullable fields — AI module populates these
- `Finding` ORM model: Already has `ai_analysis` and `ai_fix_suggestion` columns
- `ScannerSettings.claude_api_key`: Config field ready for env var `SCANNER_CLAUDE_API_KEY`
- `deduplicate_findings()`: AI analysis runs on already-deduplicated findings list
- `run_scan()` in orchestrator: Natural integration point — AI analysis after dedup, before DB persist

### Established Patterns
- Async everywhere: orchestrator uses `asyncio.gather` — AI calls should be async too
- Pydantic schemas for data contracts: AI response should have its own schema
- Config via `ScannerSettings` with YAML + env var: AI config section follows same pattern
- Per-adapter error isolation via `_run_adapter` wrapper: similar pattern for AI batch error handling

### Integration Points
- AI analysis inserts between `deduplicate_findings()` and DB persistence in `run_scan()`
- New `compound_risks` and `compound_risk_findings` tables in `scanner/models/`
- `ScanResultSchema` needs new field for AI cost tracking
- CLI summary table (`format_summary_table`) should show AI cost line
- Quality gate logic needs to consider compound risk severities

</code_context>

<specifics>
## Specific Ideas

- Cost must be visible in web dashboard (Phase 5 builds UI, but DB column exists from Phase 3)
- Component grouping by directory maps naturally to aipix's multi-language repo (PHP VMS, C++ Mediaserver, K8s infra in separate dirs)

</specifics>

<deferred>
## Deferred Ideas

- Web dashboard display of AI cost — Phase 5 scope (DB column added in Phase 3)
- Visual diff rendering of before/after fixes — Phase 4 scope (reports)
- Configurable system prompt in config.yml — keep hardcoded for v1, consider for v2

</deferred>

---

*Phase: 03-ai-analysis*
*Context gathered: 2026-03-19*
