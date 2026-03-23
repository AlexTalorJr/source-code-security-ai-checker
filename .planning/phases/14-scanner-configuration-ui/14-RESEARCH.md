# Phase 14: Scanner Configuration UI - Research

**Researched:** 2026-03-23
**Domain:** Dashboard UI (server-rendered Jinja2), Config file read/write API, CodeMirror YAML editor
**Confidence:** HIGH

## Summary

Phase 14 adds a scanner configuration dashboard page with two tabs: a visual card grid for toggling/editing individual scanner settings, and a CodeMirror 5 YAML editor for full config.yml editing. The implementation builds on established patterns from the existing dashboard (Jinja2 templates, `_get_dashboard_user` auth, CSS custom properties from `base.html.j2`) and the existing scanner registry (`ScannerRegistry.all_scanners_info()`).

The primary technical challenges are: (1) config.yml read/write with proper YAML round-tripping (preserving comments requires `ruamel.yaml` or accepting comment loss with PyYAML), (2) Pydantic schema validation of arbitrary YAML input before saving, and (3) client-side JavaScript for tab switching, card expand/collapse, three-state toggle, and CodeMirror integration -- all without a JS framework (established Phase 5 decision).

A detailed UI-SPEC already exists at `14-UI-SPEC.md` covering visual design, interaction contracts, and component specifications. The planner should treat the UI-SPEC as the authoritative visual/interaction reference.

**Primary recommendation:** Build 3 API endpoints (GET config, PATCH scanner settings, PUT full YAML) plus 1 dashboard template with vanilla JS. Use PyYAML for config read/write (comments are not preserved but acceptable since config.yml.example serves as the documented reference). Validate all writes through the existing `ScannerSettings` Pydantic model before writing to disk.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Card grid layout, 2-3 columns -- each scanner as a card
- Card shows: scanner name (title), three-state toggle (On / Auto / Off), language tags, status badge (green/red)
- All scanners in one mixed grid -- Nuclei gets a "DAST" badge, others are implicitly SAST
- No separate DAST/SAST sections
- Click a scanner card to expand inline -- reveals timeout input, extra_args field
- No separate settings page or modal -- all editing happens in-place
- Timeout: simple number input with min=30, max=900 seconds, validation on save
- Extra args: single text input, space-separated, with syntax validation before save (check for balanced quotes, no empty args)
- Save button inside the expanded card
- CodeMirror 5 via CDN (decided in v1.0.2 research -- no build step)
- Shows full config.yml -- not limited to scanners section
- Lives as a tab on the scanners config page: "Cards" tab (visual) and "YAML Editor" tab (CodeMirror)
- Validation before save: YAML syntax check + Pydantic schema validation against Settings model
- Shows specific validation errors (e.g., "scanners.semgrep.timeout must be integer")
- Save writes directly to config.yml file on disk
- Hot-reload: app reloads settings on next scan trigger (lazy reload, no restart needed)
- Dashboard reads config.yml fresh on every page load -- manual file edits are immediately visible
- Card UI and YAML editor are independent -- both read/write config.yml directly, switching tabs reloads from file
- config.yml remains the single source of truth (no database storage of config)

### Claude's Discretion
- Exact card CSS styling, spacing, colors
- Three-state toggle CSS implementation
- CodeMirror theme and keybindings
- API endpoint design for config read/write
- How to handle concurrent save conflicts (if any)
- Tab switching implementation (JS or server-side)

### Deferred Ideas (OUT OF SCOPE)
- Scan profiles (CONF-04, CONF-05) -- Phase 15
- Config version history / undo -- future consideration
- Config backup before overwrite -- could be useful but not in scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CONF-01 | Admin can enable/disable individual scanners from the dashboard | Three-state toggle (On/Auto/Off) on scanner cards, PATCH API endpoint to update `enabled` field in config.yml, `ScannerToolConfig.enabled` supports `bool \| str` |
| CONF-02 | Admin can edit per-scanner settings (timeout, extra args) from the dashboard | Inline card expansion with timeout number input and extra_args text input, validated before save via API endpoint |
| CONF-03 | Admin can edit config.yml via web-based YAML editor with syntax highlighting | CodeMirror 5 YAML mode via CDN, PUT API endpoint for full YAML content, server-side Pydantic validation before write |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.135.1 | API endpoints for config CRUD | Already installed, project standard |
| Pydantic | 2.12.5 | Config validation via ScannerSettings model | Already installed, project standard |
| pydantic-settings[yaml] | 2.13.1 | YAML config loading with env var overrides | Already installed, used by ScannerSettings |
| PyYAML | 6.0.1 | YAML parsing and serialization for config read/write | Already installed (pydantic-settings dependency) |
| Jinja2 | 3.1.6+ | Server-rendered template for scanners page | Already installed, project standard |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| CodeMirror 5 | 5.65.18 | YAML editor with syntax highlighting | CDN-loaded in template, no pip install |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| PyYAML (yaml.dump) | ruamel.yaml | Preserves YAML comments but not installed, adds dependency. PyYAML is acceptable since comments are documented in config.yml.example |
| CodeMirror 5 CDN | CodeMirror 6 | CM6 is modular/newer but requires build step. CM5 CDN is decided and fits no-build-step constraint |

