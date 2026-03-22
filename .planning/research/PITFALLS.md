# Domain Pitfalls

**Domain:** Adding Scanner Configuration UI, Nuclei DAST, and RBAC to existing security scanning platform
**Researched:** 2026-03-22
**Applies to:** Milestone v1.0.2

This document covers pitfalls specific to ADDING these three features to the existing v1.0.1 system. For foundational pitfalls (alert fatigue, AI hallucinations, dedup, CI timeout, etc.), see the original pitfalls captured during v1.0 research -- those remain valid and are not repeated here.

## Critical Pitfalls

### Pitfall 1: Config UI and config.yml Become Two Sources of Truth

**What goes wrong:** The Scanner Configuration UI writes scanner settings to SQLite while the orchestrator reads from config.yml via pydantic-settings. Changes made in the UI have no effect on actual scans because the orchestrator loads `ScannerSettings()` fresh from config.yml on every scan. Or worse, changes made in config.yml are silently overwritten by old UI state on save.

**Why it happens:** The existing architecture has a clean, one-directional config flow: `config.yml -> pydantic-settings -> ScannerSettings -> ScannerRegistry`. Adding a UI that modifies settings creates a bidirectional sync problem. Developers instinctively store UI state in the database (it is a web app, after all) but forget that the orchestrator never reads the database for configuration.

**Consequences:**
- Admin changes scanner settings in UI, triggers scan, settings are ignored -- uses config.yml values
- Admin edits config.yml directly, UI shows stale settings, admin "saves" from UI and reverts the manual change
- CI-triggered scans use config.yml while dashboard-triggered scans use UI state -- inconsistent results
- Docker volume mounts for config.yml add another layer of confusion (host file vs container file)

**Prevention:**
- Choose ONE source of truth. Recommendation: config.yml remains the single source. UI reads and writes config.yml directly (via a config service layer), never stores config in SQLite.
- The UI config editor should be a YAML editor with validation, not a separate abstraction layer. Load config.yml, present it as form fields, write back to config.yml on save.
- After any config change via UI, the in-memory `ScannerSettings` must be reloaded. Add a `reload_settings()` method to the app lifespan that re-reads config.yml and rebuilds `ScannerRegistry`.
- For "scan profiles" (named configurations), store profile YAMLs as separate files (e.g., `profiles/aggressive.yml`, `profiles/ci-quick.yml`) and let the scan request specify which profile to use.
- Never cache parsed config in memory without an invalidation mechanism.

**Detection:**
- UI shows different scanner settings than what `cat config.yml` returns
- Changing a scanner timeout in the UI has no effect on actual scan duration
- Restarting the container resets UI settings to config.yml defaults

**Phase to address:** Scanner Configuration UI phase -- this is the fundamental design decision that must be made before writing any UI code.

---

### Pitfall 2: Breaking Existing API Consumers When Adding RBAC

**What goes wrong:** Adding token-based RBAC to an API that currently uses a single shared `X-API-Key` breaks every existing Jenkins pipeline, every curl command in documentation, and every test that calls the API. The existing `require_api_key` dependency in `scanner/api/auth.py` uses `secrets.compare_digest` against a single configured key. Replacing this with per-user tokens invalidates the only authentication method that works.

**Why it happens:** The current auth is intentionally simple: one API key in config.yml/env var, checked via header. RBAC requires a user model, token storage, role assignment, and permission checking. Teams either break backward compatibility ("just update your key") or build an awkward dual-auth system that nobody understands.

**Consequences:**
- Jenkins pipelines fail with 401 after deployment, blocking all CI/CD
- Documentation examples become wrong overnight
- `test123` default key in config.yml.example stops working
- Dashboard cookie auth (`scanner_session` from `make_session_token`) conflicts with token auth

**Prevention:**
- Phase the migration: Step 1 adds RBAC as an OPTIONAL auth method alongside the existing single API key. The existing `X-API-Key` header continues to work and grants "admin" role implicitly. Step 2 (future milestone) deprecates the single key.
- Add a new header `Authorization: Bearer <token>` for token-based auth. Keep `X-API-Key` working by checking both headers in the auth dependency. If `X-API-Key` matches the configured key, treat it as admin. If `Authorization: Bearer` is present, look up the token in the database.
- Create an initial admin token during first startup (or via CLI command) that is printed to stdout/logs exactly once. Do NOT require a migration step that blocks existing usage.
- Existing tests use `X-API-Key: test123`. These must continue to pass without modification during the transition.
- Document the migration path clearly: "Your existing API key continues to work. To use RBAC, create tokens via the admin API."

