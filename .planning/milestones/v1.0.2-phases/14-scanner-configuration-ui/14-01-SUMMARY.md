---
phase: 14-scanner-configuration-ui
plan: 01
subsystem: api
tags: [fastapi, yaml, config, pydantic, rest-api]

requires:
  - phase: 12-rbac-foundation
    provides: "Auth system with roles (admin/scanner/viewer), JWT tokens, require_role dependency"
provides:
  - "Config CRUD API: GET /api/config, GET /api/config/yaml, PATCH /api/config/scanners/{name}, PUT /api/config/yaml"
  - "Dashboard /scanners route handler (template pending Plan 02)"
  - "21 tests covering toggle, settings, and YAML editor requirements"
affects: [14-02-PLAN]

tech-stack:
  added: []
  patterns: ["Config API reads/writes config.yml directly via yaml.safe_load/yaml.dump", "Pydantic ScannerSettings.model_validate for schema validation"]

key-files:
  created:
    - src/scanner/api/config.py
    - tests/phase_14/__init__.py
    - tests/phase_14/conftest.py
    - tests/phase_14/test_scanner_toggle.py
    - tests/phase_14/test_scanner_settings.py
    - tests/phase_14/test_yaml_editor.py
  modified:
    - src/scanner/api/router.py
    - src/scanner/dashboard/router.py

key-decisions:
  - "Timeout validation range 30-900 seconds (matches plan spec)"
  - "Empty extra_args strings rejected at API level before Pydantic validation"
  - "PUT /api/config/yaml writes raw text to preserve user formatting"

patterns-established:
  - "Config endpoint pattern: read_config() -> modify -> validate_config_data() -> write_config()"
  - "Dashboard reads config.yml fresh on every page load (not cached app.state.settings)"

requirements-completed: [CONF-01, CONF-02, CONF-03]

duration: 6min
completed: 2026-03-23
---

# Phase 14 Plan 01: Config API Endpoints Summary

**4 REST API endpoints for scanner config CRUD with admin-only access, Pydantic validation, and YAML file persistence -- 21 tests passing**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-23T11:57:12Z
- **Completed:** 2026-03-23T12:03:00Z
- **Tasks:** 3
- **Files modified:** 8

## Accomplishments
- Config API with GET (JSON + YAML), PATCH (per-scanner), and PUT (full YAML) endpoints
- Full test coverage: 21 tests across 3 test files (toggle, settings, YAML editor)
- Admin-only access enforced on all config endpoints via require_role(Role.ADMIN)
- Dashboard scanner route ready for template creation in Plan 02

## Task Commits

Each task was committed atomically:

1. **Task 1: Create test infrastructure for Phase 14** - `4a8bc96` (test)
2. **Task 2: Create Config API endpoints** - `77f1f5a` (feat)
3. **Task 3: Add dashboard scanner route** - `af262d4` (feat)

## Files Created/Modified
- `src/scanner/api/config.py` - Config CRUD API endpoints (GET, PATCH, PUT)
- `src/scanner/api/router.py` - Register config_router in API aggregator
- `src/scanner/dashboard/router.py` - Scanner configuration page route (admin only)
- `tests/phase_14/__init__.py` - Test package init
- `tests/phase_14/conftest.py` - Shared fixtures with config.yml and auth helpers
- `tests/phase_14/test_scanner_toggle.py` - 7 tests for CONF-01 (enable/disable scanners)
- `tests/phase_14/test_scanner_settings.py` - 7 tests for CONF-02 (timeout, extra_args)
- `tests/phase_14/test_yaml_editor.py` - 7 tests for CONF-03 (raw YAML get/put)

## Decisions Made
- Timeout validation range set to 30-900 seconds as specified in plan
- Empty extra_args strings rejected at API level before Pydantic validation
- PUT /api/config/yaml writes raw text to preserve user formatting (not re-serialized through yaml.dump)
- Dashboard scanner route reads config.yml fresh on every page load per locked decision

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All 4 Config API endpoints functional and tested
- Dashboard /scanners route exists, awaiting scanners.html.j2 template from Plan 02
- Plan 02 can build the UI dashboard knowing the API contract is verified by 21 passing tests

---
*Phase: 14-scanner-configuration-ui*
*Completed: 2026-03-23*
