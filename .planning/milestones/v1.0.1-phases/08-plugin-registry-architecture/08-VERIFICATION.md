---
phase: 08-plugin-registry-architecture
verified: 2026-03-21T17:30:00Z
status: passed
score: 12/12 must-haves verified
re_verification: false
---

# Phase 08: Plugin Registry Architecture Verification Report

**Phase Goal:** Scanners can be added and configured entirely through config.yml without touching Python code
**Verified:** 2026-03-21T17:30:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | A scanner adapter class can be loaded from a dotted path string in config.yml via importlib | VERIFIED | `registry.py` load_adapter_class() uses importlib.import_module + getattr; test_load_adapter_from_config passes |
| 2 | Missing or invalid adapter_class produces a WARNING log and the scanner is skipped (not a crash) | VERIFIED | load_error set on RegisteredScanner; logger.warning called; test_missing_module_warns, test_missing_class_warns, test_invalid_adapter_class_warns all pass |
| 3 | A class that is not a ScannerAdapter subclass is rejected with a clear error message | VERIFIED | `issubclass(cls, ScannerAdapter)` check in `_register()`; load_error = "...is not a ScannerAdapter subclass"; test_non_subclass_rejected passes |
| 4 | All 8 existing scanners parse correctly from the updated config.yml with adapter_class and languages fields | VERIFIED | config.yml has exactly 8 entries each with adapter_class; `grep -c "adapter_class" config.yml` returns 8; test_config_migration passes |
| 5 | ScannerToolConfig accepts adapter_class (str) and languages (list[str]) fields | VERIFIED | src/scanner/config.py lines 30-31: `adapter_class: str = ""` and `languages: list[str] = []` |
| 6 | The orchestrator loads scanners from the registry instead of ALL_ADAPTERS | VERIFIED | orchestrator.py line 9: `from scanner.adapters.registry import ScannerRegistry`; line 166-167: `registry = ScannerRegistry(settings.scanners)` + `get_enabled_adapters()`; no ALL_ADAPTERS anywhere in src/ |
| 7 | Language detection reads scanner languages from config.yml, not from SCANNER_LANGUAGES constant | VERIFIED | should_enable_scanner signature changed to `(tool_name, scanner_languages: list[str], detected_languages: set[str])`; no SCANNER_LANGUAGES in src/ |
| 8 | SCANNER_LANGUAGES and UNIVERSAL_SCANNERS constants are removed from language_detect.py | VERIFIED | grep of src/ for these constants returns nothing |
| 9 | GET /api/scanners returns all registered scanners with name, status, enabled, languages | VERIFIED | src/scanner/api/scanners.py implements list[ScannerInfo] endpoint; test_scanner_response_keys passes |
| 10 | Failed-to-load scanners appear in /api/scanners with status load_error and the error message | VERIFIED | test_load_error_in_api passes; status="load_error" and non-null load_error confirmed |
| 11 | Existing orchestrator tests pass with the new registry-based approach | VERIFIED | tests/phase_02/test_orchestrator.py: 9 passed, 0 failed |
| 12 | Gitleaks shallow-clone check uses dict access settings.scanners['gitleaks'] instead of attribute access | VERIFIED | orchestrator.py line 148-149: `settings.scanners.get("gitleaks")`; test_gitleaks_shallow_clone_with_gitleaks_enabled and test_gitleaks_shallow_clone_when_not_in_config pass |