**Detection:**
- Any test in `tests/phase_05/test_auth.py` fails after RBAC changes
- Jenkins pipeline returns 401 after upgrade
- Documentation says "set SCANNER_API_KEY" but RBAC requires a different flow

**Phase to address:** RBAC phase -- backward compatibility must be the first test written, before any RBAC code.

---

### Pitfall 3: Nuclei DAST Adapter Treated Like SAST Adapters

**What goes wrong:** The Nuclei adapter is built to follow the same `ScannerAdapter.run(target_path, timeout, extra_args)` interface as SAST adapters. But DAST scanners do not scan a filesystem path -- they scan a running application via URL. Passing a `target_path` to Nuclei makes no sense. The adapter either crashes, scans nothing, or the developer hacks `target_path` to mean "URL" which corrupts the data model and breaks every downstream consumer (reports, dashboard, finding storage) that assumes `target_path` is a filesystem path.

**Why it happens:** The existing `ScannerAdapter` base class has a clean contract: `run(target_path: str, timeout: int, extra_args: list[str])`. All 12 existing adapters follow this contract. It is tempting to "just make Nuclei fit" by reusing the same interface. But SAST and DAST are fundamentally different execution models.

**Consequences:**
- Finding `file_path` fields contain URLs instead of relative paths, breaking report rendering
- Finding `line_start`/`line_end` are meaningless for DAST findings (there is no source line)
- Orchestrator tries to `detect_languages` on a URL and fails
- `clone_repo` is called unnecessarily for DAST scans
- Quality gate evaluates DAST findings alongside SAST findings with no distinction

**Prevention:**
- Extend the `ScannerAdapter` interface, do not force-fit. Add an optional `target_url` parameter or create a `DastAdapter` subclass with `run(target_url: str, timeout: int, extra_args: list[str])`.
- The scan request API must accept a `target_url` field for DAST scans, separate from `path`/`repo_url`.
- Nuclei findings should use a different schema or at minimum set `file_path` to the URL endpoint path (e.g., `/api/login`) and leave `line_start`/`line_end` as None.
- The orchestrator must handle DAST and SAST scans differently: SAST gets `detect_languages -> get_enabled_adapters -> run`. DAST gets `check target reachability -> run Nuclei templates -> collect findings`.
- Do NOT mix DAST and SAST in the same scan execution. A scan is either SAST (local path / repo) or DAST (target URL). Mixed scans are a future feature.
- The `-dast` flag must be explicitly passed to Nuclei for DAST fuzzing templates. Without it, Nuclei only runs passive templates which find very little.

**Detection:**
- Finding records have URLs in the `file_path` column
- Nuclei adapter receives a filesystem path and returns zero findings
- Reports show "File: https://example.com/login Line: None" in the findings table

**Phase to address:** Nuclei DAST phase -- interface design decision before writing the adapter.

---

### Pitfall 4: SQLite Write Contention Between UI Config Saves and Scanner Execution

**What goes wrong:** The Scanner Configuration UI performs writes to SQLite (if config is stored in DB, or even for RBAC token/user tables) while a scan is running and also writing findings to SQLite. SQLite allows only one writer at a time. Even with WAL mode, a long-running write transaction in the scan persist step (which can write hundreds of finding rows) blocks UI saves for the duration. Users see "database is locked" errors or hanging save buttons.

**Why it happens:** The existing system has low write contention: scans write findings at the end, dashboard reads, API reads. Adding RBAC (token validation on every request = read, token creation = write) and a config UI (settings save = write) increases write frequency significantly. The current `create_engine` in `db/session.py` does not set `busy_timeout`, so the default SQLite busy handler returns immediately on lock contention.

**Consequences:**
- "Save settings" button in UI returns 500 during active scan
- Token validation queries intermittently fail during scan persistence
- RBAC token creation fails if a scan is persisting findings simultaneously
- In extreme cases, database corruption if two aiosqlite connections write simultaneously without proper locking

