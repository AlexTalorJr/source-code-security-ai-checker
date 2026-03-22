# Architecture Patterns

**Domain:** Scanner Configuration UI, Nuclei DAST Adapter, Token-based RBAC -- integration with existing FastAPI + ScannerRegistry + Orchestrator
**Researched:** 2026-03-22

## Recommended Architecture

Three features integrating into the existing layered architecture. Each touches different layers with minimal overlap, enabling parallel development after a shared RBAC foundation.

```
                    +-------------------+
                    |   Dashboard UI    |  (Jinja2 templates)
                    |  Scanner Config   |  <-- NEW pages
                    |  Role-aware nav   |  <-- MODIFIED
                    +--------+----------+
                             |
              +--------------+--------------+
              |                             |
     +--------v---------+        +---------v----------+
     |   Dashboard Auth  |        |    API Auth         |
     |  Cookie + Role    |        |  Token + Role       |
     |  (MODIFIED)       |        |  (MODIFIED)         |
     +--------+----------+        +---------+-----------+
              |                             |
     +--------v-----------------------------v----------+
     |              FastAPI Router                      |
     |  /api/config/*     <-- NEW endpoints             |
     |  /api/scanners/*   <-- MODIFIED                  |
     |  /scans/*          <-- EXISTING (add role check) |
     +--------+-----------------------------------------+
              |
     +--------v-----------------------------------------+
     |              ScannerSettings / Config             |
     |  config.yml + runtime overrides                  |
     |  ScannerToolConfig <-- EXISTING (no change)      |
     |  Scan Profiles     <-- NEW concept               |
     +--------+-----------------------------------------+
              |
     +--------v-----------------------------------------+
     |              ScannerRegistry                     |
     |  get_enabled_adapters()  <-- EXISTING            |
     |  update_scanner()        <-- NEW method          |
     +--------+-----------------------------------------+
              |
     +--------v-----------------------------------------+
     |              Orchestrator                        |
     |  run_scan() <-- EXISTING (add profile support)   |
     +--------+-----------------------------------------+
              |
     +--------v-----------------------------------------+
     |              Scanner Adapters                    |
     |  BanditAdapter, SemgrepAdapter, ...              |
     |  NucleiAdapter   <-- NEW adapter                 |
     +--------------------------------------------------+
```

### Component Boundaries

| Component | Responsibility | Communicates With | Status |
|-----------|---------------|-------------------|--------|
| `src/scanner/adapters/nuclei.py` | Run Nuclei CLI, parse JSONL output, normalize to FindingSchema | ScannerAdapter base, Orchestrator | **NEW** |
| `src/scanner/api/config.py` | REST endpoints: read/write scanner config, manage profiles | ScannerSettings, ScannerRegistry, ConfigService | **NEW** |
| `src/scanner/core/config_service.py` | Business logic for config CRUD -- read/write config.yml, validate, reload | ScannerSettings, filesystem (config.yml) | **NEW** |
| `src/scanner/core/profiles.py` | Scan profile management (named sets of scanner configs) | ConfigService, SQLite | **NEW** |
| `src/scanner/models/user.py` | User + Token ORM models (username, hashed password, role, API tokens) | SQLAlchemy Base | **NEW** |
| `src/scanner/models/profile.py` | ScanProfile ORM model | SQLAlchemy Base | **NEW** |
| `src/scanner/api/auth.py` | Token validation, role-based dependency injection | User model, settings | **MODIFIED** |
| `src/scanner/dashboard/auth.py` | Cookie session with role awareness | User model | **MODIFIED** |
| `src/scanner/dashboard/router.py` | Add scanner config pages, role-gated actions | ConfigService, templates | **MODIFIED** |
| `src/scanner/dashboard/templates/config.html.j2` | Scanner list with enable/disable toggles, settings forms | Dashboard router | **NEW** |
| `src/scanner/dashboard/templates/config_editor.html.j2` | Raw YAML config editor | Dashboard router | **NEW** |
| `src/scanner/dashboard/templates/profiles.html.j2` | Scan profiles management | Dashboard router | **NEW** |
| `src/scanner/main.py` | Add new routers, schema migrations for users/tokens/profiles | All routers | **MODIFIED** |
| `src/scanner/config.py` | No structural changes needed -- ScannerToolConfig already sufficient | N/A | **UNCHANGED** |
| `src/scanner/adapters/registry.py` | Add `update_scanner()` for runtime config changes | ScannerToolConfig | **MODIFIED** |
| `src/scanner/core/orchestrator.py` | Accept optional profile override for scanner selection | ScannerRegistry, profiles | **MODIFIED** |

