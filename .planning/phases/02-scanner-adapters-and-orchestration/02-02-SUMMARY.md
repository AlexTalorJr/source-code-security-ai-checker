---
phase: 02-scanner-adapters-and-orchestration
plan: 02
subsystem: scanner
tags: [semgrep, cppcheck, gitleaks, trivy, checkov, adapters, subprocess, json-parsing, xml-parsing]

requires:
  - phase: 02-01
    provides: ScannerAdapter ABC, FindingSchema, Severity enum, compute_fingerprint, ScannerExecutionError
provides:
  - SemgrepAdapter parsing JSON output with ERROR/WARNING/INFO severity mapping
  - CppcheckAdapter parsing XML v2 from stderr with C/C++ file detection
  - GitleaksAdapter parsing JSON report with secret redaction
  - TrivyAdapter parsing vulnerabilities and misconfigurations from JSON
  - CheckovAdapter parsing failed checks with check_id prefix severity mapping
  - ALL_ADAPTERS list exporting all five adapter classes
affects: [02-03-orchestration, 03-ai-analysis]

tech-stack:
  added: []
  patterns: [adapter-pattern-per-tool, severity-map-dict, exit-code-handling, stderr-xml-parsing, secret-redaction]

key-files:
  created:
    - src/scanner/adapters/semgrep.py
    - src/scanner/adapters/cppcheck.py
    - src/scanner/adapters/gitleaks.py
    - src/scanner/adapters/trivy.py
    - src/scanner/adapters/checkov.py
    - tests/phase_02/test_adapter_semgrep.py
    - tests/phase_02/test_adapter_cppcheck.py
    - tests/phase_02/test_adapter_gitleaks.py
    - tests/phase_02/test_adapter_trivy.py
    - tests/phase_02/test_adapter_checkov.py
  modified:
    - src/scanner/adapters/__init__.py

key-decisions:
  - "unittest.mock.AsyncMock used directly (no pytest-mock dependency) for adapter _execute mocking"
  - "Gitleaks secret redaction via string replace in Match field before storing snippet"
  - "Checkov severity by check_id prefix with longest-prefix-first matching (CKV2_ before CKV_)"

patterns-established:
  - "Adapter test pattern: assign AsyncMock to adapter._execute, call run(), assert findings"
  - "Exit code convention: code 1 means findings-found for Semgrep/Gitleaks/Checkov, only >= 2 is error"
  - "Severity map pattern: module-level dict constant mapping tool-native strings to Severity enum"

requirements-completed: [SCAN-01, SCAN-06]

duration: 4min
completed: 2026-03-19
---

# Phase 02 Plan 02: Scanner Adapters Summary

**Five scanner adapters (Semgrep, cppcheck, Gitleaks, Trivy, Checkov) parsing native tool output into unified FindingSchema with severity mapping, path normalization, and secret redaction**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-19T04:44:30Z
- **Completed:** 2026-03-19T04:48:22Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments
- All five adapters parse their respective tool's native output (JSON/XML) into normalized FindingSchema lists
- Severity mappings implemented per tool: Semgrep ERROR->HIGH, cppcheck error->HIGH, Gitleaks all->HIGH, Trivy CRITICAL->CRITICAL, Checkov prefix-based
- cppcheck gracefully skips when no C/C++ files exist; Gitleaks redacts secrets; exit code 1 handled as findings-found
- 25 adapter tests passing with full regression suite (75 total tests)

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement Semgrep, cppcheck, and Gitleaks adapters with tests** - `c3909a5` (feat)
2. **Task 2: Implement Trivy and Checkov adapters, update __init__.py** - `8ad11d7` (feat)

## Files Created/Modified
- `src/scanner/adapters/semgrep.py` - Semgrep adapter parsing JSON output with ERROR/WARNING/INFO severity
- `src/scanner/adapters/cppcheck.py` - cppcheck adapter parsing XML v2 from stderr with C/C++ file detection
- `src/scanner/adapters/gitleaks.py` - Gitleaks adapter parsing JSON report with secret redaction
- `src/scanner/adapters/trivy.py` - Trivy adapter parsing vulnerabilities and misconfigurations
- `src/scanner/adapters/checkov.py` - Checkov adapter parsing failed checks with prefix-based severity
- `src/scanner/adapters/__init__.py` - Updated with ALL_ADAPTERS list of all five adapter classes
- `tests/phase_02/test_adapter_semgrep.py` - 6 tests for Semgrep adapter
- `tests/phase_02/test_adapter_cppcheck.py` - 4 tests for cppcheck adapter
- `tests/phase_02/test_adapter_gitleaks.py` - 4 tests for Gitleaks adapter
- `tests/phase_02/test_adapter_trivy.py` - 5 tests for Trivy adapter
- `tests/phase_02/test_adapter_checkov.py` - 6 tests for Checkov adapter

## Decisions Made
- Used `unittest.mock.AsyncMock` directly instead of `pytest-mock` (not in dev dependencies) for mocking async `_execute` method
- Gitleaks secret redaction done via simple string replace of `Secret` field with `***REDACTED***` in the `Match` text
- Checkov severity determined by `check_id` prefix with longest-prefix-first matching to correctly distinguish CKV2_ from CKV_

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Switched from pytest-mock to unittest.mock**
- **Found during:** Task 1 (test execution)
- **Issue:** `mocker` fixture not available -- `pytest-mock` not in project dependencies
- **Fix:** Rewrote all tests to use `unittest.mock.AsyncMock` and `unittest.mock.patch` directly
- **Files modified:** All 5 test files
- **Verification:** All 25 tests pass

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Functionally equivalent mocking approach. No scope creep.

## Issues Encountered
None beyond the pytest-mock deviation noted above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All five scanner adapters ready for orchestration (Plan 03)
- ALL_ADAPTERS list provides easy iteration for scan orchestrator
- Each adapter follows identical interface contract from ScannerAdapter ABC

---
*Phase: 02-scanner-adapters-and-orchestration*
*Completed: 2026-03-19*
