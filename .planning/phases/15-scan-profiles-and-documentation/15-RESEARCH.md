# Phase 15: Scan Profiles and Documentation - Research

**Researched:** 2026-03-23
**Domain:** Config-based scan profiles, CRUD API, dashboard UI, multilingual documentation
**Confidence:** HIGH

## Summary

Phase 15 adds named scan profiles to config.yml and updates bilingual documentation across 5 languages. The scan profiles feature is a natural extension of the existing config.yml-as-single-source-of-truth pattern established in Phase 14. Profiles are stored as a `profiles:` top-level section in config.yml, selected via API/dashboard when triggering scans, and recorded on ScanResult for history tracking.

The implementation touches four domains: (1) Pydantic model extension for profiles in `config.py`, (2) Profile CRUD API endpoints in a new `api/profiles.py`, (3) Dashboard UI additions -- a third "Profiles" tab on scanners.html.j2 and a profile dropdown on the scan trigger form, (4) Documentation updates to admin-guide.md, user-guide.md, and api.md across EN/RU/FR/ES/IT.

**Primary recommendation:** Build profiles as a thin config.yml layer that overrides the base scanners map at scan-trigger time. Reuse all existing patterns (read_config/write_config from api/config.py, card grid CSS, inline expand, admin-only guards).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Profiles stored in config.yml under a new `profiles:` top-level section
- Consistent with config.yml as single source of truth (Phase 14 decision)
- Each profile has: name (key), description, and a scanners map with per-scanner overrides
- Profile scanners map can override enabled state AND per-scanner settings (timeout, extra_args)
- Unlisted scanners are disabled -- profile is an explicit allowlist, only listed scanners run
- Soft limit of 10 profiles (matches token soft limit pattern from Phase 12)
- Optional `profile` string field added to ScanRequest schema
- If omitted, base config.yml scanners section applies (implicit default -- no special "default" profile)
- If provided, must match a profile name in config.yml or return 400
- Profiles work with DAST scans too -- a "dast_only" profile listing just Nuclei is valid
- Scan result records which profile was used (profile_name field on ScanResult) for history/reports
- Dropdown selector on the scan trigger form, above the Start Scan button
- Lists all profile names + "(No profile)" option as default
- Profile name shown in scan history table
- Third tab "Profiles" on existing scanners configuration page (alongside "Cards" and "YAML Editor")
- Profile cards in a grid, each showing: name, description, scanner names as small badge tags
- "New Profile" button creates inline expanded form (same pattern as scanner card expand in Phase 14)
- Edit form shows: name input, description input, checklist of all 13 scanners with toggle + optional timeout override per scanner
- Save and Cancel buttons at bottom of inline form
- Admin-only access (consistent with scanners page)
- Update existing doc files -- no new files created
- admin-guide.md: RBAC setup (users, roles, tokens), scanner configuration UI, scan profiles management
- user-guide.md: using scan profiles, DAST scanning (target URLs), dashboard login
- api.md: authentication (Bearer tokens), profile endpoints, scanner config endpoints, DAST scan trigger
- Full translation to all 5 languages (EN, RU, FR, ES, IT) -- same content depth in each
- Text/markdown only -- no screenshots or ASCII diagrams (consistent with existing docs)

### Claude's Discretion
- Profile CRUD API endpoint design (URL structure, request/response schemas)
- Profile validation logic (e.g., must have at least one scanner enabled)
- Exact profile card CSS styling
- Tab switching implementation for the third tab
- Doc section ordering and heading structure within existing files
- How to handle profile deletion when a scan is in progress using that profile

