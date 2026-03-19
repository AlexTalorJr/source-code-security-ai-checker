---
phase: 04-reports-and-quality-gate
plan: 01
subsystem: quality-gate
tags: [pydantic, sqlalchemy, quality-gate, delta-comparison, fingerprint]

# Dependency graph
requires:
  - phase: 03-ai-analysis
    provides: "Compound risks, AI enrichment, orchestrator pipeline"
  - phase: 02-scanner-pipeline
    provides: "Orchestrator run_scan, CLI, adapters"
provides:
  - "GateConfig with configurable fail_on severity list and include_compound_risks toggle"
  - "GateConfig.evaluate() returning (passed, fail_reasons) tuple"
  - "ReportData and DeltaResult data contracts for report generation"
  - "Delta comparison via fingerprint set operations (new/fixed/persisting)"
  - "run_scan returning tuple (ScanResultSchema, findings, compound_risks)"
affects: [04-02-html-report, 04-03-pdf-report, 04-04-ci-integration]

# Tech tracking
tech-stack:
  added: [aiosqlite]
  patterns: [configurable-gate-evaluation, fingerprint-set-delta, tuple-return-orchestrator]

key-files:
  created:
    - src/scanner/reports/__init__.py
    - src/scanner/reports/models.py
    - src/scanner/reports/delta.py
    - tests/phase_04/__init__.py
    - tests/phase_04/conftest.py
    - tests/phase_04/test_gate.py
    - tests/phase_04/test_delta.py
  modified:
    - src/scanner/config.py
    - src/scanner/core/orchestrator.py
    - src/scanner/cli/main.py
    - config.yml.example
    - tests/phase_02/test_orchestrator.py
    - tests/phase_02/test_cli.py
    - tests/phase_03/test_orchestrator_ai.py

key-decisions:
  - "GateConfig uses Pydantic BaseModel nested inside ScannerSettings for YAML loading"
  - "run_scan returns tuple instead of single schema to provide findings and compound risks to callers"
  - "Delta returns None for first scan rather than empty sets to distinguish 'no comparison possible' from 'no changes'"

patterns-established:
  - "Configurable gate evaluation via GateConfig.evaluate() returning (bool, list[str])"
  - "Fingerprint set operations for delta: current - previous = new, previous - current = fixed, intersection = persisting"
  - "Data contracts via dataclasses (ReportData, DeltaResult) for report layer decoupling"

requirements-completed: [GATE-01, GATE-02, GATE-03, HIST-01, HIST-02]

# Metrics
duration: 5min
completed: 2026-03-19
---

# Phase 04 Plan 01: Quality Gate and Delta Summary

**Configurable quality gate with fail_on severity thresholds, compound risk toggle, and delta comparison via fingerprint set operations**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-19T11:20:56Z
- **Completed:** 2026-03-19T11:26:22Z
- **Tasks:** 2
- **Files modified:** 14

## Accomplishments
- GateConfig model with configurable fail_on list and include_compound_risks toggle, producing identical default behavior to previous hardcoded Critical+High check
- Delta comparison module computing new/fixed/persisting findings between scans via fingerprint set operations
- run_scan now returns findings and compound risks alongside ScanResultSchema for downstream report consumers
- Full test coverage: 17 new tests (11 gate + 6 delta), all 181 tests passing

## Task Commits

Each task was committed atomically:

1. **Task 1: GateConfig, ReportData, orchestrator refactor** - `6bb9fa5` (test: RED), `8ac7e46` (feat: GREEN)
2. **Task 2: Delta comparison module** - `2d1f331` (test: RED), `0714cbe` (feat: GREEN)

_Note: TDD tasks have two commits each (test RED -> feat GREEN)_

## Files Created/Modified
- `src/scanner/config.py` - Added GateConfig model with evaluate() method, gate field on ScannerSettings
- `src/scanner/reports/__init__.py` - New reports package
- `src/scanner/reports/models.py` - ReportData and DeltaResult data contracts
- `src/scanner/reports/delta.py` - Delta comparison via fingerprint set operations
- `src/scanner/core/orchestrator.py` - Replaced hardcoded gate with GateConfig.evaluate(), tuple return type
- `src/scanner/cli/main.py` - Updated for tuple return from run_scan
- `config.yml.example` - Added gate section with fail_on and include_compound_risks
- `tests/phase_04/conftest.py` - Shared fixtures with realistic sample data
- `tests/phase_04/test_gate.py` - 11 gate configuration tests
- `tests/phase_04/test_delta.py` - 6 delta comparison tests
- `tests/phase_02/test_orchestrator.py` - Updated for tuple return type
- `tests/phase_02/test_cli.py` - Updated mock return values for tuple
- `tests/phase_03/test_orchestrator_ai.py` - Updated for tuple return type

## Decisions Made
- GateConfig uses Pydantic BaseModel nested inside ScannerSettings for seamless YAML loading
- run_scan returns tuple (ScanResultSchema, list[FindingSchema], list[CompoundRiskSchema]) instead of just ScanResultSchema, requiring updates to CLI and all existing tests
- Delta returns None for first scan on a branch rather than empty sets, clearly distinguishing "no comparison possible" from "no changes found"

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated all run_scan callers for tuple return type**
- **Found during:** Task 1 (orchestrator refactor)
- **Issue:** Changing run_scan return type from ScanResultSchema to tuple broke CLI and all phase 02/03 tests
- **Fix:** Updated CLI to destructure tuple, updated all test assertions to use tuple unpacking
- **Files modified:** src/scanner/cli/main.py, tests/phase_02/test_orchestrator.py, tests/phase_02/test_cli.py, tests/phase_03/test_orchestrator_ai.py
- **Verification:** All 181 tests pass
- **Committed in:** 8ac7e46 (Task 1 feat commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Auto-fix was necessary consequence of planned API change. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- ReportData contract ready for HTML report template (Plan 02)
- DeltaResult available for delta section in reports
- GateConfig.evaluate() fail_reasons ready for display in report and CI output
- All data flows through run_scan tuple return, report generators can consume directly

---
*Phase: 04-reports-and-quality-gate*
*Completed: 2026-03-19*
