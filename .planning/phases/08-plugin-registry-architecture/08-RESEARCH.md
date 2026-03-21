# Phase 8: Plugin Registry Architecture - Research

**Researched:** 2026-03-21
**Domain:** Python dynamic class loading, pydantic config modeling, plugin registry patterns
**Confidence:** HIGH

## Summary

Phase 8 replaces the hard-coded `ALL_ADAPTERS` list and `SCANNER_LANGUAGES` dict with a config-driven registry. Scanners will be registered entirely through `config.yml` entries containing an `adapter_class` field (full Python dotted path), `languages` list, and the existing `enabled`/`timeout`/`extra_args` fields. The orchestrator dynamically loads adapter classes via `importlib.import_module()` at startup, validates they are `ScannerAdapter` subclasses, and skips any that fail to load with a clear warning.

The project uses pydantic v2 (2.12.5) with pydantic-settings v2 (2.13.1) and YAML config loading via `YamlConfigSettingsSource`. The current `ScannersConfig` has 8 hard-coded per-scanner fields -- this must become a dynamic dict that accepts arbitrary scanner names. Pydantic v2's `model_config = ConfigDict(extra="allow")` or a `Dict[str, ScannerToolConfig]` field are the two viable approaches.

**Primary recommendation:** Use a `dict[str, ScannerToolConfig]` field on `ScannerSettings` (replacing the `ScannersConfig` class) where `ScannerToolConfig` gains `adapter_class: str` and `languages: list[str]` fields. The registry module uses `importlib.import_module()` to load classes, validates with `issubclass()`, and exposes loaded adapters as a list the orchestrator consumes.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Flat config structure: each scanner key gets `adapter_class`, `enabled`, `timeout`, `extra_args`, and `languages` fields
- `adapter_class` is a full Python module path (e.g., `scanner.adapters.semgrep.SemgrepAdapter`) -- resolved via importlib
- `languages` list determines which projects trigger the scanner in "auto" mode
- Empty or omitted `languages` = universal scanner (runs on all projects, like gitleaks)
- Scanner order in config is for human readability only -- all enabled scanners run in parallel via asyncio.gather
- Adding a scanner requires: (1) write a ScannerAdapter subclass, (2) add config.yml entry with adapter_class
- `adapter_class` is required for every scanner entry; missing it produces a clear warning and the scanner is skipped
- Registry validates at startup that loaded classes are ScannerAdapter subclasses -- fail fast with clear error if not
- New read-only `GET /api/scanners` endpoint listing all registered scanners with name, status, enabled, languages
- Bad `adapter_class` (typo, missing module): log WARNING, skip that scanner, app continues normally
- Failed-to-load scanners appear in `/api/scanners` with `status: "load_error"` and the error message
- Missing binary at runtime: same warn-and-skip behavior -- consistent with existing `_run_adapter` exception handling
- Clean break: `adapter_class` required in new format -- old configs without it get warnings and scanners skipped
- Default `config.yml` ships with `adapter_class` and `languages` for all 8 existing scanners
- `ScannersConfig` class replaced entirely with dynamic dict (no more hard-coded per-scanner fields)
- `ALL_ADAPTERS` list in `__init__.py` removed -- registry loads from config
- `SCANNER_LANGUAGES` dict in `language_detect.py` removed -- languages come from config.yml per scanner
- Config.yml is the single source of truth for scanner registration and language mapping

### Claude's Discretion
- Exact importlib loading mechanism and error message formatting
- How to structure the dynamic ScannersConfig (pydantic dict, extra='allow', or custom validator)
- Internal registry data structure (dict, list, dataclass)
- How `detect_languages()` and `should_enable_scanner()` adapt to config-driven languages
- Test structure and organization

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PLUG-01 | Scanner adapters can be registered via config.yml `adapter_class` field without code changes | importlib dynamic loading pattern, ScannerToolConfig extension, registry module design |
| PLUG-02 | Existing hard-coded ALL_ADAPTERS list migrated to config-driven registration | Config migration for all 8 scanners, ScannersConfig replacement with dynamic dict |
| PLUG-03 | Config validation warns on missing or invalid adapter_class references | importlib error handling patterns, registry validation at load time, /api/scanners error reporting |
| PLUG-04 | SCANNER_LANGUAGES mapping extended for new scanner-to-language associations | Per-scanner `languages` field in config, `should_enable_scanner()` refactor to read from config |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pydantic | 2.12.5 | Config model validation | Already in use, provides field validation and type coercion |
| pydantic-settings | 2.13.1 | YAML config loading with env var overrides | Already in use via YamlConfigSettingsSource |
| importlib (stdlib) | Python 3.12 | Dynamic class loading from dotted paths | Standard library, no dependencies, `import_module()` is the canonical approach |
| FastAPI | (already installed) | New `/api/scanners` endpoint | Already used for all API routes |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| logging (stdlib) | Python 3.12 | WARNING-level messages for load failures | All error reporting in registry |
| inspect (stdlib) | Python 3.12 | `issubclass()` validation | Validating loaded classes are ScannerAdapter subclasses |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| importlib.import_module | stevedore (entry_points) | Overkill for <20 plugins, adds dependency |
| importlib.import_module | directory auto-scanning | Implicit, harder to control, contradicts user decision for explicit config |
| dict[str, ScannerToolConfig] | ConfigDict(extra="allow") | extra="allow" loses type validation on dynamic fields |

