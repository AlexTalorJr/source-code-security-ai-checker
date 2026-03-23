---
phase: 15-scan-profiles-and-documentation
plan: 01
subsystem: api
tags: [pydantic, fastapi, yaml, scan-profiles, crud, orchestrator]

requires:
  - phase: 14-scanner-config-ui
    provides: config CRUD API with read_config/write_config, scanner settings endpoints
provides:
  - Profile CRUD API (GET/POST/PUT/DELETE /api/config/profiles)
  - ScanProfileConfig and ScanProfileScannerConfig Pydantic models
  - Profile-aware scan triggering (profile_name on ScanRequest and ScanResult)
  - Orchestrator profile override logic (scanner filtering and timeout merging)
affects: [15-02, 15-03, dashboard-profiles-ui]

tech-stack:
  added: []
  patterns: [profile-override-with-model-copy, yaml-profile-persistence, name-validation-with-yaml-reserved]

key-files:
  created:
    - tests/phase_15/__init__.py
    - tests/phase_15/conftest.py
    - tests/phase_15/test_profile_crud.py
    - tests/phase_15/test_profile_scan.py
  modified:
    - src/scanner/config.py
    - src/scanner/models/scan.py
    - src/scanner/schemas/scan.py
    - src/scanner/api/schemas.py
    - src/scanner/api/config.py
    - src/scanner/api/scans.py
    - src/scanner/core/orchestrator.py
    - src/scanner/core/scan_queue.py
    - config.yml.example

key-decisions:
  - "Profile name validation with regex + YAML reserved word blocklist"
  - "Soft limit of 10 profiles enforced at API level"
  - "Profile override uses settings.model_copy(update=) for immutable replacement"
  - "DAST with profile lacking nuclei gives profile-specific error message"

patterns-established:
  - "Profile override pattern: model_copy with filtered scanners dict"
  - "Name validation: regex + YAML reserved words for safe YAML key names"

requirements-completed: [CONF-04, CONF-05]

duration: 6min
completed: 2026-03-23
---

# Phase 15 Plan 01: Scan Profiles Backend Summary

**Named scan profiles with CRUD API, profile-aware orchestrator override, and config.yml persistence**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-23T13:49:36Z
- **Completed:** 2026-03-23T13:55:59Z
- **Tasks:** 2
- **Files modified:** 13

## Accomplishments
- Profile CRUD API with full validation (name format, YAML reserved words, duplicate check, soft limit 10, non-empty scanners)
- Profile-aware scan triggering: profile field on ScanRequest, profile_name on ScanResult in DB
- Orchestrator profile override: filters scanners to profile-listed only, merges timeout/extra_args
- DAST profile support with nuclei-specific error when not in profile
- 24 tests covering CRUD, auth, scan trigger, and orchestrator logic

## Task Commits

Each task was committed atomically:

1. **Task 1: Profile models, DB column, CRUD API (RED)** - `60f4291` (test)
2. **Task 1: Profile models, DB column, CRUD API (GREEN)** - `abc19b8` (feat)
3. **Task 2: Profile override, scan trigger, scan_queue (RED)** - `770e999` (test)
4. **Task 2: Profile override, scan trigger, scan_queue (GREEN)** - `092f3d3` (feat)

## Files Created/Modified
- `src/scanner/config.py` - ScanProfileScannerConfig, ScanProfileConfig models + profiles field on ScannerSettings
- `src/scanner/models/scan.py` - profile_name column on ScanResult
- `src/scanner/schemas/scan.py` - profile_name field on ScanResultSchema
- `src/scanner/api/schemas.py` - profile field on ScanRequest, profile_name on ScanDetailResponse
- `src/scanner/api/config.py` - 5 profile CRUD endpoints with validation
- `src/scanner/api/scans.py` - profile validation on trigger, profile_name on db_scan
- `src/scanner/core/orchestrator.py` - profile_name param, scanner filtering, DAST profile error
- `src/scanner/core/scan_queue.py` - profile_name passthrough to run_scan
- `config.yml.example` - profiles section with quick_scan, full_audit, dast_only examples
- `tests/phase_15/conftest.py` - shared fixtures with profile in TEST_CONFIG
- `tests/phase_15/test_profile_crud.py` - 17 tests for CRUD endpoints
- `tests/phase_15/test_profile_scan.py` - 7 tests for scan trigger and orchestrator

## Decisions Made
- Profile name validation: regex `^[a-zA-Z][a-zA-Z0-9_-]{0,63}$` plus YAML reserved word blocklist (true, false, null, yes, no, on, off)
- Soft limit of 10 profiles enforced at API level (returns 400 when exceeded)
- Profile override uses `settings.model_copy(update={"scanners": filtered})` for clean immutable replacement
- DAST mode with profile that lacks nuclei returns a profile-specific ValueError

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Profile backend complete, ready for plan 15-02 (documentation generation) and 15-03 (UI)
- All 24 tests pass, providing regression safety for future changes

## Self-Check: PASSED

All 13 files verified present. All 4 commit hashes verified in git log.

---
*Phase: 15-scan-profiles-and-documentation*
*Completed: 2026-03-23*