### Data Flow

#### Feature 1: Scanner Configuration UI

```
Dashboard form submit
  --> POST /dashboard/config/scanners/{name}
  --> ConfigService.update_scanner(name, enabled, timeout, extra_args)
  --> Writes to config.yml (YAML round-trip)
  --> Next scan picks up changed config via ScannerSettings()
```

Key insight: `ScannerSettings` is re-instantiated per scan in `run_scan()` (line 166 of orchestrator.py creates `ScannerRegistry(settings.scanners)`). Config changes to `config.yml` take effect on the next scan without server restart. The `ScannerRegistry` is not a singleton -- it is created fresh each time.

#### Feature 2: Nuclei DAST Adapter

```
config.yml adds nuclei entry
  --> ScannerRegistry loads NucleiAdapter via importlib
  --> Orchestrator calls adapter.run(target_path, timeout, extra_args)
  --> NucleiAdapter runs: nuclei -u <target_url> -jsonl -t <templates>
  --> Parses JSONL output line-by-line
  --> Returns list[FindingSchema] with tool="nuclei"
```

DAST difference: Nuclei needs a URL target, not a filesystem path. The `run()` method receives `target_path` which is a local directory. For DAST, we need `target_url` passed differently. Options:
1. Use `extra_args` to pass `-u <url>` (works with existing interface, no base class changes)
2. Add optional `target_url` to `ScanRequest` and thread it through orchestrator

Recommendation: Use `extra_args` for v1.0.2. The adapter checks if target looks like a URL or extracts `-u` from extra_args. This avoids modifying the ScannerAdapter base class contract. The Nuclei adapter's `run()` simply ignores `target_path` when a URL is provided via extra_args or scan request parameters.

#### Feature 3: Token-based RBAC

```
Admin creates user via CLI or API
  --> User stored in SQLite (username, bcrypt hash, role)
  --> User generates API tokens via dashboard
  --> Token stored: sha256(token) in DB, raw token shown once

API request with X-API-Key header
  --> require_api_key() looks up token hash in DB
  --> Returns (user, role) tuple
  --> Endpoint checks role via Depends(require_role("admin"))

Dashboard login with username/password
  --> Validates bcrypt hash
  --> Sets session cookie with user_id + role
  --> require_dashboard_auth() checks cookie + loads role
  --> Templates conditionally render admin-only actions
```

## Patterns to Follow

### Pattern 1: Adapter Registration (existing, extend for Nuclei)

The Nuclei adapter follows the exact same pattern as Bandit, gosec, etc. Add entry to config.yml, implement the adapter class.

**What:** Config-driven adapter loading via importlib
**When:** Adding any new scanner
**Example:**

```yaml
# config.yml addition
nuclei:
  adapter_class: "scanner.adapters.nuclei.NucleiAdapter"
  enabled: "auto"
  timeout: 300
  extra_args: ["-t", "cves/", "-t", "vulnerabilities/"]
  languages: []  # DAST is language-agnostic
```

```python
# src/scanner/adapters/nuclei.py
class NucleiAdapter(ScannerAdapter):
    @property
    def tool_name(self) -> str:
        return "nuclei"

    def _version_command(self) -> list[str]:
        return ["nuclei", "-version"]

    async def run(self, target_path, timeout, extra_args=None):
        # Build nuclei command with JSONL output
        cmd = ["nuclei", "-jsonl", "-silent"]
        if extra_args:
            cmd.extend(extra_args)
        # If no -u in extra_args, skip (DAST needs explicit target)
        if not any(a == "-u" for a in (extra_args or [])):
            return []  # No URL target, skip silently
        stdout, stderr, rc = await self._execute(cmd, timeout)
        return self._parse_jsonl(stdout, target_path)
```

### Pattern 2: Role-gated FastAPI Dependencies

**What:** Layered dependency injection for auth + role checking
**When:** Protecting API endpoints with role requirements