### Deferred Ideas (OUT OF SCOPE)
- Config version history / undo
- Config backup before overwrite
- Profile import/export
- Profile-level quality gate overrides
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CONF-04 | Admin can create and save named scan profiles (e.g. "Quick scan", "Full audit") | Profile Pydantic model, CRUD API endpoints, Profiles tab UI, config.yml persistence |
| CONF-05 | User can select a scan profile when triggering a scan via API or dashboard | ScanRequest.profile field, profile override logic in orchestrator, dropdown on scan trigger form |
| INFRA-04 | Bilingual documentation updated with RBAC, scanner config UI, and DAST features (EN, RU, FR, ES, IT) | Documentation structure analysis, existing doc files identified, content sections mapped |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pydantic | 2.x (existing) | Profile model validation | Already used for all config models |
| FastAPI | 0.x (existing) | Profile CRUD API endpoints | Already used for all API endpoints |
| PyYAML | (existing) | Read/write profiles in config.yml | Already used by api/config.py |
| Jinja2 | (existing) | Dashboard template rendering | Already used for all dashboard pages |
| SQLAlchemy | 2.x (existing) | ScanResult model extension | Already used for all ORM models |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| httpx | (existing) | Test client for async API tests | All phase 15 tests |
| pytest-asyncio | (existing) | Async test support | All async test functions |

No new dependencies required. Phase 15 builds entirely on existing stack.

## Architecture Patterns

### Recommended Project Structure
```
src/scanner/
  config.py              # Add ScanProfileConfig model
  api/
    config.py            # Add profile CRUD endpoints (or new profiles.py)
    schemas.py           # Add profile field to ScanRequest
    scans.py             # Pass profile_name to ScanResult on creation
  core/
    orchestrator.py      # Profile override logic before scanner execution
  models/
    scan.py              # Add profile_name column to ScanResult
  schemas/
    scan.py              # Add profile_name to ScanResultSchema
  dashboard/
    router.py            # Add profile data to scanners_page, start_scan
    templates/
      scanners.html.j2   # Add Profiles tab (third tab)
      history.html.j2    # Show profile_name in scan history
docs/
  {en,ru,fr,es,it}/
    admin-guide.md       # Add RBAC, scanner config UI, profiles sections
    user-guide.md        # Add profiles, DAST, login sections
    api.md               # Add auth, profile, scanner config, DAST endpoints
config.yml.example       # Add example profiles section
```

### Pattern 1: Profile Config Model (extends existing config.py pattern)
**What:** New Pydantic model for scan profiles stored in config.yml
**When to use:** Profile validation, serialization, config loading
**Example:**
```python
# In src/scanner/config.py
class ScanProfileScannerConfig(BaseModel):
    """Per-scanner override within a profile."""
    enabled: bool = True  # Profiles use simple bool (not three-state)
    timeout: int | None = None  # None = use base scanner timeout
    extra_args: list[str] | None = None  # None = use base scanner extra_args

class ScanProfileConfig(BaseModel):
    """Named scan profile configuration."""
    description: str = ""
    scanners: dict[str, ScanProfileScannerConfig] = {}
```

Then in `ScannerSettings`:
```python
# New field
profiles: dict[str, ScanProfileConfig] = {}

@field_validator("profiles", mode="before")
@classmethod
def _coerce_profile_dicts(cls, value: dict) -> dict:
    if not isinstance(value, dict):
        return value
    return {
        k: ScanProfileConfig(**v) if isinstance(v, dict) else v
        for k, v in value.items()
    }
```

### Pattern 2: Profile Override in Orchestrator
**What:** When a profile is selected, build a filtered scanners config before creating ScannerRegistry
**When to use:** In `run_scan()` when `profile_name` is provided
**Example:**
```python
# In orchestrator.py, before building ScannerRegistry
if profile_name:
    profile = settings.profiles.get(profile_name)
    if not profile:
        raise ValueError(f"Profile '{profile_name}' not found")
    # Build filtered scanners config: only scanners listed in profile
    filtered_scanners = {}
    for scanner_name, profile_scanner in profile.scanners.items():
        base = settings.scanners.get(scanner_name)
        if base is None:
            continue  # Skip unknown scanners in profile
        merged = ScannerToolConfig(
            adapter_class=base.adapter_class,
            languages=base.languages,
            enabled=True,  # Profile scanners are explicitly enabled
            timeout=profile_scanner.timeout or base.timeout,
            extra_args=profile_scanner.extra_args if profile_scanner.extra_args is not None else base.extra_args,
        )
        filtered_scanners[scanner_name] = merged
    registry = ScannerRegistry(filtered_scanners)
else:
    registry = ScannerRegistry(settings.scanners)
```

