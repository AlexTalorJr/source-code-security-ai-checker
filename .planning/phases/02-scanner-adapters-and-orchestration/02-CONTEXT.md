# Phase 2: Scanner Adapters and Orchestration - Context

**Gathered:** 2026-03-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Run five security tools (Semgrep, cppcheck, Gitleaks, Trivy, Checkov) in parallel on a target codebase, normalize findings to the unified FindingSchema, deduplicate across tools, and persist results to SQLite. Support dual-mode input: local filesystem path (Jenkins workspace) and git repository URL with branch. Expose via CLI command.

</domain>

<decisions>
## Implementation Decisions

### Scan trigger mechanism
- CLI command: `python -m scanner scan --path /code` or `--repo-url URL --branch NAME`
- Stdout summary table (tool, findings count, status) + full results persisted to SQLite
- `--json` flag for machine-readable JSON output (for scripting/CI)
- Early quality gate: exit code 1 when Critical/High findings found, exit 0 otherwise

### Git repo handling
- Auth: support both SSH key mount (primary, standard for Bitbucket/Jenkins) and HTTPS token via `SCANNER_GIT_TOKEN` env var (fallback)
- Clone strategy: shallow clone (depth=1) for code scanners; full clone for Gitleaks (needs git history for secret scanning)
- Branch only (no tag/commit support) — matches release branch scanning use case
- Auto-delete temp clone directory after scan completes

### Partial failure behavior
- Scan status = "completed" with warnings list when tools fail/timeout (graceful degradation per SCAN-06)
- Prominent WARNING banner in CLI output showing which tools failed and why (e.g., "cppcheck timed out after 120s — C++ findings may be incomplete")
- Quality gate evaluates available findings only — tool failure does not auto-fail the gate (cppcheck timeout shouldn't block a PHP-only repo)
- Per-tool configurable timeouts in config.yml (e.g., semgrep: 180s, trivy: 120s) — some tools are naturally slower

### Scanner tool configuration
- Each tool individually enable/disable in config.yml (all enabled by default) — useful for repos without C++ or IaC
- Extra args field per tool in config.yml — power users can pass custom flags (e.g., cppcheck suppression file), sensible defaults out of the box
- Severity mapping: hardcoded sensible defaults per adapter (e.g., Semgrep ERROR→High, Trivy CRITICAL→Critical) — not configurable in v1
- Semgrep uses built-in rulesets only (p/security-audit, p/secrets) — custom aipix rules are v2 scope (RULES-01 to RULES-04)

### Claude's Discretion
- Scanner adapter interface design (base class, output parsing approach)
- Parallel execution strategy (asyncio.gather, subprocess management)
- Finding deduplication algorithm details (fingerprint matching, merge strategy)
- Config.yml structure for scanner sections
- Temp directory naming and location for git clones
- Exact CLI argument parsing library (click, typer, argparse)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — Phase 2 covers SCAN-01, SCAN-03, SCAN-04, SCAN-05, SCAN-06, SCAN-07
- `.planning/PROJECT.md` — Scanner tech stack, architecture layers, constraints

### Phase scope
- `.planning/ROADMAP.md` — Phase 2 goal and success criteria (5 criteria that must be TRUE)

### Existing code
- `src/scanner/schemas/finding.py` — FindingSchema with unified severity and fingerprint fields
- `src/scanner/schemas/scan.py` — ScanResultSchema with dual-mode fields (target_path + repo_url/branch)
- `src/scanner/core/fingerprint.py` — compute_fingerprint(file_path, rule_id, snippet) for dedup
- `src/scanner/config.py` — ScannerSettings with YAML + env var loading (scan_timeout already defined)
- `src/scanner/main.py` — FastAPI app factory with lifespan pattern
- `src/scanner/db/session.py` — Async SQLite engine and session factory

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `FindingSchema`: Ready-made Pydantic model with all fields scanners need to populate (tool, rule_id, severity, file_path, snippet, etc.)
- `ScanResultSchema`: Tracks scan execution with status, duration, per-severity counts, tool_versions dict
- `compute_fingerprint()`: Deterministic SHA-256 from file_path + rule_id + snippet — used for cross-tool dedup
- `ScannerSettings`: Config system with YAML + env var override — extend with per-tool sections

### Established Patterns
- Pydantic schemas in `scanner/schemas/` — adapters should produce `FindingSchema` instances
- Async SQLAlchemy with WAL mode — scan persistence should use existing session factory
- FastAPI lifespan for startup/shutdown — CLI can reuse settings loading pattern

### Integration Points
- Each scanner adapter produces `list[FindingSchema]` — orchestrator collects and deduplicates
- `ScanResultSchema.tool_versions` dict — adapters should report their tool version
- `ScanResultSchema.status` field — "completed" with warnings for partial failures
- SQLite models in `scanner/models/` — findings and scan results persisted via ORM

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches.

</specifics>

<deferred>
## Deferred Ideas

- Web interface for config management (enable/disable tools, edit args, timeouts via dashboard) — Phase 5 scope
- Custom Semgrep rules for aipix platform (RTSP auth, VMS API, webhooks) — v2 scope (RULES-01 to RULES-04)
- Tag/commit hash support for git ref (currently branch-only) — add if needed later

</deferred>

---

*Phase: 02-scanner-adapters-and-orchestration*
*Context gathered: 2026-03-18*
