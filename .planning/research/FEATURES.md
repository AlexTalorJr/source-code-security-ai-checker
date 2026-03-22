# Feature Research

**Domain:** Security scanning platform -- Scanner Configuration UI, Nuclei DAST adapter, Token-based RBAC
**Researched:** 2026-03-22
**Confidence:** HIGH (features well-understood from existing codebase + industry patterns)

## Feature Landscape

### A. Scanner Configuration UI

#### Table Stakes (Users Expect These)

| Feature | Why Expected | Complexity | Dependencies |
|---------|--------------|------------|--------------|
| Enable/disable scanners via UI toggle | Every scanner management UI has this. Current config.yml-only approach requires restart and file editing. | LOW | Existing `ScannerRegistry`, `/api/scanners` endpoint already returns scanner list with enabled status |
| Per-scanner settings display | Users need to see timeout, extra_args, languages for each scanner without reading YAML | LOW | Existing `ScannerToolConfig` model has all fields |
| Config editor (raw YAML) | Power users expect to edit the full config directly; this is table stakes for self-hosted tools | MEDIUM | Must validate YAML before save, handle config reload without restart |
| Scanner status/health indicators | Users must see which scanners loaded successfully vs load_error. Existing `status` field in registry covers this. | LOW | Existing `RegisteredScanner.status` property (enabled/disabled/load_error) |
| Settings persistence across restarts | Changed settings must survive container restarts -- write back to config.yml or a separate overrides file | MEDIUM | Must decide: overwrite config.yml or use overlay pattern (e.g., config.local.yml) |

#### Differentiators (Competitive Advantage)

| Feature | Value Proposition | Complexity | Dependencies |
|---------|-------------------|------------|--------------|
| Scan profiles (named presets) | Save combinations of scanner settings as named profiles (e.g., "quick-sast", "full-audit", "php-only"). DefectDojo and SonarQube both offer scan configurations / quality profiles. Reduces repetitive config for teams with multiple projects. | MEDIUM | Needs new DB table or config section for profiles; scan trigger must accept profile_id |
| Live config validation | Validate config changes before applying (test adapter_class import, check tool binary exists) | LOW | Existing `load_adapter_class()` can be reused for validation |
| Config diff / change history | Show what changed between config versions. Valuable for audit trails in security tools. | HIGH | Needs versioned config storage -- defer to future milestone |

#### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Auto-discovery of new scanner binaries | "Just detect what's installed" | Unreliable in containers, security risk (arbitrary binary execution), breaks reproducibility | Explicit registration via config.yml with adapter_class -- already implemented |
| Per-scan custom scanner selection via UI | "Let me pick scanners for each scan" | Adds complexity to scan trigger, conflicts with language auto-detection, profiles solve this better | Scan profiles that pre-select scanner combinations |
| Drag-and-drop scanner ordering | "Control execution order" | Scanners run in parallel -- ordering is meaningless. Would mislead users about execution model. | Show scanners grouped by type (SAST/SCA/DAST) instead |

---

### B. Nuclei DAST Adapter

#### Table Stakes (Users Expect These)

| Feature | Why Expected | Complexity | Dependencies |
|---------|--------------|------------|--------------|
| NucleiAdapter implementing ScannerAdapter | Must follow existing adapter pattern (tool_name, run(), _version_command()) for registry compatibility | MEDIUM | Existing `ScannerAdapter` base class, `ScannerRegistry` |
| Target URL parameter for DAST scans | DAST scans target live URLs, not file paths. `run()` currently takes `target_path` -- Nuclei needs a URL. | MEDIUM | Requires extending scan trigger to accept `target_url` alongside `target_path`, or overloading `target_path` for DAST |
| Template tag selection | Nuclei has 12,000+ templates. Users must be able to filter by tags (cve, exposure, misconfiguration, etc.) via `extra_args` | LOW | Map to Nuclei CLI flags: `-tags cve,exposure`. Fits existing `extra_args` pattern |
| JSON output parsing | Nuclei outputs JSON/JSONL. Adapter must parse into `FindingSchema` with severity mapping. | MEDIUM | Nuclei severities (info/low/medium/high/critical) map directly to existing `Severity` enum |
| Timeout handling | Nuclei scans can run long against live targets. Must respect `timeout` config. | LOW | Existing `_execute()` with `asyncio.wait_for` handles this |
| Nuclei binary in Docker image | Tool must be available in the container | LOW | Nuclei is a single Go binary (~30MB). Add to Dockerfile. |

