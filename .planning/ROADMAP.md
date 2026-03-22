# Roadmap: Source Code Security AI Scanner

## Milestones

- ✅ **v1.0 MVP** — Phases 1-6 (shipped 2026-03-20)
- ✅ **v2.0 Scanner Ecosystem** — Phase 7 (shipped 2026-03-20)
- 🚧 **v1.0.1 Scanner Plugin Registry** — Phases 8-10 (in progress)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-6) — SHIPPED 2026-03-20</summary>

- [x] Phase 1: Foundation and Data Models (3/3 plans) — completed 2026-03-18
- [x] Phase 2: Scanner Adapters and Orchestration (3/3 plans) — completed 2026-03-18
- [x] Phase 3: AI Analysis (3/3 plans) — completed 2026-03-19
- [x] Phase 4: Reports and Quality Gate (4/4 plans) — completed 2026-03-19
- [x] Phase 5: API, Dashboard, CI, and Notifications (4/4 plans) — completed 2026-03-19
- [x] Phase 6: Packaging, Portability, and Documentation (4/4 plans) — completed 2026-03-20

</details>

<details>
<summary>✅ v2.0 Scanner Ecosystem (Phase 7) — SHIPPED 2026-03-20</summary>

- [x] Phase 7: Security Scanner Ecosystem Research (2/2 plans) — completed 2026-03-20

</details>

### v1.0.1 Scanner Plugin Registry

- [ ] **Phase 8: Plugin Registry Architecture** - Config-driven scanner registration replacing hard-coded adapter list
- [ ] **Phase 9: Tier-1 Scanner Adapters** - gosec, Bandit, Brakeman, and cargo-audit adapters
- [ ] **Phase 10: Infrastructure and Documentation** - Docker image with new binaries and bilingual docs update

## Phase Details

### Phase 8: Plugin Registry Architecture
**Goal**: Scanners can be added and configured entirely through config.yml without touching Python code
**Depends on**: Phase 7 (research outcomes inform registry design)
**Requirements**: PLUG-01, PLUG-02, PLUG-03, PLUG-04
**Success Criteria** (what must be TRUE):
  1. A new scanner adapter can be registered by adding an entry with `adapter_class` to config.yml
  2. All existing 8 scanners load from config.yml registry instead of the hard-coded ALL_ADAPTERS list
  3. Starting the application with a misspelled or missing adapter_class produces a clear warning (not a crash)
  4. Adding a new language-to-scanner mapping in config.yml causes auto-detection to enable that scanner for matching projects
**Plans:** 2 plans
Plans:
- [ ] 08-01-PLAN.md — Config model extension, ScannerRegistry core, config.yml migration
- [ ] 08-02-PLAN.md — Orchestrator refactor, language_detect migration, /api/scanners endpoint

### Phase 9: Tier-1 Scanner Adapters
**Goal**: Users can scan Go, Python, Ruby/Rails, and Rust projects with dedicated security tools
**Depends on**: Phase 8 (adapters register via plugin registry)
**Requirements**: SCAN-01, SCAN-02, SCAN-03, SCAN-04
**Success Criteria** (what must be TRUE):
  1. Scanning a Go project produces gosec findings in the standard report (HTML and PDF)
  2. Scanning a Python project produces Bandit findings alongside existing Semgrep results
  3. Scanning a Ruby/Rails project produces Brakeman findings in the standard report
  4. Scanning a Rust project with a Cargo.lock produces cargo-audit dependency vulnerability findings
  5. All four new scanners produce FindingSchema-compatible output that flows through AI analysis and quality gate
**Plans:** 2 plans
Plans:
- [ ] 09-01-PLAN.md — Test infrastructure, gosec adapter, Bandit adapter
- [ ] 09-02-PLAN.md — Brakeman adapter, cargo-audit adapter, config.yml registration

### Phase 10: Infrastructure and Documentation
**Goal**: The complete platform ships as a single Docker image with all 12 scanners and up-to-date documentation
**Depends on**: Phase 9 (scanner binaries must be known before Docker packaging)
**Requirements**: INFRA-01, INFRA-02, DOCS-01
**Success Criteria** (what must be TRUE):
  1. `docker-compose up` starts a container with all 12 scanner binaries (8 existing + 4 new) available and functional
  2. Multi-arch build produces working images for both x86_64 and ARM64
  3. Documentation in all 5 languages (EN, RU, FR, ES, IT) covers plugin registry usage and new scanner capabilities
**Plans:** 3 plans
Plans:
- [ ] 10-01-PLAN.md — Dockerfile scanner installs, Makefile verify-scanners, smoke test samples
- [ ] 10-02-PLAN.md — English documentation update (8 docs + README)
- [ ] 10-03-PLAN.md — Translated documentation update (32 docs + 4 READMEs)

## Progress

| Phase | Milestone | Plans | Status | Completed |
|-------|-----------|-------|--------|-----------|
| 1. Foundation and Data Models | v1.0 | 3/3 | Complete | 2026-03-18 |
| 2. Scanner Adapters and Orchestration | v1.0 | 3/3 | Complete | 2026-03-18 |
| 3. AI Analysis | v1.0 | 3/3 | Complete | 2026-03-19 |
| 4. Reports and Quality Gate | v1.0 | 4/4 | Complete | 2026-03-19 |
| 5. API, Dashboard, CI, and Notifications | v1.0 | 4/4 | Complete | 2026-03-19 |
| 6. Packaging, Portability, and Documentation | v1.0 | 4/4 | Complete | 2026-03-20 |
| 7. Security Scanner Ecosystem Research | v2.0 | 2/2 | Complete | 2026-03-20 |
| 8. Plugin Registry Architecture | v1.0.1 | 0/2 | In progress | - |
| 9. Tier-1 Scanner Adapters | v1.0.1 | 0/2 | Not started | - |
| 10. Infrastructure and Documentation | v1.0.1 | 0/3 | Not started | - |
