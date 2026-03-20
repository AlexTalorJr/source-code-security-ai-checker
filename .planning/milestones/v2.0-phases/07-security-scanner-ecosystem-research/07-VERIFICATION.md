---
phase: 07-security-scanner-ecosystem-research
verified: 2026-03-20T20:00:00Z
status: passed
score: 12/12 must-haves verified
re_verification: false
---

# Phase 7: Security Scanner Ecosystem Research Verification Report

**Phase Goal:** Research the open-source security scanner ecosystem to produce a comprehensive report evaluating SAST, SCA, DAST, and secrets scanning tools across all supported languages, with priority-ranked recommendations for integration.
**Verified:** 2026-03-20
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

The phase has two plans, each with their own must_haves. All truths are verified against the actual content of `07-SCANNER-ECOSYSTEM-REPORT.md` (1416 lines).

#### Plan 01 Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Every language (Python, PHP, JS/TS, Go, Rust, Java, C#, C/C++, Ruby) has a dedicated section | VERIFIED | Lines 38, 148, 211, 276, 355, 430, 521, 604, 661 — all 9 sections present |
| 2 | Existing tools (Semgrep, Cppcheck, Psalm, Gitleaks, Trivy, Checkov) are re-evaluated with current status | VERIFIED | Each existing tool has a re-evaluation sub-section with status notes |
| 3 | SCA tools are compared with Trivy as baseline | VERIFIED | Lines 746-873 — Trivy marked as "Keep as primary SCA," Grype and Dep-Check evaluated against it |
| 4 | DAST tools are assessed for integration feasibility | VERIFIED | Lines 877-1019 — dedicated feasibility section with integration notes for all 3 tools |
| 5 | Secrets scanners (Gitleaks vs TruffleHog) are compared | VERIFIED | Lines 1022-1103 — full comparison matrix, Gitleaks recommended as primary |
| 6 | Each recommended tool has a research card with CLI, Docker install, output format, config snippet, effort estimate | VERIFIED | Bandit (L78-130), gosec (L282-350), cargo-audit (L362-426), Brakeman (L666-742), Grype (L787-837), etc. — all have complete research cards |
| 7 | Each language section ends with a comparison matrix | VERIFIED | Lines 131, 195, 260, 339, 413, 503, 586, 644, 729 — 9 comparison matrices present |

#### Plan 02 Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 8 | Plugin architecture patterns are researched with a concrete recommendation | VERIFIED | Lines 1161-1270 — config-driven registry recommended with full rationale, migration path, and implementation sketch |
| 9 | SARIF evaluation concludes whether to adopt SARIF as intermediate format | VERIFIED | Lines 1106-1158 — 8/13 tools support SARIF, optional parse_sarif() helper recommended |
| 10 | Orchestration improvements (parallel execution, incremental scanning) are documented | VERIFIED | Lines 1272-1343 — parallel execution assessed, incremental scanning design with 5 capable/4 non-capable tools documented |
| 11 | A priority-ranked list of tools exists with T-shirt effort estimates | VERIFIED | Lines 1345-1416 — 9 tools ranked 1-9 across 3 tiers, each with Effort column (S/M/L) |
| 12 | The report is complete and ready for human review | VERIFIED | Summary 07-02 documents human review checkpoint completed and approved |

**Score:** 12/12 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `.planning/phases/07-security-scanner-ecosystem-research/07-SCANNER-ECOSYSTEM-REPORT.md` | Comprehensive research report covering per-language SAST, SCA, DAST, secrets scanning | VERIFIED | 1416 lines, all 8 required sections present |
| `07-SCANNER-ECOSYSTEM-REPORT.md` | Contains "## Python" section header | VERIFIED | Line 38 |
| `07-SCANNER-ECOSYSTEM-REPORT.md` | Contains "## Priority" section (Plan 02 artifact) | VERIFIED | Line 1345: "## Final Priority Matrix and Recommendations" |

