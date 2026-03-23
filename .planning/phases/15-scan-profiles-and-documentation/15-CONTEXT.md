# Phase 15: Scan Profiles and Documentation - Context

**Gathered:** 2026-03-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Named scan presets that save specific scanner configurations, selectable when triggering scans via API or dashboard. Plus bilingual documentation update covering all v1.0.2 features (RBAC, scanner config UI, DAST, scan profiles) across 5 languages (EN, RU, FR, ES, IT).

Requirements: CONF-04, CONF-05, INFRA-04

</domain>

<decisions>
## Implementation Decisions

### Profile storage
- Profiles stored in config.yml under a new `profiles:` top-level section
- Consistent with config.yml as single source of truth (Phase 14 decision)
- Each profile has: name (key), description, and a scanners map with per-scanner overrides
- Profile scanners map can override enabled state AND per-scanner settings (timeout, extra_args)
- Unlisted scanners are disabled — profile is an explicit allowlist, only listed scanners run
- Soft limit of 10 profiles (matches token soft limit pattern from Phase 12)

### Profile selection (API)
- Optional `profile` string field added to ScanRequest schema
- If omitted, base config.yml scanners section applies (implicit default — no special "default" profile)
- If provided, must match a profile name in config.yml or return 400
- Profiles work with DAST scans too — a "dast_only" profile listing just Nuclei is valid
- Scan result records which profile was used (profile_name field on ScanResult) for history/reports

### Profile selection (Dashboard)
- Dropdown selector on the scan trigger form, above the Start Scan button
- Lists all profile names + "(No profile)" option as default
- Profile name shown in scan history table

### Profile management UI
- Third tab "Profiles" on existing scanners configuration page (alongside "Cards" and "YAML Editor")
- Profile cards in a grid, each showing: name, description, scanner names as small badge tags
- "New Profile" button creates inline expanded form (same pattern as scanner card expand in Phase 14)
- Edit form shows: name input, description input, checklist of all 13 scanners with toggle + optional timeout override per scanner
- Save and Cancel buttons at bottom of inline form
- Admin-only access (consistent with scanners page)

### Documentation
- Update existing doc files — no new files created
- admin-guide.md: RBAC setup (users, roles, tokens), scanner configuration UI, scan profiles management
- user-guide.md: using scan profiles, DAST scanning (target URLs), dashboard login
- api.md: authentication (Bearer tokens), profile endpoints, scanner config endpoints, DAST scan trigger
- Full translation to all 5 languages (EN, RU, FR, ES, IT) — same content depth in each
- Text/markdown only — no screenshots or ASCII diagrams (consistent with existing docs)

### Claude's Discretion
- Profile CRUD API endpoint design (URL structure, request/response schemas)
- Profile validation logic (e.g., must have at least one scanner enabled)
- Exact profile card CSS styling
- Tab switching implementation for the third tab
- Doc section ordering and heading structure within existing files
- How to handle profile deletion when a scan is in progress using that profile

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scanner configuration (profiles extend this)
- `src/scanner/config.py` — Settings/ScannerToolConfig Pydantic models, YAML loading — profiles need new Pydantic model here
- `config.yml` — Current config structure, profiles section will be added here
- `config.yml.example` — Must be updated with example profiles
- `src/scanner/adapters/registry.py` — ScannerRegistry, get_enabled_adapters() — profile override point

### Scan trigger (profile selection integration)
- `src/scanner/api/schemas.py` — ScanRequest model — add profile field here
- `src/scanner/api/scans.py` — trigger_scan endpoint — apply profile overrides here
- `src/scanner/schemas/scan.py` — ScanResultSchema — add profile_name field

### Dashboard (profile UI)
- `src/scanner/dashboard/templates/scanners.html.j2` — Add Profiles tab here (existing Cards + YAML Editor tabs)
- `src/scanner/dashboard/router.py` — Dashboard routes, admin guards
- `src/scanner/dashboard/auth.py` — _get_dashboard_user for role checking

### Existing patterns to follow
- `.planning/phases/14-scanner-configuration-ui/14-CONTEXT.md` — Card grid pattern, tab switching, CodeMirror integration, inline expand/collapse
- `.planning/phases/12-rbac-foundation/12-CONTEXT.md` — Admin-only access, token soft limit pattern

### Documentation
- `docs/en/admin-guide.md` — Add RBAC, scanner config, profiles sections
- `docs/en/user-guide.md` — Add profiles, DAST, login sections
- `docs/en/api.md` — Add auth, profile, scanner config, DAST endpoints
- `docs/{ru,fr,es,it}/` — Same files, full translation

### Requirements
- `.planning/REQUIREMENTS.md` — CONF-04, CONF-05, INFRA-04

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ScannerRegistry.all_scanners_info()` — returns all scanner metadata, usable for profile edit form checkbox list
- `ScannerToolConfig` Pydantic model — per-scanner schema (enabled, timeout, extra_args) — profile scanner overrides mirror this
- `Settings` Pydantic model with `YamlConfigSettingsSource` — extend with profiles section
- Dashboard scanners.html.j2 — tab structure (Cards/YAML Editor) already implemented, add third tab
- Card grid CSS from Phase 14 — reusable for profile cards
- Inline expand/collapse pattern from scanner card settings — reuse for profile edit form

### Established Patterns
- Server-rendered Jinja2 templates, no JS framework (Phase 5)
- config.yml as single source of truth, read fresh on page load (Phase 14)
- PUT endpoint for config writes, raw text for YAML preservation (Phase 14)
- Admin-only guards via `_get_dashboard_user` + role check (Phase 12)
- Three-state toggle for scanner enabled (On/Auto/Off) — profiles use simpler checkbox (on/off)
- Accordion card pattern — only one card expanded at a time (Phase 14)

### Integration Points
- New `profiles:` section in Settings Pydantic model
- New profile field on ScanRequest + ScanResultSchema
- Profile override logic in scan trigger flow (between config load and scanner execution)
- Third "Profiles" tab on scanners.html.j2
- Profile CRUD API endpoints (GET/POST/PUT/DELETE)
- ScanResult DB model + history table column for profile_name
- Scan history template + report header to show profile name

</code_context>

<specifics>
## Specific Ideas

- Profile is an explicit allowlist — unlisted scanners don't run, making "quick scan" truly quick
- Scanner names as badge tags on profile cards — at-a-glance understanding of what's in each profile
- Inline edit form mirrors the scanner card expand pattern from Phase 14 — consistent UX
- Profile name tracked in scan results — enables comparing results across different scan configurations

</specifics>

<deferred>
## Deferred Ideas

- Config version history / undo — noted in Phase 14, still deferred
- Config backup before overwrite — noted in Phase 14, still deferred
- Profile import/export — could be useful for sharing profiles across instances
- Profile-level quality gate overrides — profiles could have different fail_on thresholds

</deferred>

---

*Phase: 15-scan-profiles-and-documentation*
*Context gathered: 2026-03-23*
