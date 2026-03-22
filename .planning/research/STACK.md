# Technology Stack

**Project:** Security AI Scanner v1.0.2 -- Scanner UI, DAST & RBAC
**Researched:** 2026-03-22

## Existing Stack (NO CHANGES)

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.12 | Runtime |
| FastAPI | latest (via `fastapi[standard]`) | REST API + dashboard |
| Jinja2 | >=3.1.6 | Server-rendered HTML templates |
| SQLAlchemy | >=2.0 | ORM |
| aiosqlite | latest | Async SQLite driver |
| Alembic | latest | DB migrations |
| Pydantic Settings | latest (via `pydantic-settings[yaml]`) | Config with YAML + env vars |
| 12 scanner adapters | various | SAST/SCA via config-driven ScannerRegistry |

## Recommended Stack Additions

### Auth & RBAC

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| PyJWT | >=2.12.1 | JWT token creation and verification | FastAPI official docs now recommend PyJWT over abandoned python-jose. Lightweight, actively maintained, focused API. HS256 is sufficient for single-instance local auth -- no RSA/ECDSA overhead needed. |
| pwdlib[bcrypt] | >=0.3.0 | Password hashing | Replaces abandoned passlib (which breaks on Python 3.13+). FastAPI docs updated to pwdlib. bcrypt extra chosen over argon2 because bcrypt requires no extra system C libraries and is proven sufficient for admin-created accounts at this scale. |

**Why NOT python-jose:** Abandoned (~3 years since last release). FastAPI docs officially switched to PyJWT.

**Why NOT passlib:** Deprecated, throws warnings on Python 3.12+. The `crypt` module it depends on was removed in Python 3.13. FastAPI docs switched to pwdlib.

**Why NOT argon2 (via pwdlib[argon2]):** Argon2 is technically superior but requires the `argon2-cffi` C extension build. For a self-hosted Docker tool with admin-created accounts (no self-registration), bcrypt is more than sufficient and avoids build complexity.

### DAST -- Nuclei Integration

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Nuclei (CLI binary) | v3.5.x | DAST vulnerability scanner | Already decided in v2.0 research. CLI-friendly, template-based, ~30MB binary vs ZAP 500MB+. 8000+ community templates. JSONL output parses cleanly line-by-line. |

**No Python wrapper library needed.** Nuclei is invoked via `asyncio.create_subprocess_exec()` -- the exact same pattern used by all 12 existing adapters via the `ScannerAdapter._execute()` method. Do NOT add PyNuclei (unofficial, poorly maintained wrapper that adds indirection with no value).

**Docker integration:** Download pre-built Nuclei binary from GitHub releases in Dockerfile. Do NOT use `go install` -- avoids adding Go toolchain to the image.

**Key CLI flags for the adapter:**
- `-jsonl` -- machine-readable output, one JSON object per finding per line
- `-silent` -- suppress banner/progress noise
- `-severity` -- filter by severity level
- `-tags` -- filter templates by category
- `-t` -- specify template paths (custom or built-in)
- `-u` / `-target` -- single target URL

### Scanner Configuration UI

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| CodeMirror 5 (CDN) | 5.65.x | YAML config editor in browser | Server-rendered Jinja2 app has no build step. CodeMirror 5 loads from CDN (`cdnjs.cloudflare.com`), has native YAML mode, and works with a plain `<textarea>`. CodeMirror 6 requires a bundler -- over-engineering for this stack. |

**No npm/webpack/build step.** The existing dashboard is pure Jinja2 templates + CDN assets. Adding a JavaScript build pipeline for one editor widget is not justified. CodeMirror 5 via CDN keeps the stack consistent.

**No frontend framework needed.** Scanner config UI (toggle switches, settings forms, profile selector) is standard HTML forms rendered by Jinja2. Alpine.js or htmx would add dependency for minimal gain -- vanilla JS with `fetch()` for AJAX updates is sufficient for the 4-5 interactive elements needed.

### Database Schema Additions

No new dependencies needed. New tables use the existing SQLAlchemy + Alembic + aiosqlite stack.

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `users` | Auth accounts | id, username, password_hash, role, created_at, is_active |
| `api_tokens` | Bearer tokens for CI/CD | id, user_id, token_hash, name, role, created_at, expires_at, last_used_at |
| `scan_profiles` | Named scanner configurations | id, name, description, scanner_config (JSON blob), created_by, created_at |

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| JWT library | PyJWT | python-jose | Abandoned, FastAPI docs switched away |
| Password hashing | pwdlib[bcrypt] | passlib | Deprecated, breaks on Python 3.13+ |
| Password hashing | pwdlib[bcrypt] | bcrypt (direct) | pwdlib provides cleaner hash/verify API wrapping the same underlying bcrypt library |
| DAST scanner | Nuclei CLI | ZAP | 500MB+ image, complex config, decided in v2.0 research |
| DAST Python wrapper | subprocess (existing pattern) | PyNuclei | Unofficial, poorly maintained, unnecessary abstraction |
| Config editor | CodeMirror 5 (CDN) | CodeMirror 6 | Requires bundler/build step, no CDN distribution |
| Config editor | CodeMirror 5 (CDN) | Monaco Editor | 5MB+ JS payload, massive overkill for YAML editing |
| Config editor | CodeMirror 5 (CDN) | Plain textarea | No syntax highlighting, poor UX for YAML |
| Frontend | None (vanilla JS) | Alpine.js / htmx | Adds dependency for ~5 interactive elements |
| Auth framework | Simple local JWT | FastAPI-Users | Full user management framework -- too heavy for 3 fixed roles with admin-only account creation |
| Auth protocol | Local JWT | OAuth2/OIDC/LDAP | Explicitly out of scope per PROJECT.md: "simple local auth only for v1.0.2" |
| Session store | SQLite api_tokens table | Redis | No need for external store. JWT is stateless; token revocation via DB check on api_tokens is sufficient at this scale |

