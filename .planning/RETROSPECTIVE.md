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

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 | multiple | 6 | Foundation → full platform build |
| v2.0 | 1 | 1 | Research-only milestone, single session |
| v1.0.1 | 2 | 4 | Research → implementation pipeline validated; milestone audit caught real bug |

### Top Lessons (Verified Across Milestones)

1. Structured planning (research → plan → execute → verify) catches gaps early
2. Config-driven patterns scale better than hard-coded registries
3. Milestone audits pay for themselves — they catch integration gaps that unit tests miss
4. Research-first approach (v2.0 research → v1.0.1 implementation) produces well-scoped work