All artifacts exist, are substantive (1416 lines of dense research content, no placeholder sections), and the report is self-contained.

---

### Key Link Verification

#### Plan 01 Key Link: Config snippets match config.yml format

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| Research card config snippets | `config.yml` scanners format | `enabled/timeout/extra_args` pattern | VERIFIED | All config snippets use `scanners: {name}: enabled: "auto", timeout: NNN, extra_args: [...]` matching actual `config.yml` structure exactly. Confirmed against live `config.yml`. |

#### Plan 02 Key Links

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| Plugin architecture recommendation | Existing `config.yml` + `ScannersConfig` pattern | Config-driven registry extends existing pattern | VERIFIED | Lines 1192-1268: recommendation explicitly extends existing `config.yml` scanners pattern with optional `adapter_class` field; migration path documented |
| Priority matrix | Per-language recommendations from Plan 01 | Consolidates all tool recommendations into ranked list | VERIFIED | Lines 1349-1378: all 4 Tier 1 tools (gosec/Brakeman/Bandit/cargo-audit) match Plan 01 recommendations; "Tier 1...Tier 2...Tier 3" structure present at lines 1349, 1360, 1370 |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| SCAN-01 | 07-01-PLAN | Research SAST tools per language (Python, PHP, JS/TS, Go, Rust, Java, C#, C/C++, Ruby) | SATISFIED | 9 dedicated per-language sections each with tool evaluations |
| SCAN-02 | 07-01-PLAN | Research SCA tools for dependency vulnerability detection | SATISFIED | Lines 746-873: Trivy re-eval, Grype card, OWASP Dep-Check evaluated |
| SCAN-03 | 07-01-PLAN | Research DAST tools applicable to web applications | SATISFIED | Lines 877-1019: ZAP, Nuclei, Nikto with integration feasibility assessment |
| SCAN-04 | 07-01-PLAN | Evaluate scanner configuration best practices — rulesets, severity tuning, false positive reduction | SATISFIED | Every research card includes "False positive reduction" section with specific flags and configs |
| SCAN-05 | 07-02-PLAN | Research scanner plugin/adapter patterns — add new scanners without code changes | SATISFIED | Lines 1161-1270: 4 patterns compared, config-driven registry recommended with concrete implementation |
| SCAN-06 | 07-01-PLAN | Document integration requirements per tool (installation, CLI, output format, licensing) | SATISFIED | Every research card includes: Purpose, License, Output formats, CLI usage, Docker install, SARIF support, Integration effort |
| SCAN-07 | 07-02-PLAN | Produce actionable recommendations with priority ranking | SATISFIED | Lines 1345-1416: 9-tool priority matrix with T-shirt estimates, 3-tier structure, suggested phasing (Phases 8-10) |

**Coverage:** 7/7 SCAN requirements satisfied. No orphaned requirements detected (all 7 are mapped to this phase in `REQUIREMENTS.md` and claimed by plans).

---

### Anti-Patterns Found

Scanned `07-SCANNER-ECOSYSTEM-REPORT.md`, `07-01-SUMMARY.md`, `07-02-SUMMARY.md`.

| File | Pattern | Severity | Notes |
|------|---------|----------|-------|
| None found | — | — | No TODO/FIXME/placeholder comments. No empty sections. Two pattern instances of `xxxx` appeared at lines 388 and 556 but both are intentional example syntax in CLI flags (`--ignore RUSTSEC-xxxx-xxxx`, `#pragma warning disable SCSxxxx`) — not placeholders. |

No anti-patterns detected.

---

### Human Verification Required

One item was conducted as part of the phase execution:

**Task 2 of Plan 02 was a `checkpoint:human-verify` gate.** The 07-02-SUMMARY.md documents this was completed: "Research report reviewed and approved by human." No additional human verification is needed for this verification pass.

---

### Specific Acceptance Criteria Cross-Check

All acceptance criteria from both plans were verified against the actual report content:

**Plan 01 Acceptance Criteria:**
- [x] 07-SCANNER-ECOSYSTEM-REPORT.md exists and is non-empty (1416 lines)
- [x] "## Python" section header (line 38)
- [x] "## PHP" section header (line 148)
- [x] "## JavaScript/TypeScript" section header (line 211)
- [x] "## Go" section header (line 276)
- [x] "## Rust" section header (line 355)
- [x] "## Java" section header (line 430)
- [x] "## C#" section header (line 521 as `## C\#`)
- [x] "## C/C++" section header (line 604)
- [x] "## Ruby" section header (line 661)
- [x] Each language section contains "### Comparison Matrix" (9 matrices at lines 131, 195, 260, 339, 413, 503, 586, 644, 729)
- [x] gosec entry contains `enabled: "auto"` config snippet (line 295)
- [x] Bandit entry contains `enabled: "auto"` config snippet (line 87)
- [x] Brakeman entry contains `enabled: "auto"` config snippet (line 680)
- [x] eslint-plugin-security is marked "Not Recommended" (lines 227, 258, 270)
- [x] SpotBugs entry notes "requires compiled .class files" concern (line 476: "CRITICAL CONCERN: Requires compiled .class files.")
- [x] Semgrep re-evaluation mentions Opengrep fork (lines 55-59)

**Plan 02 Acceptance Criteria:**
- [x] "## SARIF Evaluation" section (line 1106)
- [x] "## Plugin Architecture Patterns" section (line 1161)
- [x] "## Orchestration Improvements" section (line 1272)
- [x] "## Final Priority Matrix" section (line 1345)
- [x] Plugin architecture section recommends "config-driven registry" pattern (line 1194)
- [x] Plugin section contains example config with "adapter_class" field (lines 1221, 1227, 1233, 1239)
- [x] SARIF section lists 8 tools with SARIF support and 5 without (line 1128: "8 of 13 tools support SARIF natively")
- [x] SARIF section recommends "parse_sarif()" shared helper (lines 1149-1150)
- [x] Orchestration section documents file-list-capable tools (Semgrep, Bandit, gosec, Brakeman, Gitleaks) and full-context-required tools (SpotBugs, Trivy, Checkov, cargo-audit)
- [x] Priority matrix has 3 tiers with 9 tools ranked 1-9 (lines 1349-1378)
- [x] Priority matrix columns: Priority, Tool, Type, Language, Effort, Docker Size, SARIF, Justification
- [x] "Not Recommended" sub-section lists eslint-plugin-security, OWASP Dependency-Check, Nikto, TruffleHog (lines 1383-1386)
- [x] Suggested implementation order mentions Phase 8, 9, 10 (lines 1402-1404)
- [x] "Opengrep" mention with "monitor but don't switch" recommendation (line 59, 1395)

**Commits verified:**
- `06eb733` — feat(07-01): write per-language SAST research sections
- `2b15733` — feat(07-01): write SCA, DAST, and secrets scanning cross-cutting sections
- `4094bc2` — feat(07-02): add SARIF evaluation, plugin architecture, orchestration, and priority matrix sections

All 3 feature commits exist in the repository.

---

## Summary

Phase 7 goal is fully achieved. The `07-SCANNER-ECOSYSTEM-REPORT.md` is a substantive 1416-line research document that delivers every item promised by the phase goal: comprehensive per-language tool evaluations for all 9 languages, SCA comparison with Trivy as baseline, DAST feasibility assessment, secrets scanner comparison, SARIF adoption analysis, plugin architecture recommendation (config-driven registry), orchestration improvement design, and a priority-ranked 9-tool implementation matrix with T-shirt effort estimates.

All 7 SCAN requirements are satisfied, all 12 must-have truths are verified, all key links are confirmed wired, no anti-patterns found, and the human review checkpoint was completed during execution.

---

_Verified: 2026-03-20_
_Verifier: Claude (gsd-verifier)_