**Installation:**
No new packages needed -- all libraries already installed.

## Architecture Patterns

### Recommended Project Structure
```
src/scanner/
├── adapters/
│   ├── __init__.py          # Simplified: exports ScannerAdapter, removes ALL_ADAPTERS
│   ├── base.py              # ScannerAdapter ABC (unchanged)
│   ├── registry.py          # NEW: ScannerRegistry class
│   ├── semgrep.py           # (unchanged)
│   ├── cppcheck.py          # (unchanged)
│   └── ...                  # (all existing adapters unchanged)
├── config.py                # ScannersConfig -> dict[str, ScannerToolConfig]
├── core/
│   ├── orchestrator.py      # Consumes registry instead of ALL_ADAPTERS
│   └── language_detect.py   # should_enable_scanner() reads from config
├── api/
│   ├── router.py            # Include new scanners router
│   └── scanners.py          # NEW: GET /api/scanners endpoint
```

### Pattern 1: importlib Dynamic Loading
**What:** Load adapter classes from dotted path strings at application startup
**When to use:** When class paths are specified in configuration files
**Example:**
```python
# Source: Python 3.12 stdlib importlib documentation
import importlib
import logging

logger = logging.getLogger(__name__)

def load_adapter_class(tool_name: str, adapter_class_path: str):
    """Load an adapter class from a dotted module path.

    Returns the class on success, or None on failure (with WARNING logged).
    """
    try:
        module_path, class_name = adapter_class_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        cls = getattr(module, class_name)
        return cls
    except (ImportError, AttributeError, ValueError) as exc:
        logger.warning(
            "Scanner '%s': failed to load adapter_class '%s': %s",
            tool_name, adapter_class_path, exc
        )
        return None
```

### Pattern 2: ScannerRegistry Dataclass
**What:** A registry object that holds loaded adapters and their load status
**When to use:** Central place for the orchestrator and API to query scanner state
**Example:**
```python
from dataclasses import dataclass, field

@dataclass
class RegisteredScanner:
    """A scanner entry in the registry."""
    name: str
    adapter_class_path: str
    adapter_class: type | None = None  # None if load failed
    enabled: bool | str = "auto"
    timeout: int = 180
    extra_args: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    load_error: str | None = None

    @property
    def status(self) -> str:
        if self.load_error:
            return "load_error"
        return "enabled" if self.enabled is True or self.enabled == "auto" else "disabled"

class ScannerRegistry:
    """Registry of all scanners loaded from config."""

    def __init__(self, scanners_config: dict[str, ScannerToolConfig]):
        self._scanners: dict[str, RegisteredScanner] = {}
        for name, config in scanners_config.items():
            self._register(name, config)

    def _register(self, name: str, config):
        entry = RegisteredScanner(
            name=name,
            adapter_class_path=config.adapter_class,
            enabled=config.enabled,
            timeout=config.timeout,
            extra_args=config.extra_args,
            languages=config.languages,
        )
        if not config.adapter_class:
            entry.load_error = "adapter_class is required"
            logger.warning("Scanner '%s': adapter_class is required, skipping", name)
        else:
            cls = load_adapter_class(name, config.adapter_class)
            if cls is None:
                entry.load_error = f"Failed to import {config.adapter_class}"
            elif not issubclass(cls, ScannerAdapter):
                entry.load_error = f"{config.adapter_class} is not a ScannerAdapter subclass"
                logger.warning("Scanner '%s': %s", name, entry.load_error)
            else:
                entry.adapter_class = cls
        self._scanners[name] = entry

    def get_enabled_adapters(self, detected_languages: set[str]) -> list[ScannerAdapter]:
        """Return instantiated adapters that should run for detected languages."""
        adapters = []
        for scanner in self._scanners.values():
            if scanner.adapter_class is None:
                continue
            if scanner.enabled is False:
                continue
            if scanner.enabled == "auto":
                if not self._should_enable(scanner, detected_languages):
                    continue
            adapters.append(scanner.adapter_class())
        return adapters

    def _should_enable(self, scanner: RegisteredScanner, detected_langs: set[str]) -> bool:
        if not scanner.languages:
            return True  # Universal scanner
        return bool(set(scanner.languages) & detected_langs)

    def all_scanners_info(self) -> list[dict]:
        """For /api/scanners endpoint."""
        return [
            {
                "name": s.name,
                "status": s.status,
                "enabled": s.enabled,
                "languages": s.languages,
                "load_error": s.load_error,
            }
            for s in self._scanners.values()
        ]
```