#### Differentiators (Competitive Advantage)

| Feature | Value Proposition | Complexity | Dependencies |
|---------|-------------------|------------|--------------|
| Custom Nuclei template directory | Allow users to mount their own templates alongside official ones. Security teams write custom checks. | LOW | Nuclei supports `-t /path/to/custom-templates` via extra_args |
| DAST-aware scan trigger | API/dashboard support `target_url` field so DAST scans are first-class citizens, not a hack on `target_path` | MEDIUM | New `target_url` field on ScanRequest and ScanResult model; dashboard form update |
| Template severity filtering | Only run templates matching minimum severity (e.g., skip info-level templates for speed) | LOW | Nuclei `-severity high,critical` flag via extra_args or dedicated config field |

#### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Full DAST target management (target inventory, scheduling) | "Manage all our DAST targets" | Massive scope creep -- turns scanner into asset management tool. Out of scope per PROJECT.md. | Single target_url per scan; external scheduling via CI/CD or cron |
| Authenticated DAST scanning (login sequences, session tokens) | "Scan behind login" | Requires complex browser automation, credential management, state handling. Nuclei supports it but setup is non-trivial. | Defer to future milestone; document Nuclei's `-header` flag for simple auth headers |
| DAST-specific report sections | "Separate DAST report format" | Findings already normalize to FindingSchema. Separate reports fragment the user experience. | Tag findings with `tool: nuclei` -- existing report handles it. Add DAST tag filter to dashboard. |
| Real-time crawling / spider integration | "Automatically discover all endpoints" | Massively increases scan time, false positives, and scope. Separate concern. | User provides target URLs explicitly; Nuclei handles the rest |

---

### C. Token-Based RBAC

#### Table Stakes (Users Expect These)

| Feature | Why Expected | Complexity | Dependencies |
|---------|--------------|------------|--------------|
| Multiple API tokens (not single shared key) | Current single `api_key` is a security anti-pattern for multi-user/multi-pipeline setups. Each CI pipeline and user needs its own token. | MEDIUM | New `api_tokens` DB table; replace `require_api_key` dependency |
| Three roles: admin, viewer, scanner | Minimum viable RBAC. Admin manages config/users, viewer sees results, scanner triggers scans. Matches PROJECT.md spec. | MEDIUM | New `users` and `tokens` tables; role field on each |
| Dashboard login with user accounts | Replace current single-API-key login with username/password per user | MEDIUM | Replace `dashboard/auth.py` hashing approach; add user management |
| API endpoint authorization by role | Scanner role can POST /scans but not change config. Viewer can GET but not POST. Admin can do everything. | MEDIUM | FastAPI dependency injection -- extend `require_api_key` to `require_role(min_role)` |
| Token generation and revocation | Admin must create tokens for CI pipelines, revoke compromised tokens | LOW | CRUD endpoints: POST/DELETE /api/tokens; admin-only |
| Password hashing (bcrypt/argon2) | Plaintext or SHA-256 passwords are unacceptable for a security product | LOW | Use `passlib` with bcrypt; replace current SHA-256 session tokens |

#### Differentiators (Competitive Advantage)