```python
# src/scanner/api/auth.py (evolved)
from enum import Enum

class Role(str, Enum):
    ADMIN = "admin"
    SCANNER = "scanner"  # CI/CD -- can trigger scans, read results
    VIEWER = "viewer"    # Read-only dashboard access

async def require_auth(request: Request, x_api_key: str = Header(...)):
    """Returns (user, role) or raises 401."""
    # Check legacy single API key first (backward compat)
    # Then check token table
    ...

def require_role(*roles: Role):
    """Dependency factory: require one of the specified roles."""
    async def checker(auth_result = Depends(require_auth)):
        user, role = auth_result
        if role not in roles:
            raise HTTPException(403, "Insufficient permissions")
        return auth_result
    return checker
```

### Pattern 3: Config Service with YAML Round-Trip

**What:** Service layer between API/dashboard and config.yml file
**When:** Reading or writing scanner configuration

```python
# src/scanner/core/config_service.py
import yaml
from pathlib import Path

class ConfigService:
    def __init__(self, config_path: str = "config.yml"):
        self.config_path = Path(config_path)

    def read_config(self) -> dict:
        """Read current config.yml as dict."""
        return yaml.safe_load(self.config_path.read_text())

    def update_scanner(self, name: str, updates: dict) -> None:
        """Update a single scanner's config and write back."""
        config = self.read_config()
        if name not in config.get("scanners", {}):
            raise ValueError(f"Unknown scanner: {name}")
        config["scanners"][name].update(updates)
        self.config_path.write_text(yaml.dump(config, default_flow_style=False))

    def write_full_config(self, raw_yaml: str) -> None:
        """Validate and write raw YAML (for config editor)."""
        parsed = yaml.safe_load(raw_yaml)  # Validates syntax
        # Additional validation: ensure scanners have adapter_class
        self.config_path.write_text(raw_yaml)
```

### Pattern 4: Backward-Compatible Auth Migration

**What:** Support both legacy single API key and new token-based auth during migration
**When:** Evolving auth without breaking existing CI/CD integrations

The current system uses a single `api_key` in settings. New RBAC must not break existing Jenkins integrations that pass `X-API-Key: <value>`.

```python
async def require_auth(request, x_api_key):
    # 1. Check if it matches legacy settings.api_key (admin role)
    if settings.api_key and compare_digest(x_api_key, settings.api_key):
        return LegacyUser(role=Role.ADMIN)

    # 2. Check token table
    token_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
    user = await lookup_token(token_hash)
    if user:
        return user

    raise HTTPException(401)
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Modifying ScannerAdapter Base Class for DAST

**What:** Adding `target_url` parameter to the abstract `run()` method
**Why bad:** Breaks all 12 existing adapters. Every adapter must be updated even though only Nuclei uses URLs.
**Instead:** Pass DAST target URL via `extra_args` (e.g., `["-u", "https://target.com"]`). The Nuclei adapter extracts it from extra_args. Alternatively, add an optional `scan_context: dict` parameter with a default of `None` -- but extra_args is simpler for v1.0.2.

### Anti-Pattern 2: In-Memory Config State

**What:** Storing config changes in app.state and losing them on restart
**Why bad:** Config changes vanish after container restart. Users expect persistence.
**Instead:** Always write through to config.yml. The existing `ScannerSettings` YAML loading already handles reading it back. Config.yml is the source of truth.

### Anti-Pattern 3: Inline Role Checks

**What:** Checking `if user.role == "admin"` inside every route handler
**Why bad:** Scattered auth logic, easy to forget, hard to audit
**Instead:** Use FastAPI dependency injection: `Depends(require_role(Role.ADMIN))`. One line per endpoint, centralized logic, easy to grep for coverage.

### Anti-Pattern 4: Storing Raw Tokens

**What:** Storing API tokens as plaintext in SQLite
**Why bad:** Database leak exposes all tokens
**Instead:** Store `sha256(token)` in the database. Show the raw token exactly once at creation time. On each request, hash the incoming token and compare hashes.

### Anti-Pattern 5: Separate Auth Systems

**What:** Building completely separate auth for dashboard vs API
**Why bad:** Two codepaths to maintain, inconsistent behavior, double the bugs
**Instead:** Shared User model and role logic. Dashboard uses cookie sessions (stores user_id). API uses bearer tokens. Both resolve to the same User+Role. The `require_auth` function handles both paths.

## Integration Points: Detailed Analysis

### What Changes in Existing Code

| File | Change Type | Details |
|------|-------------|---------|
| `src/scanner/api/auth.py` | **Major rewrite** | From single-key comparison to token lookup + role resolution. Must keep backward compat with legacy `api_key` setting. |
| `src/scanner/api/router.py` | **Minor addition** | Include new config router: `api_router.include_router(config_router)` |
| `src/scanner/api/scans.py` | **Minor modification** | Replace `Depends(require_api_key)` with `Depends(require_role(Role.SCANNER))` |
| `src/scanner/api/scanners.py` | **Minor modification** | Add role check, add detail/update endpoints |
| `src/scanner/dashboard/auth.py` | **Moderate rewrite** | From API key hash cookie to user session with role |
| `src/scanner/dashboard/router.py` | **Moderate addition** | Add config pages, pass role to templates, gate admin actions |
| `src/scanner/dashboard/templates/base.html.j2` | **Minor modification** | Add nav items for config pages, conditionally show admin links |
| `src/scanner/main.py` | **Minor modification** | Schema migrations for new tables (users, tokens, profiles) |
| `config.yml` | **Addition** | Add nuclei scanner entry |
| `Dockerfile` | **Addition** | Install nuclei binary |

### What Stays Unchanged

| File | Why |
|------|-----|
| `src/scanner/adapters/base.py` | Base class contract is sufficient -- no changes needed |
| `src/scanner/config.py` | `ScannerToolConfig` already has all fields Nuclei needs |
| `src/scanner/core/orchestrator.py` | Nuclei fits existing parallel execution model (minor profile support later) |
| `src/scanner/schemas/finding.py` | `FindingSchema` handles Nuclei output as-is |
| `src/scanner/db/session.py` | SQLite engine setup unchanged |
| All existing adapters | No interface changes |

## New Database Tables

```sql
-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(200) NOT NULL,  -- bcrypt
    role VARCHAR(20) NOT NULL DEFAULT 'viewer',  -- admin, scanner, viewer
    created_at DATETIME DEFAULT (datetime('now')),
    is_active BOOLEAN NOT NULL DEFAULT 1
);