### Pattern 3: Dynamic ScannersConfig with pydantic
**What:** Replace hard-coded ScannersConfig fields with a dict-based model
**When to use:** To parse arbitrary scanner names from config.yml
**Example:**
```python
# Extend ScannerToolConfig with new fields
class ScannerToolConfig(BaseModel):
    adapter_class: str = ""
    enabled: bool | str = "auto"
    timeout: int = 180
    extra_args: list[str] = []
    languages: list[str] = []

# Replace ScannersConfig class with a dict field on ScannerSettings
class ScannerSettings(BaseSettings):
    # ... existing fields ...
    scanners: dict[str, ScannerToolConfig] = {}
```

**Important pydantic-settings note:** With pydantic-settings v2 and YAML source, a `dict[str, ScannerToolConfig]` field will automatically parse nested YAML keys into `ScannerToolConfig` instances. Each key under `scanners:` in config.yml becomes a dict key, and its nested fields are validated as `ScannerToolConfig`.

### Pattern 4: Config-driven language detection
**What:** Replace `SCANNER_LANGUAGES` and `UNIVERSAL_SCANNERS` constants with config-sourced data
**When to use:** In the refactored `should_enable_scanner()` function
**Example:**
```python
# language_detect.py -- refactored
def should_enable_scanner(
    tool_name: str,
    scanner_languages: list[str],
    detected_languages: set[str],
) -> bool:
    """Determine if a scanner should run based on detected languages.

    Universal scanners (empty languages list) always run.
    Other scanners run only if their target languages are detected.
    """
    if not scanner_languages:
        return True  # Universal scanner (e.g., gitleaks)
    return bool(set(scanner_languages) & detected_languages)
```

### Anti-Patterns to Avoid
- **Importing all adapter modules at startup unconditionally:** The registry should only import modules referenced in config. Do NOT keep the old-style `from scanner.adapters.X import XAdapter` imports in `__init__.py` for adapter discovery.
- **Silent failure on bad adapter_class:** Always log a WARNING with the scanner name and the specific error. Never silently skip.
- **Mixing hard-coded and dynamic loading:** Do not keep a fallback to `ALL_ADAPTERS`. Clean break as decided by user -- if `adapter_class` is missing, warn and skip.
- **Using eval() or exec() for dynamic loading:** Always use `importlib.import_module()` + `getattr()`. Never evaluate arbitrary strings.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Dynamic class loading | Custom module scanner / exec-based loader | `importlib.import_module()` + `getattr()` | stdlib, safe, handles nested packages correctly |
| Config validation | Manual dict parsing with try/except | Pydantic `ScannerToolConfig` model | Type coercion, validation errors with field paths, defaults |
| YAML parsing | PyYAML manual loading | pydantic-settings `YamlConfigSettingsSource` | Already in use, handles env var override priority |
| API response serialization | Manual dict building | Pydantic response models with FastAPI | Automatic OpenAPI schema generation, validation |

**Key insight:** The entire dynamic loading mechanism is approximately 10 lines of code using stdlib `importlib`. The complexity is in the config model changes and orchestrator refactoring, not in the plugin loading itself.

## Common Pitfalls

