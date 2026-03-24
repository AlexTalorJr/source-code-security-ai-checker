---
phase: 16-v102-polish-and-tech-debt
plan: 01
subsystem: dashboard, docs
tags: [dast, target_url, bearer-token, migration, i18n]

# Dependency graph
requires:
  - phase: 13-dast-nuclei
    provides: "target_url column in ScanResult model, DAST scan flow"
  - phase: 12-jwt-auth
    provides: "Bearer token auth replacing legacy X-API-Key"
provides:
  - "target_url input in dashboard scan form for DAST scans"
  - "target_url inline migration in _apply_schema_updates"
  - "All docs updated to Bearer token auth (zero X-API-Key references)"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns: []

key-files:
  created: []
  modified:
    - src/scanner/main.py
    - src/scanner/dashboard/router.py
    - src/scanner/dashboard/templates/history.html.j2
    - docs/en/architecture.md
    - docs/en/devops-guide.md
    - docs/en/transfer-guide.md
    - docs/ru/architecture.md
    - docs/ru/devops-guide.md
    - docs/ru/transfer-guide.md
    - docs/fr/architecture.md
    - docs/fr/devops-guide.md
    - docs/fr/transfer-guide.md
    - docs/es/architecture.md
    - docs/es/devops-guide.md
    - docs/es/transfer-guide.md
    - docs/it/architecture.md
    - docs/it/devops-guide.md
    - docs/it/transfer-guide.md

key-decisions:
  - "Dashboard target_url field placed in first form-row alongside path, repo_url, branch"

patterns-established: []

requirements-completed: [DAST-02]

# Metrics
duration: 3min
completed: 2026-03-24
---

# Phase 16 Plan 01: v1.0.2 Gap Closure Summary

**Dashboard DAST target_url form field, inline migration, and Bearer token auth docs across all 5 languages**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-24T10:40:58Z
- **Completed:** 2026-03-24T10:43:50Z
- **Tasks:** 3
- **Files modified:** 18

## Accomplishments
- Added target_url VARCHAR(500) to inline schema migration dict in main.py
- Added target_url Form parameter and ScanResult pass-through in dashboard start_scan handler
- Added Target URL (DAST) input field to dashboard scan form template
- Replaced all 15 X-API-Key references with Bearer token auth across 15 doc files (5 languages x 3 file types)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add target_url migration and dashboard DAST form support** - `0885563` (feat)
2. **Task 2: Replace stale X-API-Key references with Bearer token auth in all docs** - `b9ef1c4` (fix)
3. **Task 3: Verify end-to-end integration** - verification only, no commit needed

## Files Created/Modified
- `src/scanner/main.py` - Added target_url to _apply_schema_updates migration dict
- `src/scanner/dashboard/router.py` - Added target_url Form param and ScanResult constructor arg
- `src/scanner/dashboard/templates/history.html.j2` - Added Target URL (DAST) input field
- `docs/{en,ru,fr,es,it}/architecture.md` - Replaced X-API-Key auth description with Bearer token
- `docs/{en,ru,fr,es,it}/devops-guide.md` - Replaced Jenkins X-API-Key header with Authorization Bearer
- `docs/{en,ru,fr,es,it}/transfer-guide.md` - Replaced curl X-API-Key header with Authorization Bearer

## Decisions Made
- Dashboard target_url field placed in first form-row alongside path, repo_url, and branch for consistent layout

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Pre-existing test failure: `defusedxml` module not installed (affects cppcheck adapter test) - not caused by this plan's changes
- Pre-existing test failure: `test_ai_enrichment_in_orchestrator` - not caused by this plan's changes

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- v1.0.2 milestone gap closure complete
- All three identified gaps resolved: migration, dashboard form, docs auth references

---
*Phase: 16-v102-polish-and-tech-debt*
*Completed: 2026-03-24*
