# Phase 13: Nuclei DAST Adapter - Context

**Gathered:** 2026-03-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Template-based dynamic application security scanning via Nuclei CLI. Users can trigger DAST scans against target URLs via the existing scan API. Nuclei findings flow through the standard FindingSchema pipeline into reports alongside SAST findings. Target management, DAST-specific reports, and scheduled DAST scans are out of scope (v1.0.3+).

</domain>

<decisions>
## Implementation Decisions

### Finding mapping
- Store matched-at URL in `FindingSchema.file_path` — no new schema fields needed
- Use Nuclei's built-in severity (info/low/medium/high/critical) mapped directly to the `Severity` enum
- Template ID maps to `rule_id`
- Snippet contains Nuclei's extracted/matched content from the response — shows what was actually detected
- Fingerprint computed from URL + template ID + matched content (same `compute_fingerprint` pattern)

### Scan triggering
- Add optional `target_url` field to existing `ScanRequest` — single endpoint, no separate DAST API
- If `target_url` is provided, only Nuclei runs (DAST-only scan) — SAST scanners skipped
- If `target_url` is absent, SAST as usual — Nuclei adapter skipped
- Template selection via `extra_args` in `config.yml` (e.g. `-tags cve,exposure`) — follows existing adapter pattern
- Nuclei registered in plugin registry like all other adapters (`adapter_class` in config.yml)

### Report integration
- DAST findings appear alongside SAST findings in the same report, tagged with "nuclei" tool badge
- Grouped by severity as usual — no separate DAST section
- Quality gate applies equally to DAST findings — a critical Nuclei finding blocks deployment same as SAST

### Docker & templates
- Download pre-built Nuclei binary from GitHub releases, pinned to specific version
- Use Docker `TARGETARCH` build arg for multi-arch (linux_amd64 vs linux_arm64)
- Run `nuclei -update-templates` during Docker build — templates baked into image
- No runtime network dependency for templates

### Claude's Discretion
- Nuclei JSON output parsing details and edge cases
- Exact version to pin for initial release
- Template update frequency in Docker rebuilds
- Error handling for Nuclei-specific failure modes (e.g. target unreachable)
- Whether to pass `target_url` validation (URL format check) in the adapter or API layer

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Adapter pattern
- `src/scanner/adapters/base.py` — ScannerAdapter abstract base class defining the contract (tool_name, run(), _execute())
- `src/scanner/adapters/gosec.py` — Reference adapter implementation showing JSON parsing, severity mapping, fingerprint computation
- `src/scanner/adapters/registry.py` — ScannerRegistry plugin loading pattern, config-driven registration

### Data contracts
- `src/scanner/schemas/finding.py` — FindingSchema fields that Nuclei findings must map to
- `src/scanner/schemas/severity.py` — Severity IntEnum for mapping Nuclei severities

### Integration points
- `src/scanner/api/scans.py` — Scan API endpoint where target_url field will be added to ScanRequest
- `src/scanner/api/schemas.py` — API request/response schemas (ScanRequest needs target_url)
- `src/scanner/core/orchestrator.py` — run_scan() adapter dispatch logic, needs DAST routing
- `src/scanner/config.py` — ScannerToolConfig and ScannerSettings where Nuclei config entry goes

### Docker
- `Dockerfile` — Multi-arch binary installation pattern for scanner tools

### Requirements
- `.planning/REQUIREMENTS.md` — DAST-01 through DAST-04 acceptance criteria

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ScannerAdapter` base class: provides `_execute()` subprocess helper with timeout, `_normalize_path()`, `get_version()`
- `compute_fingerprint()` in `core/fingerprint.py`: SHA-256 deterministic fingerprint computation
- `ScannerRegistry`: config-driven plugin loading via `importlib` — Nuclei adapter just needs a config.yml entry
- `ScannerExecutionError` / `ScannerTimeoutError`: existing exception types for adapter failures

### Established Patterns
- All adapters parse JSON output from CLI tools and normalize to `FindingSchema` list
- Exit code handling: code 1 = findings found (not error), >= 2 = real error
- Extra args passed through from config.yml to CLI command
- Per-tool severity maps (`GOSEC_SEVERITY_MAP` pattern) for enum conversion

### Integration Points
- `config.yml` scanners section: add `nuclei` entry with `adapter_class`, `enabled`, `timeout`, `extra_args`
- `ScanRequest` in `api/schemas.py`: add optional `target_url` field
- `run_scan()` in `core/orchestrator.py`: routing logic to select DAST vs SAST adapters based on `target_url`
- `Dockerfile`: binary download section for multi-arch tool installation
- HTML/PDF report templates: findings already display `tool` field as badge — Nuclei findings will show naturally

</code_context>

<specifics>
## Specific Ideas

No specific requirements — standard Nuclei integration following existing adapter patterns.

</specifics>

<deferred>
## Deferred Ideas

- DAST target management (save/edit target URLs) — DAST-05 in v1.0.3+
- DAST-specific report section with URL-based grouping — DAST-06 in v1.0.3+
- Scheduled DAST scans — DAST-07 in v1.0.3+
- Template category selection per scan via API parameter — could revisit in scan profiles (Phase 15)

</deferred>

---

*Phase: 13-nuclei-dast-adapter*
*Context gathered: 2026-03-23*
