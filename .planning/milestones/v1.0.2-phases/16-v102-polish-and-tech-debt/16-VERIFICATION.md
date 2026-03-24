---
phase: 16-v102-polish-and-tech-debt
verified: 2026-03-24T11:00:00Z
status: passed
score: 3/3 must-haves verified
re_verification: false
---

# Phase 16: v1.0.2 Polish and Tech Debt Verification Report

**Phase Goal:** Close v1.0.2 milestone audit gaps — dashboard target_url field, schema migration completeness, docs auth references
**Verified:** 2026-03-24T11:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #   | Truth                                                                               | Status     | Evidence                                                                                  |
| --- | ----------------------------------------------------------------------------------- | ---------- | ----------------------------------------------------------------------------------------- |
| 1   | Dashboard scan form has a target_url input field for DAST scans                     | VERIFIED   | `history.html.j2` line 91: `<input type="text" id="target_url" name="target_url" ...>`   |
| 2   | target_url column migration exists in _apply_schema_updates inline dict             | VERIFIED   | `main.py` line 37: `"target_url": "ALTER TABLE scans ADD COLUMN target_url VARCHAR(500)"` |
| 3   | No X-API-Key references remain in any docs/ files across all 5 languages            | VERIFIED   | `grep -r "X-API-Key" docs/` returns 0 matches; Bearer replacements confirmed in all 15 files |

**Score:** 3/3 truths verified

### Required Artifacts

| Artifact                                                          | Expected                                     | Status   | Details                                                             |
| ----------------------------------------------------------------- | -------------------------------------------- | -------- | ------------------------------------------------------------------- |
| `src/scanner/main.py`                                             | target_url in inline migration dict          | VERIFIED | Line 37 contains `"target_url": "ALTER TABLE scans ADD COLUMN target_url VARCHAR(500)"` |
| `src/scanner/dashboard/templates/history.html.j2`                | target_url input field in scan form          | VERIFIED | Lines 90-91: label + input with `name="target_url"` present        |
| `src/scanner/dashboard/router.py`                                 | target_url Form parameter in start_scan      | VERIFIED | Line 644: `target_url: str = Form(default="")`, line 659: `target_url=target_url or None` |
| `docs/{en,ru,fr,es,it}/architecture.md` (5 files)                | Bearer token auth description, no X-API-Key  | VERIFIED | Line 170 in each file contains language-appropriate Bearer description |
| `docs/{en,ru,fr,es,it}/devops-guide.md` (5 files)                | Jenkins Authorization Bearer header          | VERIFIED | Line 133/131 in each: `name: 'Authorization', value: "Bearer ${SCANNER_API_TOKEN}"` |
| `docs/{en,ru,fr,es,it}/transfer-guide.md` (5 files)              | curl Authorization Bearer header             | VERIFIED | Line 130 in each: `-H "Authorization: Bearer nvsec_your_token"` |

### Key Link Verification

| From                                         | To                                     | Via                                         | Status   | Details                                                    |
| -------------------------------------------- | -------------------------------------- | ------------------------------------------- | -------- | ---------------------------------------------------------- |
| `history.html.j2`                            | `router.py`                            | form POST `name="target_url"` -> Form param  | WIRED    | Template line 91 `name="target_url"` → router line 644 `target_url: str = Form(default="")` |
| `router.py`                                  | `src/scanner/models/scan.py`           | `ScanResult(target_url=target_url)`          | WIRED    | Router line 659 `target_url=target_url or None`; model line 19 `target_url = Column(String(500))` |

### Requirements Coverage

| Requirement | Source Plan    | Description                                             | Status    | Evidence                                                                              |
| ----------- | -------------- | ------------------------------------------------------- | --------- | ------------------------------------------------------------------------------------- |
| DAST-02     | 16-01-PLAN.md  | Scan API accepts optional target_url field for DAST scans | SATISFIED | Dashboard form now exposes target_url to users; API layer (Phase 13) and orchestrator routing already covered. Phase 16 extends coverage to dashboard form layer. REQUIREMENTS.md lists Phase 13 as primary satisfier; Phase 16 completes the dashboard surface. |

**Note on DAST-02 ownership:** REQUIREMENTS.md coverage table records DAST-02 as Phase 13. Phase 16 claims partial re-satisfaction, adding the dashboard form input that was absent from Phase 13. This is additive, not a contradiction — the core API requirement was met in Phase 13; Phase 16 closes the dashboard gap that surfaced in the v1.0.2 audit.

### Anti-Patterns Found

No anti-patterns found in the three modified code files. The `placeholder=` attributes in `history.html.j2` are legitimate HTML input placeholders, not code stubs.

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| —    | —    | —       | —        | —      |

### Human Verification Required

#### 1. Dashboard DAST Scan Form UX

**Test:** Load the dashboard scan history page in a browser, click "New Scan," and confirm the "Target URL (DAST)" input field is visible in the form row alongside Path, Repo URL, and Branch.
**Expected:** Input field labelled "Target URL (DAST)" is rendered and accepts a URL; submitting with a target_url value creates a queued scan record with that URL stored.
**Why human:** Visual rendering and form submission flow cannot be confirmed by static grep.

### Gaps Summary

No gaps. All three must-have truths are fully satisfied:

- **Truth 1 (dashboard form field):** `history.html.j2` line 91 contains the complete `<input>` element with `name="target_url"` and appropriate label/placeholder.
- **Truth 2 (migration dict):** `main.py` line 37 adds the `target_url VARCHAR(500)` column to `_apply_schema_updates` alongside all other schema migrations, completing the inline migration dict.
- **Truth 3 (zero X-API-Key in docs):** All 15 doc files updated across 5 languages. Zero `X-API-Key` occurrences remain. Architecture, devops-guide, and transfer-guide files now consistently use `Authorization: Bearer` syntax.

Both key links are wired end-to-end: form field → router Form parameter → ScanResult constructor → database column. The model column (`target_url = Column(String(500), nullable=True)`) was established in Phase 13 and is intact.

Commits `0885563` and `b9ef1c4` are verified present in git history and match the expected file change counts.

---

_Verified: 2026-03-24T11:00:00Z_
_Verifier: Claude (gsd-verifier)_
