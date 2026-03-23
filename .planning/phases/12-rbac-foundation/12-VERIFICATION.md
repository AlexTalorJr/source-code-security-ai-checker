---
phase: 12-rbac-foundation
verified: 2026-03-23T05:30:00Z
status: passed
score: 9/9 must-haves verified
re_verification:
  previous_status: gaps_found
  previous_score: 7/9
  gaps_closed:
    - "All existing API endpoints require authentication and return correct status codes for unauthenticated/unauthorized access"
    - "Scanner endpoint accessible at /api/scanners with proper auth enforcement"
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "Navigate to /dashboard/login in a browser"
    expected: "Centered card with 'Security Scanner' heading, username and password fields with correct placeholder text, blue 'Log In' button, error banner visible when ?error=1 query param present"
    why_human: "Visual layout, spacing, color correctness cannot be verified programmatically"
  - test: "Log in as admin, scanner, and viewer users and inspect the navbar"
    expected: "Admin = blue (#0d6efd), Scanner = gray (#6c757d), Viewer = green (#28a745) badges"
    why_human: "Browser rendering of inline styles; color correctness requires visual inspection"
  - test: "Create a token from /dashboard/tokens; note the raw token display; navigate away and return"
    expected: "Token visible immediately after creation with 'Copy it now' alert; token NOT visible after navigating away (only masked prefix shown in table)"
    why_human: "Redirect-with-query-param pattern needs to be verified in an actual browser session"
  - test: "Log in as a viewer or scanner user and navigate to /dashboard/users"
    expected: "403 page with 'Access Denied', role information, 'Back to Dashboard' link"
    why_human: "Template rendering with correct role values in context requires browser verification"
---

# Phase 12: RBAC Foundation Verification Report

**Phase Goal:** Users can securely authenticate and access the platform according to their assigned role
**Verified:** 2026-03-23T05:30:00Z
**Status:** passed
**Re-verification:** Yes — after gap closure (scanners router prefix bug fixed in commit 909a0e3)

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | User and APIToken tables exist after app startup with correct schema | VERIFIED | `src/scanner/models/user.py` defines both ORM models with correct columns and constraints |
| 2 | Initial admin user created from env vars on first startup; app refuses to start without credentials when no users exist | VERIFIED | `lifespan()` in `src/scanner/main.py` contains admin bootstrap, `RuntimeError` guard, `IntegrityError` race-condition handling, and secret key file persistence |
| 3 | API requests with valid Bearer token resolve to correct User; unauthenticated API requests return 401 | VERIFIED | `get_current_user()` Bearer path works; `test_unauthenticated_api_returns_401` PASSES (GET /api/scanners returns 401); all 4 auth tests pass |
| 4 | Dashboard login with username+password sets JWT HttpOnly cookie | VERIFIED | `src/scanner/dashboard/router.py` `login_submit` uses `verify_password` + `create_session_jwt`, sets `scanner_session` cookie; `test_login_with_credentials` passes |
| 5 | require_role dependency returns 403 when user lacks required role | VERIFIED | `require_role()` in `src/scanner/api/auth.py` returns `HTTPException(status_code=403)`; `test_viewer_restricted` and `test_scanner_role_limits` pass |
| 6 | Admin can create, list, update, and deactivate users | VERIFIED | `src/scanner/api/users.py` has POST/GET/PUT/DELETE endpoints all protected with `require_role(Role.ADMIN)`; all 5 user CRUD tests pass |
| 7 | User can create, list, and revoke personal API tokens; raw token shown once | VERIFIED | `src/scanner/api/tokens.py` has create/list/revoke; `nvsec_` prefix enforced; `SOFT_TOKEN_LIMIT=10`; all 4 token tests pass |
| 8 | Dashboard UI shows username/role badge and hides admin navigation from non-admin roles | VERIFIED | `base.html.j2` has `user.username`, `user.role` badge display, admin-gated "Users" link; `test_navbar_shows_username_and_role` passes |
| 9 | Scanner endpoint accessible at /api/scanners with proper auth enforcement | VERIFIED | `scanners.py` router prefix corrected to `/scanners` (commit 909a0e3); `test_admin_full_access` passes (GET /api/scanners returns 200 for admin, 401 for unauthenticated) |

