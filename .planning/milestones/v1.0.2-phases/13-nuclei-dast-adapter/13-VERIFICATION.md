---
phase: 13-nuclei-dast-adapter
verified: 2026-03-23T12:00:00Z
status: passed
score: 12/12 must-haves verified
re_verification: false
---

# Phase 13: Nuclei DAST Adapter Verification Report

**Phase Goal:** Users can run dynamic application security scans against target URLs alongside existing SAST scans
**Verified:** 2026-03-23T12:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #  | Truth | Status | Evidence |
|----|-------|--------|----------|
| 1  | NucleiAdapter parses JSONL output into FindingSchema objects with correct field mapping | VERIFIED | `src/scanner/adapters/nuclei.py` lines 53-63 and 65-90: line-by-line json.loads with full FindingSchema construction |
| 2  | Nuclei severity strings (info/low/medium/high/critical) map to correct Severity enum values | VERIFIED | `NUCLEI_SEVERITY_MAP` dict at lines 11-17; `test_severity_mapping` covers all 5 levels |
| 3  | Fingerprint computed from matched-at URL + template-id + snippet via compute_fingerprint | VERIFIED | `nuclei.py` line 77: `compute_fingerprint(matched_at, template_id, snippet)`; `test_fingerprint` verifies exact match |
| 4  | Non-zero Nuclei exit code raises ScannerExecutionError | VERIFIED | `nuclei.py` lines 48-51: `if returncode != 0: raise ScannerExecutionError(...)`; `test_execution_error` covers this |
| 5  | Empty JSONL output returns an empty list without error | VERIFIED | `nuclei.py` line 54: `stdout.strip().splitlines()` on empty string returns []; `test_empty_output` covers this |
| 6  | Nuclei binary installation in Dockerfile using zip format with multi-arch support | VERIFIED | `Dockerfile` lines 72-78: `ARG TARGETARCH`, GitHub releases zip download, `unzip -o` |
| 7  | Nuclei templates baked into image and owned by scanner user before USER switch | VERIFIED | `Dockerfile` lines 80-89: `nuclei -update-templates`, cp to `/home/scanner/.local`, `chown -R scanner:scanner` |
| 8  | config.yml.example has nuclei scanner entry with adapter_class, enabled, timeout, extra_args | VERIFIED | `config.yml.example` lines 48-53: all four fields present, `enabled: true`, `timeout: 300` |
| 9  | User can trigger DAST scan by POSTing {target_url: ...} to /api/scans and receiving 202 | VERIFIED | `scans.py` line 57: `@router.post("", status_code=202)`; `trigger_scan` stores `body.target_url`; `test_target_url_only` validates schema |
| 10 | ScanRequest rejects target_url combined with path or repo_url (422 validation error) | VERIFIED | `schemas.py` lines 22-28: model_validator raises ValueError; `test_target_url_with_path_rejected` and `test_target_url_with_repo_url_rejected` confirm 422 |
| 11 | Orchestrator routes to NucleiAdapter when target_url provided, skips SAST adapters | VERIFIED | `orchestrator.py` lines 158-198: `if target_url:` branch calls `registry.get_scanner_config("nuclei")`; `test_dast_mode_runs_nuclei_only` asserts `get_enabled_adapters` NOT called |
| 12 | DAST findings appear in HTML/PDF reports alongside SAST findings (DAST-04) | VERIFIED | `report.html.j2` line 566: `{{ finding.tool|e }}` and line 560: `data-tool="{{ finding.tool }}"` — tool label is data-driven; Nuclei findings with `tool="nuclei"` render automatically |