### Pattern 3: Profile CRUD API (follows existing config.py pattern)
**What:** REST endpoints for profile management
**When to use:** Admin creates/edits/deletes profiles
**Recommended URL structure:**
```
GET    /api/config/profiles          # List all profiles
POST   /api/config/profiles          # Create profile
GET    /api/config/profiles/{name}   # Get single profile
PUT    /api/config/profiles/{name}   # Update profile
DELETE /api/config/profiles/{name}   # Delete profile
```
Place in existing `src/scanner/api/config.py` (it already has config CRUD patterns) or create a new `profiles.py` router included under `/api/config`. Both approaches are valid; keeping in config.py is simpler since it already has `read_config()` and `write_config()` helpers.

### Pattern 4: Dashboard Scan Trigger with Profile Dropdown
**What:** Add profile selector to `start_scan` form
**When to use:** Dashboard scan trigger form
**Example:**
```python
# In dashboard/router.py start_scan endpoint, add Form parameter:
profile: str = Form(default="")

# Then pass to ScanResult creation:
scan = ScanResult(
    target_path=path or None,
    repo_url=repo_url or None,
    branch=branch or None,
    skip_ai=bool(skip_ai),
    profile_name=profile or None,  # NEW
    status="queued",
)
```

### Pattern 5: Third Tab on Scanners Page
**What:** Add "Profiles" tab to existing tab bar in scanners.html.j2
**When to use:** Profile management UI
**Implementation approach:**
- Add third button to `.tab-bar`: `<button class="tab-btn" data-tab="profiles" onclick="switchTab('profiles')">Profiles</button>`
- Add `<div id="tab-profiles">` with profile cards grid
- Extend `switchTab()` JavaScript to handle third tab (hide other panels, show profiles)
- Profile cards reuse `.scanner-card` CSS with badge tags for scanner names
- Inline edit form uses same expand/collapse pattern as scanner card settings

### Anti-Patterns to Avoid
- **Storing profiles in database:** Profiles belong in config.yml for consistency with Phase 14's config-as-truth pattern. Database storage would split config into two locations.
- **Profile as scanner filter after get_enabled_adapters:** The override must happen BEFORE ScannerRegistry is created, not after. Otherwise, auto-detection logic would still run for non-profile scanners.
- **Default profile magic:** No implicit "default" profile. When no profile is selected, base config.yml scanners apply. This avoids confusion about which config layer is active.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Config persistence | Custom file I/O | `read_config()`/`write_config()` from api/config.py | Already handles YAML serialization, path resolution |
| Config validation | Manual field checks | Pydantic model validation (`ScanProfileConfig`) | Consistent with all other config models |
| Admin access guards | Custom role checks | `require_role(Role.ADMIN)` for API, `_require_dashboard_role(user, "admin")` for dashboard | Established Phase 12 pattern |
| YAML editing | Profile-specific YAML endpoints | Existing YAML editor tab already handles full config | Profiles appear in YAML editor automatically when stored in config.yml |
| Card grid UI | New CSS grid system | Reuse `.scanner-grid` and `.scanner-card` CSS classes | Already styled and responsive |

## Common Pitfalls

### Pitfall 1: Profile Override Not Reaching DAST Mode
**What goes wrong:** The DAST code path in orchestrator.py has a separate branch that directly calls `registry.get_scanner_config("nuclei")` instead of going through `get_enabled_adapters()`. Profile override must work for both paths.
**Why it happens:** DAST mode was added in Phase 13 with a hardcoded Nuclei path, bypassing the normal registry flow.
**How to avoid:** When a profile is active, check if the profile includes nuclei for DAST mode. If profile doesn't include nuclei but target_url is provided, that's a validation error (400).
**Warning signs:** DAST scans ignore profile selection and always run Nuclei regardless.

