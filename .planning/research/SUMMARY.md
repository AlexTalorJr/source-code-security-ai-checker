# Project Research Summary

**Project:** Security AI Scanner v1.0.2 — Scanner Config UI, Nuclei DAST, RBAC
**Domain:** Self-hosted security scanning platform (SAST/SCA/DAST) with role-based access
**Researched:** 2026-03-22
**Confidence:** HIGH

## Executive Summary

This milestone extends an already-functional v1.0.1 scanning platform (FastAPI + Jinja2 + SQLAlchemy + 12 adapters) with three cohesive capabilities: a scanner configuration UI, a Nuclei DAST adapter, and token-based RBAC. All three build on the existing, well-understood architecture rather than introducing new paradigms. The stack additions are minimal and deliberately conservative: PyJWT + pwdlib[bcrypt] for auth (the current FastAPI-recommended replacements for abandoned python-jose and passlib), Nuclei CLI binary via subprocess (the same pattern as the 12 existing adapters), and CodeMirror 5 via CDN for the YAML editor (no build step, consistent with the Jinja2-only frontend). No frontend build pipeline, no new database engine, no external services.

The recommended implementation order is RBAC first, then Nuclei adapter and Scanner Config UI in parallel, then scan profiles. RBAC is a hard dependency because the Scanner Config UI must be admin-gated before any write endpoints are exposed. The Nuclei adapter is independent: it only touches new files and config.yml and can be built without waiting for UI work. The most important architectural constraint is that config.yml must remain the single source of truth for scanner settings — storing them in SQLite instead would silently decouple the UI from actual scan behavior. A critical insight from codebase analysis is that `ScannerSettings` is re-instantiated per scan (the orchestrator creates `ScannerRegistry` fresh on each `run_scan()` call), so config changes written to config.yml by the UI take effect on the next scan without any reload mechanism.

The principal risks are all architectural decisions that become expensive to reverse: using the wrong config persistence model (HIGH recovery cost), breaking backward compatibility in the auth migration (HIGH recovery cost), and force-fitting Nuclei into the SAST adapter interface (HIGH recovery cost). All three are well-understood and preventable if the correct design is chosen upfront. SQLite write contention is a one-line fix (`busy_timeout` pragma) that should be the first commit of the milestone — it prevents visible user-facing errors and costs nothing to address early.

## Key Findings

### Recommended Stack

The existing stack requires only two new Python dependencies. PyJWT (>=2.12.1) handles JWT token creation and verification; it is the current FastAPI-recommended library after python-jose was abandoned (~3 years without a release). pwdlib[bcrypt] (>=0.3.0) handles password hashing as the successor to deprecated passlib, which throws warnings on Python 3.12+ and breaks on 3.13+. The bcrypt variant is preferred over argon2 because it requires no C build extensions — appropriate for a self-hosted Docker tool with admin-managed accounts and no self-registration. Nuclei v3.5.x is downloaded as a pre-built binary in the Dockerfile (single `curl` + `unzip`), avoiding any Go toolchain dependency in the image. CodeMirror 5 is loaded from CDN with no npm or build step.

**Core technologies:**
- PyJWT >=2.12.1: JWT token creation/verification — FastAPI's current official recommendation, actively maintained
- pwdlib[bcrypt] >=0.3.0: password hashing — replaces deprecated passlib, no C extensions needed
- Nuclei CLI v3.5.x: DAST scanning — 30MB binary, 12000+ templates, JSONL output, subprocess pattern
- CodeMirror 5 (CDN): YAML config editor — no build step, native YAML mode, works with plain textarea
- SQLAlchemy + Alembic (existing): three new tables (users, api_tokens, scan_profiles) via migration

### Expected Features

**Must have (v1.0.2 table stakes):**
- RBAC: users table, 3 roles (admin/scanner/viewer), bcrypt password hashing — foundation for all other features
- RBAC: multiple API tokens per user, replacing the single shared api_key — each CI pipeline gets its own token
- RBAC: endpoint authorization via FastAPI `Depends` injection — one line per endpoint, centralized logic
- RBAC: dashboard login with username/password user accounts — replaces single-key dashboard login
- Nuclei DAST adapter: registered in config.yml, runs against target URLs, parses JSONL findings
- target_url field on ScanRequest: DAST scans as first-class citizens, not a hack on target_path
- Scanner Config UI: enable/disable toggles + settings display per scanner — core value of the feature
- Scanner Config UI: config persistence across restarts — config.yml as the single source of truth

