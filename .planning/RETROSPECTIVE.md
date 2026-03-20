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

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 | multiple | 6 | Foundation → full platform build |
| v2.0 | 1 | 1 | Research-only milestone, single session |

### Top Lessons (Verified Across Milestones)

1. Structured planning (research → plan → execute → verify) catches gaps early
2. Config-driven patterns scale better than hard-coded registries