**Installation:**
```bash
# No new packages needed -- all dependencies already installed
# CodeMirror 5 loaded via CDN in template
```

## Architecture Patterns

### Recommended Project Structure
```
src/scanner/
├── api/
│   ├── scanners.py         # EXTEND: add config read/write endpoints
│   └── ...
├── dashboard/
│   ├── router.py           # EXTEND: add /scanners route (admin-only)
│   └── templates/
│       ├── base.html.j2    # MODIFY: add "Scanners" nav link
│       └── scanners.html.j2  # NEW: scanner config page with tabs
├── config.py               # READ: ScannerSettings, ScannerToolConfig models
└── adapters/
    └── registry.py         # READ: ScannerRegistry.all_scanners_info()
```

### Pattern 1: Config Read/Write via YAML File
**What:** Read config.yml with PyYAML, validate with Pydantic, write back with PyYAML.
**When to use:** All config read/write operations in the new API endpoints.
**Example:**
```python
import yaml
import os
from scanner.config import ScannerSettings

def read_config_yaml(config_path: str) -> dict:
    """Read raw YAML dict from config file."""
    if not os.path.exists(config_path):
        return {}
    with open(config_path) as f:
        return yaml.safe_load(f) or {}

def write_config_yaml(config_path: str, data: dict) -> None:
    """Write dict to config.yml as YAML."""
    with open(config_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

def validate_config(data: dict) -> list[str]:
    """Validate config dict against ScannerSettings Pydantic model.
    Returns list of validation error strings (empty = valid)."""
    from pydantic import ValidationError
    try:
        ScannerSettings(**data)
        return []
    except ValidationError as e:
        return [f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}" for err in e.errors()]
```

### Pattern 2: Dashboard Route with Admin Guard
**What:** Follow existing dashboard route pattern with `_get_dashboard_user` + `_require_dashboard_role`.
**When to use:** The new `/dashboard/scanners` route.
**Example:**
```python
@router.get("/scanners", response_class=HTMLResponse)
async def scanners_page(request: Request):
    """Render scanner configuration page (admin only)."""
    user = await _get_dashboard_user(request)
    check = _require_dashboard_role(user, "admin")
    if check:
        return check

    # Load scanner info for card rendering
    settings = request.app.state.settings
    registry = ScannerRegistry(settings.scanners)
    scanners = registry.all_scanners_info()

    template = _jinja_env.get_template("scanners.html.j2")
    return HTMLResponse(template.render(
        scanners=scanners,
        user=user,
        active_page="scanners",
    ))
```

### Pattern 3: Lazy Config Reload
**What:** Dashboard reads config.yml fresh on each page load. Scanner registry rebuilds from fresh settings on next scan trigger.
**When to use:** After config save -- no app restart needed.
**Implementation approach:**
- Dashboard page loads: read config.yml fresh, build registry, render
- API config endpoints: read config.yml fresh for GET, write to file for PUT/PATCH
- Scan trigger: `ScannerSettings()` constructor re-reads config.yml (already the behavior in `ScanQueue.worker`)
- `app.state.settings` is NOT updated on config save -- it was set at startup. The lazy reload happens because scan orchestration creates fresh settings.

**Critical insight:** The existing `app.state.settings` is loaded once at startup (in `lifespan`). For the dashboard to show current config, it must read the YAML file directly rather than using `app.state.settings`. For scan execution, `ScannerSettings()` is constructed fresh in the scan queue worker, so config changes take effect on the next scan.

### Pattern 4: API Endpoint Design (Claude's Discretion)
**Recommended endpoints:**
```
GET  /api/config              # Read full config as JSON (admin only)
GET  /api/config/yaml         # Read raw config.yml content as text (admin only)
PATCH /api/config/scanners/{name}  # Update single scanner settings (admin only)
PUT  /api/config/yaml         # Write full config.yml from raw YAML text (admin only)
```

