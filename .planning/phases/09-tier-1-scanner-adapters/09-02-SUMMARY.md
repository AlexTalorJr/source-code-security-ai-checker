---
phase: 09-tier-1-scanner-adapters
plan: 02
subsystem: scanner
tags: [brakeman, cargo-audit, ruby, rust, cvss, sast, sca, plugin-registry]

# Dependency graph
requires:
  - phase: 09-tier-1-scanner-adapters (plan 01)
    provides: "GosecAdapter, BanditAdapter, ScannerAdapter base class, registry"
  - phase: 08-config-driven-registry
    provides: "ScannerRegistry, ScannerToolConfig, config.yml structure"
provides:
  - "BrakemanAdapter for Ruby/Rails SAST scanning"
  - "CargoAuditAdapter for Rust SCA scanning with CVSS severity"
  - "All 4 Tier-1 scanners registered in config.yml (gosec, bandit, brakeman, cargo_audit)"
  - "Config registration integration tests"
affects: [phase-10-sarif-tier2, scanner-orchestrator]

# Tech tracking
tech-stack:
  added: [cvss>=3.2]
  patterns: [confidence-weighted-severity, cvss-score-severity-mapping, lockfile-generation]

key-files:
  created:
    - src/scanner/adapters/brakeman.py
    - src/scanner/adapters/cargo_audit.py
    - tests/phase_09/fixtures/brakeman_output.json
    - tests/phase_09/fixtures/cargo_audit_output.json
    - tests/phase_09/test_adapter_brakeman.py
    - tests/phase_09/test_adapter_cargo_audit.py
    - tests/phase_09/test_config_registration.py
  modified:
    - config.yml
    - pyproject.toml
    - tests/phase_08/test_config_migration.py

key-decisions:
  - "Brakeman uses confidence-weighted severity: High->HIGH, Medium->MEDIUM, Weak->LOW (downgraded)"
  - "cargo-audit uses cvss library for CVSS vector to severity conversion with score ranges"
  - "cargo-audit defaults to MEDIUM when CVSS vector is null (safe default)"
  - "cargo-audit generates Cargo.lock via cargo generate-lockfile if missing (per CONTEXT.md decision)"

patterns-established:
  - "Confidence-weighted severity: map tool confidence levels to Severity enum"
  - "CVSS-to-severity conversion: 9.0+ CRITICAL, 7.0-8.9 HIGH, 4.0-6.9 MEDIUM, 0.1-3.9 LOW"
  - "Lockfile generation: auto-generate dependency lockfiles before SCA scanning"
  - "Graceful tool absence: return empty results when tool binary not installed"

requirements-completed: [SCAN-03, SCAN-04]

# Metrics
duration: 3min
completed: 2026-03-21
---

# Phase 09 Plan 02: Brakeman & Cargo-Audit Adapters Summary

**Brakeman adapter with confidence-weighted severity and cargo-audit adapter with CVSS-based severity, plus all 4 Tier-1 scanners registered in config.yml**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-21T21:49:04Z
- **Completed:** 2026-03-21T21:52:35Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments
- BrakemanAdapter parses JSON warnings with confidence-weighted severity (High->HIGH, Medium->MEDIUM, Weak->LOW downgrade)
- CargoAuditAdapter parses vulnerabilities with CVSS-based severity using cvss library, ignores warnings section
- cargo-audit auto-generates Cargo.lock if missing via cargo generate-lockfile, gracefully handles missing cargo binary
- All 4 new Tier-1 scanners registered in config.yml (12 total scanners)
- Integration tests verify all 4 adapters load via importlib and filter by language correctly
- 24 new tests (9 brakeman + 12 cargo-audit + 3 config registration), 44 total phase 09 tests passing

## Task Commits

Each task was committed atomically:

1. **Task 1: Create Brakeman adapter with tests** - `d395884` (feat)
2. **Task 2: Create cargo-audit adapter with tests, register all 4 scanners** - `8583bfe` (feat)

## Files Created/Modified
- `src/scanner/adapters/brakeman.py` - BrakemanAdapter with confidence-weighted severity mapping
- `src/scanner/adapters/cargo_audit.py` - CargoAuditAdapter with CVSS-based severity and lockfile generation
- `tests/phase_09/fixtures/brakeman_output.json` - Brakeman fixture with 3 warnings (High/Medium/Weak)
- `tests/phase_09/fixtures/cargo_audit_output.json` - cargo-audit fixture with 2 vulns + 1 yanked warning
- `tests/phase_09/test_adapter_brakeman.py` - 9 tests for Brakeman parsing, severity, edge cases
- `tests/phase_09/test_adapter_cargo_audit.py` - 12 tests for cargo-audit parsing, CVSS, lockfile generation
- `tests/phase_09/test_config_registration.py` - 3 integration tests for registry loading and language filtering
- `config.yml` - Added gosec, bandit, brakeman, cargo_audit scanner entries
- `pyproject.toml` - Added cvss>=3.2 dependency
- `tests/phase_08/test_config_migration.py` - Updated expected scanner count from 8 to 12

## Decisions Made
- Brakeman uses confidence-weighted severity: High->HIGH, Medium->MEDIUM, Weak->LOW (downgraded one level)
- cargo-audit uses cvss library (CVSS3 class) for score-based severity ranges per CONTEXT.md
- Null CVSS defaults to MEDIUM (safe default per CONTEXT.md)
- cargo-audit generates Cargo.lock if missing via cargo generate-lockfile (per CONTEXT.md user decision)
- Non-Rails Ruby projects handled gracefully (empty results, no error)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated phase 08 test to include new scanner entries**
- **Found during:** Task 2 (config.yml registration)
- **Issue:** test_config_migration.py expected exactly 8 scanners, now has 12
- **Fix:** Updated EXPECTED_SCANNERS set and test name to include gosec, bandit, brakeman, cargo_audit
- **Files modified:** tests/phase_08/test_config_migration.py
- **Verification:** All 78 phase 08+09 tests pass
- **Committed in:** 8583bfe (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary update to existing test reflecting new config.yml entries. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 4 Tier-1 scanner adapters complete (gosec, bandit, brakeman, cargo-audit)
- 12 total scanners registered in config.yml with adapter_class paths
- Plugin registry fully operational with dynamic loading and language filtering
- Ready for SARIF helpers and Tier-2 scanner adapters

---
*Phase: 09-tier-1-scanner-adapters*
*Completed: 2026-03-21*