**Score:** 9/9 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/scanner/models/user.py` | User and APIToken ORM models | VERIFIED | `class User(Base)` with `__tablename__ = "users"`, `class APIToken(Base)` with `token_hash unique=True` |
| `src/scanner/schemas/auth.py` | Pydantic schemas for auth | VERIFIED | All 7 classes present: `UserCreate`, `UserResponse`, `UserUpdate`, `TokenCreate`, `TokenResponse`, `TokenCreatedResponse`, `LoginRequest` |
| `src/scanner/config.py` | Admin bootstrap env var fields | VERIFIED | `admin_user`, `admin_password`, `secret_key` fields present |
| `src/scanner/main.py` | Admin bootstrap logic in lifespan | VERIFIED | Contains `from scanner.models.user import User`, `hash_password`, `IntegrityError`, `RuntimeError`, `.secret_key` file generation |
| `src/scanner/api/auth.py` | Unified `get_current_user()`, `require_role()`, `Role` enum | VERIFIED | All present; Bearer token + JWT cookie dual-path; `sha256` hashing; `last_used_at` update; `is_active` check |
| `src/scanner/dashboard/auth.py` | JWT session management, password verification | VERIFIED | `hash_password`, `verify_password`, `create_session_jwt`, `verify_session_jwt` all present and functionally tested |
| `src/scanner/api/users.py` | User CRUD endpoints (admin only) | VERIFIED | POST/GET/GET-me/PUT/DELETE routes; `require_role(Role.ADMIN)` on all admin ops; lockout guards |
| `src/scanner/api/tokens.py` | Token management endpoints | VERIFIED | POST/GET/DELETE routes; `nvsec_` prefix; `SOFT_TOKEN_LIMIT=10`; SHA-256 hashing |
| `src/scanner/api/router.py` | Updated to include users and tokens routers | VERIFIED | `include_router(users_router)` and `include_router(tokens_router)` present |
| `src/scanner/api/scans.py` | Role-gated scan endpoints | VERIFIED | `require_role(Role.ADMIN, Role.SCANNER)` on POST (trigger); `get_current_user` on GET endpoints |
| `src/scanner/api/scanners.py` | Auth guard on scanners endpoint, correct prefix | VERIFIED | `prefix="/scanners"` (fixed); `get_current_user` dependency; route registers as `/api/scanners` |
| `src/scanner/dashboard/router.py` | JWT-based role-aware dashboard | VERIFIED | `_get_dashboard_user`, `_require_dashboard_role`, login/logout, `/users`, `/tokens` routes |
| `src/scanner/dashboard/templates/login.html.j2` | Username+password login form | VERIFIED | `name="username"`, `name="password"`, "Security Scanner" heading, error display |
| `src/scanner/dashboard/templates/403.html.j2` | Forbidden page | VERIFIED | "Access Denied", `{{ required_role }}`, `{{ user_role }}`, "Back to Dashboard" link |
| `src/scanner/dashboard/templates/users.html.j2` | Admin user management page | VERIFIED | "Create User" button, role select (admin/scanner/viewer), deactivate confirm dialog |
| `src/scanner/dashboard/templates/tokens.html.j2` | Token management page | VERIFIED | "Generate Token", `nvsec_` masked display, "Token created successfully", revoke confirm, 10-token limit message |
| `src/scanner/dashboard/templates/base.html.j2` | Updated navbar with user info | VERIFIED | `user.username`, `user.role` badge, admin-gated "Users" link, "API Tokens" link |
| `tests/phase_12/conftest.py` | Auth-aware test fixtures | VERIFIED | `auth_client`, `get_admin_token`, `TEST_ADMIN_USER`; no `SCANNER_API_KEY` |
| `tests/phase_12/test_db_pragmas.py` | INFRA-03 busy_timeout test | VERIFIED | `test_busy_timeout`, `test_wal_mode`, `test_foreign_keys` all pass |
| `tests/phase_12/test_auth.py` | AUTH-07 unauthenticated 401 tests | VERIFIED | All 4 tests pass including `test_unauthenticated_api_returns_401` (GET /api/scanners → 401) |
| `tests/phase_12/test_user_crud.py` | AUTH-01 CRUD tests | VERIFIED | All 5 test functions pass |
| `tests/phase_12/test_tokens.py` | AUTH-03 token tests | VERIFIED | All 4 test functions pass |
| `tests/phase_12/test_roles.py` | AUTH-04/05/06 role tests | VERIFIED | All 3 tests pass including `test_admin_full_access` (GET /api/scanners → 200) |
| `tests/phase_12/test_dashboard_login.py` | AUTH-02 login tests | VERIFIED | All 6 test functions pass |
| `tests/phase_05/conftest.py` | Migrated to Bearer token auth | VERIFIED | All 57 phase 05 tests pass with Bearer token auth; no regressions |

**Test results:** 25/25 phase 12 tests pass; 57/57 phase 05 regression tests pass

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `src/scanner/main.py` | `src/scanner/models/user.py` | `from scanner.models.user import User` | WIRED | Present in lifespan scope |
| `src/scanner/main.py` | `src/scanner/config.py` | `settings.admin_user` | WIRED | Used in lifespan bootstrap |
| `src/scanner/api/auth.py` | `src/scanner/models/user.py` | `select(User)`, `select(APIToken)` | WIRED | Both queries present in `get_current_user` |
| `src/scanner/api/auth.py` | `src/scanner/dashboard/auth.py` | `verify_session_jwt` | WIRED | `from scanner.dashboard.auth import COOKIE_NAME, verify_session_jwt` |
| `src/scanner/dashboard/auth.py` | `src/scanner/config.py` | `secret_key` | WIRED | `secret_key` parameter threaded through all JWT calls |
| `src/scanner/dashboard/router.py` | `src/scanner/api/auth.py` | `get_current_user` | WIRED | Imported and used for API-path auth in dashboard |
| `src/scanner/dashboard/router.py` | `src/scanner/dashboard/auth.py` | `create_session_jwt`, `verify_password`, `COOKIE_NAME` | WIRED | All three present in dashboard router |
| `src/scanner/api/users.py` | `src/scanner/api/auth.py` | `require_role(Role.ADMIN)` | WIRED | All admin endpoints use this dependency |
| `src/scanner/api/router.py` | `src/scanner/api/users.py` | `include_router(users_router)` | WIRED | Present |
| `src/scanner/api/router.py` | `src/scanner/api/tokens.py` | `include_router(tokens_router)` | WIRED | Present |
| `src/scanner/api/scanners.py` | `src/scanner/api/auth.py` | `get_current_user` dependency | WIRED | `Depends(get_current_user)` on `list_scanners`; route resolves at `/api/scanners` |
| `tests/phase_12/conftest.py` | `src/scanner/main.py` | `from scanner.main import create_app` | WIRED | Present in conftest |
| `tests/phase_05/conftest.py` | `src/scanner/api/auth.py` | `Authorization: Bearer` header | WIRED | Bearer token used in migrated `api_headers` fixture |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| AUTH-01 | 12-01, 12-04, 12-05 | Admin can create user accounts with username and password | SATISFIED | `POST /api/users` (plan 04), dashboard `/users` form (plan 05), all 5 user CRUD tests pass |
| AUTH-02 | 12-02, 12-05 | User can log in to dashboard with username and password | SATISFIED | Login page form + `login_submit` route (plan 05), all 6 dashboard login tests pass |
| AUTH-03 | 12-04, 12-05 | User can generate and revoke personal API tokens for CI/CD | SATISFIED | `POST/DELETE /api/tokens`, dashboard `/tokens` page, all 4 token tests pass |
| AUTH-04 | 12-04, 12-05 | Admin role has full access to all endpoints and dashboard pages | SATISFIED | `test_admin_full_access` PASSES: admin reaches `/api/scanners` (200), all role tests pass |
| AUTH-05 | 12-04, 12-05 | Viewer role can view scan results but cannot trigger scans or change settings | SATISFIED | `test_viewer_restricted` passes: viewer gets 403 on POST /api/scans and POST /api/users |
| AUTH-06 | 12-04, 12-05 | Scanner role can trigger scans via API only (no dashboard config access) | SATISFIED | `test_scanner_role_limits` passes: scanner gets 403 on GET/POST /api/users |
| AUTH-07 | 12-02, 12-03 | Unauthenticated requests to API return 401 | SATISFIED | `test_unauthenticated_api_returns_401` PASSES: GET /api/scanners → 401; `test_invalid_bearer_token_returns_401` passes |
| INFRA-03 | 12-01, 12-03 | SQLite busy_timeout configured to prevent write contention | SATISFIED | `busy_timeout=5000` is first pragma; `test_busy_timeout` passes |

All 8 phase 12 requirements are fully satisfied. No orphaned requirements found.

### Anti-Patterns Found

None. The previously identified blocker (`prefix="/api"` in `scanners.py`) was resolved in commit 909a0e3. No new anti-patterns detected.

### Human Verification Required

#### 1. Login page visual appearance

**Test:** Navigate to `/dashboard/login` in a browser
**Expected:** Centered card with "Security Scanner" heading, username and password fields with correct placeholder text, blue "Log In" button, error banner visible when `?error=1` query param present
**Why human:** Visual layout, spacing, color correctness cannot be verified programmatically

#### 2. Navbar role badge colors

**Test:** Log in as admin, scanner, and viewer users and inspect the navbar
**Expected:** Admin = blue (#0d6efd), Scanner = gray (#6c757d), Viewer = green (#28a745) badges
**Why human:** Browser rendering of inline styles; color correctness requires visual inspection

#### 3. Token "shown once" UX on dashboard

**Test:** Create a token from `/dashboard/tokens`; note the raw token display; navigate away and return
**Expected:** Token visible immediately after creation with "Copy it now" alert; token NOT visible after navigating away (only masked prefix shown in table)
**Why human:** Redirect-with-query-param pattern needs to be verified in an actual browser session

#### 4. 403 page display for non-admin accessing /dashboard/users

**Test:** Log in as a viewer or scanner user and navigate to `/dashboard/users`
**Expected:** 403 page with "Access Denied", role information, "Back to Dashboard" link
**Why human:** Template rendering with correct role values in context requires browser verification

### Re-verification Summary

**Gap closed:** The single blocker from initial verification (wrong router prefix in `src/scanner/api/scanners.py`) was fixed in commit 909a0e3. The fix changed `prefix="/api"` to `prefix="/scanners"` and also corrected the endpoint path from `"/"` to `""`. The phase 08 scanner tests were updated in the same commit to match the corrected route path.

**Test results after fix:**
- Phase 12: 25/25 tests pass (previously 23/25)
- Phase 05: 57/57 tests pass (no regressions)

**All 8 requirements now fully satisfied.** The authentication backbone, user management, token management, dashboard login, role enforcement, and scanner endpoint auth are all correctly implemented, wired, and tested.

---

_Verified: 2026-03-23T05:30:00Z_
_Verifier: Claude (gsd-verifier)_
_Re-verification: Yes — gap closure confirmed_