**Should have (add after v1.0.2 validation):**
- Scan profiles: named scanner configuration presets (cap at 5-7; store profile name in scan result for reproducibility)
- Admin UI for user/token management via dashboard — once RBAC is proven via API
- Token expiration dates (`expires_at` field) with enforcement
- Audit log for auth events
- Raw YAML config editor with CodeMirror 5

**Defer (v2+):**
- Config diff / change history — requires versioned storage, low priority until enterprise use
- Token scoping per-project — complex, defer until multi-project support exists
- Authenticated DAST scanning — browser automation and credential management, document manual Nuclei approach first

### Architecture Approach

The three features integrate into the existing layered architecture with minimal overlap, enabling parallel development after the RBAC foundation is established. New components are: `NucleiAdapter` (new file, follows existing ScannerAdapter pattern exactly), `ConfigService` (YAML round-trip service, config.yml as source of truth), `api/config.py` (REST endpoints for scanner config and profiles), and ORM models for users/tokens/profiles. Modified components are `api/auth.py` (major rewrite with backward compat for legacy api_key), `dashboard/auth.py` (role-aware sessions), and `adapters/registry.py` (add `update_scanner()` method). The orchestrator, the ScannerAdapter base class, and all 12 existing adapters remain unchanged.

**Major components:**
1. `NucleiAdapter(ScannerAdapter)` — runs Nuclei CLI via subprocess, parses JSONL output, normalizes to FindingSchema; config.yml entry is auto-discovered by ScannerRegistry
2. `ConfigService` — single-responsibility service for reading and writing config.yml; the UI never touches SQLite for scanner settings
3. Unified RBAC layer — one `get_current_user()` dependency resolving all three entry points (Bearer token, legacy X-API-Key, dashboard cookie) to the same User+Role object
4. Three new DB tables — users, api_tokens, scan_profiles — added via Alembic migrations
5. Scanner Config UI pages — Jinja2 templates + vanilla JS `fetch()` + admin-gated dashboard routes

### Critical Pitfalls

1. **Config UI creating two sources of truth** — choose config.yml as the single source before writing any UI code; ConfigService reads and writes config.yml directly; never store scanner settings in SQLite. Recovery cost: HIGH.

2. **Breaking existing API consumers during RBAC migration** — implement dual-auth from day one: legacy X-API-Key header continues to work (maps to admin role), new Bearer token runs in parallel; write backward-compat test before any RBAC code is added. Recovery cost: HIGH.

3. **Force-fitting Nuclei into the SAST adapter interface** — DAST targets URLs, not filesystem paths; create a DastAdapter subclass with `run(target_url, ...)` or pass URL via extra_args; never put URLs in FindingSchema `file_path`. Recovery cost: HIGH.

4. **SQLite write contention** — add `PRAGMA busy_timeout=5000` to `db/session.py` as the very first commit of the milestone; one-line fix that prevents user-visible 500 errors during concurrent config saves and scan persistence. Recovery cost: LOW if done first, disruptive if deferred.

5. **Auth system divergence** — build one `get_current_user()` dependency handling all three entry points; do not build separate auth logic for dashboard, API, and legacy key. Recovery cost: HIGH.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: SQLite Hardening + RBAC Foundation
**Rationale:** All three features depend on auth; RBAC must come first. SQLite busy_timeout is a one-line fix that prevents write contention across all subsequent phases. This phase establishes the user/token data model and the unified auth dependency that both Config UI and future admin pages require.
**Delivers:** `PRAGMA busy_timeout=5000` in db/session.py; users table + api_tokens table via Alembic migration; bcrypt password hashing via pwdlib; token CRUD API (create/list/revoke); legacy X-API-Key backward compatibility; unified `get_current_user()`; 3-role authorization via FastAPI `Depends(require_role(...))`; initial admin bootstrap mechanism
**Addresses:** All P1 RBAC features from FEATURES.md
**Avoids:** Pitfall 2 (backward compat), Pitfall 4 (SQLite contention), Pitfall 8 (auth divergence)
**Research flag:** Standard FastAPI JWT patterns — skip phase research; PyJWT + pwdlib fully documented in official FastAPI tutorials

