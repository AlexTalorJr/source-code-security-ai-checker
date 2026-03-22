---
phase: 08-plugin-registry-architecture
plan: 02
subsystem: api
tags: [registry, orchestrator, language-detect, fastapi, scanner-api]

requires:
  - phase: 08-plugin-registry-architecture (plan 01)
    provides: ScannerRegistry, ScannerToolConfig dict, config.yml scanner entries
provides:
  - Registry-based scan orchestration (no more ALL_ADAPTERS)
  - Config-driven language detection (no more SCANNER_LANGUAGES constant)
  - GET /api/scanners endpoint with status visibility
affects: [09-sarif-tier2, 10-incremental-dast]

tech-stack:
  added: []
  patterns: [registry-based orchestration, dict-access scanner config, API scanner listing]

key-files:
  created:
    - src/scanner/api/scanners.py
    - tests/phase_08/test_orchestrator_registry.py
    - tests/phase_08/test_language_detect.py
    - tests/phase_08/test_api_scanners.py
  modified:
    - src/scanner/core/orchestrator.py
    - src/scanner/core/language_detect.py
    - src/scanner/api/router.py
    - tests/phase_02/test_orchestrator.py

key-decisions:
  - "Patch detect_languages at source module since it is imported inside function body"
  - "should_enable_scanner takes scanner_languages list from config instead of looking up SCANNER_LANGUAGES dict"

patterns-established:
  - "Registry pattern: ScannerRegistry(settings.scanners) creates registry, get_enabled_adapters() returns instances"
  - "Dict access: settings.scanners[tool_name] for per-tool config, settings.scanners.get(key) for optional lookups"
  - "API scanner listing: request.app.state.settings provides config to endpoint"

requirements-completed: [PLUG-02, PLUG-04]

duration: 4min
completed: 2026-03-21
---

# Phase 08 Plan 02: Orchestrator Registry Integration Summary

**Registry-based orchestrator replacing ALL_ADAPTERS, config-driven language detection, and GET /api/scanners endpoint**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-21T17:14:34Z
- **Completed:** 2026-03-21T17:18:53Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Orchestrator uses ScannerRegistry instead of hard-coded ALL_ADAPTERS list
- Removed SCANNER_LANGUAGES and UNIVERSAL_SCANNERS constants from language_detect.py
- should_enable_scanner now accepts scanner_languages parameter from config
- Gitleaks shallow-clone check uses dict-based settings.scanners.get("gitleaks")
- GET /api/scanners endpoint returns all registered scanners with status, enabled, languages, load_error
- All existing orchestrator tests migrated to registry-based mocking

## Task Commits

Each task was committed atomically:

1. **Task 1: Refactor orchestrator + language_detect** - `6a2b26d` (test: RED), `9e616a9` (feat: GREEN)
2. **Task 2: Add GET /api/scanners endpoint** - `5500707` (test: RED), `40c4744` (feat: GREEN)

_Note: TDD tasks have RED/GREEN commits_

## Files Created/Modified
- `src/scanner/core/orchestrator.py` - Registry-based adapter loading, dict config access
- `src/scanner/core/language_detect.py` - Removed hard-coded constants, new should_enable_scanner signature
- `src/scanner/api/scanners.py` - New GET /api/scanners endpoint with ScannerInfo model
- `src/scanner/api/router.py` - Added scanners_router to API aggregator
- `tests/phase_08/test_orchestrator_registry.py` - Registry-based orchestrator tests
- `tests/phase_08/test_language_detect.py` - Config-driven language detection tests
- `tests/phase_08/test_api_scanners.py` - API endpoint tests with httpx AsyncClient
- `tests/phase_02/test_orchestrator.py` - Migrated from ALL_ADAPTERS to registry mocking

## Decisions Made
- Patching detect_languages at source module level since it is imported inside function body via lazy import
- should_enable_scanner signature changed to accept scanner_languages list, making it config-driven rather than constant-driven

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed test mock patch path for detect_languages**
- **Found during:** Task 1 (GREEN phase)
- **Issue:** detect_languages is imported inside function body, so patching at orchestrator module level fails
- **Fix:** Changed patch target to scanner.core.language_detect.detect_languages
- **Files modified:** tests/phase_08/test_orchestrator_registry.py, tests/phase_02/test_orchestrator.py
- **Verification:** All 43 tests pass
- **Committed in:** 9e616a9 (part of Task 1 GREEN commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Minor test fixture adjustment. No scope creep.

## Issues Encountered
- Pre-existing `defusedxml` module not installed prevents running full phase_02 test suite; unrelated to this plan's changes

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Plugin registry architecture complete: adding a new scanner requires only an adapter class + config.yml entry
- Ready for Phase 09 (SARIF + Tier 2 scanners) or Phase 10 (incremental + DAST)
- No blockers

---
*Phase: 08-plugin-registry-architecture*
*Completed: 2026-03-21*
