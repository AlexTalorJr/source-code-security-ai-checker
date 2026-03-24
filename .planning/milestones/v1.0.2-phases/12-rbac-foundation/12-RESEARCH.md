# Phase 12: RBAC Foundation - Research

**Researched:** 2026-03-22
**Domain:** User authentication, API token management, role-based access control, SQLite hardening
**Confidence:** HIGH

## Summary

Phase 12 replaces the current single shared API key authentication with a full user-based RBAC system. The existing auth is minimal: one `SCANNER_API_KEY` env var checked via `X-API-Key` header (API) and SHA-256 hashed cookie (dashboard). The new system adds user accounts with password hashing, personal API tokens with SHA-256 hash storage, three roles (admin/scanner/viewer), and a unified `get_current_user()` dependency that resolves both cookie sessions and Bearer tokens to the same User model.

The stack additions are PyJWT 2.12.1 for JWT session tokens and pwdlib[bcrypt] 0.3.0 for password hashing -- both recommended by current FastAPI official documentation as replacements for the abandoned python-jose and deprecated passlib. The CONTEXT.md specifies a clean break from legacy X-API-Key auth (no backward compatibility period), admin bootstrap via env vars, and opaque `nvsec_`-prefixed API tokens stored as SHA-256 hashes.

SQLite hardening (PRAGMA busy_timeout=5000) is a one-line prerequisite that must land first. The existing `_set_sqlite_pragmas` listener in `db/session.py` already sets WAL mode and foreign keys -- adding busy_timeout follows the same pattern.

