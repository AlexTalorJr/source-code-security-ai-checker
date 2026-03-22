# Milestones

## v1.0.1 Scanner Plugin Registry (Shipped: 2026-03-22)

**Phases completed:** 4 phases, 8 plans, 24 tasks
**Git range:** `40cbb4f`..`e2b1965` (28 commits)
**Timeline:** 2026-03-21 → 2026-03-22 (2 days)

**Key accomplishments:**

- Config-driven plugin registry — scanners added via `config.yml` `adapter_class` without code changes
- 4 Tier-1 scanner adapters integrated: gosec (Go SAST), Bandit (Python SAST), Brakeman (Ruby/Rails SAST), cargo-audit (Rust SCA)
- Docker image ships all 12 scanners with multi-arch support (x86_64, ARM64)
- Bilingual documentation updated across 5 languages (EN, RU, FR, ES, IT) with 12 scanner cards and plugin registry docs
- Orchestrator migrated from hard-coded ALL_ADAPTERS to dynamic ScannerRegistry
- cargo-audit tool_name/config key mismatch fixed — Rust project scans work end-to-end

---

## v2.0 Scanner Ecosystem (Shipped: 2026-03-20)

**Phases completed:** 1 phase, 2 plans, 4 tasks
**Git range:** `06eb733`..`913f725` (5 commits)
**Artifact:** 1416-line scanner ecosystem research report

**Key accomplishments:**

- Researched 13 security scanning tools across 9 languages with per-tool research cards
- Recommended 4 Tier-1 tools for immediate integration: gosec (Go), Brakeman (Ruby), Bandit (Python), cargo-audit (Rust)
- Recommended config-driven plugin registry architecture extending existing config.yml
- Evaluated SARIF support (8/13 tools) — recommended shared `parse_sarif()` helper
- Assessed DAST feasibility — Nuclei recommended over ZAP for CLI-friendly integration
- Produced priority-ranked implementation roadmap: Phase 8 (Tier 1 + registry), Phase 9 (SARIF + Tier 2), Phase 10 (incremental + DAST)

---

## v1.0 MVP (Shipped: 2026-03-20)

**Phases completed:** 6 phases, 21 plans, 0 tasks

**Key accomplishments:**

- (none recorded)

---
