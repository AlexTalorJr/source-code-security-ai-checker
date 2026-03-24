---
phase: 15-scan-profiles-and-documentation
verified: 2026-03-23T19:00:57Z
status: passed
score: 3/3 success criteria verified
re_verification: false
---

# Phase 15: Scan Profiles and Documentation Verification Report

**Phase Goal:** Users can select predefined scan configurations and all v1.0.2 features are documented
**Verified:** 2026-03-23T19:00:57Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (from ROADMAP.md Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Admin can create a named scan profile that saves a specific scanner configuration | VERIFIED | `src/scanner/api/config.py` lines 196–290 implement full CRUD at `/api/config/profiles`; `src/scanner/config.py` has `ScanProfileConfig` + `ScanProfileScannerConfig` models and `profiles:` field on `ScannerSettings`; config.yml.example shows `profiles:` section |
| 2 | User can select a scan profile when triggering a scan via API or dashboard, and only that profile's scanners execute | VERIFIED | `src/scanner/api/schemas.py` l.19: `profile: str | None = None` on `ScanRequest`; `src/scanner/api/scans.py` l.70–89: validates profile exists and sets `profile_name=body.profile` on `ScanResult`; `src/scanner/core/orchestrator.py` l.151–171: filters `settings.scanners` to profile-listed only via `model_copy`; `src/scanner/core/scan_queue.py` l.78+99: passes `profile_name` through to `run_scan`; `src/scanner/dashboard/router.py` l.660: `profile_name=profile or None` in dashboard start_scan; `src/scanner/dashboard/templates/history.html.j2` l.101: profile dropdown with `(No profile)` default |
| 3 | Bilingual documentation (EN, RU, FR, ES, IT) covers RBAC setup, scanner config UI usage, DAST scanning, and scan profiles | VERIFIED | All 15 doc files confirmed present (3 x 5 languages); EN admin-guide l.378 has RBAC section, l.480 has Scan Profiles, l.537 has DAST; all 5 `api.md` files use Bearer auth (zero X-API-Key matches); RU/FR/ES/IT translations have equivalent sections in their respective languages |

**Score: 3/3 truths verified**

---

## Required Artifacts

### Plan 15-01 Artifacts

| Artifact | Provided | Status | Details |
|----------|----------|--------|---------|
| `src/scanner/config.py` | `ScanProfileScannerConfig`, `ScanProfileConfig`, `profiles` on `ScannerSettings` | VERIFIED | l.34: `class ScanProfileScannerConfig`, l.42: `class ScanProfileConfig`, l.168: `profiles: dict[str, ScanProfileConfig] = {}` |
| `src/scanner/api/config.py` | Profile CRUD endpoints (GET/POST/PUT/DELETE /api/config/profiles) | VERIFIED | Routes at l.196, 205, 237, 250, 275; `YAML_RESERVED` at l.173; `ProfileCreateRequest` at l.185 |
| `src/scanner/models/scan.py` | `profile_name` column on `ScanResult` | VERIFIED | l.25: `profile_name = Column(String(200), nullable=True)` |
| `src/scanner/core/orchestrator.py` | Profile override logic before scanner execution | VERIFIED | l.114: `profile_name: str | None = None` param; l.152: `settings.profiles.get(profile_name)`; l.171: `settings.model_copy(update={"scanners": filtered_scanners})` |
| `tests/phase_15/test_profile_crud.py` | CRUD API tests for profiles | VERIFIED | 239 lines (min 100); 17 test cases |
| `tests/phase_15/test_profile_scan.py` | Profile scan integration tests | VERIFIED | 211 lines (min 50); 7 test cases |

### Plan 15-02 Artifacts

| Artifact | Provided | Status | Details |
|----------|----------|--------|---------|
| `src/scanner/dashboard/templates/scanners.html.j2` | Profiles tab with card grid, inline edit form, New Profile button | VERIFIED | l.88: `data-tab="profiles"` button; l.165: `id="tab-profiles"` panel; l.172: `id="new-profile-card"`; `saveNewProfile()`, `updateProfile()`, `deleteProfile()` JS functions; `scanner-checklist` CSS class |
| `src/scanner/dashboard/templates/history.html.j2` | Profile dropdown on scan form, profile column in history table | VERIFIED | l.101: `name="profile"` select; l.102: `(No profile)` default; l.119: `<th>Profile</th>`; l.132: `{{ scan.profile_name }}` |
| `src/scanner/dashboard/router.py` | Profile data passed to templates | VERIFIED | l.987: `profiles=profiles`; l.988: `all_scanner_names=all_scanner_names`; l.402: `profile_names=profile_names`; l.660: `profile_name=profile or None` |

### Plan 15-03 Artifacts

| Artifact | Provided | Status | Details |
|----------|----------|--------|---------|
| `docs/en/admin-guide.md` | RBAC setup, scanner config UI, scan profiles management | VERIFIED | Contains "Scan Profiles" (l.480), "RBAC" (l.378), "DAST" (l.537), "Scanner Configuration" (l.452) |
| `docs/en/user-guide.md` | Using scan profiles, DAST scanning, dashboard login | VERIFIED | Contains "Scan Profiles", "DAST", dashboard login section |
| `docs/en/api.md` | Bearer auth, profile endpoints, scanner config endpoints, DAST trigger | VERIFIED | l.11: Bearer auth; zero X-API-Key; `/api/config/profiles` documented; `target_url` documented |
| `docs/ru/admin-guide.md` | Russian translation of admin guide | VERIFIED | Contains "RBAC" (l.378), "DAST" (l.537), `profiles:` code (l.499) in Russian prose |
| `tests/phase_15/test_docs.py` | Doc existence and section verification tests | VERIFIED | 92 lines (min 40); 5 test functions covering all 5 languages |

---

## Key Link Verification

### Plan 15-01 Key Links

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `src/scanner/api/config.py` | `config.yml` | `read_config`/`write_config` for profile persistence | VERIFIED | l.196–290: all CRUD endpoints call `read_config()`/`write_config()`; `config["profiles"]` key used |
| `src/scanner/core/orchestrator.py` | `src/scanner/config.py` | `settings.profiles.get(profile_name)` for override | VERIFIED | l.152: `profile = settings.profiles.get(profile_name)` then `model_copy` at l.171 |
| `src/scanner/api/scans.py` | `src/scanner/models/scan.py` | `profile_name` field on `ScanResult` creation | VERIFIED | l.89: `profile_name=body.profile` on `ScanResult` constructor |

### Plan 15-02 Key Links

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `scanners.html.j2` | `/api/config/profiles` | `fetch` POST/PUT/DELETE for profile CRUD | VERIFIED | l.498: `fetch('/api/config/profiles', ...)` POST; l.555: `fetch('.../'+profileName, ...)` PUT; l.577: DELETE |
| `src/scanner/dashboard/router.py` | `config.yml` | Read profiles from config for template rendering | VERIFIED | l.982: `config.get("profiles", {})` read; passed as `profiles=profiles` to template |
| `history.html.j2` | `/dashboard/start-scan` | Form submit with `profile` field | VERIFIED | l.101: `<select name="profile">` inside `.start-scan-form`; router l.660 reads `profile: str = Form(default="")` |

### Plan 15-03 Key Links

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `docs/en/api.md` | `src/scanner/api/` | Endpoint docs match actual API routes | VERIFIED | Profile CRUD routes (`/api/config/profiles`), scanner config routes (`/api/config`), DAST `target_url`, all present in docs |
| `docs/en/admin-guide.md` | Dashboard | UI usage instructions reference actual pages | VERIFIED | References `/dashboard/scanners`, `/dashboard/tokens`, `/dashboard/users` — all actual routes |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| CONF-04 | 15-01, 15-02 | Admin can create and save named scan profiles | SATISFIED | Profile CRUD API at `/api/config/profiles`; config.yml persistence; Profiles tab UI in dashboard |
| CONF-05 | 15-01, 15-02 | User can select a scan profile when triggering a scan via API or dashboard | SATISFIED | `profile` field on `ScanRequest`; profile validation in `trigger_scan`; profile dropdown on dashboard scan form; orchestrator filters scanners to profile-listed only |
| INFRA-04 | 15-03 | Bilingual documentation updated with RBAC, scanner config UI, and DAST features (EN, RU, FR, ES, IT) | SATISFIED | All 15 doc files (3 x 5 languages) updated; Bearer auth used throughout; RBAC, DAST, scan profiles covered in all languages |

**No orphaned requirements.** REQUIREMENTS.md maps exactly CONF-04, CONF-05, INFRA-04 to Phase 15 — all three are claimed across the three plans and verified in the codebase.

---

## Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| `src/scanner/core/orchestrator.py` | `datetime.utcnow()` deprecated (Python 3.12 warning) | Info | No functional impact; pre-existing pattern, not introduced by this phase |
| `src/scanner/core/scan_queue.py` | `datetime.utcnow()` deprecated | Info | Same — pre-existing, not a phase 15 gap |

No blockers or warnings introduced by phase 15 changes. The deprecation warnings are pre-existing across the codebase.

---

## Human Verification Required

### 1. Profiles Tab Visual Layout

**Test:** Start the app (`python3 -m scanner.main`), log in as admin, navigate to `/dashboard/scanners`, click the "Profiles" tab.
**Expected:** Third tab appears alongside Scanners and YAML Editor; empty state shown if no profiles; "New Profile" button visible.
**Why human:** Visual rendering and tab switching behavior cannot be verified programmatically.

### 2. Profile Create/Edit/Delete from UI

**Test:** Click "New Profile", fill in name `quick_test`, description, check 2 scanners, click "Save Profile". Then click the card to edit, then delete with confirm dialog.
**Expected:** Card appears with name, description, and scanner badges. Edit pre-fills form fields. Delete shows `confirm()` dialog and removes card on confirm.
**Why human:** JavaScript interaction, DOM manipulation, and fetch behavior require a browser.

### 3. Profile Dropdown on Scan Form

**Test:** Navigate to `/dashboard/history`, click "Start New Scan", inspect the profile dropdown.
**Expected:** Dropdown shows "(No profile)" as default plus names of any defined profiles.
**Why human:** Dynamic data (profile names from config.yml) in rendered template requires visual inspection.

---

## Test Results

All 30 automated tests in `tests/phase_15/` pass:
- `tests/phase_15/test_profile_crud.py`: 17 tests — profile CRUD, auth (403 for non-admin), validation (name format, YAML reserved, duplicate, limit, empty scanners)
- `tests/phase_15/test_profile_scan.py`: 7 tests — scan trigger with profile, unknown profile returns 400, orchestrator filtering, DAST profile without nuclei
- `tests/phase_15/test_docs.py`: 6 tests — all 15 files exist, admin-guide sections, user-guide sections, Bearer auth in all api.md files, profile endpoints in all api.md files, no X-API-Key

**Run:** `python3 -m pytest tests/phase_15/ -q` → `30 passed, 25 warnings in 23.20s`

---

## Gaps Summary

No gaps. All three success criteria are fully satisfied:

1. **Admin can create named scan profiles** — CRUD API fully implemented and tested; config.yml persistence verified; Profiles tab in dashboard UI wired to API.

2. **User can select a profile on scan trigger** — Profile field on `ScanRequest`, validation on trigger, orchestrator filters scanners to only those in the profile, `profile_name` recorded on `ScanResult`, profile dropdown on dashboard form, profile column in history table.

3. **Documentation in 5 languages** — All 15 doc files present and substantive; Bearer auth throughout (zero X-API-Key); RBAC, scanner config UI, DAST, scan profiles covered in all languages; doc tests pass.

---

_Verified: 2026-03-23T19:00:57Z_
_Verifier: Claude (gsd-verifier)_
