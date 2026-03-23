---
phase: 13-nuclei-dast-adapter
plan: 01
subsystem: scanner
tags: [nuclei, dast, jsonl, adapter, async]

# Dependency graph
requires:
  - phase: 04-scanner-core
    provides: ScannerAdapter base class, FindingSchema, compute_fingerprint, exceptions
provides:
  - NucleiAdapter class parsing Nuclei JSONL into FindingSchema
  - NUCLEI_SEVERITY_MAP for all 5 severity levels
  - Phase 13 test infrastructure with JSONL fixtures
affects: [13-02, 13-03, nuclei-integration, dast-api]

# Tech tracking
tech-stack:
  added: []
  patterns: [JSONL line-by-line parsing, DAST URL-as-file-path, extracted-results/matched-line snippet fallback]

key-files:
  created:
    - src/scanner/adapters/nuclei.py
    - tests/phase_13/__init__.py
    - tests/phase_13/conftest.py
    - tests/phase_13/fixtures/nuclei_output.jsonl
    - tests/phase_13/test_nuclei_adapter.py
  modified: []

key-decisions:
  - "Nuclei exit code != 0 is error (unlike gosec >= 2) per Nuclei CLI semantics"
  - "Snippet uses extracted-results joined by newline, with matched-line as fallback"
  - "file_path stores full URL (no _normalize_path) since DAST targets are URLs not file paths"

patterns-established:
  - "DAST adapter pattern: URL as file_path, line_start/line_end always None"
  - "JSONL parsing: line-by-line json.loads with JSONDecodeError skip"

requirements-completed: [DAST-01]

# Metrics
duration: 2min
completed: 2026-03-23
---

# Phase 13 Plan 01: NucleiAdapter Core Summary

**NucleiAdapter parses Nuclei JSONL output into FindingSchema with severity mapping, fingerprint computation, and extracted-results/matched-line snippet fallback**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-23T09:58:54Z
- **Completed:** 2026-03-23T09:59:55Z
- **Tasks:** 1 (TDD: RED + GREEN)
- **Files modified:** 5

## Accomplishments
- NucleiAdapter subclasses ScannerAdapter with all abstract methods implemented
- JSONL parsing handles single-line, multi-line, and empty output correctly
- All 5 Nuclei severity levels mapped to Severity enum with INFO default for unknowns
- Fingerprint computed from matched-at URL + template-id + snippet
- 10 unit tests covering all behaviors with mocked subprocess

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Failing tests for NucleiAdapter** - `07af8a4` (test)
2. **Task 1 GREEN: Implement NucleiAdapter** - `12f2908` (feat)

_TDD task with RED/GREEN commits._

## Files Created/Modified
- `src/scanner/adapters/nuclei.py` - NucleiAdapter class with JSONL parsing and severity mapping
- `tests/phase_13/__init__.py` - Package init for phase 13 tests
- `tests/phase_13/conftest.py` - Shared fixtures: mock_execute, fixture paths, sample event
- `tests/phase_13/fixtures/nuclei_output.jsonl` - 3-event JSONL fixture (info, critical, medium)
- `tests/phase_13/test_nuclei_adapter.py` - 10 unit tests for NucleiAdapter

## Decisions Made
- Nuclei exit code != 0 is error (unlike gosec >= 2) per Nuclei CLI semantics
- Snippet uses extracted-results joined by newline, with matched-line as fallback
- file_path stores full URL (no _normalize_path) since DAST targets are URLs not file paths

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- NucleiAdapter ready for integration in plan 13-02 (API routing, Docker install)
- Test infrastructure in tests/phase_13/ ready for additional tests

---
*Phase: 13-nuclei-dast-adapter*
*Completed: 2026-03-23*