| Feature | Value Proposition | Complexity | Dependencies |
|---------|-------------------|------------|--------------|
| Token scoping (per-project or per-scanner) | Tokens that only work for specific scanners or scan targets. Fine-grained CI/CD security. | HIGH | Needs scope field on tokens, evaluation at scan trigger time -- defer |
| Admin UI for user/token management | Manage users and tokens from the dashboard, not just CLI/API | MEDIUM | New dashboard pages; depends on admin role being implemented first |
| Audit log of auth events | Log login attempts, token usage, role changes. Critical for security products. | MEDIUM | New `audit_log` table; middleware to capture events |
| API token expiration dates | Tokens that auto-expire force rotation. Good security hygiene. | LOW | `expires_at` field on tokens table; check at auth time |

#### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| OAuth/SSO/LDAP integration | "Enterprise needs SSO" | Massive complexity (redirect flows, token exchange, provider config). Out of scope per PROJECT.md. SQLite constraint makes this impractical. | Simple local auth. Document how to put a reverse proxy with SSO in front. |
| User self-registration | "Let users sign up" | Security scanning platform should not have open registration. Admin controls access. | Admin creates accounts; PROJECT.md explicitly excludes self-registration |
| Complex permission matrices (per-resource ACLs) | "Fine-grained permissions on every object" | Overkill for a self-hosted tool with 3 roles. Adds complexity with little value. | Three fixed roles cover all use cases. Add scope later if needed. |
| Session-based API auth (cookies for API) | "Why not just use cookies for API too?" | Breaks CI/CD integration, stateful, harder to manage programmatically | Bearer tokens for API, cookies for dashboard -- standard separation |

---

## Feature Dependencies

```
[RBAC: Users & Tokens table]
    |-- requires --> [Password hashing]
    |-- requires --> [DB migration (add users, tokens tables)]
    |-- enables --> [Dashboard login with user accounts]
    |-- enables --> [API endpoint authorization by role]
    |-- enables --> [Admin UI for user/token management]

[Scanner Config UI]
    |-- requires --> [RBAC: admin role] (only admins should change scanner config)
    |-- requires --> [Config persistence mechanism]
    |-- enables --> [Scan profiles]
    |-- uses ----> [Existing ScannerRegistry + /api/scanners]

[Nuclei DAST Adapter]
    |-- requires --> [Nuclei binary in Docker]
    |-- requires --> [target_url field on scan model]
    |-- follows --> [Existing ScannerAdapter pattern]
    |-- independent of --> [Scanner Config UI] (can be config.yml only initially)
    |-- independent of --> [RBAC] (works with existing api_key auth)

[Scan Profiles]
    |-- requires --> [Scanner Config UI]
    |-- enhances --> [Nuclei DAST Adapter] (DAST profile with target_url preset)
```

### Dependency Notes

- **Scanner Config UI requires RBAC admin role:** Without role-based access, any authenticated user can change scanner configuration -- unacceptable for a security tool. RBAC must come first or in parallel.
- **Nuclei adapter is independent:** Can be implemented with config.yml registration only, no UI dependency. Lowest coupling to other features.
- **Scan profiles require Scanner Config UI:** Profiles are saved scanner configurations -- need the config management layer first.
- **target_url field is a cross-cutting concern:** Both Nuclei adapter and scan trigger API need this. Small schema change but touches DB model, API schema, and dashboard form.

---

## MVP Definition

### Launch With (v1.0.2)

- [ ] **RBAC: users table + 3 roles + password hashing** -- Foundation that all other features depend on for security
- [ ] **RBAC: multiple API tokens per user** -- Replace single shared api_key; each CI pipeline gets its own token
- [ ] **RBAC: endpoint authorization by role** -- Scanner role triggers scans, viewer reads, admin manages
- [ ] **RBAC: dashboard login with user accounts** -- Replace current single-key login
- [ ] **Scanner Config UI: enable/disable toggles + settings display** -- Core value of the feature
- [ ] **Scanner Config UI: config persistence** -- Settings must survive restarts
- [ ] **Nuclei DAST adapter** -- Register in config.yml, run against target URLs, parse JSON output
- [ ] **target_url field on scan model** -- Enable DAST scans as first-class citizens

### Add After Validation (v1.0.x)

