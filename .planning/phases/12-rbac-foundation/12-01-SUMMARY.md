---
phase: 12-rbac-foundation
plan: 01
subsystem: auth
tags: [sqlalchemy, pydantic, pyjwt, pwdlib, bcrypt, sqlite, rbac]

# Dependency graph
requires: []
provides:
  - User and APIToken ORM models
  - Auth Pydantic schemas (UserCreate, UserResponse, UserUpdate, TokenCreate, TokenResponse, TokenCreatedResponse, LoginRequest)
  - Admin bootstrap mechanism in app lifespan
  - JWT secret key auto-generation
  - SQLite busy_timeout pragma for write contention
affects: [12-02, 12-03, 12-04, 12-05]

# Tech tracking
tech-stack:
  added: [PyJWT>=2.12.1, pwdlib[bcrypt]>=0.3.0]
  patterns: [admin-bootstrap-on-first-startup, jwt-secret-file-persistence]

key-files:
  created:
    - src/scanner/models/user.py
    - src/scanner/schemas/auth.py
  modified:
    - pyproject.toml
    - src/scanner/db/session.py
    - src/scanner/config.py
    - src/scanner/main.py

key-decisions:
  - "Removed legacy api_key from config with extra=ignore for env var backward compat"
  - "JWT secret key persisted to .secret_key file alongside database"

patterns-established:
  - "Admin bootstrap: check user count at startup, create from env vars if zero"
  - "Secret key file: auto-generate and persist alongside db_path"

requirements-completed: [INFRA-03, AUTH-01]

# Metrics
duration: 3min
completed: 2026-03-23
---

# Phase 12 Plan 01: RBAC Data Layer Summary

**User/APIToken ORM models, auth Pydantic schemas, SQLite busy_timeout hardening, and admin bootstrap from env vars on first startup**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-23T04:24:06Z
- **Completed:** 2026-03-23T04:27:15Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- User and APIToken ORM models with proper constraints (unique username, unique token_hash)
- Auth Pydantic schemas covering login, CRUD, and token management
- SQLite busy_timeout=5000 as first pragma to prevent write contention
- Admin bootstrap in lifespan with IntegrityError race condition guard
- JWT secret key auto-generation with file persistence
- PyJWT and pwdlib[bcrypt] dependencies installed

## Task Commits

Each task was committed atomically:

1. **Task 1: Add dependencies, SQLite hardening, User/APIToken models, and auth schemas** - `91dde1f` (feat)
2. **Task 2: Config changes and admin bootstrap in lifespan** - `afb5187` (feat)

## Files Created/Modified
- `src/scanner/models/user.py` - User and APIToken ORM models
- `src/scanner/schemas/auth.py` - Pydantic schemas for auth requests/responses
- `pyproject.toml` - Added PyJWT and pwdlib[bcrypt] dependencies
- `src/scanner/db/session.py` - Added busy_timeout=5000 as first pragma
- `src/scanner/config.py` - Added admin_user, admin_password, secret_key; removed api_key
- `src/scanner/main.py` - Added admin bootstrap and JWT secret key management in lifespan

## Decisions Made
- Removed legacy `api_key` field from ScannerSettings (clean break from legacy auth). Added `extra="ignore"` to SettingsConfigDict so existing SCANNER_API_KEY env vars don't crash startup.
- JWT secret key persisted to `.secret_key` file in same directory as the database file, auto-generated on first run if SCANNER_SECRET_KEY env var not set.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added extra="ignore" to SettingsConfigDict**
- **Found during:** Task 2 (Config changes)
- **Issue:** Removing api_key field caused pydantic to reject SCANNER_API_KEY env var that was still set in environment
- **Fix:** Added `extra="ignore"` to SettingsConfigDict so unknown env vars are silently ignored
- **Files modified:** src/scanner/config.py
- **Verification:** ScannerSettings instantiation succeeds with SCANNER_API_KEY in env
- **Committed in:** afb5187 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Essential fix for backward compatibility during auth migration. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- User and APIToken models ready for JWT auth endpoints (Plan 02)
- Auth schemas ready for login/registration/token CRUD routes
- Admin bootstrap ensures at least one admin user exists before auth enforcement
- Legacy api_key auth references in src/scanner/api/auth.py and src/scanner/dashboard/auth.py will need updating in Plan 02/03

---
*Phase: 12-rbac-foundation*
*Completed: 2026-03-23*