### Pitfall 1: Circular imports when loading adapters
**What goes wrong:** `registry.py` imports `ScannerAdapter` from `base.py`, and adapter modules may import from packages that reference the registry.
**Why it happens:** Python circular import chains when module-level imports form loops.
**How to avoid:** Keep `registry.py` imports minimal: only `importlib`, `logging`, and `ScannerAdapter` from `base.py`. Adapters should never import from registry. The registry loads adapter modules lazily via `importlib.import_module()`, not via static imports.
**Warning signs:** `ImportError` at startup mentioning partially initialized modules.

### Pitfall 2: getattr on settings.scanners breaks with dict
**What goes wrong:** The orchestrator currently uses `getattr(settings.scanners, instance.tool_name)` to get per-tool config. This breaks when `scanners` becomes a `dict` instead of a model with named attributes.
**Why it happens:** Changing from `ScannersConfig` (class with named fields) to `dict[str, ScannerToolConfig]`.
**How to avoid:** Replace all `getattr(settings.scanners, tool_name)` with `settings.scanners[tool_name]` or `settings.scanners.get(tool_name)`. Search the codebase for all `getattr(settings.scanners` usages.
**Warning signs:** `TypeError: 'dict' object has no attribute` at runtime.

### Pitfall 3: Gitleaks shallow-clone check breaks
**What goes wrong:** The orchestrator has special logic at line 148: `gitleaks_enabled = settings.scanners.gitleaks.enabled`. With a dict, this becomes `settings.scanners["gitleaks"].enabled`. If gitleaks is not in config at all, this KeyError crashes the scan.
**Why it happens:** Direct key access on the new dict without checking existence.
**How to avoid:** Use `settings.scanners.get("gitleaks")` with a default, or check registry for gitleaks enablement status.
**Warning signs:** KeyError on scanner names in orchestrator.

### Pitfall 4: Tests mocking ALL_ADAPTERS break
**What goes wrong:** Existing tests in `tests/phase_02/test_orchestrator.py` patch `scanner.core.orchestrator.ALL_ADAPTERS`. After removal, these patches target a non-existent symbol.
**Why it happens:** Tests are tightly coupled to the `ALL_ADAPTERS` import.
**How to avoid:** Update tests to mock the registry instead. The test helper `_patch_all_adapters()` must be rewritten to provide a mock `ScannerRegistry` or mock the `settings.scanners` dict.
**Warning signs:** `AttributeError: module has no attribute 'ALL_ADAPTERS'` in test output.

### Pitfall 5: Config YAML indentation matters for dict parsing
**What goes wrong:** pydantic-settings YAML source may not parse nested scanner configs correctly if indentation is inconsistent.
**Why it happens:** YAML is indentation-sensitive. If `adapter_class` is not properly indented under the scanner key, it becomes a sibling instead of a child.
**How to avoid:** Validate the default `config.yml` structure carefully. Write a test that loads the actual `config.yml` and verifies all 8 scanners parse correctly with their `adapter_class` and `languages` fields.
**Warning signs:** `ScannerToolConfig` fields have default values instead of config values.

### Pitfall 6: pydantic-settings dict field may not auto-coerce nested YAML
**What goes wrong:** A `dict[str, ScannerToolConfig]` field on BaseSettings may receive raw dicts from the YAML source instead of validated ScannerToolConfig instances.
**Why it happens:** pydantic-settings YAML source passes raw parsed YAML data; nested model coercion depends on pydantic's discriminated union / model validation behavior.
**How to avoid:** Test this early. If auto-coercion does not work, add a `@field_validator("scanners", mode="before")` that manually constructs `ScannerToolConfig` from each dict entry. Alternatively, keep `ScannersConfig` as a model with `model_config = ConfigDict(extra="allow")` and a custom `__getitem__` for dict-like access.
**Warning signs:** `ValidationError` or raw dict values where ScannerToolConfig instances are expected.

## Code Examples

