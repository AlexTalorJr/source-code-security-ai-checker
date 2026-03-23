---
phase: 12-rbac-foundation
plan: 04
subsystem: api
tags: [rbac, crud, tokens, fastapi, authorization]

# Dependency graph
requires:
  - phase: 12-rbac-foundation (plan 01)
    provides: User/APIToken ORM models, Pydantic auth schemas
  - phase: 12-rbac-foundation (plan 02)
    provides: get_current_user, require_role auth dependencies
  - phase: 12-rbac-foundation (plan 03)
    provides: Auth-aware test fixtures (conftest.py, get_admin_token)
provides:
  - User CRUD API endpoints (admin only)
  - Token management API endpoints (per user)
  - Role-based auth guards on all existing API endpoints
  - Comprehensive tests for AUTH-01, AUTH-03, AUTH-04, AUTH-05, AUTH-06
affects: [12-rbac-foundation plan 05, dashboard-rbac]

# Tech tracking
tech-stack:
  added: []
  patterns: [admin-only CRUD via require_role(Role.ADMIN), per-user token management via get_current_user, soft token limit]

key-files:
  created:
    - src/scanner/api/users.py
    - src/scanner/api/tokens.py
    - tests/phase_12/test_user_crud.py
    - tests/phase_12/test_tokens.py
    - tests/phase_12/test_roles.py
  modified:
    - src/scanner/api/router.py
    - src/scanner/api/scans.py
    - src/scanner/api/findings.py
    - src/scanner/api/scanners.py

key-decisions:
  - "Findings suppress/unsuppress endpoints guarded with get_current_user (any authenticated user)"
  - "Scanners list endpoint guarded with get_current_user (any authenticated user)"

patterns-established:
  - "Admin-only endpoints: Depends(require_role(Role.ADMIN))"
  - "Scan trigger: Depends(require_role(Role.ADMIN, Role.SCANNER))"
  - "Read-only endpoints: Depends(get_current_user)"
  - "Token soft limit of 10 per user with nvsec_ prefix"

requirements-completed: [AUTH-01, AUTH-03, AUTH-04, AUTH-05, AUTH-06]

# Metrics
duration: 3min
completed: 2026-03-23
---

# Phase 12 Plan 04: API Endpoints & Role Enforcement Summary

**User CRUD (admin-only), token management (per-user with nvsec_ prefix), and role-based auth guards on all existing API endpoints**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-23T04:34:35Z
- **Completed:** 2026-03-23T04:37:46Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- User CRUD API: create (201), list (200), update (200), deactivate (204) -- admin only with self-protection guards
- Token management API: create (200 with raw_token shown once), list (200 with masked prefix), revoke (204) -- soft limit of 10
- All existing API endpoints migrated from legacy require_api_key to role-based auth
- POST scan trigger requires admin or scanner role; GET endpoints require any authenticated user
- Comprehensive tests covering AUTH-01 (user CRUD), AUTH-03 (token management), AUTH-04 (admin full access), AUTH-05 (viewer restrictions), AUTH-06 (scanner limits)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create User CRUD and Token management API endpoints** - `2c353a8` (feat)
2. **Task 2: Create role enforcement and CRUD integration tests** - `345c305` (test)

**Plan metadata:** pending (docs: complete plan)

## Files Created/Modified
- `src/scanner/api/users.py` - User management CRUD (admin only): create, list, get /me, update, deactivate
- `src/scanner/api/tokens.py` - Token management: create with nvsec_ prefix, list masked, revoke
- `src/scanner/api/router.py` - Added users and tokens router includes
- `src/scanner/api/scans.py` - Replaced require_api_key with role-based auth
- `src/scanner/api/findings.py` - Replaced require_api_key with get_current_user
- `src/scanner/api/scanners.py` - Added get_current_user auth guard
- `tests/phase_12/test_user_crud.py` - AUTH-01 tests (5 tests)
- `tests/phase_12/test_tokens.py` - AUTH-03 tests (4 tests)
- `tests/phase_12/test_roles.py` - AUTH-04/05/06 tests (3 tests)

## Decisions Made
- Findings suppress/unsuppress endpoints guarded with get_current_user (any authenticated user can manage suppressions)
- Scanners list endpoint guarded with get_current_user (any authenticated user can view scanner registry)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added auth guard to scanners.py**
- **Found during:** Task 1
- **Issue:** scanners.py had no authentication -- any unauthenticated user could list scanners
- **Fix:** Added get_current_user dependency to list_scanners endpoint
- **Files modified:** src/scanner/api/scanners.py
- **Verification:** Static analysis confirms get_current_user import and usage
- **Committed in:** 2c353a8 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** Auth guard addition was necessary for the "all existing API endpoints require authentication" requirement. No scope creep.

## Issues Encountered
- pwdlib not installed in execution environment -- verification done via static AST analysis instead of runtime import checks

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All API endpoints protected with role-based auth
- User CRUD and token management APIs ready for dashboard integration (Plan 05)
- Test fixtures support creating users with specific roles via _create_user_with_token helper

## Self-Check: PASSED

All 6 created files verified on disk. Both task commits (2c353a8, 345c305) confirmed in git log.

---
*Phase: 12-rbac-foundation*
*Completed: 2026-03-23*
