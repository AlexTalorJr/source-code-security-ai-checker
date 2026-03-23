# Phase 14: Scanner Configuration UI - Context

**Gathered:** 2026-03-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Admins can manage scanner settings from the dashboard without editing config files manually. Includes a visual scanner card grid with toggle/settings, a CodeMirror YAML editor for full config.yml, and config persistence via file write with lazy hot-reload. Scan profiles (CONF-04, CONF-05) are Phase 15 scope.

</domain>

<decisions>
## Implementation Decisions

### Scanner toggle page
- Card grid layout, 2-3 columns — each scanner as a card
- Card shows: scanner name (title), three-state toggle (On / Auto / Off), language tags, status badge (green/red)
- All scanners in one mixed grid — Nuclei gets a "DAST" badge, others are implicitly SAST
- No separate DAST/SAST sections

### Settings editor per scanner
- Click a scanner card to expand inline — reveals timeout input, extra_args field
- No separate settings page or modal — all editing happens in-place
- Timeout: simple number input with min=30, max=900 seconds, validation on save
- Extra args: single text input, space-separated, with syntax validation before save (check for balanced quotes, no empty args)
- Save button inside the expanded card

### YAML config editor
- CodeMirror 5 via CDN (decided in v1.0.2 research — no build step)
- Shows full config.yml — not limited to scanners section
- Lives as a tab on the scanners config page: "Cards" tab (visual) and "YAML Editor" tab (CodeMirror)
- Validation before save: YAML syntax check + Pydantic schema validation against Settings model
- Shows specific validation errors (e.g., "scanners.semgrep.timeout must be integer")

### Config persistence
- Save writes directly to config.yml file on disk
- Hot-reload: app reloads settings on next scan trigger (lazy reload, no restart needed)
- Dashboard reads config.yml fresh on every page load — manual file edits are immediately visible
- Card UI and YAML editor are independent — both read/write config.yml directly, switching tabs reloads from file
- config.yml remains the single source of truth (no database storage of config)

### Claude's Discretion
- Exact card CSS styling, spacing, colors
- Three-state toggle CSS implementation
- CodeMirror theme and keybindings
- API endpoint design for config read/write
- How to handle concurrent save conflicts (if any)
- Tab switching implementation (JS or server-side)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scanner configuration
- `src/scanner/config.py` — Settings/ScannerToolConfig Pydantic models, YAML loading, env var overrides
- `config.yml.example` — Full config structure with all scanner entries and defaults
- `src/scanner/adapters/registry.py` — ScannerRegistry, all_scanners_info() for card data

### Dashboard patterns
- `src/scanner/dashboard/templates/base.html.j2` — Dashboard base layout, nav structure, CSS custom properties
- `src/scanner/dashboard/templates/history.html.j2` — Table pattern reference
- `src/scanner/dashboard/router.py` — Dashboard route patterns, auth guards
- `src/scanner/dashboard/auth.py` — _get_dashboard_user for role checking

### API patterns
- `src/scanner/api/scanners.py` — Existing GET /scanners endpoint (read-only), ScannerInfo response model
- `src/scanner/api/auth.py` — get_current_user dependency, role enforcement

### RBAC
- `.planning/phases/12-rbac-foundation/12-CONTEXT.md` — Admin-only access decisions, dashboard auth flow

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ScannerRegistry.all_scanners_info()` — returns scanner name, status, enabled, languages, load_error — directly usable for card rendering
- `ScannerToolConfig` Pydantic model — defines per-scanner fields (enabled, timeout, extra_args, adapter_class, languages) — schema validation source
- `Settings` Pydantic model with `YamlConfigSettingsSource` — handles config.yml loading, can be reused for validation endpoint
- Dashboard base template with CSS custom properties — spacing, typography, color tokens already defined
- `_get_dashboard_user` — returns current user or redirects to login, already handles role checking

### Established Patterns
- Server-rendered Jinja2 templates with no JS framework (Phase 5 decision)
- Dashboard routes use `@router.get("/path")` with `_get_dashboard_user` dependency
- API routes use `get_current_user` with role-based Depends
- Config loaded via `pydantic_settings.YamlConfigSettingsSource` — reads config.yml at startup

### Integration Points
- New dashboard page: `src/scanner/dashboard/templates/scanners.html.j2` — extends base.html.j2
- New dashboard route in `src/scanner/dashboard/router.py` — admin-only guard
- New API endpoints for config CRUD — read config, update scanner settings, write full YAML
- Nav link in base.html.j2 — "Scanners" link, admin-only visibility
- CodeMirror 5 CSS/JS from CDN in the template

</code_context>

<specifics>
## Specific Ideas

- Three-state toggle (On / Auto / Off) is the centerpiece UX element — should feel intuitive, not confusing
- Card expand/collapse for inline settings editing should be smooth (no page reloads for editing)
- YAML editor validation should catch errors before save, not after restart

</specifics>

<deferred>
## Deferred Ideas

- Scan profiles (CONF-04, CONF-05) — Phase 15
- Config version history / undo — future consideration
- Config backup before overwrite — could be useful but not in scope

</deferred>

---

*Phase: 14-scanner-configuration-ui*
*Context gathered: 2026-03-23*