All endpoints use `require_role(Role.ADMIN)` dependency from `scanner.api.auth`.

### Anti-Patterns to Avoid
- **Storing config in database alongside config.yml:** Creates two sources of truth. config.yml is the single source of truth (locked decision).
- **Updating `app.state.settings` on config save:** This would bypass the YAML file as source of truth. Dashboard must always read from file.
- **Using `ruamel.yaml` for comment preservation:** Not installed, adds complexity. Comments in config.yml.example serve as documentation.
- **Building a SPA or using a JS framework:** Project uses server-rendered Jinja2 with vanilla JS (Phase 5 decision).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML parsing | Custom parser | `yaml.safe_load()` / `yaml.dump()` | Edge cases with YAML spec |
| YAML syntax highlighting | Custom highlighter | CodeMirror 5 YAML mode | Mature, battle-tested |
| Config validation | Field-by-field checks | `ScannerSettings(**data)` Pydantic model | Already defines all fields with types/defaults |
| Extra args validation | Complex regex | `shlex.split()` for balanced quote checking | Standard library, handles shell quoting |
| Three-state toggle | Radio buttons with custom styling | Segmented button group with CSS | Simple HTML buttons with active state |

**Key insight:** The Pydantic model `ScannerSettings` already defines the complete schema for config validation. Don't re-implement validation logic -- instantiate the model and catch `ValidationError`.

## Common Pitfalls

### Pitfall 1: Config File Path Resolution
**What goes wrong:** Hardcoding `config.yml` path instead of respecting `SCANNER_CONFIG_PATH` env var.
**Why it happens:** The env var is only referenced in `ScannerSettings.settings_customise_sources()`.
**How to avoid:** Always resolve path via `os.environ.get("SCANNER_CONFIG_PATH", "config.yml")`. Create a helper function used by all endpoints.
**Warning signs:** Tests pass locally but fail in Docker where config path differs.

### Pitfall 2: YAML Write Clobbers Non-Scanner Config
**What goes wrong:** Reading only the `scanners` section, modifying it, then writing back -- losing `ai`, `gate`, `notifications` sections.
**Why it happens:** Card UI only edits scanner settings, tempting a partial read/write.
**How to avoid:** Always read the FULL config dict, modify the relevant keys, write back the full dict.
**Warning signs:** Missing config sections after saving scanner settings from the card UI.

### Pitfall 3: ScannerSettings Constructor Side Effects
**What goes wrong:** Using `ScannerSettings()` for validation in API endpoints triggers env var reading and config file loading.
**Why it happens:** `ScannerSettings` is a `BaseSettings` subclass that reads from multiple sources on construction.
**How to avoid:** For validation-only, pass the data as init kwargs to override file/env sources: `ScannerSettings(**data)` where `data` is the full config dict. This works because init values have highest priority. Alternatively, validate using `ScannerSettings.model_validate(data)`.
**Warning signs:** Validation returns different results than expected because env vars override the submitted data.

### Pitfall 4: Extra Args Injection via Config
**What goes wrong:** Malicious extra_args values like `; rm -rf /` get written to config and later passed to subprocess.
**Why it happens:** Extra args are passed to scanner CLI tools via subprocess.
**How to avoid:** Validate extra_args format (balanced quotes, starts with `-`), and ensure the scanner adapters use `subprocess.run()` with list args (not shell=True). Current adapters already use list args.
**Warning signs:** No validation on extra_args content.

### Pitfall 5: Race Condition Between Card Save and YAML Save
**What goes wrong:** Admin opens card tab, opens YAML tab in another browser tab, saves from both -- one overwrites the other.
**Why it happens:** No locking on config.yml writes.
**How to avoid:** Acceptable risk per CONTEXT.md ("single-admin expected usage"). Tab switching reloads fresh data. No locking mechanism needed for v1.0.2.
**Warning signs:** This is a known accepted risk, not a bug.

### Pitfall 6: PyYAML `yaml.dump()` Output Formatting
**What goes wrong:** `yaml.dump()` with default settings produces awkward output: quoted strings, sorted keys, flow-style lists.
**Why it happens:** PyYAML defaults are not human-friendly.
**How to avoid:** Use `yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)`.
**Warning signs:** Lists rendered as `[item1, item2]` instead of multi-line, keys reordered alphabetically.

## Code Examples

### Config File Path Helper
```python
import os

def get_config_path() -> str:
    """Resolve config.yml path from env var or default."""
    return os.environ.get("SCANNER_CONFIG_PATH", "config.yml")
```

