---
phase: 07-security-scanner-ecosystem-research
plan: 01
subsystem: research
tags: [sast, sca, dast, secrets, semgrep, bandit, gosec, brakeman, cargo-audit, grype, nuclei, gitleaks, trivy]

# Dependency graph
requires:
  - phase: none
    provides: first plan in phase 07
provides:
  - "Comprehensive scanner ecosystem research report covering 9 languages, SCA, DAST, and secrets scanning"
  - "Per-tool research cards with CLI, Docker, SARIF, config snippets, FindingSchema mappings"
  - "Comparison matrices for each language and cross-cutting section"
affects: [07-02-PLAN, future scanner implementation phases]

# Tech tracking
tech-stack:
  added: []
  patterns: ["per-tool research card template", "comparison matrix format"]

key-files:
  created:
    - ".planning/phases/07-security-scanner-ecosystem-research/07-SCANNER-ECOSYSTEM-REPORT.md"
  modified: []

key-decisions:
  - "Bandit recommended as Python complement to Semgrep (S effort, 47 checks)"
  - "gosec recommended for Go SAST (S effort, 70+ checks, JSON/SARIF)"
  - "Brakeman recommended for Rails Ruby SAST (S effort, 33 vuln types)"
  - "cargo-audit recommended for Rust SCA (S effort, RustSec DB)"
  - "eslint-plugin-security NOT recommended for JS/TS (Semgrep covers it better)"
  - "SpotBugs noted as high effort due to compilation requirement"
  - "Trivy kept as primary SCA, Grype considered as complement for EPSS/KEV scoring"
  - "Nuclei recommended if DAST pursued, ZAP deferred"
  - "Gitleaks kept as primary secrets scanner, TruffleHog as optional complement"
  - "Semgrep Opengrep fork: monitor but do not switch yet"

patterns-established:
  - "Research card template: Purpose, Languages, License, Output, CLI, Docker, SARIF, Effort, Config, FindingSchema, FP reduction, Pros, Cons"
  - "Config snippets follow scanners.{name}.enabled/timeout/extra_args pattern"

requirements-completed: [SCAN-01, SCAN-02, SCAN-03, SCAN-04, SCAN-06]

# Metrics
duration: 5min
completed: 2026-03-20
---

# Phase 07 Plan 01: Scanner Ecosystem Research Report Summary

**Per-language SAST research for 9 languages plus SCA/DAST/secrets cross-cutting analysis with tool research cards, config snippets, and comparison matrices**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-20T19:18:42Z
- **Completed:** 2026-03-20T19:24:15Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- Wrote 9 per-language SAST sections with tool research cards covering Python, PHP, JS/TS, Go, Rust, Java, C#, C/C++, Ruby
- Identified 4 recommended additions (Bandit, gosec, cargo-audit, Brakeman) and 1 not-recommended (eslint-plugin-security)
- Wrote SCA comparison (Trivy vs Grype vs OWASP Dep-Check), DAST feasibility (Nuclei vs ZAP vs Nikto), secrets comparison (Gitleaks vs TruffleHog)
- Every research card includes CLI usage, Docker install, SARIF support, config snippet, FindingSchema mapping, false positive reduction guidance

## Task Commits

Each task was committed atomically:

1. **Task 1: Write per-language SAST research sections** - `06eb733` (feat)
2. **Task 2: Write SCA, DAST, and secrets scanning cross-cutting sections** - `2b15733` (feat)

## Files Created/Modified
- `.planning/phases/07-security-scanner-ecosystem-research/07-SCANNER-ECOSYSTEM-REPORT.md` - Comprehensive scanner ecosystem research report (1098 lines)

## Decisions Made
- Bandit (Python), gosec (Go), Brakeman (Ruby), cargo-audit (Rust) recommended as Tier 1 additions
- eslint-plugin-security not recommended (14 rules vs Semgrep's 100+ JS/TS rules, Node.js runtime cost)
- SpotBugs documented as high value but high effort due to Java compilation requirement
- security-code-scan documented as medium effort due to .NET SDK dependency
- Grype considered as SCA complement for EPSS/KEV risk scoring, not replacement for Trivy
- Nuclei recommended as DAST starting point if DAST is pursued (M effort, 30MB, template-based)
- ZAP deferred (L effort, 500MB, JVM), Nikto not recommended (server-level only)
- Gitleaks kept as primary secrets scanner; TruffleHog as optional complement
- Semgrep Opengrep fork: monitor but do not switch yet (CE works well, fork backward compatible)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Research report complete with per-language sections, SCA, DAST, and secrets sections
- Plan 02 can now write SARIF evaluation, plugin architecture, orchestration improvements, and final priority matrix sections
- All tool research cards include config snippets matching existing config.yml format

## Self-Check: PASSED

- FOUND: `.planning/phases/07-security-scanner-ecosystem-research/07-SCANNER-ECOSYSTEM-REPORT.md`
- FOUND: `.planning/phases/07-security-scanner-ecosystem-research/07-01-SUMMARY.md`
- FOUND: commit `06eb733` (Task 1)
- FOUND: commit `2b15733` (Task 2)

---
*Phase: 07-security-scanner-ecosystem-research*
*Completed: 2026-03-20*