## What NOT to Add

These were explicitly evaluated and rejected:

1. **No frontend build pipeline** -- No npm, webpack, vite. Stays pure Jinja2 + CDN.
2. **No PyNuclei** -- Subprocess pattern already proven across 12 adapters.
3. **No OAuth/SSO/LDAP** -- Explicitly out of scope per PROJECT.md.
4. **No user self-registration** -- Admin creates accounts, per PROJECT.md.
5. **No FastAPI-Users** -- Overkill for 3 fixed roles (admin, viewer, scanner).
6. **No Redis/session store** -- JWT tokens are stateless. DB-based token revocation is sufficient.
7. **No argon2** -- bcrypt is sufficient for this use case. Avoids C extension complexity.

## Installation

```toml
# pyproject.toml -- add to dependencies list
"PyJWT>=2.12.1",
"pwdlib[bcrypt]>=0.3.0",
```

```bash
# Install new Python deps
pip install PyJWT>=2.12.1 "pwdlib[bcrypt]>=0.3.0"
```

```dockerfile
# Dockerfile addition for Nuclei binary
ARG NUCLEI_VERSION=3.5.0
RUN curl -sSL "https://github.com/projectdiscovery/nuclei/releases/download/v${NUCLEI_VERSION}/nuclei_${NUCLEI_VERSION}_linux_amd64.zip" \
    -o /tmp/nuclei.zip && \
    unzip /tmp/nuclei.zip -d /usr/local/bin/ && \
    rm /tmp/nuclei.zip && \
    chmod +x /usr/local/bin/nuclei
# Templates downloaded at first run or via: nuclei -update-templates
```

```html
<!-- CDN includes for CodeMirror 5 YAML editor (add to config editor Jinja2 template) -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.18/codemirror.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.18/codemirror.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.18/mode/yaml/yaml.min.js"></script>
```

## Integration Points with Existing Stack

### Auth Migration Path

Current auth: single shared `api_key` in config.yml, checked via `X-API-Key` header (API) and SHA-256 cookie (dashboard). New system replaces this:

- **API routes:** Bearer JWT tokens with role claim. `require_api_key()` dependency in `src/scanner/api/auth.py` evolves to `require_token(roles=[...])` using FastAPI's `Depends()`.
- **Dashboard:** Cookie-based JWT session. `require_dashboard_auth()` in `src/scanner/dashboard/auth.py` evolves to check JWT cookie with role verification.
- **Backward compatibility:** Keep `X-API-Key` header support during migration, mapping it to admin role. Allows existing Jenkins integrations to keep working while migrating to tokens.

### Nuclei Adapter Pattern

Follows the exact same pattern as all 12 existing adapters:
1. Create `NucleiAdapter(ScannerAdapter)` in `src/scanner/adapters/nuclei.py`
2. Add config entry in `config.yml` under `scanners.nuclei` with `adapter_class: "scanner.adapters.nuclei.NucleiAdapter"`
3. `ScannerRegistry` auto-discovers via importlib
4. Runs via `self._execute()` with `-jsonl -silent` flags
5. Parses JSONL output into `FindingSchema` list

**Key difference from SAST adapters:** Nuclei targets a URL, not a file path. The adapter's `run()` method will use `target_url` (from scan request) instead of `target_path`. The orchestrator needs minor extension to pass target URL for DAST-type scans.

### Scanner Config UI API

The existing `/api/scanners` GET endpoint (in `src/scanner/api/scanners.py`) returns scanner list from `ScannerRegistry.all_scanners_info()`. New endpoints extend this:
- `PUT /api/scanners/{name}` -- update scanner settings (enabled, timeout, extra_args)
- `GET /api/scan-profiles` -- list saved profiles
- `POST /api/scan-profiles` -- create profile
- `PUT /api/scan-profiles/{id}` -- update profile
- `DELETE /api/scan-profiles/{id}` -- delete profile

Config changes persist to `config.yml` (runtime updates) or to `scan_profiles` table (named profiles). The existing `ScannerSettings` Pydantic model reloads from file.

Dashboard pages render forms via Jinja2 templates in `src/scanner/dashboard/templates/`, submit via `fetch()` to API endpoints.

## Sources

- [FastAPI Official JWT Tutorial](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/) -- PyJWT + pwdlib recommendation (HIGH confidence)
- [FastAPI Discussion #11345: Abandon python-jose](https://github.com/fastapi/fastapi/discussions/11345) -- python-jose deprecation (HIGH confidence)
- [FastAPI Discussion #11773: passlib replacement](https://github.com/fastapi/fastapi/discussions/11773) -- pwdlib adoption (HIGH confidence)
- [pwdlib on PyPI](https://pypi.org/project/pwdlib/) -- v0.3.0, Oct 2025 (HIGH confidence)
- [PyJWT on PyPI](https://pypi.org/project/PyJWT/) -- v2.12.1, Mar 2026 (HIGH confidence)
- [Nuclei GitHub](https://github.com/projectdiscovery/nuclei) -- v3.5.x (HIGH confidence)
- [Nuclei Running Docs](https://docs.projectdiscovery.io/opensource/nuclei/running) -- CLI flags reference (HIGH confidence)
- [Nuclei Docker Hub](https://hub.docker.com/r/projectdiscovery/nuclei) -- Docker image info (HIGH confidence)
- [CodeMirror 5 YAML mode](https://codemirror.net/5/mode/yaml/) -- CDN-compatible YAML editor (HIGH confidence)
- [PROJECT.md constraints](../PROJECT.md) -- Scope boundaries and existing decisions (HIGH confidence)
