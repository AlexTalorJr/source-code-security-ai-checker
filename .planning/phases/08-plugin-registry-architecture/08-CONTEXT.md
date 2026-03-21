# Phase 8: Plugin Registry Architecture - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Config-driven scanner registration replacing the hard-coded `ALL_ADAPTERS` list and `SCANNER_LANGUAGES` dict. Scanners can be added and configured entirely through `config.yml` without touching Python code (beyond writing the adapter class itself). Existing 8 scanners migrate to the new registry format.

</domain>

<decisions>
## Implementation Decisions

### Config format
- Flat structure: each scanner key gets `adapter_class`, `enabled`, `timeout`, `extra_args`, and `languages` fields
- `adapter_class` is a full Python module path (e.g., `scanner.adapters.semgrep.SemgrepAdapter`) — resolved via importlib
- `languages` list determines which projects trigger the scanner in "auto" mode
- Empty or omitted `languages` = universal scanner (runs on all projects, like gitleaks)
- Scanner order in config is for human readability only — all enabled scanners run in parallel via asyncio.gather

### New scanner workflow
- Adding a scanner requires: (1) write a ScannerAdapter subclass, (2) add config.yml entry with adapter_class — no other files to touch
- `adapter_class` is required for every scanner entry; missing it produces a clear warning and the scanner is skipped
- Registry validates at startup that loaded classes are ScannerAdapter subclasses — fail fast with clear error if not
- New read-only `GET /api/scanners` endpoint listing all registered scanners with name, status, enabled, languages

### Error handling
- Bad `adapter_class` (typo, missing module): log WARNING with scanner name and import error, skip that scanner, app continues normally
- Failed-to-load scanners appear in `/api/scanners` with `status: "load_error"` and the error message — visible for troubleshooting
- Missing binary at runtime (e.g., gosec not installed): same warn-and-skip behavior — consistent with existing `_run_adapter` exception handling in orchestrator.py

### Migration path
- Clean break: `adapter_class` is required in the new format — old configs without it get warnings and scanners are skipped
- Default `config.yml` ships with `adapter_class` and `languages` for all 8 existing scanners
- `ScannersConfig` class replaced entirely with dynamic dict (no more hard-coded per-scanner fields)
- `ALL_ADAPTERS` list in `__init__.py` removed — registry loads from config
- `SCANNER_LANGUAGES` dict in `language_detect.py` removed — languages come from config.yml per scanner
- Config.yml is the single source of truth for scanner registration and language mapping

### Claude's Discretion
- Exact importlib loading mechanism and error message formatting
- How to structure the dynamic ScannersConfig (pydantic dict, extra='allow', or custom validator)
- Internal registry data structure (dict, list, dataclass)
- How `detect_languages()` and `should_enable_scanner()` adapt to config-driven languages
- Test structure and organization

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Current adapter architecture (to be refactored)
- `src/scanner/adapters/__init__.py` — Hard-coded `ALL_ADAPTERS` list (to be replaced by registry)
- `src/scanner/adapters/base.py` — `ScannerAdapter` abstract base class (stays as-is, adapter contract)
- `src/scanner/core/orchestrator.py` — `run_scan()` iterates `ALL_ADAPTERS` at line 166 (must switch to registry)
- `src/scanner/core/language_detect.py` — `SCANNER_LANGUAGES` dict and `should_enable_scanner()` (languages move to config)
- `src/scanner/config.py` — `ScannersConfig` with 8 hard-coded fields (must become dynamic), `ScannerToolConfig` model

### Existing adapter implementations (must all migrate)
- `src/scanner/adapters/semgrep.py`
- `src/scanner/adapters/cppcheck.py`
- `src/scanner/adapters/gitleaks.py`
- `src/scanner/adapters/trivy.py`
- `src/scanner/adapters/checkov.py`
- `src/scanner/adapters/psalm.py`
- `src/scanner/adapters/enlightn.py`
- `src/scanner/adapters/php_security_checker.py`

### Config and API
- `config.yml` — Current scanner config (must add adapter_class + languages to all entries)
- `src/scanner/api/` — API routes (new GET /api/scanners endpoint needed)

### Requirements
- `.planning/REQUIREMENTS.md` — PLUG-01 through PLUG-04

### Research outcomes
- `.planning/milestones/v2.0-phases/07-security-scanner-ecosystem-research/07-SCANNER-ECOSYSTEM-REPORT.md` — Plugin architecture patterns section, config-driven registry recommendation

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ScannerAdapter` base class: Well-defined contract (tool_name, run, get_version, _version_command, _execute) — unchanged by this phase
- `ScannerToolConfig` pydantic model: enabled/timeout/extra_args — extend with adapter_class and languages fields
- `detect_languages()` function: File extension scanning logic stays, but `should_enable_scanner()` must read languages from config instead of hard-coded dict
- `_run_adapter()` in orchestrator: Existing error isolation pattern (catch exceptions, return as tuple) — unchanged

### Established Patterns
- Pydantic BaseSettings with YAML source: `ScannerSettings` loads from config.yml via `YamlConfigSettingsSource`
- Async subprocess execution via `ScannerAdapter._execute()` with timeout
- `getattr(settings.scanners, instance.tool_name)` pattern in orchestrator — must change for dynamic dict access

### Integration Points
- `orchestrator.py:run_scan()` — Main consumer of adapter list, lines 165-173 must switch from ALL_ADAPTERS iteration to registry
- `orchestrator.py:168` — `getattr(settings.scanners, instance.tool_name)` for per-tool config — changes with dynamic ScannersConfig
- `language_detect.py` — `should_enable_scanner()` currently reads from `SCANNER_LANGUAGES` constant
- API routes — new `/api/scanners` endpoint
- Tests in `tests/phase_02/test_orchestrator.py` — reference ALL_ADAPTERS, must be updated

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 08-plugin-registry-architecture*
*Context gathered: 2026-03-21*
