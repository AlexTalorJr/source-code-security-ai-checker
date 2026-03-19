---
phase: 04-reports-and-quality-gate
plan: 04
subsystem: cli
tags: [typer, weasyprint, docker, reports, delta, quality-gate]

# Dependency graph
requires:
  - phase: 04-01
    provides: "GateConfig.evaluate, run_scan tuple return, delta module"
  - phase: 04-02
    provides: "generate_html_report, ReportData model"
  - phase: 04-03
    provides: "generate_pdf_report with charts"
provides:
  - "End-to-end CLI pipeline: scan -> gate -> delta -> HTML/PDF reports -> exit code"
  - "Docker image with WeasyPrint system dependencies"
  - "--output-dir CLI option for report output location"
  - "Delta summary and gate fail reasons in CLI output"
affects: [phase-05, phase-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Async helper for delta computation in sync CLI context"
    - "Graceful PDF fallback with warning on generation failure"

key-files:
  created: []
  modified:
    - src/scanner/cli/main.py
    - Dockerfile
    - tests/phase_02/test_cli.py
    - .gitignore

key-decisions:
  - "Async delta helper wraps engine create/dispose lifecycle for CLI context"
  - "PDF generation wrapped in try/except for graceful degradation"

patterns-established:
  - "Report naming convention: scan-{id}-{branch}-{date}.html/.pdf"
  - "CLI output order: severity table -> delta line -> gate status -> report paths"

requirements-completed: [RPT-04, GATE-01, GATE-03]

# Metrics
duration: 4min
completed: 2026-03-19
---

# Phase 04 Plan 04: CLI Integration and Pipeline Wiring Summary

**Full CLI pipeline wiring: scan -> gate evaluation -> delta comparison -> HTML/PDF report generation with --output-dir option and WeasyPrint Docker deps**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-19T11:35:00Z
- **Completed:** 2026-03-19T11:49:00Z
- **Tasks:** 2 (1 auto + 1 visual verification checkpoint)
- **Files modified:** 4

## Accomplishments
- Wired report generation (HTML + PDF) into CLI scan command with --output-dir option
- Added delta summary line and gate fail reasons to CLI output
- Updated Dockerfile with WeasyPrint system dependencies (libpango, libharfbuzz)
- Visual verification confirmed: HTML interactive filters, PDF charts, gate banners all render correctly

## Task Commits

Each task was committed atomically:

1. **Task 1: CLI integration with reports, delta, gate reasons, and Docker update** - `2ff50bd` (feat)
2. **Task 2: Visual verification of generated reports** - checkpoint approved by user (no code changes)

## Files Created/Modified
- `src/scanner/cli/main.py` - Added report generation, delta computation, gate fail reasons, --output-dir option
- `Dockerfile` - Added libpango, libpangoft2, libharfbuzz system deps for WeasyPrint
- `tests/phase_02/test_cli.py` - Extended CLI tests for new report/delta/gate output
- `.gitignore` - Added reports/ directory to gitignore

## Decisions Made
- Async delta helper wraps engine create/dispose lifecycle for CLI sync context
- PDF generation wrapped in try/except with yellow warning for graceful degradation
- Report naming: scan-{id}-{branch}-{date}.html/.pdf

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 04 complete: quality gate, delta comparison, HTML/PDF reports, CLI integration all working
- Full pipeline operational: scan -> gate -> delta -> reports -> exit code
- Ready for Phase 05

---
*Phase: 04-reports-and-quality-gate*
*Completed: 2026-03-19*

## Self-Check: PASSED
- All key files exist on disk
- Task 1 commit 2ff50bd verified in git history
- Task 2 checkpoint approved by user
