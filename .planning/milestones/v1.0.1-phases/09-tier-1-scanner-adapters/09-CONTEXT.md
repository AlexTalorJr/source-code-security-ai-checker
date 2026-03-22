# Phase 9: Tier-1 Scanner Adapters - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement 4 new scanner adapters (gosec, Bandit, Brakeman, cargo-audit) using the Phase 8 plugin registry. Each adapter follows the established ScannerAdapter pattern: subclass, implement `run()` with native JSON parsing, register via `config.yml`. All findings flow through existing AI analysis and quality gate pipeline.

</domain>

<decisions>
## Implementation Decisions

### Severity mapping
- Follow Phase 7 research report recommendations for each tool
- gosec: map severity HIGH/MEDIUM/LOW directly to Severity.HIGH/MEDIUM/LOW
- Bandit: use confidence × severity matrix — HIGH sev + HIGH conf → CRITICAL, HIGH sev + MED conf → HIGH, MED sev + HIGH conf → MEDIUM, etc. Reduces noise from low-confidence findings
- Brakeman: confidence-weighted — warnings with 'Weak' confidence get downgraded one severity level
- cargo-audit: CVSS-based ranges — 9.0+ → CRITICAL, 7.0-8.9 → HIGH, 4.0-6.9 → MEDIUM, 0.1-3.9 → LOW, no CVSS → MEDIUM (safe default)

### Output parsing strategy
- Parse each tool's native JSON output directly (not SARIF) — consistent with semgrep.py pattern
- SARIF helper deferred to v1.0.2 (SARIF-01 requirement)
- Each adapter: run tool with `--json`/`-f json`/`--format json`, parse stdout, map fields to FindingSchema
- Same pattern as existing adapters — no shared helper abstractions for this phase
- For single-line tools (gosec, cargo-audit): set `line_end = line_start`

### cargo-audit specifics
- If no `Cargo.lock` found: run `cargo generate-lockfile` first to generate it from `Cargo.toml`
- `file_path` in FindingSchema = `"Cargo.lock"`, `line_start`/`line_end` = None (dependency vulnerability, not source location)
- `rule_id` = advisory ID (e.g., `RUSTSEC-2023-0001`)
- Only report actual vulnerabilities (CVEs/advisories) as findings — exclude unmaintained/yanked crate warnings (informational noise)

### Bandit + Semgrep overlap
- No deduplication — show findings from both tools independently. Each has distinct `tool` field
- Cross-tool dedup planned for v1.0.3 (DEDUP-01)
- Quality gate treats all findings independently regardless of source tool — no special weighting for overlap
- Both scanners auto-enabled for Python projects via `languages: ["python"]` in config.yml

### Claude's Discretion
- Exact CLI command construction per tool (flags, excludes, target path handling)
- Error handling for non-zero exit codes per tool (some tools use exit code 1 for "findings found")
- Test fixture structure and mock data
- Whether to include snippet extraction (some tools include source code context, others don't)
- Config.yml default values for timeout and extra_args per scanner

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Adapter pattern (copy this)
- `src/scanner/adapters/base.py` — ScannerAdapter abstract base class (tool_name, run, _version_command, _execute)
- `src/scanner/adapters/semgrep.py` — Reference implementation: JSON parsing, severity mapping, FindingSchema construction
- `src/scanner/schemas/finding.py` — FindingSchema fields: fingerprint, tool, rule_id, file_path, line_start, line_end, snippet, severity, title, description
- `src/scanner/schemas/severity.py` — Severity enum (CRITICAL, HIGH, MEDIUM, LOW, INFO)
- `src/scanner/core/fingerprint.py` — compute_fingerprint(file_path, rule_id, snippet)

### Plugin registry (Phase 8 output)
- `src/scanner/adapters/registry.py` — ScannerRegistry, RegisteredScanner, load_adapter_class
- `src/scanner/config.py` — ScannerToolConfig (adapter_class, languages, enabled, timeout, extra_args), ScannerSettings
- `config.yml` — Scanner registration entries (add new scanners here)

### Phase 7 research (tool-specific details)
- `.planning/milestones/v2.0-phases/07-security-scanner-ecosystem-research/07-SCANNER-ECOSYSTEM-REPORT.md` — Detailed per-tool analysis: CLI usage, output format, severity mapping, Docker install, config examples for gosec, Bandit, Brakeman, cargo-audit

### Requirements
- `.planning/REQUIREMENTS.md` — SCAN-01 through SCAN-04

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ScannerAdapter` base class: well-defined contract — subclass and implement 3 methods
- `ScannerAdapter._execute()`: async subprocess with timeout, returns (stdout, stderr, returncode)
- `ScannerAdapter._normalize_path()`: strips target prefix from file paths
- `compute_fingerprint()`: SHA-256 from file_path + rule_id + snippet
- `ScannerExecutionError` / `ScannerTimeoutError`: established error types

### Established Patterns
- JSON parsing: `json.loads(stdout)`, extract results array, iterate and build FindingSchema list
- Severity mapping: tool-specific dict mapping tool severity strings → Severity enum values
- Exit code handling: some tools use exit code 1 for "findings found" (not error) — handle per tool
- Exclude patterns: `.venv`, `node_modules`, `.git`, `vendor`, `storage`

### Integration Points
- `config.yml` — add 4 new scanner entries with adapter_class and languages
- `src/scanner/adapters/` — new adapter files: gosec.py, bandit.py, brakeman.py, cargo_audit.py
- `tests/phase_09/` — new test directory for adapter tests
- No changes needed to orchestrator, registry, or language_detect (Phase 8 made them config-driven)

</code_context>

<specifics>
## Specific Ideas

- Phase 7 research report has exact CLI commands, JSON output examples, and config snippets for all 4 tools — adapters should follow those recommendations closely
- cargo-audit should auto-generate Cargo.lock if missing (user preference over warn-and-skip)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 09-tier-1-scanner-adapters*
*Context gathered: 2026-03-21*