### Phase 2a: Nuclei DAST Adapter
**Rationale:** Purely additive. Only touches new files, config.yml entry, and Dockerfile. No dependency on Config UI or RBAC (works with existing api_key auth and new Bearer token auth from Phase 1). Can proceed in parallel with Phase 2b.
**Delivers:** `NucleiAdapter(ScannerAdapter)` class; Nuclei v3.5.x binary in Dockerfile; target_url field on ScanRequest and ScanResult; JSONL output parsing to FindingSchema with `tool="nuclei"` and `scan_type="dast"`; curated default template subset (cves/, vulnerabilities/, misconfiguration/); pinned template version
**Uses:** Existing `ScannerAdapter` base class, `_execute()` method, `ScannerRegistry` auto-discovery via importlib
**Avoids:** Pitfall 3 (DAST as SAST — separate interface or extra_args URL passing), Pitfall 7 (template management — pin version, curated tags), Pitfall 10 (DAST findings skewing quality gate — tag with scan_type)
**Research flag:** Nuclei CLI flags and JSONL output schema well-documented — skip phase research; validate exact JSONL field names during implementation

### Phase 2b: Scanner Configuration UI
**Rationale:** Depends on RBAC admin role from Phase 1 to gate write endpoints. Independent of Nuclei adapter but benefits from it being registered (shows 13 scanners in the UI). Can proceed in parallel with Phase 2a.
**Delivers:** `core/config_service.py` with ruamel.yaml round-trip; `api/config.py` REST endpoints (GET/PUT per scanner, scan profile CRUD); dashboard config pages (Jinja2 templates + vanilla JS); enable/disable toggles; per-scanner settings display; config persistence to config.yml; admin-only write gate
**Implements:** ConfigService component; scanner config dashboard pages
**Avoids:** Pitfall 1 (two sources of truth — config.yml is the only source), Pitfall 9 (invalid config saves — validate with pydantic before write), Pitfall 12 (YAML comments — use ruamel.yaml for round-trip)
**Research flag:** ruamel.yaml round-trip behavior with pydantic-settings loading may need a brief validation pass if comment preservation is a hard requirement; otherwise standard patterns apply

### Phase 3: Scan Profiles + Admin UI
**Rationale:** Builds on Config UI (Phase 2b) for the profile management layer and on RBAC (Phase 1) for the user/token admin pages. Lower priority than foundational capabilities; validates user demand before investing in profile complexity.
**Delivers:** scan_profiles table + CRUD API; named scanner configuration presets (cap 5-7); admin dashboard pages for user/token management; token expiration enforcement (`expires_at` + `revoked_at` fields); profile name stored in scan result for audit reproducibility
**Addresses:** All P2 features from FEATURES.md (scan profiles, admin UI, token expiration, audit hygiene)
**Avoids:** Pitfall 5 (profile explosion — cap and validate), Pitfall 11 (no token revocation — revoked_at field from day one)
**Research flag:** Standard CRUD patterns — skip phase research

### Phase Ordering Rationale

- RBAC must precede Config UI because any write endpoint for scanner settings must be admin-gated; building the UI without roles first would require a security retrofit.
- Nuclei adapter is architecturally independent and can proceed in parallel with Config UI — it only touches new files.
- The SQLite busy_timeout fix is included in Phase 1 rather than its own phase because it is a one-line change that pays dividends immediately across all subsequent write operations.
- Backward compatibility with the existing single api_key is a Phase 1 constraint, not a Phase 3 cleanup — breaking CI/CD pipelines on first deploy is unacceptable for a security tool.
- Scan profiles require the ConfigService to exist, so they follow Config UI naturally and do not block earlier phases.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2b (Scanner Config UI):** The ruamel.yaml round-trip comment preservation behavior warrants a quick validation if preserving inline comments in config.yml is a hard requirement. If the decision is to use raw textarea editing instead of form fields, this is moot.
- **Phase 3 (Scan Profiles):** Profile-to-scan linkage (storing which profile was active for a given scan result) touches the scan history schema; a brief check of the current scan result model is needed before writing migrations.