### Pitfall 2: ScanResult Column Migration
**What goes wrong:** Adding `profile_name` column to ScanResult requires existing databases to be updated. The project uses `Base.metadata.create_all` which only creates missing tables, not missing columns on existing tables.
**Why it happens:** No Alembic migration system. `create_all` is idempotent for tables but doesn't add columns to existing tables.
**How to avoid:** Use `Column(..., nullable=True)` for the new column. Add a manual `ALTER TABLE` in the startup code or document that users need to delete/recreate the DB. Since this is a development-stage project, the simpler approach is to document the DB schema change. Alternatively, add startup migration logic that checks for the column and adds it.
**Warning signs:** `OperationalError: no such column: scans.profile_name` on existing installations.

### Pitfall 3: Config Validation Rejects Unknown Fields
**What goes wrong:** `ScannerSettings` has `extra="ignore"` which ignores unknown top-level fields, but `validate_config_data()` in api/config.py constructs a full `ScannerSettings.model_validate(data)`. If `profiles:` is added to config.yml before the `ScannerSettings` model is updated, validation will silently ignore it but won't persist properly.
**Why it happens:** The profiles field must be added to `ScannerSettings` model BEFORE any profile data is written to config.yml.
**How to avoid:** Add the `profiles` field to `ScannerSettings` in the same commit as the profile CRUD endpoints. The `extra="ignore"` means unknown fields won't cause errors, but they also won't be loaded.

### Pitfall 4: write_config() Clobbers Non-Scanner Data
**What goes wrong:** `write_config()` uses `yaml.dump()` which rewrites the entire config. Profile CRUD must use the same `read_config()` -> modify -> `write_config()` pattern as scanner settings to avoid losing other config sections.
**Why it happens:** Each write replaces the whole file.
**How to avoid:** Always read full config, modify only the profiles section, write back full config. This is the same pattern used by `update_scanner_config()`.

### Pitfall 5: Profile Name Conflicts with YAML Keys
**What goes wrong:** Profile names like "true", "false", "null", "on", "off" are interpreted as YAML booleans/null by PyYAML.
**Why it happens:** YAML 1.1 specification treats these as reserved values.
**How to avoid:** Validate profile names: alphanumeric + hyphens + underscores only. Reject names that are YAML reserved words. Apply same validation on API create/update endpoints.

### Pitfall 6: Documentation Translation Inconsistency
**What goes wrong:** Translated docs drift from English source, missing sections or having outdated content.
**Why it happens:** Manual translation across 5 languages is error-prone.
**How to avoid:** Write EN docs first as the canonical source. Then translate section-by-section. Verify all 5 language files have the same section headings (translated). Use a checklist to ensure parity.

## Code Examples

### Profile CRUD: Create Profile
```python
# In api/config.py (or new profiles.py)
class ProfileCreateRequest(BaseModel):
    name: str
    description: str = ""
    scanners: dict[str, dict] = {}  # scanner_name -> {timeout?, extra_args?}

@router.post("/profiles")
async def create_profile(
    body: ProfileCreateRequest,
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    config = read_config()
    profiles = config.get("profiles", {})

    if len(profiles) >= 10:
        raise HTTPException(status_code=400, detail="Maximum 10 profiles allowed")
    if body.name in profiles:
        raise HTTPException(status_code=409, detail=f"Profile '{body.name}' already exists")
    if not body.scanners:
        raise HTTPException(status_code=422, detail="Profile must have at least one scanner")

    # Validate profile name
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', body.name):
        raise HTTPException(status_code=422, detail="Profile name must be alphanumeric with hyphens/underscores only")

    profiles[body.name] = {
        "description": body.description,
        "scanners": body.scanners,
    }
    config["profiles"] = profiles
    write_config(config)
    return {"status": "ok", "profile": body.name}
```