**Prevention:**
- Add `PRAGMA busy_timeout=5000` to `_set_sqlite_pragmas` in `db/session.py`. This makes SQLite retry for 5 seconds before returning "database is locked." This is the single most important fix.
- Keep write transactions as short as possible. The current scan persistence writes all findings in one transaction -- consider batching (50 findings per commit) to release the write lock periodically.
- Use a single shared `async_sessionmaker` instance (already done via `app.state.session_factory`), not multiple engines.
- For RBAC token validation (read-heavy), ensure these are read-only queries that do not take write locks. Use `SELECT` directly, never `SELECT ... FOR UPDATE` (which does not exist in SQLite but some ORMs emulate it with writes).
- Consider separating auth data (users, tokens) from scan data (scans, findings) into different SQLite files if contention becomes measurable. This is a last resort.

**Detection:**
- HTTP 500 errors on config save during active scans
- "database is locked" in application logs
- Dashboard becomes unresponsive for 5+ seconds during scan completion

**Phase to address:** Must be addressed early -- add `busy_timeout` before any new write-heavy features. This is a one-line fix in `db/session.py` that should be the first commit of the milestone.

---

## Moderate Pitfalls

### Pitfall 5: Scan Profiles Create Configuration Explosion

**What goes wrong:** The "scan profiles" feature (e.g., "quick CI scan", "full security audit", "OWASP Top 10 only") starts with 3 profiles and grows to 15 as teams request variations. Each profile has slightly different scanner settings, different timeout values, different quality gate thresholds. Nobody knows which profile was used for a given historical scan, making audit trails unreliable.

**Prevention:**
- Cap profiles at a small number (5-7). Use composition instead of proliferation: base config + override layer.
- Store the profile name (or full profile snapshot) in the scan result record. Every scan must be reproducible.
- Validate profiles against available scanners at load time -- a profile referencing a scanner that does not exist should warn, not crash.
- Provide a "diff from default" view so admins can see exactly what a profile changes.

---

### Pitfall 6: RBAC Role Granularity Wrong From the Start

**What goes wrong:** Starting with three roles (admin, viewer, scanner) seems clean. Then requirements emerge: "viewers should see reports but not AI analysis costs", "scanner role should trigger scans but not see other scanners' results", "we need a role that can suppress findings but not change config." Retrofitting finer-grained permissions onto coarse roles requires rewriting every permission check.

**Prevention:**
- Implement roles as collections of permissions, not hardcoded role checks. Define permissions: `scan.trigger`, `scan.view`, `config.read`, `config.write`, `findings.suppress`, `admin.users`. Map roles to permission sets.
- Check permissions, not roles, in endpoint dependencies: `require_permission("config.write")` not `require_role("admin")`.
- Start with three roles but make the mapping configurable (in config.yml or a permissions table). Adding a new role should require zero code changes -- just a new permission mapping.
- The "scanner" role (for CI/CD tokens) should have exactly: `scan.trigger`, `scan.view`. Nothing else.

---

### Pitfall 7: Nuclei Template Management Overlooked

**What goes wrong:** Nuclei's power comes from its 9000+ community templates. But running all templates against a target takes hours and generates thousands of findings. Teams either run too many templates (noise) or too few (miss real issues). Template updates (new CVEs) are not tracked, so the same target scanned twice may produce different results due to template changes.

**Prevention:**
- Ship with a curated template subset: `cves/`, `vulnerabilities/`, `misconfiguration/` -- skip `fuzzing/` and `headless/` by default.
- Pin Nuclei template version in Docker image (via `nuclei -ut -duc`). Update templates as part of Docker image rebuild, not at scan time.
- Allow per-profile template selection via tags: `-tags cve,owasp-top-10` for quick scans, `-tags cve,owasp-top-10,misconfig,exposure` for full audits.
- Store the template version/hash in the scan result for reproducibility.
- Rate-limit Nuclei requests (`-rl 50 -c 10`) to avoid overwhelming the target or triggering WAF blocks.

---

### Pitfall 8: Dashboard Auth and API Auth Diverge Into Separate Systems

**What goes wrong:** The dashboard uses cookie-based session auth (`scanner_session` cookie from `make_session_token`). The API uses `X-API-Key` header auth. RBAC adds token-based auth. Now there are three separate auth systems, each with different user models, different permission semantics, and different session lifetimes. A user logged into the dashboard cannot use the API without a separate token. An admin managing tokens via API cannot manage dashboard sessions.

