# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v2.0 — Scanner Ecosystem

**Shipped:** 2026-03-20
**Phases:** 1 | **Plans:** 2 | **Sessions:** 1

### What Was Built
- 1416-line scanner ecosystem research report covering 13 tools across 9 languages
- Priority-ranked implementation roadmap (Tiers 1-3) with T-shirt effort estimates
- Architecture recommendations: config-driven plugin registry, SARIF helper, incremental scanning

### What Worked
- Research-heavy phase executed cleanly in a single session
- Wave-based execution with checkpoint for human review caught nothing to fix — plan quality was high
- Structured research cards (CLI, Docker, SARIF, config snippet, FindingSchema) made tool comparison systematic

### What Was Inefficient
- Milestone was research-only (1 phase) — overhead of milestone ceremony (archive, retrospective) is high relative to work done
- Consider bundling research phases into implementation milestones in the future

### Patterns Established
- Per-tool research card template with config snippets matching existing `config.yml` format
- Comparison matrices per language section for quick decision-making
- Tiered priority ranking (Tier 1: high value/low effort first)

### Key Lessons
1. Research milestones work well as standalone phases — clear deliverable, easy to verify
2. Human review checkpoint at end of research report ensures quality before closing
3. Config-driven patterns should extend existing conventions, not introduce new frameworks

### Cost Observations
- Model mix: ~80% opus (executors), ~20% sonnet (verifier)
- Sessions: 1
- Notable: Research plans are token-heavy due to large report generation but complete quickly

---

## Milestone: v1.0.1 — Scanner Plugin Registry

**Shipped:** 2026-03-22
**Phases:** 4 | **Plans:** 8 | **Tasks:** 24
**Timeline:** 2 days (2026-03-21 → 2026-03-22)

### What Was Built
- Config-driven plugin registry replacing hard-coded ALL_ADAPTERS list
- 4 Tier-1 scanner adapters: gosec (Go), Bandit (Python), Brakeman (Ruby), cargo-audit (Rust)
- Docker image with all 12 scanners, multi-arch (x86_64, ARM64)
- Bilingual documentation updated across 5 languages (40+ doc files)
- cargo-audit tool_name fix resolving runtime KeyError on Rust projects

### What Worked
- Milestone audit caught the cargo-audit tool_name/config key mismatch that unit tests missed — justified the audit step
- Gap closure phase (Phase 11) was fast and focused — well-scoped bug fix completed in one plan
- Research → plan → execute → verify pipeline caught real integration issues
- Config-driven registry pattern worked exactly as v2.0 research recommended

### What Was Inefficient
- cargo-audit KeyError was a 1-line fix but required a full phase cycle (context → plan → execute → verify) — overhead for trivial fixes
- Phase 8-9 roadmap checkboxes weren't updated to `[x]` during execution, leaving stale state until milestone completion
- 5 flaky async tests in phase_03/test_orchestrator_ai.py — test isolation debt from v1.0 still accumulating

### Patterns Established
- Adapter pattern: tool_name must use underscores matching config.yml keys
- ScannerRegistry dynamic loading via importlib with graceful error handling
- Per-phase test directories (tests/phase_XX/) for isolation
- Confidence-weighted severity mapping (Bandit's 9-cell matrix, Brakeman's confidence downgrade)

### Key Lessons
1. Milestone audits are worth the cost — the cargo-audit mismatch would have shipped broken without it
2. tool_name convention (underscore matching config keys) should be documented and enforced in base class
3. Research recommendations (v2.0) translated directly into implementation — research-first approach validated
4. Doc translation across 5 languages is mechanical but high-volume — plan accordingly

### Cost Observations
- Model mix: ~70% opus (executors, planners), ~30% sonnet (checkers, verifiers)
- Sessions: 2
- Notable: Phase 11 (gap closure) used minimal tokens — skip-research + single plan + skip-Nyquist

---

## Milestone: v1.0.2 — Scanner UI, DAST & RBAC

**Shipped:** 2026-03-24
**Phases:** 5 | **Plans:** 14 | **Tasks:** 29
**Timeline:** 2 days (2026-03-23 → 2026-03-24)

### What Was Built
- RBAC with JWT auth: user accounts, API tokens, 3 roles (admin/scanner/viewer), dashboard login
- Nuclei DAST adapter: dynamic scanning via target URLs, JSONL parsing, multi-arch Docker
- Scanner configuration UI: card grid with three-state toggles, CodeMirror YAML editor
- Scan profiles: named scanner presets, API + dashboard selection, per-scanner overrides
- Bilingual documentation: all v1.0.2 features in 5 languages (EN/RU/FR/ES/IT)
- Gap closure: dashboard DAST form, schema migration fix, Bearer token auth in all docs

### What Worked
- Milestone audit (pre-completion) caught 3 real gaps: missing dashboard target_url field, missing inline migration entry, stale X-API-Key references — all fixed in Phase 16
- Phase 12 (RBAC, 5 plans) was the largest phase yet — wave-based execution handled it cleanly
- Research phase accurately predicted PyJWT + pwdlib as auth stack replacements
- Parallel phase execution (13 + 14 after 12) saved time — two independent feature tracks
- Reusing existing UI patterns (accordion cards from Phase 14 in Phase 15) kept UI consistent

### What Was Inefficient
- 150 files changed including 15 doc files x 5 languages — translation volume is the dominant cost for doc phases
- Phase 16 gap closure was 3 small fixes but required full phase ceremony (plan → execute → verify)
- Roadmap plan checkboxes still show `[ ]` even after execution — only milestone completion marks the summary

### Patterns Established
- Dual auth pattern: JWT cookies for dashboard, Bearer tokens for API/CI
- Three-state toggle pattern (On/Auto/Off) for scanner enable UI
- URL-as-path pattern for DAST: target_url stored in file_path field
- Scan profiles as named presets over config.yml duplication
- _get_dashboard_user returns None (not 401) for redirect-based login flow

### Key Lessons
1. Milestone audits continue to pay for themselves — 3 real gaps caught in v1.0.2
2. Auth decisions (JWT library, password hashing) matter long-term — research phase prevented choosing abandoned libraries
3. Dashboard and API should always ship features in parallel — Phase 13 shipped DAST API-only, requiring Phase 16 to add dashboard form
4. 5-language docs are a volume multiplier — consider tooling for translation in future milestones
5. CodeMirror via CDN (no build step) was the right call for a Python-first project

### Cost Observations
- Model mix: ~70% opus (executors, planners), ~30% sonnet (checkers, verifiers)
- Sessions: 2
- Notable: Phase 16 (gap closure) was very efficient — 1 plan, 3 tasks, 3 commits

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 | multiple | 6 | Foundation → full platform build |
| v2.0 | 1 | 1 | Research-only milestone, single session |
| v1.0.1 | 2 | 4 | Research → implementation pipeline validated; milestone audit caught real bug |
| v1.0.2 | 2 | 5 | Largest milestone (14 plans); parallel phases; milestone audit caught 3 gaps |

### Top Lessons (Verified Across Milestones)

1. Structured planning (research → plan → execute → verify) catches gaps early
2. Config-driven patterns scale better than hard-coded registries
3. Milestone audits pay for themselves — they catch integration gaps that unit tests miss
4. Research-first approach (v2.0 research → v1.0.1 implementation) produces well-scoped work
5. API and dashboard features should ship together — shipping API-only creates gap-closure overhead (v1.0.2 lesson)
6. 5-language documentation is a volume multiplier — consider automation for future milestones