### Updated config.yml (all 8 scanners migrated)
```yaml
scanners:
  semgrep:
    adapter_class: "scanner.adapters.semgrep.SemgrepAdapter"
    enabled: true
    timeout: 180
    extra_args: ["--exclude", ".venv", "--exclude", "node_modules"]
    languages: ["python", "php", "javascript", "typescript", "go", "java", "kotlin", "ruby", "csharp", "rust"]
  cppcheck:
    adapter_class: "scanner.adapters.cppcheck.CppcheckAdapter"
    enabled: true
    timeout: 120
    extra_args: ["-i.venv", "-inode_modules"]
    languages: ["cpp"]
  gitleaks:
    adapter_class: "scanner.adapters.gitleaks.GitleaksAdapter"
    enabled: true
    timeout: 120
    extra_args: []
    languages: []  # Universal scanner -- runs on all projects
  trivy:
    adapter_class: "scanner.adapters.trivy.TrivyAdapter"
    enabled: true
    timeout: 120
    extra_args: []
    languages: ["docker", "terraform", "yaml"]
  checkov:
    adapter_class: "scanner.adapters.checkov.CheckovAdapter"
    enabled: true
    timeout: 120
    extra_args: ["--skip-path", ".venv", "--skip-path", "node_modules"]
    languages: ["docker", "terraform", "yaml", "ci"]
  psalm:
    adapter_class: "scanner.adapters.psalm.PsalmAdapter"
    enabled: "auto"
    timeout: 300
    extra_args: []
    languages: ["php"]
  enlightn:
    adapter_class: "scanner.adapters.enlightn.EnlightnAdapter"
    enabled: "auto"
    timeout: 120
    extra_args: []
    languages: ["laravel"]
  php_security_checker:
    adapter_class: "scanner.adapters.php_security_checker.PhpSecurityCheckerAdapter"
    enabled: "auto"
    timeout: 30
    extra_args: []
    languages: ["php"]
```

### Extended ScannerToolConfig
```python
class ScannerToolConfig(BaseModel):
    """Per-tool scanner configuration with registry fields."""
    adapter_class: str = ""
    enabled: bool | str = "auto"
    timeout: int = 180
    extra_args: list[str] = []
    languages: list[str] = []
```

### Simplified __init__.py after migration
```python
"""Scanner tool adapters package."""

from scanner.adapters.base import ScannerAdapter

__all__ = ["ScannerAdapter"]
```

### GET /api/scanners endpoint
```python
from fastapi import APIRouter, Depends
from scanner.config import ScannerSettings

router = APIRouter(prefix="/api", tags=["scanners"])

@router.get("/scanners")
async def list_scanners(settings: ScannerSettings = Depends(get_settings)):
    """List all registered scanners with status information."""
    registry = get_scanner_registry(settings)
    return registry.all_scanners_info()
```

