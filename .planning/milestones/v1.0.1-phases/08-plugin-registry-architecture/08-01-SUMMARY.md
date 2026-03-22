---
phase: 08-plugin-registry-architecture
plan: 01
subsystem: scanner
tags: [registry, importlib, pydantic, plugin-architecture, config]

requires:
  - phase: 07-security-scanner-ecosystem-research
    provides: "Config-driven plugin registry design recommendation"
provides:
  - "ScannerRegistry class with dynamic importlib adapter loading"
  - "Extended ScannerToolConfig with adapter_class and languages fields"
  - "Migrated config.yml with all 8 scanners in plugin format"
  - "RegisteredScanner dataclass with status/error tracking"
affects: [08-02-orchestrator-refactor, scanner-api, language-detect]

tech-stack:
  added: []
  patterns: ["importlib dynamic loading", "config-driven plugin registry", "dataclass registry entry"]

key-files:
  created:
    - src/scanner/adapters/registry.py
    - tests/phase_08/test_config_migration.py
    - tests/phase_08/test_registry.py
  modified:
    - src/scanner/config.py
    - src/scanner/adapters/__init__.py
    - config.yml

key-decisions:
  - "Replaced ScannersConfig class with dict[str, ScannerToolConfig] for dynamic scanner registration"
  - "Added field_validator to coerce raw YAML dicts into ScannerToolConfig instances"
  - "Removed ALL_ADAPTERS from __init__.py -- orchestrator will be updated in Plan 02"

patterns-established:
  - "Plugin loading: importlib.import_module + getattr for dotted class paths"
  - "Graceful degradation: invalid adapter_class logs WARNING, scanner skipped (no crash)"
  - "Universal scanners: languages=[] means always included regardless of detected languages"

requirements-completed: [PLUG-01, PLUG-03]

duration: 3min
completed: 2026-03-21
---

# Phase 08 Plan 01: Plugin Registry Core Summary

**Config-driven ScannerRegistry with importlib dynamic loading, extended ScannerToolConfig (adapter_class + languages), and migrated config.yml for all 8 scanners**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-21T17:08:55Z
- **Completed:** 2026-03-21T17:12:16Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- ScannerToolConfig extended with adapter_class and languages fields, ScannersConfig removed
- ScannerRegistry dynamically loads adapter classes via importlib with full error handling
- config.yml migrated with all 8 scanners including adapter_class paths and language lists
- 20 tests covering config migration, registry loading, validation, language filtering

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Config migration tests** - `40cbb4f` (test)
2. **Task 1 GREEN: Config model + config.yml** - `92b59af` (feat)
3. **Task 2 RED: Registry tests** - `3da54e5` (test)
4. **Task 2 GREEN: Registry + simplified __init__.py** - `25a087e` (feat)

_TDD: RED/GREEN commits for each task_

## Files Created/Modified
- `src/scanner/adapters/registry.py` - ScannerRegistry, load_adapter_class, RegisteredScanner (124 lines)
- `src/scanner/config.py` - Extended ScannerToolConfig with adapter_class/languages, dict-based scanners
- `src/scanner/adapters/__init__.py` - Simplified to single ScannerAdapter export (ALL_ADAPTERS removed)
- `config.yml` - All 8 scanners with adapter_class and languages fields
- `tests/phase_08/test_config_migration.py` - 9 tests for config model and YAML loading
- `tests/phase_08/test_registry.py` - 11 tests for registry loading, validation, filtering

## Decisions Made
- Replaced ScannersConfig class with dict[str, ScannerToolConfig] for dynamic scanner registration
- Added pydantic field_validator to coerce raw YAML dicts into ScannerToolConfig instances
- Removed ALL_ADAPTERS from __init__.py -- orchestrator import will be updated in Plan 02

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- ScannerRegistry and config model ready for Plan 02 orchestrator refactoring
- Orchestrator currently imports ALL_ADAPTERS (now removed) -- Plan 02 must update to use ScannerRegistry
- Orchestrator attribute access (settings.scanners.gitleaks) must change to dict access in Plan 02

---
*Phase: 08-plugin-registry-architecture*
*Completed: 2026-03-21*