**Primary recommendation:** Build in strict order: (1) SQLite busy_timeout, (2) User + Token models + password hashing, (3) Admin bootstrap in lifespan, (4) API Bearer token auth, (5) Dashboard cookie-JWT login, (6) Role enforcement on all endpoints, (7) User management API/UI, (8) Token management API/UI.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- First admin created via env vars: `SCANNER_ADMIN_USER` and `SCANNER_ADMIN_PASSWORD`
- On startup, if no users exist in DB, create admin from env vars; if users exist, skip silently with log message
- App refuses to start if no admin env vars set and no users exist
- Admin can create additional users from both dashboard UI and API endpoints
- Opaque random tokens with `nvsec_` prefix (e.g., `nvsec_a1b2c3d4e5...`)
- Full token shown only at creation time; after that, only masked prefix displayed
- Token stored as SHA-256 hash in the database (raw token never persisted)
- Optional expiration via `expires_at` field -- non-expiring tokens allowed for CI/CD
- Soft limit of 10 active tokens per user
- Revocation supported via `revoked_at` timestamp
- Username/password login with cookie-based sessions (JWT in HttpOnly cookie)
- Session duration: 7 days before requiring re-login
- Dashboard header shows username + role badge + logout link
- Login page styled consistently with existing dashboard CSS/layout
- Navigation hides links to pages the user's role cannot access
- Direct URL access to forbidden pages shows a friendly styled 403 page
- 3 roles: admin, scanner, viewer (admin=full, viewer=read-only, scanner=API scan trigger only)
- Unauthenticated API requests return 401
- Clean break: remove legacy X-API-Key header support entirely
- Remove `SCANNER_API_KEY` env var (Claude's discretion on whether to repurpose or remove)
- API uses `Authorization: Bearer <token>` header
- Dashboard uses separate cookie-based sessions (not Bearer tokens)
- Both paths resolve to the same User model via unified `get_current_user()` dependency
- Add `PRAGMA busy_timeout=5000` to `db/session.py` as the first change

### Claude's Discretion
- Whether to remove `SCANNER_API_KEY` env var entirely or repurpose it as a secondary bootstrap mechanism
- Exact JWT cookie implementation details (signing algorithm, cookie name)
- Database migration approach (Alembic vs lightweight inline migrations)
- User CRUD API endpoint design (URL structure, request/response schemas)
- Password complexity requirements (if any)
- Exact 403 page design and wording

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| AUTH-01 | Admin can create user accounts with username and password | User model with pwdlib[bcrypt] hashing; POST /api/users endpoint; dashboard user management page |
| AUTH-02 | User can log in to dashboard with username and password | Login form rewrite (username+password fields); JWT in HttpOnly cookie; 7-day session duration |
| AUTH-03 | User can generate and revoke personal API tokens for CI/CD | APIToken model with SHA-256 hash storage; nvsec_ prefix; POST/DELETE /api/tokens endpoints; dashboard token page |
| AUTH-04 | Admin role has full access to all endpoints and dashboard pages | Role enum with admin/scanner/viewer; `require_role(Role.ADMIN)` dependency on admin-only endpoints |
| AUTH-05 | Viewer role can view scan results and reports but cannot trigger scans or change settings | Viewer allowed on GET scan/finding/report endpoints; blocked on POST /api/scans, config changes; dashboard hides action buttons |
| AUTH-06 | Scanner role can trigger scans and view results via API only (no dashboard config access) | Scanner role allowed on POST /api/scans and GET scan endpoints; no dashboard config page access |
| AUTH-07 | Unauthenticated requests to API return 401 | Unified `get_current_user()` dependency raises HTTPException(401) when no valid auth found |
| INFRA-03 | SQLite busy_timeout configured to prevent write contention | Add `PRAGMA busy_timeout=5000` to `_set_sqlite_pragmas` in `db/session.py` |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyJWT | 2.12.1 | JWT creation/verification for dashboard sessions | FastAPI official docs recommend PyJWT over abandoned python-jose; HS256 sufficient for single-instance local auth |
| pwdlib[bcrypt] | 0.3.0 | Password hashing for user accounts | FastAPI docs replaced passlib with pwdlib; bcrypt avoids C extension complexity of argon2 |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| secrets (stdlib) | N/A | Generate cryptographically secure random tokens | Token generation (`secrets.token_hex(32)`) for nvsec_ prefixed API tokens |
| hashlib (stdlib) | N/A | SHA-256 hashing of API tokens for storage | Hash tokens before DB storage; hash incoming tokens for lookup |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| PyJWT | python-jose | python-jose abandoned ~3 years; FastAPI switched away |
| pwdlib[bcrypt] | passlib | passlib deprecated, breaks on Python 3.13+ (crypt module removed) |
| pwdlib[bcrypt] | pwdlib[argon2] | Argon2 technically superior but requires argon2-cffi C extension build |
| Custom RBAC | FastAPI-Users | FastAPI-Users is a full user management framework -- overkill for 3 fixed roles |

**Installation:**
```toml
# pyproject.toml -- add to dependencies list
"PyJWT>=2.12.1",
"pwdlib[bcrypt]>=0.3.0",
```

**Version verification:**
- PyJWT: 2.12.1 (latest on PyPI, confirmed 2026-03-22)
- pwdlib: 0.3.0 (latest on PyPI, confirmed 2026-03-22)

## Architecture Patterns

### Recommended Project Structure
```
src/scanner/
  models/
    user.py              # NEW: User + APIToken ORM models
  schemas/
    auth.py              # NEW: LoginRequest, TokenCreate, TokenResponse, UserCreate, UserResponse Pydantic schemas
  api/
    auth.py              # REWRITE: get_current_user(), require_role() dependencies
    users.py             # NEW: User CRUD endpoints (admin only)
    tokens.py            # NEW: Token CRUD endpoints (per user)
  dashboard/
    auth.py              # REWRITE: JWT cookie login/verify, role-aware guards
    router.py            # MODIFY: Add user/token management pages, role-aware nav
    templates/
      login.html.j2      # REWRITE: Username + password form (was API key only)
      base.html.j2        # MODIFY: Add username/role badge to navbar, role-gated nav links
      403.html.j2         # NEW: Friendly forbidden page explaining required role
      users.html.j2       # NEW: Admin user management page
      tokens.html.j2      # NEW: Personal token management page
  db/
    session.py            # MODIFY: Add PRAGMA busy_timeout=5000
  config.py              # MODIFY: Add SCANNER_ADMIN_USER, SCANNER_ADMIN_PASSWORD env vars; remove SCANNER_API_KEY
  main.py                # MODIFY: Admin bootstrap in lifespan; create users/tokens tables
```

### Pattern 1: Unified Auth Dependency
**What:** A single `get_current_user()` FastAPI dependency that handles both API Bearer tokens and dashboard JWT cookies, returning the same User model.
**When to use:** Every protected endpoint (API and dashboard).
**Example:**
```python
# src/scanner/api/auth.py
from enum import Enum
from fastapi import Depends, HTTPException, Request
from scanner.models.user import User

class Role(str, Enum):
    ADMIN = "admin"
    SCANNER = "scanner"
    VIEWER = "viewer"

async def get_current_user(request: Request) -> User:
    """Resolve current user from Bearer token or session cookie.

    Args:
        request: FastAPI request object.

    Returns:
        Authenticated User object.

    Raises:
        HTTPException: 401 if no valid authentication found.
    """
    # 1. Check Authorization: Bearer <token> header
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        raw_token = auth_header[7:]
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        # Look up token_hash in api_tokens table
        # Check not revoked, not expired
        # Return associated user
        ...

    # 2. Check JWT session cookie
    session_cookie = request.cookies.get("scanner_session")
    if session_cookie:
        # Decode JWT, extract user_id
        # Load user from DB
        ...

    raise HTTPException(status_code=401, detail="Authentication required")

def require_role(*roles: Role):
    """Dependency factory: require one of the specified roles."""
    async def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in [r.value for r in roles]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return checker
```

### Pattern 2: Admin Bootstrap in Lifespan
**What:** Create initial admin user from env vars on first startup when no users exist.
**When to use:** App startup in `main.py` lifespan.
**Example:**
```python
# In main.py lifespan, after table creation
async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
    await conn.run_sync(_apply_schema_updates)

# Admin bootstrap
session_factory = create_session_factory(engine)
async with session_factory() as session:
    user_count = await session.scalar(select(func.count(User.id)))
    if user_count == 0:
        admin_user = settings.admin_user
        admin_pass = settings.admin_password
        if not admin_user or not admin_pass:
            raise RuntimeError(
                "No users exist and SCANNER_ADMIN_USER / SCANNER_ADMIN_PASSWORD not set. "
                "Cannot start without authentication."
            )
        hashed = PasswordHash.hash(admin_pass)
        user = User(username=admin_user, password_hash=hashed, role="admin")
        session.add(user)
        await session.commit()
        logger.info("Created initial admin user: %s", admin_user)
    else:
        logger.info("Users exist, skipping admin bootstrap")
```

### Pattern 3: Token Generation with nvsec_ Prefix
**What:** Opaque tokens with identifiable prefix, SHA-256 hash stored in DB.
**When to use:** Token creation endpoint.
**Example:**
```python
import secrets
import hashlib

def generate_api_token() -> tuple[str, str]:
    """Generate a new API token and its hash.

    Returns:
        Tuple of (raw_token, token_hash). Raw token shown once;
        token_hash stored in database.
    """
    random_part = secrets.token_hex(32)  # 64 hex chars
    raw_token = f"nvsec_{random_part}"
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    return raw_token, token_hash
```

### Pattern 4: Dashboard JWT Cookie Sessions
**What:** JWT token in HttpOnly cookie for dashboard authentication.
**When to use:** Dashboard login/verification.
**Example:**
```python
import jwt
from datetime import datetime, timedelta, timezone

SECRET_KEY = settings.secret_key  # Generate once, store in env/config
ALGORITHM = "HS256"
SESSION_DURATION = timedelta(days=7)
COOKIE_NAME = "scanner_session"

def create_session_jwt(user_id: int, role: str) -> str:
    """Create a JWT for dashboard session."""
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": datetime.now(timezone.utc) + SESSION_DURATION,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_session_jwt(token: str) -> dict | None:
    """Verify and decode a session JWT. Returns payload or None."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.InvalidTokenError:
        return None
```

### Anti-Patterns to Avoid
- **Separate auth systems for API and dashboard:** Both must resolve to the same User model. One `get_current_user()` function handles both Bearer tokens and cookies.
- **Inline role checks (`if user.role == "admin"`):** Use `Depends(require_role(Role.ADMIN))` for centralized, auditable access control.
- **Storing raw API tokens in DB:** Always store SHA-256 hash. Show raw token exactly once at creation.
- **Hardcoded JWT secret:** Generate a random secret on first startup if none provided via `SCANNER_SECRET_KEY` env var. Store it so it persists across restarts.
- **Checking roles instead of modeling permissions:** While 3 fixed roles are fine for now, implement the role check as a dependency factory (`require_role()`) so adding granularity later is a localized change.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Password hashing | Custom bcrypt wrapper | `pwdlib[bcrypt]` PasswordHash.hash() / .verify() | Timing-safe comparison, salt management, algorithm versioning handled |
| JWT encoding/decoding | Manual base64 + HMAC | `PyJWT` jwt.encode() / jwt.decode() | Claim validation, expiration checking, algorithm verification built-in |
| Token generation | uuid4 or custom random | `secrets.token_hex(32)` | Cryptographically secure randomness guaranteed by stdlib |
| Timing-safe string comparison | `==` operator | `secrets.compare_digest()` | Prevents timing attacks on token/password comparison |

**Key insight:** Authentication is a domain where subtle bugs (timing attacks, weak randomness, improper hash comparison) have severe security consequences. Use well-tested libraries for every crypto-adjacent operation.

## Common Pitfalls

### Pitfall 1: JWT Secret Key Management
**What goes wrong:** JWT secret generated at random on every app restart, invalidating all existing sessions.
**Why it happens:** Developer generates `secrets.token_hex(32)` in code without persisting it.
**How to avoid:** Accept `SCANNER_SECRET_KEY` env var. If not set, generate one on first startup and write it to a file (e.g., `/data/.secret_key`). Load from file on subsequent startups. Document that setting `SCANNER_SECRET_KEY` explicitly is recommended for production.
**Warning signs:** All dashboard users logged out after container restart.

### Pitfall 2: Token Lookup Performance
**What goes wrong:** Every API request hashes the incoming token and does a full table scan on `api_tokens`.
**Why it happens:** No index on `token_hash` column.
**How to avoid:** Add `UNIQUE` constraint on `token_hash` column (SQLAlchemy `unique=True`). This creates an implicit index. Lookup is O(1).
**Warning signs:** API response times degrade with token count.

### Pitfall 3: Admin Bootstrap Race Condition
**What goes wrong:** Multiple workers start simultaneously, each sees zero users, each tries to create admin -- one fails with unique constraint violation.
**Why it happens:** Check-then-act pattern without locking.
**How to avoid:** Wrap bootstrap in a try/except for IntegrityError. If insert fails because user already exists, that is fine -- another worker created it. Single-process uvicorn (current setup) makes this unlikely but the guard costs nothing.
**Warning signs:** Startup crash with "UNIQUE constraint failed: users.username".

### Pitfall 4: Dashboard Auth Redirect Loop
**What goes wrong:** User with expired JWT cookie hits `/dashboard/history`, gets redirected to `/dashboard/login`, login page also checks auth and redirects again.
**Why it happens:** Login page handler accidentally includes auth check.
**How to avoid:** Login page (GET `/dashboard/login` and POST `/dashboard/login`) must NOT require authentication. Explicitly exclude these routes from the auth middleware/dependency.
**Warning signs:** Browser shows "too many redirects" error.

### Pitfall 5: Role Enforcement Gaps
**What goes wrong:** New endpoints added without role checks; scanner role can access admin-only pages.
**Why it happens:** Developer forgets to add `Depends(require_role(...))` to new route.
**How to avoid:** Write a test that iterates all registered routes and verifies each has an auth dependency. Use a router-level dependency for groups of endpoints (e.g., all `/api/users/*` routes require admin).
**Warning signs:** Viewer can trigger scans; scanner can access user management.

### Pitfall 6: Forgetting to Update Existing Tests
**What goes wrong:** All phase_05 tests break because `X-API-Key` header is no longer accepted.
**Why it happens:** Clean break from legacy auth means existing test fixtures using `{"X-API-Key": "test-api-key-12345"}` stop working.
**How to avoid:** Update test conftest to create a test user and generate a Bearer token. Provide a new `api_headers` fixture that uses `{"Authorization": "Bearer nvsec_..."}`. Update all existing test files that import from phase_05 conftest.
**Warning signs:** Every pre-existing API test returns 401 or 422.

## Code Examples

### Password Hashing with pwdlib
```python
# Source: FastAPI official JWT tutorial + pwdlib PyPI docs
from pwdlib import PasswordHash

# Create hasher (bcrypt backend auto-detected from pwdlib[bcrypt] install)
password_hash = PasswordHash.default()

# Hash a password
hashed = password_hash.hash("user_password_here")
# Result: "$2b$12$..." (bcrypt format)

# Verify a password
is_valid = password_hash.verify("user_password_here", hashed)
# Returns True/False; timing-safe internally
```

### JWT Creation and Verification with PyJWT
```python
# Source: PyJWT 2.12.1 docs
import jwt
from datetime import datetime, timedelta, timezone

SECRET = "your-secret-key"

# Encode
token = jwt.encode(
    {
        "sub": "42",
        "role": "admin",
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
    },
    SECRET,
    algorithm="HS256",
)

# Decode (raises jwt.ExpiredSignatureError, jwt.InvalidTokenError on failure)
payload = jwt.decode(token, SECRET, algorithms=["HS256"])
user_id = int(payload["sub"])
role = payload["role"]
```

### SQLite Busy Timeout
```python
# In db/session.py _set_sqlite_pragmas function
def _set_sqlite_pragmas(dbapi_conn, connection_record):
    """Enable WAL mode and other SQLite optimizations on every connection."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA busy_timeout=5000")  # ADD THIS FIRST
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
```

### User and APIToken ORM Models
```python
# src/scanner/models/user.py
"""User account and API token ORM models."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from scanner.models.base import Base


class User(Base):
    """User account for authentication and authorization."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="viewer")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    tokens: Mapped[list["APIToken"]] = relationship(back_populates="user")


class APIToken(Base):
    """Personal API token for CI/CD and programmatic access."""

    __tablename__ = "api_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship(back_populates="tokens")
```

### Recommended Discretion Decisions

**SCANNER_API_KEY removal:** Remove entirely. It served as the only auth mechanism; with user-based auth, it has no purpose. Repurposing it would create confusion between "bootstrap password" and "API key". The admin bootstrap is handled cleanly by `SCANNER_ADMIN_USER` + `SCANNER_ADMIN_PASSWORD`.

**JWT signing:** HS256 with `SCANNER_SECRET_KEY` env var. If not set, auto-generate and persist to `/data/.secret_key` file. Cookie name: `scanner_session` (matches existing convention).

**Database migration:** Use lightweight inline migrations (extend existing `_apply_schema_updates` pattern in `main.py`). The project already uses this pattern for adding columns. For new tables, `Base.metadata.create_all` already handles creation. Alembic exists in deps but is unused -- adding it now would add complexity without benefit for a 2-table addition.

**User CRUD API design:**
- `POST /api/users` -- create user (admin only)
- `GET /api/users` -- list users (admin only)
- `PUT /api/users/{id}` -- update user (admin only, cannot change own role)
- `DELETE /api/users/{id}` -- deactivate user (admin only, cannot deactivate self)
- `POST /api/tokens` -- create personal token (any authenticated user)
- `GET /api/tokens` -- list own tokens (any authenticated user)
- `DELETE /api/tokens/{id}` -- revoke own token (any authenticated user)
- `GET /api/users/me` -- get current user profile (any authenticated user)

**Password complexity:** Minimum 8 characters. No other requirements -- this is a self-hosted internal tool with admin-created accounts. Overly strict rules cause more harm than good at this scale.

**403 page:** Clean card layout matching login page style. Text: "Access Denied -- You need the [role_name] role to access this page. Your current role is [user_role]. Contact your administrator for access." Include a "Go Back" link.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| python-jose for JWT | PyJWT | 2024 (FastAPI docs update) | python-jose abandoned; PyJWT is actively maintained |
| passlib for password hashing | pwdlib | 2024 (FastAPI docs update) | passlib breaks on Python 3.13+ (crypt module removed) |
| Single shared API key | Per-user tokens + RBAC | This phase | Enables multi-user access with role separation |
| X-API-Key header | Authorization: Bearer | This phase | Standard HTTP auth pattern |

**Deprecated/outdated:**
- `python-jose`: Abandoned ~3 years, FastAPI officially switched away
- `passlib`: Deprecated, breaks on Python 3.13+ due to removed `crypt` module
- Single API key auth: Replaced by per-user tokens

## Open Questions

1. **Secret key persistence in containerized environments**
   - What we know: JWT secret must persist across container restarts for session continuity
   - What's unclear: Whether `/data/` volume is always mounted in all deployment scenarios
   - Recommendation: Require `SCANNER_SECRET_KEY` env var in production docs; auto-generate fallback to `/data/.secret_key` for development

2. **Existing phase_05 test compatibility**
   - What we know: Tests use `X-API-Key: test-api-key-12345` fixtures; clean break means these will fail
   - What's unclear: Whether to update all phase_05 tests or create new phase_12 tests that supersede them
   - Recommendation: Create new phase_12 test suite; update phase_05 conftest to use new Bearer auth so existing assertions still pass

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio |
| Config file | `pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `pytest tests/phase_12/ -x -q` |
| Full suite command | `pytest tests/ -x -q` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AUTH-01 | Admin creates user account with username/password | integration | `pytest tests/phase_12/test_user_crud.py::test_admin_creates_user -x` | Wave 0 |
| AUTH-02 | User logs in to dashboard with username/password | integration | `pytest tests/phase_12/test_dashboard_login.py::test_login_with_credentials -x` | Wave 0 |
| AUTH-03 | User generates and revokes API tokens | integration | `pytest tests/phase_12/test_tokens.py::test_create_and_revoke_token -x` | Wave 0 |
| AUTH-04 | Admin has full access to all endpoints | integration | `pytest tests/phase_12/test_roles.py::test_admin_full_access -x` | Wave 0 |
| AUTH-05 | Viewer cannot trigger scans or change settings | integration | `pytest tests/phase_12/test_roles.py::test_viewer_restricted -x` | Wave 0 |
| AUTH-06 | Scanner can trigger scans via API but not access dashboard config | integration | `pytest tests/phase_12/test_roles.py::test_scanner_role_limits -x` | Wave 0 |
| AUTH-07 | Unauthenticated API requests return 401 | integration | `pytest tests/phase_12/test_auth.py::test_unauthenticated_returns_401 -x` | Wave 0 |
| INFRA-03 | SQLite busy_timeout prevents write contention | unit | `pytest tests/phase_12/test_db_pragmas.py::test_busy_timeout -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/phase_12/ -x -q`
- **Per wave merge:** `pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/phase_12/__init__.py` -- package init
- [ ] `tests/phase_12/conftest.py` -- shared fixtures (test user creation, auth_client with Bearer token, session factory)
- [ ] `tests/phase_12/test_db_pragmas.py` -- INFRA-03 busy_timeout verification
- [ ] `tests/phase_12/test_auth.py` -- AUTH-07 unauthenticated 401 + Bearer token auth flow
- [ ] `tests/phase_12/test_user_crud.py` -- AUTH-01 admin user creation
- [ ] `tests/phase_12/test_dashboard_login.py` -- AUTH-02 username/password login
- [ ] `tests/phase_12/test_tokens.py` -- AUTH-03 token generation and revocation
- [ ] `tests/phase_12/test_roles.py` -- AUTH-04, AUTH-05, AUTH-06 role enforcement
- [ ] Update `tests/phase_05/conftest.py` -- migrate test fixtures from X-API-Key to Bearer auth

## Sources

### Primary (HIGH confidence)
- PyJWT 2.12.1 on PyPI -- verified latest version 2026-03-22
- pwdlib 0.3.0 on PyPI -- verified latest version 2026-03-22
- Existing codebase: `src/scanner/api/auth.py`, `src/scanner/dashboard/auth.py`, `src/scanner/db/session.py`, `src/scanner/main.py`, `src/scanner/config.py`
- `.planning/research/STACK.md` -- PyJWT + pwdlib selection rationale
- `.planning/research/ARCHITECTURE.md` -- Unified auth dependency design
- `.planning/research/PITFALLS.md` -- Auth divergence, SQLite contention, backward compat pitfalls
- `.planning/codebase/CONVENTIONS.md` -- Two-model pattern, naming conventions, docstring style

### Secondary (MEDIUM confidence)
- FastAPI Official JWT Tutorial (https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/) -- PyJWT + pwdlib recommendation
- `.planning/research/FEATURES.md` -- Feature prioritization for RBAC

### Tertiary (LOW confidence)
- None -- all findings verified against primary sources

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- PyJWT and pwdlib versions verified against PyPI; recommended by FastAPI official docs
- Architecture: HIGH -- Patterns derived from existing codebase analysis; unified auth dependency well-documented in project research
- Pitfalls: HIGH -- Pitfalls documented in project research; confirmed against actual codebase patterns (existing test fixtures, auth code)

**Research date:** 2026-03-22
**Valid until:** 2026-04-22 (stable libraries, no fast-moving dependencies)