### Profile Dropdown in Dashboard Template
```html
<!-- In scan trigger form (history.html.j2 or wherever the scan form lives) -->
<div class="form-group">
  <label for="profile">Scan Profile</label>
  <select name="profile" id="profile" class="form-input">
    <option value="">(No profile)</option>
    {% for name in profiles %}
    <option value="{{ name }}">{{ name }}</option>
    {% endfor %}
  </select>
</div>
```

### Profile Badge Tags on Cards
```html
<!-- Profile card in scanners.html.j2 profiles tab -->
<div class="scanner-card profile-card" data-profile="{{ name }}">
  <div class="card-title-row">
    <span class="card-title">{{ name }}</span>
  </div>
  {% if profile.description %}
  <div class="card-languages">{{ profile.description }}</div>
  {% endif %}
  <div class="profile-scanners" style="margin-top: 8px;">
    {% for scanner_name in profile.scanners %}
    <span class="badge badge--success" style="font-size: 11px; margin: 2px;">{{ scanner_name }}</span>
    {% endfor %}
  </div>
</div>
```

### Config.yml Profile Structure
```yaml
# Example profiles section in config.yml
profiles:
  quick_scan:
    description: "Fast scan with essential tools only"
    scanners:
      semgrep:
        timeout: 60
      gitleaks: {}
  full_audit:
    description: "Complete security audit with all tools"
    scanners:
      semgrep: {}
      cppcheck: {}
      gitleaks: {}
      trivy: {}
      checkov: {}
      psalm: {}
      bandit: {}
      gosec: {}
      brakeman: {}
      cargo_audit: {}
      nuclei: {}
  dast_only:
    description: "DAST scanning with Nuclei only"
    scanners:
      nuclei:
        timeout: 600
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| X-API-Key header auth | Bearer token auth (Phase 12) | Phase 12 | Docs must use Bearer tokens, not X-API-Key |
| No scanner config UI | Card grid + YAML editor (Phase 14) | Phase 14 | Profiles tab extends existing UI |
| SAST only | SAST + DAST via Nuclei (Phase 13) | Phase 13 | Docs must cover DAST target_url scanning |

**Deprecated/outdated in existing docs:**
- api.md still references `X-API-Key` header authentication (must be updated to Bearer token auth)
- user-guide.md references `X-API-Key` in examples (must update to Bearer tokens)
- api.md is missing: DAST target_url field, scanner config endpoints, token management endpoints, user management endpoints

## Open Questions

1. **Database column migration strategy**
   - What we know: `create_all` only creates new tables, not columns on existing tables
   - What's unclear: Best approach for existing installations
   - Recommendation: Add startup migration logic that executes `ALTER TABLE scans ADD COLUMN profile_name VARCHAR(200)` if column doesn't exist. This is lightweight and safe for SQLite.

2. **Profile deletion while scan in progress**
   - What we know: A scan stores profile_name on the ScanResult record at creation time
   - What's unclear: Whether to prevent deletion or allow it
   - Recommendation: Allow deletion. The profile_name string is already saved on ScanResult, so the scan continues with whatever scanners were resolved at start time. History shows the deleted profile name as a plain string.

3. **Orchestrator function signature**
   - What we know: `run_scan()` currently takes target_path, repo_url, branch, target_url, skip_ai, settings, progress_callback
   - What's unclear: Cleanest way to add profile_name parameter
   - Recommendation: Add `profile_name: str | None = None` parameter. Apply profile override early in the function, before the DAST/SAST branch.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio |
| Config file | pyproject.toml (existing) |
| Quick run command | `python -m pytest tests/phase_15/ -x -q` |
| Full suite command | `python -m pytest tests/ -x -q` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CONF-04a | Create profile via API persists to config.yml | unit | `python -m pytest tests/phase_15/test_profile_crud.py::test_create_profile -x` | Wave 0 |
| CONF-04b | Profile soft limit of 10 enforced | unit | `python -m pytest tests/phase_15/test_profile_crud.py::test_profile_limit -x` | Wave 0 |
| CONF-04c | Profile name validation rejects invalid names | unit | `python -m pytest tests/phase_15/test_profile_crud.py::test_invalid_name -x` | Wave 0 |
| CONF-04d | Update profile via API | unit | `python -m pytest tests/phase_15/test_profile_crud.py::test_update_profile -x` | Wave 0 |
| CONF-04e | Delete profile via API | unit | `python -m pytest tests/phase_15/test_profile_crud.py::test_delete_profile -x` | Wave 0 |
| CONF-04f | Non-admin cannot manage profiles | unit | `python -m pytest tests/phase_15/test_profile_crud.py::test_non_admin_rejected -x` | Wave 0 |
| CONF-05a | ScanRequest accepts profile field | unit | `python -m pytest tests/phase_15/test_profile_scan.py::test_scan_with_profile -x` | Wave 0 |
| CONF-05b | Invalid profile name returns 400 | unit | `python -m pytest tests/phase_15/test_profile_scan.py::test_scan_invalid_profile -x` | Wave 0 |
| CONF-05c | Profile overrides scanner selection | unit | `python -m pytest tests/phase_15/test_profile_scan.py::test_profile_scanner_override -x` | Wave 0 |
| CONF-05d | Profile name recorded on ScanResult | unit | `python -m pytest tests/phase_15/test_profile_scan.py::test_profile_recorded -x` | Wave 0 |
| INFRA-04 | Documentation files exist with required sections | smoke | `python -m pytest tests/phase_15/test_docs.py -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/phase_15/ -x -q`
- **Per wave merge:** `python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/phase_15/__init__.py` -- package init
- [ ] `tests/phase_15/conftest.py` -- shared fixtures (extend from phase_14 conftest pattern with profiles in TEST_CONFIG)
- [ ] `tests/phase_15/test_profile_crud.py` -- covers CONF-04
- [ ] `tests/phase_15/test_profile_scan.py` -- covers CONF-05
- [ ] `tests/phase_15/test_docs.py` -- covers INFRA-04 (verify doc files have required sections)

## Sources

### Primary (HIGH confidence)
- Project codebase: `src/scanner/config.py` -- ScannerSettings, ScannerToolConfig models (direct inspection)
- Project codebase: `src/scanner/api/config.py` -- read_config/write_config/validate_config_data patterns (direct inspection)
- Project codebase: `src/scanner/core/orchestrator.py` -- run_scan flow, DAST/SAST branching (direct inspection)
- Project codebase: `src/scanner/dashboard/router.py` -- scanners_page, start_scan, admin guards (direct inspection)
- Project codebase: `src/scanner/dashboard/templates/scanners.html.j2` -- tab structure, card grid, JS patterns (direct inspection)
- Project codebase: `src/scanner/models/scan.py` -- ScanResult ORM model (direct inspection)
- Project codebase: `src/scanner/api/schemas.py` -- ScanRequest model (direct inspection)
- Project codebase: `docs/{en,ru,fr,es,it}/` -- existing documentation structure (direct inspection)
- Project codebase: `tests/phase_14/` -- test patterns, conftest fixtures (direct inspection)
- Phase 15 CONTEXT.md -- all user decisions and canonical references

### Secondary (MEDIUM confidence)
- Pydantic v2 field_validator, model_validate -- well-established patterns used throughout project
- SQLAlchemy Column addition -- standard ORM pattern
- FastAPI router patterns -- consistent with existing project code

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies, all patterns established in prior phases
- Architecture: HIGH -- direct extension of Phase 14 patterns, all integration points clearly identified
- Pitfalls: HIGH -- identified from direct codebase inspection (DAST path, DB migration, YAML reserved words)

**Research date:** 2026-03-23
**Valid until:** 2026-04-23 (stable -- no external dependency changes)