-- API tokens table (multiple per user)
CREATE TABLE api_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    token_hash VARCHAR(64) NOT NULL UNIQUE,  -- sha256 hex
    label VARCHAR(100),  -- e.g., "jenkins-prod", "local-dev"
    created_at DATETIME DEFAULT (datetime('now')),
    last_used_at DATETIME,
    is_active BOOLEAN NOT NULL DEFAULT 1
);

-- Scan profiles table
CREATE TABLE scan_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    scanner_overrides TEXT NOT NULL,  -- JSON: {"semgrep": {"enabled": true}, ...}
    created_by INTEGER REFERENCES users(id),
    created_at DATETIME DEFAULT (datetime('now'))
);
```

## Build Order (dependency-driven)

The three features have a dependency chain:

```
1. RBAC (foundation) -- other features need auth/roles to gate access
   |
   +---> 2a. Scanner Config UI (needs admin role gate)
   |
   +---> 2b. Nuclei Adapter (independent, but config UI shows it)
```

**Recommended build order:**

1. **RBAC: User model + token auth** -- New tables, auth rewrite, backward compat with legacy API key. Everything else depends on role-based access.

2. **Nuclei DAST Adapter** -- Purely additive, follows existing adapter pattern exactly. Can be built in parallel with step 3 since it only touches new files + config.yml.

3. **Scanner Configuration UI** -- Depends on RBAC (admin-only access). Depends on ScannerRegistry existing (already does). Benefits from Nuclei being registered (shows 13 scanners in UI).

4. **Scan Profiles** -- Nice-to-have built on top of Config UI. Depends on config service and RBAC.

## Scalability Considerations

| Concern | Current (v1.0.1) | After v1.0.2 |
|---------|-------------------|--------------|
| Auth overhead | Single string compare per request | Token hash lookup in SQLite -- negligible for single-user/small-team use |
| Config writes | Manual config.yml editing | ConfigService writes YAML -- file lock needed for concurrent writes |
| Nuclei scan time | N/A | Nuclei template scans can be slow (5-10min for full template set). Use timeout + template subset via extra_args |
| User count | Single shared API key | Dozens of users max (self-hosted tool). SQLite handles this fine |
| Token table size | N/A | Hundreds of tokens max. SHA-256 index lookup is O(1) |

## Sources

- Codebase analysis: `src/scanner/` directory (all files read directly)
- Existing architecture established in v1.0 through v1.0.1
- Nuclei DAST decision documented in PROJECT.md key decisions (confirmed v2.0 research)
- FastAPI dependency injection: established pattern in existing `auth.py`
- SQLite for auth: consistent with project constraint (SQLite only, no external DB)
