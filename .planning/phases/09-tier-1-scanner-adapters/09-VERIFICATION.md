---
phase: 09-tier-1-scanner-adapters
verified: 2026-03-21T22:00:00Z
status: passed
score: 15/15 must-haves verified
re_verification: false
---

# Phase 09: Tier-1 Scanner Adapters Verification Report

**Phase Goal:** Implement tier-1 scanner adapters (gosec, Bandit, Brakeman, cargo-audit) with full test coverage
**Verified:** 2026-03-21T22:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | gosec adapter parses native JSON output into FindingSchema list | VERIFIED | `src/scanner/adapters/gosec.py` lines 49-80; `data.get("Issues", [])` loop builds `FindingSchema` list |
| 2 | gosec severity mapping: HIGH->HIGH, MEDIUM->MEDIUM, LOW->LOW | VERIFIED | `GOSEC_SEVERITY_MAP` dict at line 11; `test_gosec_severity_mapping` asserts G101->HIGH, G304->MEDIUM, G104->LOW |
| 3 | Bandit adapter parses native JSON with confidence x severity matrix | VERIFIED | `BANDIT_SEVERITY_MATRIX` dict at lines 12-22; `_bandit_severity()` function at line 25 |
| 4 | Bandit HIGH sev + HIGH conf -> CRITICAL, HIGH sev + MED conf -> HIGH | VERIFIED | `("HIGH","HIGH"): Severity.CRITICAL`, `("HIGH","MEDIUM"): Severity.HIGH` in matrix; `test_bandit_severity_matrix` passes |
| 5 | Both gosec+Bandit adapters treat exit code 1 as findings-found, not error | VERIFIED | Both check `if returncode >= 2` before raising; `test_gosec_exit_code_1_is_not_error` and `test_bandit_exit_code_1_is_not_error` pass |
| 6 | Both gosec+Bandit adapters raise ScannerExecutionError on exit code >= 2 | VERIFIED | `raise ScannerExecutionError(...)` on `returncode >= 2`; both exit-code-2 tests pass |
| 7 | Brakeman adapter parses JSON warnings with confidence-weighted severity | VERIFIED | `BRAKEMAN_CONFIDENCE_SEVERITY` dict; `test_brakeman_confidence_weighted_severity` asserts SQL->HIGH, XSS->MEDIUM, MassAssignment->LOW |
| 8 | Brakeman Weak confidence findings get downgraded one severity level | VERIFIED | `"Weak": Severity.LOW` in map; `test_brakeman_weak_confidence_downgrade` explicitly checks MassAssignment->LOW |
| 9 | Brakeman gracefully returns empty list for non-Rails Ruby projects | VERIFIED | Checks `"Please supply the path to a Rails application"` in stderr and returns `[]`; `test_brakeman_non_rails_graceful` passes |
| 10 | cargo-audit adapter parses vulnerabilities.list with CVSS-based severity | VERIFIED | `_cvss_to_severity()` uses `CVSS3(cvss_vector).scores()[0]`; `test_cargo_audit_cvss_severity` asserts RUSTSEC-2023-0001 (9.8)->CRITICAL |
| 11 | cargo-audit ignores warnings section (unmaintained/yanked crates) | VERIFIED | Only `vuln_section.get("list", [])` is iterated; `test_cargo_audit_ignores_warnings` confirms 2 findings not 3 |
| 12 | cargo-audit defaults to MEDIUM when CVSS vector is null | VERIFIED | `if not cvss_vector: return Severity.MEDIUM`; `test_cargo_audit_null_cvss_defaults_medium` passes |
| 13 | cargo-audit generates Cargo.lock via cargo generate-lockfile if missing | VERIFIED | `_ensure_lockfile()` async function at lines 43-87 calls `asyncio.create_subprocess_exec("cargo","generate-lockfile",cwd=target_path)` |
| 14 | All 4 new scanners are registered in config.yml and load via registry | VERIFIED | `config.yml` lines 70-93 contain gosec/bandit/brakeman/cargo_audit; `test_registry_loads_all_new_scanners` and `test_registry_language_filtering` pass |
| 15 | 44 tests across all phase 09 test files pass | VERIFIED | `python3 -m pytest tests/phase_09/ -x -q` exits 0; output: `44 passed in 0.52s` |

