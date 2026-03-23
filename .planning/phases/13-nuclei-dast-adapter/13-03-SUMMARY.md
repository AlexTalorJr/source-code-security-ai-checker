---
phase: 13-nuclei-dast-adapter
plan: 03
subsystem: scanner
tags: [dast, nuclei, api, orchestrator, alembic, target-url]

# Dependency graph
requires:
  - phase: 13-nuclei-dast-adapter
    provides: NucleiAdapter class (plan 01), nuclei config entry (plan 02)
  - phase: 04-scanner-core
    provides: ScannerAdapter base, ScannerRegistry, orchestrator, scan_queue
provides:
  - DAST scan triggerable via POST /api/scans with target_url field
  - Orchestrator DAST routing to NucleiAdapter (skips SAST flow)
  - ScanResult model with target_url column and Alembic migration
  - Scan queue worker passes target_url through to orchestrator
affects: [reports, dashboard, notifications]

# Tech tracking
tech-stack:
  added: []
  patterns: [DAST/SAST routing branch in orchestrator, three-way target validation in ScanRequest]

key-files:
  created:
    - alembic/versions/002_add_target_url_to_scans.py
    - tests/phase_13/test_scan_request.py
    - tests/phase_13/test_dast_routing.py
  modified:
    - src/scanner/api/schemas.py
    - src/scanner/models/scan.py
    - src/scanner/schemas/scan.py
    - src/scanner/core/orchestrator.py
    - src/scanner/core/scan_queue.py
    - src/scanner/api/scans.py

key-decisions:
  - "Three-way ScanRequest validation: target_url exclusive with path/repo_url"
  - "DAST mode uses registry.get_scanner_config('nuclei') instead of get_enabled_adapters"
  - "target_url passed as target_path parameter to NucleiAdapter.run() (URL-as-path pattern)"

patterns-established:
  - "DAST/SAST routing: if target_url branch runs only Nuclei, else standard SAST flow"
  - "Shared post-scan pipeline: dedup, AI, gate, persist shared between DAST and SAST"

requirements-completed: [DAST-02, DAST-04]

# Metrics
duration: 3min
completed: 2026-03-23
---

# Phase 13 Plan 03: DAST API Integration Summary

**DAST scan wired end-to-end: target_url field through API schema, orchestrator routing, DB model, and queue worker with three-way validation**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-23T10:02:30Z
- **Completed:** 2026-03-23T10:05:43Z
- **Tasks:** 1 (TDD: RED + GREEN)
- **Files modified:** 9

## Accomplishments
- ScanRequest validates three-way target selection (path, repo_url, or target_url) with mutual exclusion
- Orchestrator routes to NucleiAdapter when target_url provided, skipping language detection and git clone
- ScanResult model gains target_url column with Alembic migration 002
- Scan queue worker reads target_url from DB and passes to orchestrator
- 11 new tests covering validation (7) and DAST routing (4)

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Failing tests for ScanRequest validation and DAST routing** - `11d45d4` (test)
2. **Task 1 GREEN: Wire DAST target_url through API, orchestrator, model, and queue** - `1df285b` (feat)

_TDD task with RED/GREEN commits._

## Files Created/Modified
- `src/scanner/api/schemas.py` - ScanRequest with target_url field and three-way validation; ScanDetailResponse with target_url
- `src/scanner/models/scan.py` - ScanResult with target_url column
- `src/scanner/schemas/scan.py` - ScanResultSchema with target_url field
- `src/scanner/core/orchestrator.py` - DAST routing branch in run_scan(); target_url in result construction and persistence
- `src/scanner/core/scan_queue.py` - Worker reads target_url from DB, passes to run_scan
- `src/scanner/api/scans.py` - trigger_scan stores target_url; _scan_to_detail includes target_url
- `alembic/versions/002_add_target_url_to_scans.py` - Migration adding target_url column to scans table
- `tests/phase_13/test_scan_request.py` - 7 validation tests for ScanRequest target_url
- `tests/phase_13/test_dast_routing.py` - 4 orchestrator DAST routing tests

## Decisions Made
- Three-way ScanRequest validation: target_url exclusive with path/repo_url
- DAST mode uses registry.get_scanner_config("nuclei") instead of get_enabled_adapters to avoid language detection
- target_url passed as target_path parameter to NucleiAdapter.run() following URL-as-path pattern from plan 01

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed detect_languages mock path in test**
- **Found during:** Task 1 GREEN (test_sast_mode_skips_nuclei)
- **Issue:** detect_languages is imported inside the else branch (lazy import), so patching scanner.core.orchestrator.detect_languages fails
- **Fix:** Patched at source: scanner.core.language_detect.detect_languages
- **Files modified:** tests/phase_13/test_dast_routing.py
- **Verification:** All 11 tests pass
- **Committed in:** 1df285b (Task 1 GREEN commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Minor test fix for lazy import pattern. No scope creep.

## Issues Encountered
None beyond the test mock path fix documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- End-to-end DAST scanning is wired: API accepts target_url, orchestrator routes to Nuclei, results persist
- DAST findings render in reports automatically via existing tool badge system (DAST-04)
- Phase 13 complete after this plan

---
*Phase: 13-nuclei-dast-adapter*
*Completed: 2026-03-23*