**Prevention:**
- Unify auth under one system: RBAC tokens. Dashboard login creates a session that maps to a token with the user's role. API uses the same token via `Authorization: Bearer` header. The old `X-API-Key` is an alias for admin token (backward compatibility).
- Dashboard sessions should be short-lived (8 hours) with a session cookie that maps to a token record in the database. Logging out invalidates the session, not the token.
- All three entry points (dashboard cookie, API bearer token, legacy X-API-Key) should resolve to the same `CurrentUser` object with the same permissions.
- Write one `get_current_user()` dependency that handles all three, not three separate auth dependencies.

---

### Pitfall 9: Config UI Allows Invalid Configurations

**What goes wrong:** The UI lets an admin disable all scanners, set timeout to 0, enter an invalid adapter_class path, or create a scan profile that references a nonexistent scanner. The configuration is saved successfully but the next scan crashes or produces no results.

**Prevention:**
- Validate configuration at save time, not scan time. Use the existing `ScannerToolConfig` pydantic model for validation. If `adapter_class` path cannot be imported, reject the save with a clear error.
- Prevent saving a config with zero enabled scanners (warn, do not block -- admin may be configuring before enabling).
- Add a "test configuration" button that attempts to load all adapter classes and reports which ones fail.
- The config editor should have a "reset to defaults" button that restores config.yml.example values.
- Never allow editing `adapter_class` from the UI -- this is a developer setting, not an admin setting. Expose it as read-only.

---

## Minor Pitfalls

### Pitfall 10: DAST Findings Skew Quality Gate Metrics

**What goes wrong:** DAST findings (from Nuclei) are evaluated by the same quality gate as SAST findings. A Nuclei template detecting an exposed admin panel creates a "CRITICAL" finding that blocks the CI/CD pipeline, even though the DAST scan was run against a staging environment and the SAST scan against production code. The quality gate conflates two different risk contexts.

**Prevention:**
- Quality gate should evaluate SAST and DAST findings separately, or allow per-scan-type gate thresholds.
- Tag findings with `scan_type: "sast"` or `scan_type: "dast"` in the finding schema.
- For v1.0.2, consider making DAST findings informational by default (do not block gate) unless explicitly configured otherwise.

---

### Pitfall 11: Token Rotation and Revocation Not Designed In

**What goes wrong:** RBAC tokens are created but there is no mechanism to rotate or revoke them. A compromised CI/CD token grants permanent access. An employee leaves and their token continues to work. Token expiry is not enforced because "we will add that later."

**Prevention:**
- Tokens must have a `created_at` and optional `expires_at` field from day one.
- Add a `revoked_at` field. Token validation must check `revoked_at IS NULL` on every request.
- Provide a `/api/tokens/{id}/revoke` endpoint from the start.
- CI/CD tokens should default to 90-day expiry. Dashboard sessions to 8 hours.
- Log token usage (last_used_at) for audit and to identify stale tokens.

---

### Pitfall 12: Config YAML Comments and Formatting Destroyed by UI Save

**What goes wrong:** Admin has carefully commented config.yml with explanations for each setting. UI reads the YAML, presents it as form fields, user changes one value, UI writes back the YAML. All comments are stripped, key ordering changes, formatting is different. The config file diff becomes unreadable, and inline documentation is lost.

**Prevention:**
- Use `ruamel.yaml` instead of `PyYAML` for reading/writing config.yml. `ruamel.yaml` preserves comments, key order, and formatting (round-trip mode).
- Alternatively, do not rewrite the entire file. Parse the YAML, modify only the changed values, write back with comment preservation.
- If using a "raw editor" mode (textarea with YAML), validate the YAML syntax before save but do not reformat.
- Show a diff preview before saving ("You are about to change: semgrep.timeout from 180 to 300").

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Scanner Config UI | Two sources of truth (Pitfall 1) | config.yml is single source; UI reads/writes it directly |
| Scanner Config UI | Invalid config saves (Pitfall 9) | Validate with pydantic before write; test adapter loading |
| Scanner Config UI | YAML comments destroyed (Pitfall 12) | Use ruamel.yaml for round-trip YAML handling |
| Scan Profiles | Configuration explosion (Pitfall 5) | Cap at 5-7 profiles; store profile name in scan results |
| Nuclei DAST | SAST adapter interface reuse (Pitfall 3) | Create DastAdapter subclass; separate scan_type |
| Nuclei DAST | Template management (Pitfall 7) | Pin template version in Docker; curate default subset |
| Nuclei DAST | Quality gate skew (Pitfall 10) | Separate DAST/SAST gate evaluation or DAST=informational |
| RBAC tokens | Breaking existing API (Pitfall 2) | Dual-auth: legacy X-API-Key + new Bearer token |
| RBAC roles | Role granularity (Pitfall 6) | Permission-based checks, not role-based |
| RBAC auth | Three auth systems (Pitfall 8) | Unify under single get_current_user() dependency |
| RBAC tokens | No revocation (Pitfall 11) | expires_at + revoked_at fields from day one |
| SQLite | Write contention (Pitfall 4) | Add busy_timeout=5000; batch finding writes |