### YAML Read/Write with Validation
```python
import yaml
from pydantic import ValidationError
from scanner.config import ScannerSettings

def read_config() -> dict:
    path = get_config_path()
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}

def write_config(data: dict) -> None:
    path = get_config_path()
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

def validate_config_data(data: dict) -> list[str]:
    """Validate against ScannerSettings. Returns error strings."""
    try:
        ScannerSettings(**data)
        return []
    except ValidationError as e:
        return [
            f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}"
            for err in e.errors()
        ]
```

### PATCH Scanner Settings Endpoint
```python
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from scanner.api.auth import require_role, Role

class ScannerSettingsUpdate(BaseModel):
    enabled: bool | str | None = None
    timeout: int | None = None
    extra_args: list[str] | None = None

@router.patch("/config/scanners/{scanner_name}")
async def update_scanner_config(
    scanner_name: str,
    update: ScannerSettingsUpdate,
    request: Request,
    user = Depends(require_role(Role.ADMIN)),
):
    config = read_config()
    scanners = config.get("scanners", {})
    if scanner_name not in scanners:
        raise HTTPException(404, f"Scanner '{scanner_name}' not found in config")

    if update.enabled is not None:
        scanners[scanner_name]["enabled"] = update.enabled
    if update.timeout is not None:
        if not (30 <= update.timeout <= 900):
            raise HTTPException(422, "Timeout must be between 30 and 900")
        scanners[scanner_name]["timeout"] = update.timeout
    if update.extra_args is not None:
        scanners[scanner_name]["extra_args"] = update.extra_args

    errors = validate_config_data(config)
    if errors:
        raise HTTPException(422, detail=errors)

    write_config(config)
    return {"status": "ok", "scanner": scanner_name}
```

### Extra Args Validation (Client-Side)
```javascript
function validateExtraArgs(value) {
    if (!value.trim()) return { valid: true, args: [] };

    // Check balanced quotes
    let singleQuotes = (value.match(/'/g) || []).length;
    let doubleQuotes = (value.match(/"/g) || []).length;
    if (singleQuotes % 2 !== 0) return { valid: false, error: "Unbalanced single quotes" };
    if (doubleQuotes % 2 !== 0) return { valid: false, error: "Unbalanced double quotes" };

    // Split respecting quotes and check for empty segments
    let args = value.trim().split(/\s+/).filter(a => a.length > 0);
    if (args.length === 0) return { valid: false, error: "No arguments provided" };

    return { valid: true, args: args };
}
```