**Score:** 12/12 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/scanner/adapters/nuclei.py` | NucleiAdapter class | VERIFIED | 91 lines; `class NucleiAdapter(ScannerAdapter)`; exports `NucleiAdapter`, `NUCLEI_SEVERITY_MAP` |
| `tests/phase_13/test_nuclei_adapter.py` | Unit tests for NucleiAdapter | VERIFIED | 172 lines; 9 async tests + `test_tool_name`; includes `test_severity_mapping` |
| `tests/phase_13/fixtures/nuclei_output.jsonl` | Sample JSONL fixture data | VERIFIED | 3 events covering info/critical/medium; all have `template-id` field |
| `Dockerfile` | Nuclei binary installation | VERIFIED | Lines 72-89: zip install, template baking, user ownership |
| `config.yml.example` | Nuclei scanner configuration entry | VERIFIED | Lines 48-53: `nuclei:` block with `adapter_class: "scanner.adapters.nuclei.NucleiAdapter"` |
| `src/scanner/api/schemas.py` | ScanRequest with target_url field | VERIFIED | `target_url: str | None = None` with three-way model_validator |
| `src/scanner/core/orchestrator.py` | DAST routing in run_scan() | VERIFIED | `if target_url:` branch, lines 158-198 |
| `src/scanner/models/scan.py` | ScanResult with target_url column | VERIFIED | Line 19: `target_url = Column(String(500), nullable=True)` |
| `alembic/versions/002_add_target_url_to_scans.py` | DB migration for target_url | VERIFIED | `op.add_column("scans", sa.Column("target_url", ...))` with downgrade |
| `tests/phase_13/test_scan_request.py` | ScanRequest validation tests | VERIFIED | 7 tests; includes `test_target_url_only`, `test_target_url_with_path_rejected` |
| `tests/phase_13/test_dast_routing.py` | Orchestrator DAST routing tests | VERIFIED | 4 tests; includes `test_dast_mode_runs_nuclei_only` |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `src/scanner/adapters/nuclei.py` | `src/scanner/adapters/base.py` | class inheritance | WIRED | Line 20: `class NucleiAdapter(ScannerAdapter)` |
| `src/scanner/adapters/nuclei.py` | `src/scanner/core/fingerprint.py` | compute_fingerprint import | WIRED | Line 7: `from scanner.core.fingerprint import compute_fingerprint`; used at line 77 |
| `src/scanner/adapters/nuclei.py` | `src/scanner/schemas/finding.py` | FindingSchema construction | WIRED | Line 8: `from scanner.schemas.finding import FindingSchema`; used at lines 79-90 |
| `config.yml.example` | `src/scanner/adapters/nuclei.py` | adapter_class dotted path | WIRED | `"scanner.adapters.nuclei.NucleiAdapter"` in config; ScannerRegistry loads via `adapter_class` |
| `Dockerfile` | nuclei binary | GitHub releases download | WIRED | `projectdiscovery/nuclei/releases/download/v3.7.1/nuclei_3.7.1_linux_${TARGETARCH}.zip` |
| `src/scanner/api/scans.py` | `src/scanner/models/scan.py` | target_url stored in DB | WIRED | Line 74: `target_url=body.target_url` in ScanResult constructor |
| `src/scanner/core/scan_queue.py` | `src/scanner/core/orchestrator.py` | target_url passed to run_scan | WIRED | Lines 77, 94: `target_url = db_scan.target_url`; `target_url=target_url` |
| `src/scanner/core/orchestrator.py` | `src/scanner/adapters/nuclei.py` | NucleiAdapter in DAST mode | WIRED | Lines 161-167: `registry.get_scanner_config("nuclei")`, `nuclei_entry.adapter_class()` |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| DAST-01 | 13-01-PLAN.md | Nuclei adapter scans target URLs using templates and produces FindingSchema-compatible results | SATISFIED | `NucleiAdapter.run()` parses JSONL into `FindingSchema` objects; 10 unit tests pass |
| DAST-02 | 13-03-PLAN.md | Scan API accepts optional target_url field for DAST scans | SATISFIED | `ScanRequest.target_url` field with validation; `trigger_scan` stores it; `test_scan_request.py` validates |
| DAST-03 | 13-02-PLAN.md | Nuclei binary installed in Docker image with multi-arch support | SATISFIED | `Dockerfile` ARG TARGETARCH, zip install, template baking before USER switch |
| DAST-04 | 13-03-PLAN.md | Nuclei findings appear in HTML/PDF reports alongside SAST findings | SATISFIED | Report templates use `finding.tool` dynamically; Nuclei findings with `tool="nuclei"` render via existing badge system without template changes |

All four DAST requirements satisfied. No orphaned requirements detected.

---

### Anti-Patterns Found

No anti-patterns found in phase 13 artifacts.

Checked `src/scanner/adapters/nuclei.py`, `src/scanner/core/orchestrator.py`, `src/scanner/api/scans.py`, `src/scanner/core/scan_queue.py`, `src/scanner/models/scan.py`, `alembic/versions/002_add_target_url_to_scans.py`:
- No TODO/FIXME/PLACEHOLDER comments
- No empty return stubs (`return null`, `return {}`, `return []`)
- No incomplete handlers
- DAST routing branch is fully implemented and tested

---

### Human Verification Required

#### 1. Nuclei binary actually installs and runs in built Docker image

**Test:** Build the Docker image (`docker build .`) and run `docker run --rm <image> nuclei -version`
**Expected:** Nuclei v3.7.1 version string on stdout, exit code 0
**Why human:** Cannot execute Docker build in automated verification; multi-arch download from GitHub releases may fail if the URL format changes between versions

#### 2. End-to-end DAST scan execution against a live URL

**Test:** Start the service with a valid config and `POST /api/scans` with `{"target_url": "http://testphp.vulnweb.com"}`, then poll `/api/scans/{id}` until completed
**Expected:** Scan transitions pending -> queued -> running -> completed with nuclei findings visible
**Why human:** Requires live Nuclei binary, internet access, and a live target URL; cannot mock this end-to-end in automated tests

#### 3. Nuclei findings appear in HTML report with correct tool badge

**Test:** View the HTML report for a completed DAST scan in a browser
**Expected:** Findings show "nuclei" as the tool badge; the filter UI includes a "nuclei" checkbox; severity and template-id visible
**Why human:** Template rendering requires a complete browser run with actual scan data

---

### Summary

Phase 13 achieved its goal. All 12 observable truths are verified, all 11 required artifacts exist with substantive implementations, and all 8 key links are wired. The four DAST requirements (DAST-01 through DAST-04) are satisfied by the actual code.

Key architectural decisions that matter:
- NucleiAdapter uses URL-as-path pattern: `target_url` is passed as `target_path` to `NucleiAdapter.run()`, storing the URL in `file_path` of each FindingSchema
- Orchestrator DAST branch calls `registry.get_scanner_config("nuclei")` directly instead of `get_enabled_adapters`, cleanly isolating DAST from SAST language detection
- Scan queue worker reads `target_url` from the DB record and passes it through to `run_scan`, completing the end-to-end chain
- DAST-04 requires zero template changes: the existing `finding.tool` data-driven badge system in `report.html.j2` handles `tool="nuclei"` automatically

21 phase 13 tests pass (10 NucleiAdapter unit tests + 7 ScanRequest validation tests + 4 orchestrator routing tests), no warnings at test level.

---

_Verified: 2026-03-23T12:00:00Z_
_Verifier: Claude (gsd-verifier)_
