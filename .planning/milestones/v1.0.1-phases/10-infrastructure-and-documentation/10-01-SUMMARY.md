---
phase: 10-infrastructure-and-documentation
plan: 01
subsystem: infra
tags: [docker, dockerfile, makefile, gosec, bandit, brakeman, cargo-audit, smoke-tests, pytest]

# Dependency graph
requires:
  - phase: 09-tier1-scanner-adapters
    provides: "Scanner adapter implementations for gosec, bandit, brakeman, cargo-audit"
provides:
  - "Dockerfile with all 12 scanner binaries installed"
  - "verify-scanners Makefile target for CI smoke testing"
  - "Smoke test samples for Go, Python, Ruby, Rust"
  - "Doc consistency test scaffold (tests/phase_10/)"
affects: [10-02, 10-03]

# Tech tracking
tech-stack:
  added: [gosec v2.25.0, bandit, brakeman <8, cargo-audit v0.22.1]
  patterns: [binary tarball install, pip install, apt+gem install]

key-files:
  created:
    - tests/smoke/go_sample/main.go
    - tests/smoke/python_sample/vuln.py
    - tests/smoke/ruby_sample/Gemfile
    - tests/smoke/ruby_sample/app/controllers/application_controller.rb
    - tests/smoke/rust_sample/Cargo.toml
    - tests/phase_10/__init__.py
    - tests/phase_10/conftest.py
    - tests/phase_10/test_docs_consistency.py
  modified:
    - Dockerfile
    - Makefile

key-decisions:
  - "Pinned brakeman < 8 for Ruby 3.1 compatibility (Debian Bookworm)"

patterns-established:
  - "Smoke test samples: minimal files with known vulnerabilities per scanner"
  - "Doc consistency tests: pytest-based grep checks across all 5 languages"

requirements-completed: [INFRA-01, INFRA-02]

# Metrics
duration: 2min
completed: 2026-03-22
---

# Phase 10 Plan 01: Infrastructure and Documentation Summary

**Dockerfile extended with gosec, bandit, brakeman, cargo-audit installs; verify-scanners Makefile target and doc consistency test scaffold created**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-22T08:21:54Z
- **Completed:** 2026-03-22T08:23:43Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments
- Dockerfile now installs all 12 scanner binaries with multi-arch support
- Smoke test sample projects created for Go, Python, Ruby, and Rust with known vulnerabilities
- verify-scanners Makefile target checks all 12 scanners inside Docker container
- Doc consistency test scaffold with 7 automated checks ready for Plans 02/03

## Task Commits

Each task was committed atomically:

1. **Task 1: Add 4 new scanner installs to Dockerfile and create smoke test samples** - `04bda73` (feat)
2. **Task 2: Add verify-scanners Makefile target and create doc consistency test scaffold** - `4266e8f` (feat)

## Files Created/Modified
- `Dockerfile` - Added gosec, bandit, brakeman, cargo-audit install blocks before non-root user creation
- `Makefile` - Added verify-scanners target with 12 scanner checks, updated .PHONY
- `tests/smoke/go_sample/main.go` - Go sample with gosec G101 hardcoded credentials
- `tests/smoke/python_sample/vuln.py` - Python sample with bandit B105 hardcoded password
- `tests/smoke/ruby_sample/Gemfile` - Minimal Rails Gemfile for brakeman
- `tests/smoke/ruby_sample/app/controllers/application_controller.rb` - SQL injection pattern
- `tests/smoke/rust_sample/Cargo.toml` - Cargo.toml with vulnerable smallvec 0.6.9
- `tests/phase_10/__init__.py` - Package init
- `tests/phase_10/conftest.py` - Shared fixtures: scanner names, languages, doc file paths
- `tests/phase_10/test_docs_consistency.py` - 7 doc consistency checks across 5 languages

## Decisions Made
- Pinned brakeman to < 8 (using `gem install brakeman -v '< 8'`) because Debian Bookworm provides Ruby 3.1 and Brakeman 8.0.4 requires Ruby >= 3.2.0

## Deviations from Plan

None - plan executed exactly as written (brakeman version pin was anticipated in the plan's NOTE).

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Dockerfile ready for Docker build verification (INFRA-01/INFRA-02 can be validated with `make install && make verify-scanners`)
- Doc consistency tests will fail until Plans 02/03 update documentation with 12-scanner references
- Smoke test samples ready for scanner verification inside Docker

## Self-Check: PASSED

All 10 files verified present. Both task commits (04bda73, 4266e8f) confirmed in git log.

---
*Phase: 10-infrastructure-and-documentation*
*Completed: 2026-03-22*
