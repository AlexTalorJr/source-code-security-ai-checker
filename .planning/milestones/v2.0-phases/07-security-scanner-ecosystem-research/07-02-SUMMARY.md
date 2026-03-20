---
phase: 07-security-scanner-ecosystem-research
plan: 02
subsystem: research
tags: [plugin-architecture, sarif, orchestration, priority-matrix, config-driven-registry, incremental-scanning]

# Dependency graph
requires:
  - phase: 07-security-scanner-ecosystem-research
    provides: "Per-language SAST research, SCA/DAST/secrets sections from Plan 01"
provides:
  - "SARIF evaluation with parse_sarif() helper recommendation"
  - "Config-driven plugin registry architecture recommendation"
  - "Orchestration improvements (incremental scanning, deduplication)"
  - "Priority-ranked tool matrix (9 tools in 3 tiers) with T-shirt estimates"
  - "Suggested implementation phasing (Phases 8-10)"
affects: [future scanner implementation phases, phase-08, phase-09, phase-10]

# Tech tracking
tech-stack:
  added: []
  patterns: ["config-driven scanner registry with adapter_class field", "optional SARIF parse helper pattern", "incremental scanning opt-in pattern"]

key-files:
  created: []
  modified:
    - ".planning/phases/07-security-scanner-ecosystem-research/07-SCANNER-ECOSYSTEM-REPORT.md"

key-decisions:
  - "Config-driven registry recommended over stevedore/importlib/directory-scanning for plugin architecture"
  - "SARIF: optional parse_sarif() helper for 8 SARIF-capable tools, custom parsers kept for 5 non-SARIF tools"
  - "Incremental scanning: opt-in mode, tools split into file-list-capable vs full-context-required"
  - "Priority Tier 1: gosec, Brakeman, Bandit, cargo-audit (all S effort)"
  - "Priority Tier 2: Grype, security-code-scan, Nuclei (S-M effort)"
  - "Priority Tier 3: SpotBugs+FindSecBugs, ZAP (L effort)"
  - "Not recommended: eslint-plugin-security, OWASP Dependency-Check, Nikto, TruffleHog"
  - "Suggested phasing: Phase 8 (Tier 1 + plugin registry), Phase 9 (SARIF + Tier 2), Phase 10 (incremental + DAST)"

patterns-established:
  - "Config-driven registry: extend config.yml scanners section with adapter_class field"
  - "SARIF helper: shared parse_sarif() mapping ruleId/level/locations to FindingSchema"
  - "Incremental scanning: orchestrator accepts optional changed_files parameter"

requirements-completed: [SCAN-05, SCAN-07]

# Metrics
duration: 4min
completed: 2026-03-20
---

# Phase 07 Plan 02: Scanner Architecture and Priority Matrix Summary

**Config-driven plugin registry, SARIF helper pattern, incremental scanning design, and 9-tool priority matrix with 3-tier implementation roadmap (Phases 8-10)**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-20T19:25:00Z
- **Completed:** 2026-03-20T19:29:00Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- Wrote SARIF evaluation section: 8 tools with SARIF support, 5 without, recommending shared parse_sarif() helper
- Designed config-driven plugin registry extending existing config.yml pattern with adapter_class field
- Documented orchestration improvements: incremental scanning (5 tools support file-list, 4 need full context), cross-tool deduplication
- Created final priority matrix ranking 9 tools across 3 tiers with Docker size, SARIF support, and effort estimates
- Mapped suggested implementation order across Phases 8-10
- Research report reviewed and approved by human

## Task Commits

Each task was committed atomically:

1. **Task 1: Write plugin architecture, SARIF evaluation, orchestration improvements, and priority matrix sections** - `4094bc2` (feat)
2. **Task 2: Review completed research report** - checkpoint:human-verify, approved by human (no code commit)

## Files Created/Modified
- `.planning/phases/07-security-scanner-ecosystem-research/07-SCANNER-ECOSYSTEM-REPORT.md` - Added SARIF evaluation, plugin architecture, orchestration improvements, and final priority matrix sections (1416 lines total)

## Decisions Made
- Config-driven registry chosen over stevedore (overkill), importlib entry_points (less infrastructure), and directory scanning (implicit ordering) -- matches existing config.yml pattern
- SARIF adoption is optional/incremental: shared helper for SARIF-capable tools, existing custom parsers kept for non-SARIF tools
- Incremental scanning designed as opt-in: orchestrator passes changed_files to capable tools, falls back to full scan for others
- Cross-tool deduplication deferred to implementation phase (grouping by file_path + line_range + vulnerability_class)
- Opengrep: monitor but do not switch from Semgrep CE yet

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Complete research report approved, ready to guide implementation phases
- Phase 8 should implement Tier 1 tools (gosec, Brakeman, Bandit, cargo-audit) plus config-driven plugin registry
- Phase 9 should add SARIF helper and Tier 2 tools (Grype, security-code-scan)
- Phase 10 should implement incremental scanning and explore DAST (Nuclei)
- All tool research cards include config snippets, CLI usage, Docker install, and FindingSchema mappings

## Self-Check: PASSED

- FOUND: `.planning/phases/07-security-scanner-ecosystem-research/07-02-SUMMARY.md`
- FOUND: `.planning/phases/07-security-scanner-ecosystem-research/07-SCANNER-ECOSYSTEM-REPORT.md`
- FOUND: commit `4094bc2` (Task 1)

---
*Phase: 07-security-scanner-ecosystem-research*
*Completed: 2026-03-20*