**Score:** 12/12 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/scanner/adapters/registry.py` | ScannerRegistry class with load_adapter_class, RegisteredScanner, get_enabled_adapters, all_scanners_info | VERIFIED | 123 lines (>80 required); all 4 symbols present |
| `src/scanner/config.py` | Extended ScannerToolConfig with adapter_class and languages; dynamic scanners dict | VERIFIED | adapter_class, languages fields on ScannerToolConfig; `scanners: dict[str, ScannerToolConfig] = {}`; ScannersConfig removed |
| `config.yml` | All 8 scanners with adapter_class and languages fields | VERIFIED | 8 adapter_class entries confirmed; all 8 scanner keys present |
| `tests/phase_08/test_registry.py` | Tests for registry loading, validation, error handling, language filtering | VERIFIED | 11 tests, all pass |
| `src/scanner/core/orchestrator.py` | Registry-based scan orchestration | VERIFIED | Contains `from scanner.adapters.registry import ScannerRegistry` and `ScannerRegistry(settings.scanners)` |
| `src/scanner/core/language_detect.py` | Language detection without hard-coded SCANNER_LANGUAGES | VERIFIED | No SCANNER_LANGUAGES or UNIVERSAL_SCANNERS; new should_enable_scanner signature present |
| `src/scanner/api/scanners.py` | GET /api/scanners endpoint | VERIFIED | 26 lines (>15 required); `@router.get("/scanners")`, `class ScannerInfo(BaseModel)`, `ScannerRegistry(settings.scanners)` |
| `tests/phase_08/test_orchestrator_registry.py` | Tests for orchestrator using registry | VERIFIED | 4 tests, all pass |
| `tests/phase_08/test_language_detect.py` | Tests for config-driven language detection | VERIFIED | 5 tests, all pass |
| `tests/phase_08/test_api_scanners.py` | Tests for /api/scanners endpoint | VERIFIED | 5 tests including test_load_error_in_api; all pass |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `src/scanner/adapters/registry.py` | `src/scanner/adapters/base.py` | `issubclass(cls, ScannerAdapter)` | WIRED | Line 81: `elif not issubclass(cls, ScannerAdapter)` |
| `src/scanner/adapters/registry.py` | `src/scanner/config.py` | ScannerToolConfig consumption | WIRED | Line 8: `from scanner.config import ScannerToolConfig`; used in `__init__` signature and `_register()` |
| `src/scanner/config.py` | `config.yml` | pydantic-settings YAML loading | WIRED | `dict[str, ScannerToolConfig]` field with field_validator; YamlConfigSettingsSource in settings_customise_sources |
| `src/scanner/core/orchestrator.py` | `src/scanner/adapters/registry.py` | ScannerRegistry import and usage | WIRED | Line 9: `from scanner.adapters.registry import ScannerRegistry`; line 166: `ScannerRegistry(settings.scanners)` |
| `src/scanner/core/orchestrator.py` | `src/scanner/config.py` | dict access for per-tool config | WIRED | Line 196-197: `settings.scanners[adapter.tool_name].timeout` and `.extra_args` |
| `src/scanner/api/scanners.py` | `src/scanner/adapters/registry.py` | all_scanners_info() call | WIRED | Line 6: `from scanner.adapters.registry import ScannerRegistry`; line 26: `registry.all_scanners_info()` |
| `src/scanner/api/router.py` | `src/scanner/api/scanners.py` | include_router | WIRED | Line 7: `from scanner.api.scanners import router as scanners_router`; line 14: `api_router.include_router(scanners_router)` |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| PLUG-01 | 08-01-PLAN.md | Scanner adapters can be registered via config.yml adapter_class field without code changes | SATISFIED | ScannerRegistry.load_adapter_class() via importlib; config.yml drives all 8 adapters; no Python code change needed to add a scanner |
| PLUG-02 | 08-02-PLAN.md | Existing hard-coded ALL_ADAPTERS list migrated to config-driven registration | SATISFIED | ALL_ADAPTERS removed from `__init__.py`; orchestrator uses ScannerRegistry; grep of src/ returns no matches for ALL_ADAPTERS |
| PLUG-03 | 08-01-PLAN.md | Config validation warns on missing or invalid adapter_class references | SATISFIED | Missing adapter_class logs WARNING; non-ScannerAdapter subclass logs WARNING; load_error field surfaces errors gracefully |
| PLUG-04 | 08-02-PLAN.md | SCANNER_LANGUAGES mapping extended for new scanner-to-language associations | SATISFIED | SCANNER_LANGUAGES constant removed; languages now per-scanner in config.yml (e.g., semgrep has 10 languages, gitleaks has [], psalm has ["php"]); config-driven, no code change needed to extend |

All 4 phase-8 requirements satisfied. No orphaned requirements found (REQUIREMENTS.md traceability table confirms PLUG-01 through PLUG-04 are phase 8, all accounted for by the two plans).

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/scanner/core/orchestrator.py` | 141, 263 | `datetime.utcnow()` deprecated (Python 3.12 warning) | Info | No functional impact; pre-existing issue unrelated to phase 8 |
| `tests/phase_08/test_registry.py` | 91 | Test named `test_missing_adapter_class_sets_error` instead of `test_missing_adapter_class_warns` as specified in plan | Info | Test covers the required behavior; only naming differs from plan acceptance criteria; no functional gap |

No blocker or warning-severity anti-patterns. No TODO/FIXME/placeholder comments in phase 8 files. No stub implementations detected.

---

### Human Verification Required

None. All observable behaviors are verifiable programmatically:

- The registry loads real adapter classes (tests confirm with actual adapter imports)
- The API endpoint returns correct JSON shape (httpx AsyncClient tests confirm)
- Language filtering is tested with real and mock adapters
- Gitleaks shallow-clone behavior tested end-to-end through run_scan

---

### Test Run Summary

```
tests/phase_08/  — 34 passed, 0 failed, 13 warnings (all DeprecationWarning unrelated to phase 8)
tests/phase_02/test_orchestrator.py — 9 passed, 0 failed (regression check)
Combined: 43 passed, 0 failed
```

---

### Gaps Summary

No gaps. All must-haves from both plan files are verified:

- Plan 01 must-haves (PLUG-01, PLUG-03): 5/5 truths verified, all artifacts exist and are wired
- Plan 02 must-haves (PLUG-02, PLUG-04): 7/7 truths verified, all artifacts exist and are wired
- Zero references to ALL_ADAPTERS, SCANNER_LANGUAGES, UNIVERSAL_SCANNERS, or ScannersConfig in src/
- config.yml drives all 8 scanner registrations without any Python code involvement

The phase goal is fully achieved: a new scanner adapter can be added by creating an adapter class file and adding a single entry to config.yml — no other Python changes required.

---

_Verified: 2026-03-21T17:30:00Z_
_Verifier: Claude (gsd-verifier)_