### Orchestrator refactored scan loop
```python
# Replace:
#   for adapter_cls in ALL_ADAPTERS:
#       instance = adapter_cls()
#       tool_config = getattr(settings.scanners, instance.tool_name)
# With:
registry = ScannerRegistry(settings.scanners)
enabled_adapters = registry.get_enabled_adapters(detected_langs)
for adapter in enabled_adapters:
    tool_config = settings.scanners[adapter.tool_name]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hard-coded adapter list | Config-driven registry with importlib | This phase | New scanners added via config only |
| Per-scanner fields in ScannersConfig | Dynamic dict[str, ScannerToolConfig] | This phase | No Python code changes for new scanners |
| SCANNER_LANGUAGES constant | Per-scanner `languages` field in config | This phase | Language mappings configurable without code |
| getattr(settings.scanners, name) | settings.scanners[name] / dict access | This phase | Dynamic scanner names supported |

**Deprecated/outdated after this phase:**
- `ALL_ADAPTERS` list in `adapters/__init__.py`: Removed entirely
- `ScannersConfig` with hard-coded fields: Replaced with `dict[str, ScannerToolConfig]`
- `SCANNER_LANGUAGES` dict in `language_detect.py`: Removed, languages sourced from config
- `UNIVERSAL_SCANNERS` set in `language_detect.py`: Removed, empty `languages` list = universal

## Open Questions

1. **pydantic-settings dict coercion behavior**
   - What we know: pydantic v2 validates nested models well; pydantic-settings loads YAML via PyYAML
   - What's unclear: Whether `dict[str, ScannerToolConfig]` auto-coerces from YAML nested dicts without a custom validator
   - Recommendation: Implement and test early (Wave 0). If auto-coercion fails, add a `@field_validator` or use a wrapper model with `ConfigDict(extra="allow")`

2. **Registry lifecycle and caching**
   - What we know: The orchestrator creates a new registry per scan call
   - What's unclear: Whether to create the registry once at app startup and cache it, or rebuild per scan
   - Recommendation: Build once at startup (or lazily on first use) and cache on the settings object or as a module-level singleton. Scanners don't change mid-run.

3. **Backward compatibility of config.yml**
   - What we know: User decided "clean break" -- adapter_class required
   - What's unclear: Whether users with old config.yml files (without adapter_class) will see helpful upgrade messages
   - Recommendation: When a scanner entry lacks `adapter_class`, the warning should say: "Scanner '{name}' missing required 'adapter_class' field -- add adapter_class to config.yml. See documentation for migration."

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `python -m pytest tests/phase_08/ -x -q` |
| Full suite command | `python -m pytest tests/ -x -q` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PLUG-01 | Adapter loaded from config adapter_class via importlib | unit | `python -m pytest tests/phase_08/test_registry.py::test_load_adapter_from_config -x` | Wave 0 |
| PLUG-01 | New scanner works with only config.yml entry (no code changes beyond adapter) | integration | `python -m pytest tests/phase_08/test_registry.py::test_register_new_scanner_config_only -x` | Wave 0 |
| PLUG-02 | All 8 existing scanners load from config registry | integration | `python -m pytest tests/phase_08/test_registry.py::test_all_existing_scanners_load -x` | Wave 0 |
| PLUG-02 | ALL_ADAPTERS import removed, orchestrator uses registry | unit | `python -m pytest tests/phase_08/test_orchestrator_registry.py::test_orchestrator_uses_registry -x` | Wave 0 |
| PLUG-03 | Missing adapter_class produces WARNING and scanner skipped | unit | `python -m pytest tests/phase_08/test_registry.py::test_missing_adapter_class_warns -x` | Wave 0 |
| PLUG-03 | Typo in adapter_class produces WARNING with error details | unit | `python -m pytest tests/phase_08/test_registry.py::test_invalid_adapter_class_warns -x` | Wave 0 |
| PLUG-03 | Non-ScannerAdapter subclass rejected with clear error | unit | `python -m pytest tests/phase_08/test_registry.py::test_non_subclass_rejected -x` | Wave 0 |
| PLUG-03 | Failed scanners visible in /api/scanners with load_error | integration | `python -m pytest tests/phase_08/test_api_scanners.py::test_load_error_in_api -x` | Wave 0 |
| PLUG-04 | Scanner with languages=["python"] only runs when Python detected | unit | `python -m pytest tests/phase_08/test_registry.py::test_language_filtering -x` | Wave 0 |
| PLUG-04 | Scanner with languages=[] runs for any project (universal) | unit | `python -m pytest tests/phase_08/test_registry.py::test_universal_scanner -x` | Wave 0 |
| PLUG-04 | should_enable_scanner reads from config languages, not SCANNER_LANGUAGES | unit | `python -m pytest tests/phase_08/test_language_detect.py::test_config_driven_languages -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/phase_08/ -x -q`
- **Per wave merge:** `python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/phase_08/__init__.py` -- package init
- [ ] `tests/phase_08/test_registry.py` -- registry loading, validation, language filtering
- [ ] `tests/phase_08/test_orchestrator_registry.py` -- orchestrator using registry instead of ALL_ADAPTERS
- [ ] `tests/phase_08/test_api_scanners.py` -- GET /api/scanners endpoint
- [ ] `tests/phase_08/test_language_detect.py` -- config-driven language detection
- [ ] `tests/phase_08/test_config_migration.py` -- all 8 scanners parse from updated config.yml
- [ ] Update `tests/phase_02/test_orchestrator.py` -- remove ALL_ADAPTERS mocking, use registry mocking

## Sources

### Primary (HIGH confidence)
- Codebase inspection: `src/scanner/adapters/__init__.py`, `src/scanner/config.py`, `src/scanner/core/orchestrator.py`, `src/scanner/core/language_detect.py` -- current architecture fully understood
- Phase 7 research report: Plugin Architecture Patterns section -- config-driven registry recommended
- Phase 8 CONTEXT.md -- locked decisions and canonical references

### Secondary (MEDIUM confidence)
- Python 3.12 importlib documentation -- `import_module()` and `getattr()` are the standard dynamic loading pattern
- pydantic v2.12 -- `ConfigDict(extra="allow")` and dict field validation behavior

### Tertiary (LOW confidence)
- pydantic-settings v2.13 YAML source behavior with `dict[str, BaseModel]` fields -- needs validation via test (Open Question 1)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already in use, no new dependencies
- Architecture: HIGH -- pattern is simple (importlib + dict config), well-understood from Phase 7 research
- Pitfalls: HIGH -- identified from direct codebase inspection of all integration points
- pydantic dict coercion: MEDIUM -- needs early validation test

**Research date:** 2026-03-21
**Valid until:** 2026-04-21 (stable domain, no fast-moving dependencies)
