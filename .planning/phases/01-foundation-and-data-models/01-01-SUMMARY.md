---
phase: 01-foundation-and-data-models
plan: 01
subsystem: infra
tags: [pydantic, pydantic-settings, fastapi, sqlalchemy, sha256, config, yaml]

# Dependency graph
requires: []
provides:
  - "ScannerSettings config system with YAML + env var override priority"
  - "Severity IntEnum (CRITICAL=5 through INFO=1) with ordering support"
  - "FindingSchema and ScanResultSchema Pydantic models"
  - "Deterministic SHA-256 fingerprint for finding deduplication"
  - "Python project skeleton with pyproject.toml and dev tooling"
affects: [01-02, 01-03, 02-scanner-integration, 03-ai-analysis, 04-quality-gates]

# Tech tracking
tech-stack:
  added: [fastapi, pydantic-settings, sqlalchemy, aiosqlite, alembic, pytest, pytest-asyncio, httpx, hatchling]
  patterns: [pydantic-settings-yaml-env-override, intenum-severity, sha256-fingerprint-dedup, tdd-red-green]

key-files:
  created:
    - pyproject.toml
    - src/scanner/__init__.py
    - src/scanner/config.py
    - src/scanner/schemas/__init__.py
    - src/scanner/schemas/severity.py
    - src/scanner/schemas/finding.py
    - src/scanner/schemas/scan.py
    - src/scanner/core/__init__.py
    - src/scanner/core/fingerprint.py
    - config.yml.example
    - .env.example
    - .gitignore
    - tests/__init__.py
    - tests/conftest.py
    - tests/test_config.py
    - tests/test_fingerprint.py
  modified: []

key-decisions:
  - "Dynamic YAML path resolution via os.environ.get in settings_customise_sources rather than model_config for testability"
  - "hatchling build backend with src layout for clean package structure"

patterns-established:
  - "Config: YAML file + env var overrides with SCANNER_ prefix, env wins over YAML"
  - "Severity: IntEnum with CRITICAL=5 to INFO=1 for natural comparison operators"
  - "Fingerprint: SHA-256 of normalized (path, rule_id, snippet) for cross-platform dedup"
  - "TDD: tests written first (RED), implementation second (GREEN), verified at each step"

requirements-completed: [SCAN-02, INFRA-03, INFRA-04]

# Metrics
duration: 5min
completed: 2026-03-18
---

# Phase 01 Plan 01: Project Skeleton Summary

**Pydantic config with YAML+env overrides, Severity IntEnum, Finding/ScanResult schemas, and SHA-256 fingerprint dedup module with 24 passing tests**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-18T20:03:15Z
- **Completed:** 2026-03-18T20:08:10Z
- **Tasks:** 2
- **Files modified:** 16

## Accomplishments
- ScannerSettings loads from YAML with env var overrides (env takes priority)
- Severity IntEnum with 5 levels and natural ordering for quality gate logic
- FindingSchema and ScanResultSchema Pydantic v2 models for the scanner data contract
- Deterministic fingerprint with path/whitespace/case normalization for finding dedup
- 24 tests covering config, severity, schemas, and fingerprint behavior

## Task Commits

Each task was committed atomically:

1. **Task 1: Project skeleton, config system, and Pydantic schemas** - `ac27031` (feat)
2. **Task 2: Fingerprint module with deterministic dedup hashing** - `433105b` (feat)

## Files Created/Modified
- `pyproject.toml` - Project metadata, deps (fastapi, pydantic-settings, sqlalchemy), pytest config
- `.gitignore` - Python defaults plus config.yml, .env, *.db exclusions
- `config.yml.example` - Template config with placeholder values, no secrets
- `.env.example` - Template env vars with placeholder values
- `src/scanner/__init__.py` - Package init with version
- `src/scanner/config.py` - ScannerSettings with YamlConfigSettingsSource and env override
- `src/scanner/schemas/__init__.py` - Schema exports
- `src/scanner/schemas/severity.py` - Severity IntEnum (CRITICAL=5 to INFO=1)
- `src/scanner/schemas/finding.py` - FindingSchema with all vulnerability fields
- `src/scanner/schemas/scan.py` - ScanResultSchema with status, counts, metadata
- `src/scanner/core/__init__.py` - Core utilities package
- `src/scanner/core/fingerprint.py` - compute_fingerprint with normalization and SHA-256
- `tests/__init__.py` - Test package
- `tests/conftest.py` - Shared fixtures (tmp_config_file, clean_env)
- `tests/test_config.py` - 14 tests for severity, config, and schema validation
- `tests/test_fingerprint.py` - 10 tests for fingerprint determinism and normalization

## Decisions Made
- Used `hatchling` build backend with src layout for clean separation of package code
- Resolved YAML config path dynamically in `settings_customise_sources` (not at class definition time) so tests can override SCANNER_CONFIG_PATH per-test via monkeypatch

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed static YAML path resolution in ScannerSettings**
- **Found during:** Task 1 (config implementation)
- **Issue:** `model_config = SettingsConfigDict(yaml_file=os.environ.get(...))` resolved at import time, not at instantiation, so test monkeypatching of SCANNER_CONFIG_PATH had no effect
- **Fix:** Moved YAML path resolution into `settings_customise_sources` via `YamlConfigSettingsSource(settings_cls, yaml_file=os.environ.get(...))`
- **Files modified:** src/scanner/config.py
- **Verification:** test_yaml_loading and test_config_path_env both pass
- **Committed in:** ac27031 (Task 1 commit)

**2. [Rule 3 - Blocking] Fixed hatchling build backend path**
- **Found during:** Task 1 (pip install)
- **Issue:** `build-backend = "hatchling.backends"` should be `"hatchling.build"`
- **Fix:** Corrected the build-backend value in pyproject.toml
- **Files modified:** pyproject.toml
- **Verification:** pip install -e ".[dev]" succeeds
- **Committed in:** ac27031 (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking)
**Impact on plan:** Both fixes necessary for correct operation. No scope creep.

## Issues Encountered
- System Python had no pip; resolved by creating a venv with python3 -m venv

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Config, schemas, and fingerprint module ready for use by Plan 02 (SQLAlchemy ORM models + DB) and Plan 03 (FastAPI health endpoint + Docker)
- All Pydantic schemas serve as the data contract for the entire scanner pipeline

## Self-Check: PASSED

All 16 files verified present. Both commit hashes (ac27031, 433105b) confirmed in git log. 24/24 tests passing.

---
*Phase: 01-foundation-and-data-models*
*Completed: 2026-03-18*