## Pitfall Ordering by Implementation Priority

These pitfalls should be addressed in this order to minimize cascading issues:

1. **SQLite busy_timeout** (Pitfall 4) -- one-line fix, prevents all write contention issues. Do this first.
2. **Config single source of truth** (Pitfall 1) -- architectural decision that shapes all UI work.
3. **Backward-compatible auth** (Pitfall 2) -- must be decided before writing any RBAC code.
4. **DAST adapter interface** (Pitfall 3) -- must be decided before writing the Nuclei adapter.
5. **Unified auth system** (Pitfall 8) -- design decision before implementing dashboard changes.
6. Everything else follows from these foundational decisions.

## Recovery Costs

| Pitfall | Recovery Cost | Why |
|---------|---------------|-----|
| Two sources of truth (1) | HIGH | Requires choosing one source and migrating all config reads/writes; may need data migration if DB was used |
| Breaking API consumers (2) | HIGH | Every CI/CD pipeline, every test, every doc example must be updated simultaneously |
| DAST as SAST (3) | HIGH | Finding schema contaminated with URLs in file_path; historical data corrupted; reports must handle both formats |
| SQLite contention (4) | LOW | Add one PRAGMA statement; no data model change |
| Scan profile explosion (5) | LOW | Just prune profiles and add validation |
| Role granularity (6) | MEDIUM | Rewrite permission checks from role-based to permission-based across all endpoints |
| Template management (7) | LOW | Add template pinning and tag-based selection |
| Auth system divergence (8) | HIGH | Three auth paths must be unified; session management must be redesigned |
| Invalid config saves (9) | LOW | Add validation layer; no data model change |
| Quality gate skew (10) | LOW | Add scan_type tag; adjust gate logic |
| No token revocation (11) | MEDIUM | Schema migration to add columns; token validation query must be updated |
| YAML comments destroyed (12) | LOW | Switch to ruamel.yaml; no data model change |

## Sources

- [SQLite WAL Mode Documentation](https://www.sqlite.org/wal.html)
- [SQLite Connection Pool Pitfalls](https://www.jtti.cc/supports/3154.html)
- [Abusing SQLite to Handle Concurrency](https://blog.skypilot.co/abusing-sqlite-to-handle-concurrency/)
- [The SQLite Renaissance 2026](https://dev.to/pockit_tools/the-sqlite-renaissance-why-the-worlds-most-deployed-database-is-taking-over-production-in-2026-3jcc)
- [10 RBAC Best Practices 2025](https://www.osohq.com/learn/rbac-best-practices)
- [RBAC Implementation Best Practices](https://www.action1.com/blog/rbac-implementation-best-practices/)
- [How RBAC Improves API Permission Management](https://zuplo.com/learning-center/how-rbac-improves-api-permission-management)
- [Nuclei DAST Integration Guide](https://iaraoz.medium.com/how-to-use-nuclei-as-an-appsec-dast-tool-in-devsecops-90d0ab5963bb)
- [Nuclei Template Accuracy](https://www.appsecengineer.com/blog/testing-with-nuclei-templates-make-your-dast-scans-10x-more-accurate)
- [Nuclei DAST Payload Bug #5561](https://github.com/projectdiscovery/nuclei/issues/5561)
- [Craft CMS Project Config Sync Issues](https://craftcms.com/docs/5.x/system/project-config.html)
- [Home Assistant YAML vs UI Configuration](https://community.home-assistant.io/t/wth-can-we-edit-yaml-files-in-the-ui/472909)
- [FastAPI JWT Token Authentication](https://testdriven.io/blog/fastapi-jwt-auth/)
- [FastAPI Authentication Guide](https://betterstack.com/community/guides/scaling-python/authentication-fastapi/)

---
*Pitfalls research for: naveksoft-security v1.0.2 -- Scanner Config UI, Nuclei DAST, RBAC*
*Researched: 2026-03-22*