Phases with standard patterns (skip phase research):
- **Phase 1 (RBAC Foundation):** FastAPI JWT + pwdlib patterns fully documented in official FastAPI tutorials; PyJWT and pwdlib are both current FastAPI recommendations with clear migration guidance.
- **Phase 2a (Nuclei DAST Adapter):** Follows existing adapter pattern exactly; Nuclei CLI flags and JSONL schema are stable and well-documented.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All technology choices validated against official FastAPI docs, PyPI current versions, and GitHub releases as of 2026-03-22 |
| Features | HIGH | Feature set derived from direct codebase analysis plus industry comparators (DefectDojo, SonarQube); no speculative features |
| Architecture | HIGH | Architecture based on direct reading of all `src/scanner/` files; integration points are concrete, not theoretical |
| Pitfalls | HIGH | Pitfalls sourced from SQLite official docs, RBAC best practice guides, and Nuclei DAST community experience; recovery costs assessed against actual code |

**Overall confidence:** HIGH

### Gaps to Address

- **Nuclei JSONL output field names:** Exact field names in Nuclei's JSON output (e.g., `info.severity`, `matched-at`) need validation against actual Nuclei run output during Phase 2a implementation; the schema is documented but field names change between major versions.
- **target_url threading decision:** Architecture recommends passing URL via extra_args for v1.0.2 to avoid modifying the ScannerAdapter base class. If the team prefers a cleaner `DastAdapter` subclass, that decision must be made at the start of Phase 2a — it affects the base class contract and all downstream callers.
- **ruamel.yaml vs PyYAML for config writes:** PITFALLS.md recommends ruamel.yaml for comment preservation; STACK.md does not list it as a new dependency (PyYAML is already present via pydantic-settings). If comment preservation is required, ruamel.yaml must be added to pyproject.toml. If not required (raw textarea editor mode), PyYAML is sufficient.
- **Initial admin account bootstrap:** RBAC needs a first admin account; the exact mechanism (CLI command, env-var seeding, or printed one-time credentials on first run) is a design decision for Phase 1 that affects deployment documentation.
- **Multi-arch Nuclei binary in Docker:** The Dockerfile must parameterize the Nuclei download URL by CPU architecture (linux_amd64 vs linux_arm64) for teams running Docker on Apple Silicon or ARM servers.

## Sources

### Primary (HIGH confidence)
- [FastAPI Official JWT Tutorial](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/) — PyJWT + pwdlib recommendation
- [FastAPI Discussion #11345](https://github.com/fastapi/fastapi/discussions/11345) — python-jose abandonment confirmed
- [FastAPI Discussion #11773](https://github.com/fastapi/fastapi/discussions/11773) — pwdlib adoption confirmed
- [PyJWT on PyPI](https://pypi.org/project/PyJWT/) — v2.12.1 confirmed as of 2026-03-22
- [pwdlib on PyPI](https://pypi.org/project/pwdlib/) — v0.3.0 confirmed as of 2026-03-22
- [Nuclei GitHub](https://github.com/projectdiscovery/nuclei) — v3.5.x current release
- [Nuclei Running Docs](https://docs.projectdiscovery.io/opensource/nuclei/running) — CLI flags reference
- [Nuclei Docker Hub](https://hub.docker.com/r/projectdiscovery/nuclei) — Docker integration approach
- [CodeMirror 5 YAML mode](https://codemirror.net/5/mode/yaml/) — CDN distribution confirmed
- Existing codebase (`src/scanner/`) — all architectural claims verified against actual source files

### Secondary (MEDIUM confidence)
- [RBAC Best Practices 2025](https://www.osohq.com/learn/rbac-best-practices) — permission-based vs role-based checks recommendation
- [RBAC Implementation Guide](https://www.permit.io/blog/fastapi-rbac-full-implementation-tutorial) — FastAPI RBAC dependency injection patterns
- [Nuclei DAST Integration Guide](https://iaraoz.medium.com/how-to-use-nuclei-as-an-appsec-dast-tool-in-devsecops-90d0ab5963bb) — DAST adapter design patterns
- [SQLite WAL Mode](https://www.sqlite.org/wal.html) — busy_timeout behavior and write contention

### Tertiary (LOW confidence)
- [Home Assistant YAML vs UI](https://community.home-assistant.io/t/wth-can-we-edit-yaml-files-in-the-ui/472909) — config source-of-truth failure modes (community experience, not official docs)
- [Nuclei DAST Payload Bug #5561](https://github.com/projectdiscovery/nuclei/issues/5561) — known DAST template edge cases

---
*Research completed: 2026-03-22*
*Ready for roadmap: yes*
