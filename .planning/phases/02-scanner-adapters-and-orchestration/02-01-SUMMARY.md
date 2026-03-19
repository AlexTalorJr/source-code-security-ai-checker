---
phase: 02-scanner-adapters-and-orchestration
plan: 01
subsystem: scanner
tags: [abc, asyncio, subprocess, git-clone, pydantic, fixtures]

# Dependency graph
requires:
  - phase: 01-foundation-and-data-models
    provides: FindingSchema, Severity, compute_fingerprint, ScannerSettings, config.yml
provides:
  - ScannerAdapter ABC with run/get_version/_execute/_normalize_path contract
  - ScannerTimeoutError, ScannerExecutionError, GitCloneError exceptions
  - ScannerToolConfig and ScannersConfig for per-tool settings
  - Git clone module with SSH passthrough and HTTPS token auth
  - Test fixtures for semgrep, cppcheck, gitleaks, trivy, checkov
affects: [02-02, 02-03, all adapter implementations]

# Tech tracking
tech-stack:
  added: []
  patterns: [ScannerAdapter ABC pattern, asyncio subprocess with timeout, GIT_ASKPASS token injection]

key-files:
  created:
    - src/scanner/adapters/__init__.py
    - src/scanner/adapters/base.py
    - src/scanner/core/exceptions.py
    - src/scanner/core/git.py
    - tests/phase_02/__init__.py
    - tests/phase_02/conftest.py
    - tests/phase_02/test_git.py
    - tests/phase_02/test_base_adapter.py
    - tests/phase_02/fixtures/semgrep_output.json
    - tests/phase_02/fixtures/cppcheck_output.xml
    - tests/phase_02/fixtures/gitleaks_output.json
    - tests/phase_02/fixtures/trivy_output.json
    - tests/phase_02/fixtures/checkov_output.json
  modified:
    - src/scanner/config.py
    - config.yml.example

key-decisions:
  - "config.yml is gitignored; updated config.yml.example with scanners section instead"
  - "ScannerAdapter.tool_name as abstract property (not class attribute) for cleaner ABC contract"

patterns-established:
  - "ScannerAdapter ABC: all adapters implement run(), _version_command(), inherit _execute() with timeout"
  - "GIT_ASKPASS script injection for HTTPS token auth without leaking tokens in process args"
  - "Phase test fixtures in tests/phase_NN/fixtures/ with conftest.py loading helpers"

requirements-completed: [SCAN-04, SCAN-05, SCAN-06]

# Metrics
duration: 4min
completed: 2026-03-19
---

# Phase 02 Plan 01: Contracts and Infrastructure Summary

**Scanner adapter ABC with asyncio subprocess execution, git clone module with token auth, and realistic test fixtures for all five tools**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-19T04:38:30Z
- **Completed:** 2026-03-19T04:42:17Z
- **Tasks:** 2
- **Files modified:** 15

## Accomplishments
- ScannerAdapter ABC defines run/get_version/_execute/_normalize_path contract for all five tool adapters
- ScannerSettings extended with ScannersConfig (per-tool enabled/timeout/extra_args) and git_token
- Git clone module supports SSH passthrough and HTTPS token auth via GIT_ASKPASS
- Realistic test fixtures for semgrep, cppcheck, gitleaks, trivy, and checkov output formats
- 11 new tests pass, 39 existing tests unaffected (50 total)

## Task Commits

Each task was committed atomically:

1. **Task 1: Exceptions, config extension, and base adapter ABC** - `27fe17c` (feat)
2. **Task 2: Git clone module, test fixtures, and tests** - `747540d` (feat)

## Files Created/Modified
- `src/scanner/core/exceptions.py` - ScannerError, ScannerTimeoutError, ScannerExecutionError, GitCloneError
- `src/scanner/config.py` - Extended with ScannerToolConfig, ScannersConfig, git_token
- `src/scanner/adapters/__init__.py` - Package init exporting ScannerAdapter
- `src/scanner/adapters/base.py` - ScannerAdapter ABC with _execute timeout handling and _normalize_path
- `src/scanner/core/git.py` - clone_repo (async) and cleanup_clone functions
- `config.yml.example` - Added scanners section with per-tool defaults
- `tests/phase_02/conftest.py` - Shared fixtures for phase 02 tests
- `tests/phase_02/test_git.py` - 5 tests for git clone/cleanup
- `tests/phase_02/test_base_adapter.py` - 6 tests for adapter ABC methods
- `tests/phase_02/fixtures/*.json|xml` - Realistic output fixtures for all 5 tools

## Decisions Made
- config.yml is gitignored; updated config.yml.example with scanners section instead
- ScannerAdapter.tool_name implemented as abstract property rather than class attribute for cleaner ABC enforcement

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated config.yml.example instead of gitignored config.yml**
- **Found during:** Task 1 (config extension)
- **Issue:** config.yml is in .gitignore, cannot be committed
- **Fix:** Applied scanners section to config.yml.example (the tracked template file)
- **Files modified:** config.yml.example
- **Verification:** File committed successfully
- **Committed in:** 27fe17c (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary adaptation for gitignore pattern. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- ScannerAdapter ABC ready for concrete adapter implementations (Plan 02)
- All five fixture files available for adapter parse_output tests
- Exception classes ready for error handling in adapters
- ScannersConfig provides per-tool settings for adapter initialization

---
*Phase: 02-scanner-adapters-and-orchestration*
*Completed: 2026-03-19*
