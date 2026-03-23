---
phase: 12-rbac-foundation
plan: 02
subsystem: auth
tags: [jwt, bcrypt, pwdlib, pyjwt, fastapi, rbac, bearer-token]

# Dependency graph
requires:
  - phase: 12-rbac-foundation/01
    provides: User and APIToken ORM models, ScannerSettings with secret_key
provides:
  - Unified get_current_user() FastAPI dependency (Bearer + cookie)
  - require_role() authorization factory
  - Role enum (admin, scanner, viewer)
  - JWT session creation/verification for dashboard
  - Password hashing/verification via pwdlib bcrypt
affects: [12-rbac-foundation/03, 12-rbac-foundation/04, 12-rbac-foundation/05]

# Tech tracking
tech-stack:
  added: [PyJWT, pwdlib-bcrypt]
  patterns: [dual-auth-path, dependency-factory-authorization]

key-files:
  created: []
  modified:
    - src/scanner/api/auth.py
    - src/scanner/dashboard/auth.py
    - src/scanner/main.py

key-decisions:
  - "Used explicit BcryptHasher instead of PasswordHash.default() which does not exist in pwdlib 0.3.0"
  - "Reused hash_password from dashboard.auth in main.py admin bootstrap for single source of truth"

patterns-established:
  - "Dual auth path: get_current_user checks Bearer token first, then JWT cookie"
  - "Role authorization via require_role() dependency factory returning Depends-compatible async function"

requirements-completed: [AUTH-02, AUTH-07]

# Metrics
duration: 2min
completed: 2026-03-23
---

# Phase 12 Plan 02: Unified Auth Core Summary

**Unified get_current_user() resolving Bearer tokens and JWT cookies to User model, with require_role() authorization factory and bcrypt password hashing via pwdlib**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-23T04:29:03Z
- **Completed:** 2026-03-23T04:31:24Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Rewritten dashboard/auth.py with JWT session management (HS256, 7-day expiry) and bcrypt password hashing
- Rewritten api/auth.py with unified get_current_user() supporting both Bearer token and JWT cookie auth paths
- require_role() dependency factory for per-endpoint authorization returning 403
- All legacy auth code removed (require_api_key, X-API-Key, make_session_token, require_dashboard_auth)

## Task Commits

Each task was committed atomically:

1. **Task 1: Rewrite dashboard/auth.py with JWT session management** - `fcee0b1` (feat)
2. **Task 2: Rewrite api/auth.py with unified get_current_user() and require_role()** - `3c8870f` (feat)

## Files Created/Modified
- `src/scanner/dashboard/auth.py` - JWT session creation/verification, password hashing/verification
- `src/scanner/api/auth.py` - Unified get_current_user(), require_role() factory, Role enum
- `src/scanner/main.py` - Fixed admin bootstrap to use dashboard.auth.hash_password

## Decisions Made
- Used explicit `BcryptHasher()` constructor instead of `PasswordHash.default()` which does not exist in pwdlib 0.3.0
- Consolidated password hashing: main.py admin bootstrap now imports `hash_password` from dashboard.auth instead of duplicating pwdlib setup

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed PasswordHash.default() API call**
- **Found during:** Task 1 (dashboard/auth.py rewrite)
- **Issue:** Plan specified `PasswordHash.default()` but pwdlib 0.3.0 has no `default()` method; the correct API is `PasswordHash((BcryptHasher(),))`
- **Fix:** Used explicit `BcryptHasher` import and `PasswordHash((BcryptHasher(),))` constructor
- **Files modified:** src/scanner/dashboard/auth.py
- **Verification:** hash_password/verify_password tests pass
- **Committed in:** fcee0b1 (Task 1 commit)

**2. [Rule 1 - Bug] Fixed same PasswordHash.default() bug in main.py**
- **Found during:** Task 1 (dashboard/auth.py rewrite)
- **Issue:** main.py admin bootstrap also used `PasswordHash.default()` (from Plan 01)
- **Fix:** Replaced with import of `hash_password` from `scanner.dashboard.auth` for single source of truth
- **Files modified:** src/scanner/main.py
- **Verification:** Import chain verified, no duplicate pwdlib setup
- **Committed in:** fcee0b1 (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (2 bugs)
**Impact on plan:** Both fixes required for runtime correctness. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Auth core complete: get_current_user() and require_role() ready for route integration
- Dashboard login route (Plan 03) can now use create_session_jwt and verify_password
- API routes can use require_role(Role.ADMIN) etc. for endpoint protection

---
*Phase: 12-rbac-foundation*
*Completed: 2026-03-23*