- [ ] **Scan profiles** -- Once config UI is stable and users request preset combinations
- [ ] **Admin UI for user/token management** -- Once RBAC is proven via API, add dashboard management
- [ ] **Token expiration dates** -- Once token management is working
- [ ] **Audit log** -- Once auth events are well-defined
- [ ] **Config editor (raw YAML)** -- Once config persistence pattern is established

### Future Consideration (v2+)

- [ ] **Config diff / change history** -- Needs versioned storage, low priority until enterprise use
- [ ] **Token scoping (per-project)** -- Complex, defer until multi-project support exists
- [ ] **Authenticated DAST scanning** -- Complex Nuclei setup, document manual approach first

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| RBAC: users + roles + tokens | HIGH | MEDIUM | P1 |
| RBAC: endpoint authorization | HIGH | MEDIUM | P1 |
| RBAC: dashboard user login | HIGH | LOW | P1 |
| Nuclei DAST adapter | HIGH | MEDIUM | P1 |
| target_url field on scan model | HIGH | LOW | P1 |
| Scanner Config UI: toggles + display | MEDIUM | LOW | P1 |
| Scanner Config UI: persistence | MEDIUM | MEDIUM | P1 |
| Password hashing (bcrypt) | HIGH | LOW | P1 |
| Token generation/revocation API | HIGH | LOW | P1 |
| Scan profiles | MEDIUM | MEDIUM | P2 |
| Admin UI for user/token management | MEDIUM | MEDIUM | P2 |
| Token expiration | MEDIUM | LOW | P2 |
| Live config validation | LOW | LOW | P2 |
| Audit log | MEDIUM | MEDIUM | P2 |
| Config editor (raw YAML) | LOW | MEDIUM | P3 |
| Custom Nuclei template directory | LOW | LOW | P3 |

**Priority key:**
- P1: Must have for v1.0.2 launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

---

## Competitor Feature Analysis

| Feature | DefectDojo | SonarQube | Our Approach |
|---------|------------|-----------|--------------|
| Scanner config | Tool Configuration pages per scanner type, separate scan configs per API/UI | Quality Profiles with inheritance, per-project assignment | Dashboard page with enable/disable toggles + per-scanner settings form, backed by config.yml overlay |
| DAST integration | Imports DAST results (Nuclei, ZAP, Burp) as findings | No native DAST -- relies on plugins | Native Nuclei adapter in scanner registry, first-class target_url support |
| Auth model | Full user management, LDAP/SSO, API tokens per user | Built-in users + LDAP/SAML, project-level permissions | Simple local auth: username/password + API tokens, 3 fixed roles (admin/viewer/scanner) |
| Scan profiles | Product-level scan configurations | Quality Gates + Quality Profiles | Named presets selecting scanner combinations + settings |
| Config persistence | PostgreSQL-backed | PostgreSQL-backed | config.yml overlay file (config.local.yml) or SQLite-backed settings table |

---

## Sources

- [ProjectDiscovery Nuclei documentation](https://docs.projectdiscovery.io/opensource/nuclei/overview)
- [Nuclei GitHub repository](https://github.com/projectdiscovery/nuclei)
- [DefectDojo SonarQube API Import documentation](https://docs.defectdojo.com/en/connecting_your_tools/parsers/api/sonarqube/)
- [Rapid7 InsightAppSec scan configuration](https://docs.rapid7.com/insightappsec/scan-configuration/)
- [FastAPI RBAC with JWT - Logto](https://docs.logto.io/api-protection/python/fastapi)
- [FastAPI RBAC implementation tutorial - Permit.io](https://www.permit.io/blog/fastapi-rbac-full-implementation-tutorial)
- [Nuclei vs Nikto DAST comparison](https://appsecsanta.com/nuclei-vs-nikto)
- Existing codebase: `scanner/adapters/registry.py`, `scanner/api/auth.py`, `scanner/dashboard/auth.py`, `scanner/config.py`

---
*Feature research for: Security scanning platform v1.0.2 -- Scanner Configuration UI, Nuclei DAST, RBAC*
*Researched: 2026-03-22*