### CodeMirror 5 CDN Integration
```html
<!-- In head_extra block -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.18/codemirror.min.css">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.18/theme/material-darker.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.18/codemirror.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.18/mode/yaml/yaml.min.js"></script>

<script>
// Initialize CodeMirror on the textarea
var editor = CodeMirror.fromTextArea(document.getElementById("yaml-editor"), {
    mode: "yaml",
    theme: "material-darker",
    lineNumbers: true,
    tabSize: 2,
    indentWithTabs: false,
});
editor.setSize(null, "60vh");

// Debounced validation on change
let validateTimer;
editor.on("change", function() {
    clearTimeout(validateTimer);
    validateTimer = setTimeout(validateYaml, 300);
});
</script>
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Editing config.yml by hand + restart | Dashboard UI + lazy reload | Phase 14 | Admin UX improvement, no restart needed |
| `app.state.settings` as runtime source | config.yml as single source, fresh read per operation | Phase 14 | Consistent behavior between dashboard and scan execution |

**Deprecated/outdated:**
- None specific to this phase. All libraries are current.

## Open Questions

1. **PyYAML comment preservation**
   - What we know: PyYAML `yaml.dump()` strips comments. `ruamel.yaml` preserves them but is not installed.
   - What's unclear: Whether users care about losing inline comments from config.yml when saving via UI.
   - Recommendation: Accept comment loss. config.yml.example serves as documented reference. If user demand arises, `ruamel.yaml` can be added later.

2. **Lazy reload scope**
   - What we know: Dashboard reads fresh from file. Scan queue creates fresh `ScannerSettings()` per scan.
   - What's unclear: Whether `app.state.settings` should also be refreshed (for other code that reads `request.app.state.settings`).
   - Recommendation: Do NOT update `app.state.settings` on save. Document that config changes affect next scan trigger. Other uses of `app.state.settings` (JWT secret, db_path) should not change at runtime.

3. **ScannerSettings validation with env var overrides**
   - What we know: `ScannerSettings(**data)` will still read env vars because of BaseSettings behavior.
   - What's unclear: Whether this causes validation to pass for data that would fail without env vars.
   - Recommendation: For pure validation, use `ScannerSettings.model_validate(data)` or construct with explicit init overrides. Test this behavior.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 + pytest-asyncio 1.3.0 |
| Config file | `pyproject.toml` ([tool.pytest.ini_options]) |
| Quick run command | `python -m pytest tests/phase_14/ -x -q` |
| Full suite command | `python -m pytest tests/ -x -q` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CONF-01 | Admin toggles scanner enabled state via API, persists to config.yml | integration | `python -m pytest tests/phase_14/test_scanner_toggle.py -x` | No -- Wave 0 |
| CONF-01 | Non-admin gets 403 on toggle endpoint | integration | `python -m pytest tests/phase_14/test_scanner_toggle.py::test_non_admin_forbidden -x` | No -- Wave 0 |
| CONF-02 | Admin edits timeout + extra_args, persists to config.yml | integration | `python -m pytest tests/phase_14/test_scanner_settings.py -x` | No -- Wave 0 |
| CONF-02 | Timeout validation rejects out-of-range values | unit | `python -m pytest tests/phase_14/test_scanner_settings.py::test_timeout_validation -x` | No -- Wave 0 |
| CONF-02 | Extra args validation rejects malformed input | unit | `python -m pytest tests/phase_14/test_scanner_settings.py::test_extra_args_validation -x` | No -- Wave 0 |
| CONF-03 | Admin saves full YAML via PUT endpoint, validated and persisted | integration | `python -m pytest tests/phase_14/test_yaml_editor.py -x` | No -- Wave 0 |
| CONF-03 | Invalid YAML returns 422 with error details | integration | `python -m pytest tests/phase_14/test_yaml_editor.py::test_invalid_yaml -x` | No -- Wave 0 |
| CONF-03 | Pydantic validation errors returned for structurally valid but schema-invalid YAML | integration | `python -m pytest tests/phase_14/test_yaml_editor.py::test_schema_validation -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/phase_14/ -x -q`
- **Per wave merge:** `python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/phase_14/__init__.py` -- package init
- [ ] `tests/phase_14/conftest.py` -- shared fixtures (reuse Phase 12 pattern: test_env, auth_client, get_admin_token + add config.yml fixture)
- [ ] `tests/phase_14/test_scanner_toggle.py` -- CONF-01 toggle tests
- [ ] `tests/phase_14/test_scanner_settings.py` -- CONF-02 settings tests
- [ ] `tests/phase_14/test_yaml_editor.py` -- CONF-03 YAML editor tests

## Sources

### Primary (HIGH confidence)
- `src/scanner/config.py` -- ScannerSettings and ScannerToolConfig Pydantic models (direct code inspection)
- `src/scanner/adapters/registry.py` -- ScannerRegistry.all_scanners_info() (direct code inspection)
- `src/scanner/dashboard/router.py` -- Dashboard route patterns, auth guards (direct code inspection)
- `src/scanner/dashboard/templates/base.html.j2` -- CSS custom properties, nav structure (direct code inspection)
- `src/scanner/api/scanners.py` -- Existing scanner listing endpoint (direct code inspection)
- `src/scanner/api/auth.py` -- get_current_user, require_role, Role enum (direct code inspection)
- `src/scanner/main.py` -- App factory, lifespan, settings loading (direct code inspection)
- `config.yml.example` -- Full config structure (direct code inspection)
- `14-UI-SPEC.md` -- Visual/interaction design contract (project artifact)
- `14-CONTEXT.md` -- User decisions and constraints (project artifact)
- `pyproject.toml` -- Dependencies and test configuration (direct inspection)
- Installed package versions verified via `pip show` (PyYAML 6.0.1, pydantic 2.12.5, pydantic-settings 2.13.1, FastAPI 0.135.1)

### Secondary (MEDIUM confidence)
- CodeMirror 5 CDN availability at cdnjs.cloudflare.com -- well-known CDN, version 5.65.18 is the final CM5 release

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already installed and verified, no new dependencies
- Architecture: HIGH -- follows established project patterns (Jinja2 templates, FastAPI routes, Pydantic models)
- Pitfalls: HIGH -- identified from direct code analysis of config loading, YAML handling, and auth patterns
- Validation: HIGH -- test patterns established in Phase 12/13, same conftest approach applies

**Research date:** 2026-03-23
**Valid until:** 2026-04-22 (stable -- no fast-moving dependencies)
