# Phase 12: RBAC Foundation - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning

<domain>
## Phase Boundary

User accounts, API tokens, role-based authorization (admin/scanner/viewer), and SQLite hardening. Users can securely authenticate and access the platform according to their assigned role. Dashboard login, API token auth, and per-role endpoint access are all in scope. OAuth/SSO/LDAP, self-registration, and audit logging are explicitly out of scope.

</domain>

<decisions>
## Implementation Decisions

### Admin bootstrap
- First admin created via env vars: `SCANNER_ADMIN_USER` and `SCANNER_ADMIN_PASSWORD`
- On startup, if no users exist in DB, create admin from env vars
- If users already exist, ignore env vars entirely (skip silently, log a message)
- App refuses to start if no admin env vars are set and no users exist — always require auth
- Admin can create additional users from both the dashboard UI and API endpoints

### Token design
- Opaque random tokens with `nvsec_` prefix (e.g., `nvsec_a1b2c3d4e5...`)
- Full token shown only at creation time; after that, only masked prefix displayed
- Token stored as SHA-256 hash in the database (raw token never persisted)
- Optional expiration via `expires_at` field — non-expiring tokens allowed for CI/CD
- Soft limit of 10 active tokens per user
- Revocation supported via `revoked_at` timestamp

### Dashboard login flow
- Username/password login with cookie-based sessions (JWT in HttpOnly cookie)
- Session duration: 7 days before requiring re-login
- Dashboard header shows username + role badge (e.g., "admin") + logout link
- Login page styled consistently with existing dashboard CSS/layout (centered form within standard frame)
- Navigation hides links to pages the user's role cannot access
- Direct URL access to forbidden pages shows a friendly styled 403 page explaining which role is needed

### Role enforcement
- 3 roles: admin, scanner, viewer
- Admin: full access to all endpoints and dashboard pages
- Viewer: can view scan results and reports, cannot trigger scans or change settings (403)
- Scanner: can trigger scans and view results via API token only, no dashboard config access
- Unauthenticated API requests return 401

### Legacy API migration
- Clean break: remove legacy X-API-Key header support entirely
- Remove `SCANNER_API_KEY` env var — Claude's discretion on whether to repurpose or remove
- API uses `Authorization: Bearer <token>` header (standard HTTP auth)
- Dashboard uses separate cookie-based sessions (not Bearer tokens)
- Both paths resolve to the same User model via unified `get_current_user()` dependency

### SQLite hardening
- Add `PRAGMA busy_timeout=5000` to `db/session.py` as the first change
- Prevents write contention errors during concurrent operations

### Claude's Discretion
- Whether to remove `SCANNER_API_KEY` env var entirely or repurpose it as a secondary bootstrap mechanism
- Exact JWT cookie implementation details (signing algorithm, cookie name)
- Database migration approach (Alembic vs lightweight inline migrations)
- User CRUD API endpoint design (URL structure, request/response schemas)
- Password complexity requirements (if any)
- Exact 403 page design and wording

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Authentication stack
- `.planning/research/STACK.md` — PyJWT + pwdlib[bcrypt] selection rationale, version requirements
- `.planning/research/PITFALLS.md` — Auth system divergence pitfall, backward compat pitfall, SQLite contention fix
- `.planning/research/FEATURES.md` — P1/P2 feature prioritization for RBAC

### Architecture
- `.planning/research/ARCHITECTURE.md` — Unified auth dependency design, component integration points
- `.planning/codebase/ARCHITECTURE.md` — Current layered architecture, entry points, data flow
- `.planning/codebase/CONVENTIONS.md` — Naming patterns, Pydantic usage, two-model pattern

### Existing auth code (to be replaced)
- `src/scanner/api/auth.py` — Current X-API-Key dependency (will be replaced)
- `src/scanner/dashboard/auth.py` — Current cookie-based session (will be rewritten)
- `src/scanner/db/session.py` — SQLite engine setup (add busy_timeout here)
- `src/scanner/main.py` — App lifespan (add admin bootstrap and user table creation here)

### Requirements
- `.planning/REQUIREMENTS.md` — AUTH-01 through AUTH-07, INFRA-03

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/scanner/db/session.py`: Async SQLAlchemy engine with WAL mode — add busy_timeout pragma here
- `src/scanner/models/base.py`: Declarative base — new User, APIToken models extend this
- `src/scanner/config.py`: ScannerSettings with pydantic-settings — add admin bootstrap env vars here
- `src/scanner/main.py`: Lifespan with `_apply_schema_updates()` — pattern for lightweight migrations
- `src/scanner/dashboard/router.py`: Jinja2 template-based dashboard — add login page and user management pages

### Established Patterns
- Two-model pattern: Pydantic schemas in `schemas/` + SQLAlchemy ORM in `models/` with explicit mapping at persistence boundaries
- FastAPI `Depends()` injection for auth — currently `Depends(require_api_key)` on API routes
- Cookie-based dashboard auth with `require_dashboard_auth()` check per route
- Module-level `logger = logging.getLogger(__name__)` for all logging
- Google-style docstrings on all public functions

### Integration Points
- `src/scanner/api/router.py`: API router — replace `require_api_key` dependency with new `get_current_user()`
- `src/scanner/dashboard/router.py`: Dashboard router — replace `require_dashboard_auth()` with role-aware version
- `src/scanner/main.py`: App lifespan — add user table creation and admin bootstrap
- `src/scanner/api/scans.py`: Scan endpoints — add role checks (admin/scanner can trigger, viewer cannot)

</code_context>

<specifics>
## Specific Ideas

- Token prefix `nvsec_` for easy identification in logs and configs (short for "naveksoft security")
- GitHub/GitLab-style "show once" token display — user copies token at creation, never sees it again
- Clean break from legacy auth — no dual-auth complexity, simpler codebase
- 7-day sessions for a self-hosted internal tool — convenience over strict security

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 12-rbac-foundation*
*Context gathered: 2026-03-22*