**Score:** 15/15 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/scanner/adapters/gosec.py` | GosecAdapter subclass of ScannerAdapter | VERIFIED | 81 lines; `class GosecAdapter(ScannerAdapter)`; exports `GosecAdapter` |
| `src/scanner/adapters/bandit.py` | BanditAdapter subclass of ScannerAdapter | VERIFIED | 99 lines; `class BanditAdapter(ScannerAdapter)`; exports `BanditAdapter` |
| `src/scanner/adapters/brakeman.py` | BrakemanAdapter subclass of ScannerAdapter | VERIFIED | 98 lines; `class BrakemanAdapter(ScannerAdapter)`; exports `BrakemanAdapter` |
| `src/scanner/adapters/cargo_audit.py` | CargoAuditAdapter subclass of ScannerAdapter | VERIFIED | 182 lines; `class CargoAuditAdapter(ScannerAdapter)`; exports `CargoAuditAdapter` |
| `config.yml` | Scanner entries for all 4 new adapters | VERIFIED | 12 total adapter_class entries (8 existing + 4 new); gosec/bandit/brakeman/cargo_audit present with correct dotted paths and language lists |
| `tests/phase_09/test_adapter_gosec.py` | Unit tests for gosec adapter | VERIFIED | 103 lines; 8 async test functions |
| `tests/phase_09/test_adapter_bandit.py` | Unit tests for Bandit adapter | VERIFIED | 105 lines; 8 async test functions |
| `tests/phase_09/test_adapter_brakeman.py` | Unit tests for Brakeman adapter | VERIFIED | 118 lines; 9 async test functions |
| `tests/phase_09/test_adapter_cargo_audit.py` | Unit tests for cargo-audit adapter | VERIFIED | 274 lines; 13 test functions (11 async + 2 more) |
| `tests/phase_09/test_config_registration.py` | Integration test for registry loading | VERIFIED | 84 lines; 3 test functions including `test_load_adapter_class` (parametrized over 4 adapters) and `test_registry_loads_all_new_scanners` |
| `tests/phase_09/conftest.py` | Shared fixtures for phase 09 | VERIFIED | 37 lines; provides `gosec_output`, `bandit_output`, `brakeman_output`, `cargo_audit_output` fixtures |
| `tests/phase_09/fixtures/gosec_output.json` | 3-finding gosec fixture | VERIFIED | `"Issues"` key with 3 entries; HIGH/MEDIUM/LOW severities |
| `tests/phase_09/fixtures/bandit_output.json` | 4-finding bandit fixture | VERIFIED | `"results"` key with 4 entries covering HIGH/HIGH, HIGH/MEDIUM, MEDIUM/HIGH, LOW/LOW matrix cells |
| `tests/phase_09/fixtures/brakeman_output.json` | Brakeman fixture with 3 warnings | VERIFIED | `"warnings"` key with 3 entries; High/Medium/Weak confidence |
| `tests/phase_09/fixtures/cargo_audit_output.json` | cargo-audit fixture: 2 vulns + 1 yanked warning | VERIFIED | `vulnerabilities.list` with 2 items (one CVSS, one null); `warnings.yanked` with 1 item (should be ignored) |
| `pyproject.toml` | cvss>=3.2 dependency | VERIFIED | `"cvss>=3.2"` at line 23 in dependencies list |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `src/scanner/adapters/gosec.py` | `scanner.adapters.base.ScannerAdapter` | class inheritance | VERIFIED | `class GosecAdapter(ScannerAdapter)` at line 18 |
| `src/scanner/adapters/bandit.py` | `scanner.adapters.base.ScannerAdapter` | class inheritance | VERIFIED | `class BanditAdapter(ScannerAdapter)` at line 31 |
| `src/scanner/adapters/brakeman.py` | `scanner.adapters.base.ScannerAdapter` | class inheritance | VERIFIED | `class BrakemanAdapter(ScannerAdapter)` at line 23 |
| `src/scanner/adapters/cargo_audit.py` | `scanner.adapters.base.ScannerAdapter` | class inheritance | VERIFIED | `class CargoAuditAdapter(ScannerAdapter)` at line 90 |
| `config.yml` | `src/scanner/adapters/registry.py` | adapter_class dotted path | VERIFIED | All 4 entries use `scanner.adapters.<module>.<Class>` pattern; `test_registry_loads_all_new_scanners` loads each via `ScannerRegistry` with zero `load_error` |
| `src/scanner/adapters/cargo_audit.py` | `_ensure_lockfile()` | internal wiring | VERIFIED | `lockfile_ready = await _ensure_lockfile(target_path)` called at line 107 before audit cmd |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| SCAN-01 | 09-01 | gosec adapter scans Go source code and produces FindingSchema-compatible results | SATISFIED | `GosecAdapter.run()` returns `list[FindingSchema]`; 8 unit tests pass; importable via `scanner.adapters.gosec.GosecAdapter` |
| SCAN-02 | 09-01 | Bandit adapter scans Python source code and produces FindingSchema-compatible results | SATISFIED | `BanditAdapter.run()` returns `list[FindingSchema]`; 8 unit tests pass; importable via `scanner.adapters.bandit.BanditAdapter` |
| SCAN-03 | 09-02 | Brakeman adapter scans Ruby/Rails applications and produces FindingSchema-compatible results | SATISFIED | `BrakemanAdapter.run()` returns `list[FindingSchema]`; 9 unit tests pass; non-Rails graceful handling verified |
| SCAN-04 | 09-02 | cargo-audit adapter scans Rust dependencies via Cargo.lock and produces FindingSchema-compatible results | SATISFIED | `CargoAuditAdapter.run()` returns `list[FindingSchema]`; 13 tests pass; CVSS severity mapping, lockfile generation, warnings-ignore all verified |

All 4 phase-9-assigned requirements from REQUIREMENTS.md are satisfied. No orphaned requirements detected (INFRA-01, INFRA-02, DOCS-01 are mapped to Phase 10; PLUG-01 through PLUG-04 are mapped to Phase 8).

### Anti-Patterns Found

No blocking or warning-level anti-patterns found.

Scan of all phase 09 adapter files and test files:
- No `TODO`/`FIXME`/`PLACEHOLDER` comments
- No empty return stubs (`return null`, `return {}`, `return []` only in properly guarded edge-case branches)
- No console.log-only implementations
- No placeholder components

One informational note: `cargo_audit.py` uses a bare `except Exception` in `_cvss_to_severity()` (line 30) to catch malformed CVSS vectors and return `Severity.MEDIUM` as a safe default. This is intentional defensive coding per CONTEXT.md, not a bug.

### Human Verification Required

None. All critical behaviors are programmatically verified:
- Severity mappings are asserted by unit tests using the actual mapping functions
- Exit code handling is tested with `AsyncMock`
- Registry loading is tested via `ScannerRegistry` in-process integration tests
- CVSS score calculation relies on the `cvss` library (version-pinned dependency)

---

## Summary

Phase 09 goal is fully achieved. All 4 tier-1 scanner adapters (gosec, Bandit, Brakeman, cargo-audit) are implemented with substantive logic, correctly subclass `ScannerAdapter`, are wired into `config.yml` for plugin registry discovery, and are covered by 44 passing unit and integration tests.

Key implementation choices correctly applied:
- gosec: direct HIGH/MEDIUM/LOW severity mapping with string-to-int line number conversion
- Bandit: 9-cell confidence x severity matrix producing CRITICAL through INFO
- Brakeman: confidence-weighted severity (High/Medium/Weak) with graceful non-Rails handling
- cargo-audit: CVSS-score-based severity via `cvss` library; warnings section ignored; Cargo.lock auto-generated if missing

All 4 requirements (SCAN-01 through SCAN-04) are satisfied. `pyproject.toml` has `cvss>=3.2` added. `config.yml` has 12 total scanner entries (8 pre-existing + 4 new).

---

_Verified: 2026-03-21T22:00:00Z_
_Verifier: Claude (gsd-verifier)_
