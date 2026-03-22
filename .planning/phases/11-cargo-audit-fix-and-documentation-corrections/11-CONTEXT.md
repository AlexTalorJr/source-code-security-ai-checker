# Phase 11: Cargo-Audit Fix and Documentation Corrections - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix the cargo-audit KeyError that prevents Rust project scanning, correct the run() signature in admin-guide documentation examples, and update Makefile scanner count description. Gap closure for v1.0.1 milestone audit findings.

</domain>

<decisions>
## Implementation Decisions

### KeyError fix
- Change `tool_name` property in `CargoAuditAdapter` from `"cargo-audit"` to `"cargo_audit"` to match the config.yml key
- This ensures `settings.scanners[adapter.tool_name]` resolves correctly in the orchestrator
- Accepts that logs/reports will show `cargo_audit` (underscore) instead of `cargo-audit` (hyphen)

### Documentation corrections
- Fix the `run()` signature in admin-guide.md "Adding a New Scanner" example to match the actual base class: `async def run(self, target_path: str, timeout: int, extra_args: list[str] | None = None) -> list[FindingSchema]`
- Apply the fix across all 5 language versions (EN, RU, FR, ES, IT)

### Makefile update
- Change verify-scanners description from "11 scanner binaries" to "12 scanners (11 binaries)" per success criteria

### Claude's Discretion
- Whether to also update `_version_command` from `["cargo-audit", ...]` to `["cargo_audit", ...]` (binary name stays `cargo-audit` on disk, so likely keep as-is)
- Exact test structure for the integration test

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Source code
- `src/scanner/adapters/cargo_audit.py` — CargoAuditAdapter with tool_name property (line 94) that needs fixing
- `src/scanner/adapters/base.py` — ScannerAdapter base class with correct run() signature
- `src/scanner/core/orchestrator.py` — Lines 196-197 where settings.scanners[adapter.tool_name] causes KeyError

### Configuration
- `config.yml` — Line 88: `cargo_audit` key (underscore) that tool_name must match

### Documentation
- `docs/en/admin-guide.md` — Line 138: incorrect run() signature in "Adding a New Scanner" example

### Tests
- `tests/phase_09/test_adapter_cargo_audit.py` — Existing cargo-audit adapter tests (may need tool_name assertion update)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tests/phase_09/test_adapter_cargo_audit.py`: Existing adapter tests to extend or verify tool_name change
- `tests/phase_09/test_config_registration.py`: Config registration tests showing pattern for config lookup testing

### Established Patterns
- All other adapters (bandit, gosec, brakeman) use underscore-free names that match their config keys
- Orchestrator assumes `adapter.tool_name` matches `settings.scanners` dict key exactly

### Integration Points
- `src/scanner/core/orchestrator.py:196` — The exact line that fails with KeyError on Rust projects

</code_context>

<specifics>
## Specific Ideas

- The binary on disk is still called `cargo-audit` — the `_version_command` should keep using the hyphenated binary name
- All 5 language doc files need the same signature fix for consistency

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 11-cargo-audit-fix-and-documentation-corrections*
*Context gathered: 2026-03-22*
