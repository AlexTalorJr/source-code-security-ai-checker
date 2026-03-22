---
phase: 09-tier-1-scanner-adapters
plan: 01
subsystem: scanner
tags: [gosec, bandit, sast, go, python, adapter]

requires:
  - phase: 08-scanner-plugin-registry
    provides: ScannerAdapter base class, plugin registry, FindingSchema
provides:
  - GosecAdapter for Go SAST scanning
  - BanditAdapter for Python SAST scanning with confidence x severity matrix
  - Phase 09 test infrastructure (conftest, fixtures)
affects: [09-02, scanner-registry-config]

tech-stack:
  added: []
  patterns: [confidence-severity-matrix, string-line-number-conversion]

key-files:
  created:
    - src/scanner/adapters/gosec.py
    - src/scanner/adapters/bandit.py
    - tests/phase_09/conftest.py
    - tests/phase_09/test_adapter_gosec.py
    - tests/phase_09/test_adapter_bandit.py
    - tests/phase_09/fixtures/gosec_output.json
    - tests/phase_09/fixtures/bandit_output.json
  modified: []

key-decisions:
  - "Gosec uses direct severity mapping (HIGH/MEDIUM/LOW) with single-line findings"
  - "Bandit uses confidence x severity matrix for 9-cell severity resolution"

patterns-established:
  - "Confidence x severity matrix: BANDIT_SEVERITY_MATRIX dict[tuple[str,str], Severity] pattern for tools with dual axes"
  - "String-to-int line number conversion for tools that emit string line numbers (gosec)"

requirements-completed: [SCAN-01, SCAN-02]

duration: 2min
completed: 2026-03-21
---

# Phase 09 Plan 01: Gosec and Bandit Adapters Summary

**Gosec and Bandit SAST adapters with direct severity mapping and confidence x severity matrix, 16 unit tests passing**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-21T21:45:11Z
- **Completed:** 2026-03-21T21:47:06Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- GosecAdapter parsing native JSON with direct HIGH/MEDIUM/LOW severity mapping
- BanditAdapter with 9-cell confidence x severity matrix (HIGH/HIGH->CRITICAL down to LOW/LOW->INFO)
- Phase 09 test infrastructure with shared conftest and fixture files
- 16 unit tests covering parsing, severity, path normalization, exit codes, fingerprints, edge cases

## Task Commits

Each task was committed atomically:

1. **Task 1: Create test infrastructure and gosec adapter with tests** - `e9e8376` (feat)
2. **Task 2: Create Bandit adapter with tests** - `4122fc6` (feat)

## Files Created/Modified
- `src/scanner/adapters/gosec.py` - GosecAdapter with direct severity mapping and string line conversion
- `src/scanner/adapters/bandit.py` - BanditAdapter with confidence x severity matrix
- `tests/phase_09/__init__.py` - Package init
- `tests/phase_09/conftest.py` - Shared fixtures for all phase 09 tests
- `tests/phase_09/test_adapter_gosec.py` - 8 unit tests for gosec adapter
- `tests/phase_09/test_adapter_bandit.py` - 8 unit tests for bandit adapter
- `tests/phase_09/fixtures/gosec_output.json` - 3-finding gosec fixture
- `tests/phase_09/fixtures/bandit_output.json` - 4-finding bandit fixture

## Decisions Made
- Gosec uses direct severity mapping (HIGH/MEDIUM/LOW) -- no confidence axis needed
- Bandit uses confidence x severity matrix producing 9 mapped severity levels
- Both adapters treat exit code 1 as findings-found (not error), >= 2 as error

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Gosec and Bandit adapters ready for registry integration
- Phase 09 Plan 02 (Brakeman + cargo-audit) can proceed using same test infrastructure
- conftest.py already includes brakeman_output and cargo_audit_output fixtures

---
*Phase: 09-tier-1-scanner-adapters*
*Completed: 2026-03-21*
