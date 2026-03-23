# Roadmap: Source Code Security AI Scanner

## Milestones

- ✅ **v1.0 MVP** — Phases 1-6 (shipped 2026-03-20)
- ✅ **v2.0 Scanner Ecosystem** — Phase 7 (shipped 2026-03-20)
- ✅ **v1.0.1 Scanner Plugin Registry** — Phases 8-11 (shipped 2026-03-22)
- **v1.0.2 Scanner UI, DAST & RBAC** — Phases 12-15 (in progress)

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

<details>
<summary>✅ v1.0.1 Scanner Plugin Registry (Phases 8-11) — SHIPPED 2026-03-22</summary>

- [x] Phase 8: Plugin Registry Architecture (2/2 plans) — completed 2026-03-21
- [x] Phase 9: Tier-1 Scanner Adapters (2/2 plans) — completed 2026-03-21
- [x] Phase 10: Infrastructure and Documentation (3/3 plans) — completed 2026-03-22
- [x] Phase 11: Cargo-Audit Fix and Documentation Corrections (1/1 plan) — completed 2026-03-22

</details>

### v1.0.2 Scanner UI, DAST & RBAC (In Progress)

**Milestone Goal:** Add web-based scanner configuration, Nuclei DAST adapter, and token-based authentication with role-based access control.

- [ ] **Phase 12: RBAC Foundation** - User accounts, API tokens, role-based authorization, and SQLite hardening
- [ ] **Phase 13: Nuclei DAST Adapter** - Template-based dynamic security scanning via Nuclei CLI
- [ ] **Phase 14: Scanner Configuration UI** - Dashboard pages for scanner enable/disable, settings, and config editing
- [ ] **Phase 15: Scan Profiles and Documentation** - Named scan presets and bilingual docs for all v1.0.2 features

## Phase Details

### Phase 12: RBAC Foundation
**Goal**: Users can securely authenticate and access the platform according to their assigned role
**Depends on**: Phase 11
**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-04, AUTH-05, AUTH-06, AUTH-07, INFRA-03
**Success Criteria** (what must be TRUE):
  1. Admin can create a user account and that user can log in to the dashboard with username and password
  2. User can generate a personal API token, use it to call scan endpoints, and revoke it
  3. Viewer-role user can view scan results but receives 403 when attempting to trigger a scan or change settings
  4. Scanner-role user can trigger scans and view results via API token but cannot access dashboard configuration pages
  5. Unauthenticated API requests return 401; SQLite handles concurrent writes without busy errors
**Plans**: 5 plans

Plans:
- [ ] 12-01-PLAN.md — Models, schemas, config, SQLite hardening, admin bootstrap
- [ ] 12-02-PLAN.md — Unified auth core (get_current_user, require_role, JWT sessions)
- [ ] 12-03-PLAN.md — Test infrastructure and Phase 05 fixture migration
- [ ] 12-04-PLAN.md — User CRUD API, Token API, role enforcement on endpoints
- [ ] 12-05-PLAN.md — Dashboard UI (login, 403, navbar, users, tokens pages)

### Phase 13: Nuclei DAST Adapter
**Goal**: Users can run dynamic application security scans against target URLs alongside existing SAST scans
**Depends on**: Phase 12
**Requirements**: DAST-01, DAST-02, DAST-03, DAST-04
**Success Criteria** (what must be TRUE):
  1. User can trigger a DAST scan by providing a target_url via API and Nuclei executes against that URL
  2. Nuclei findings appear in HTML and PDF reports alongside SAST findings with severity and template info
  3. Nuclei binary is installed in the Docker image and works on both x86_64 and ARM64
**Plans**: TBD

Plans:
- [ ] 13-01: TBD
- [ ] 13-02: TBD

### Phase 14: Scanner Configuration UI
**Goal**: Admins can manage scanner settings from the dashboard without editing config files manually
**Depends on**: Phase 12
**Requirements**: CONF-01, CONF-02, CONF-03
**Success Criteria** (what must be TRUE):
  1. Admin can enable or disable individual scanners from the dashboard and changes persist across restarts
  2. Admin can edit per-scanner settings (timeout, extra args) from the dashboard and the next scan uses the updated values
  3. Admin can edit config.yml via a web-based YAML editor with syntax highlighting
**Plans**: TBD

Plans:
- [ ] 14-01: TBD
- [ ] 14-02: TBD

### Phase 15: Scan Profiles and Documentation
**Goal**: Users can select predefined scan configurations and all v1.0.2 features are documented
**Depends on**: Phase 13, Phase 14
**Requirements**: CONF-04, CONF-05, INFRA-04
**Success Criteria** (what must be TRUE):
  1. Admin can create a named scan profile (e.g. "Quick scan") that saves a specific scanner configuration
  2. User can select a scan profile when triggering a scan via API or dashboard, and only that profile's scanners execute
  3. Bilingual documentation (EN, RU, FR, ES, IT) covers RBAC setup, scanner config UI usage, DAST scanning, and scan profiles
**Plans**: TBD

Plans:
- [ ] 15-01: TBD
- [ ] 15-02: TBD

## Progress

**Execution Order:**
Phases 13 and 14 can execute in parallel after Phase 12 completes.

| Phase | Milestone | Plans | Status | Completed |
|-------|-----------|-------|--------|-----------|
| 1. Foundation and Data Models | v1.0 | 3/3 | Complete | 2026-03-18 |
| 2. Scanner Adapters and Orchestration | v1.0 | 3/3 | Complete | 2026-03-18 |
| 3. AI Analysis | v1.0 | 3/3 | Complete | 2026-03-19 |
| 4. Reports and Quality Gate | v1.0 | 4/4 | Complete | 2026-03-19 |
| 5. API, Dashboard, CI, and Notifications | v1.0 | 4/4 | Complete | 2026-03-19 |
| 6. Packaging, Portability, and Documentation | v1.0 | 4/4 | Complete | 2026-03-20 |
| 7. Security Scanner Ecosystem Research | v2.0 | 2/2 | Complete | 2026-03-20 |
| 8. Plugin Registry Architecture | v1.0.1 | 2/2 | Complete | 2026-03-21 |
| 9. Tier-1 Scanner Adapters | v1.0.1 | 2/2 | Complete | 2026-03-21 |
| 10. Infrastructure and Documentation | v1.0.1 | 3/3 | Complete | 2026-03-22 |
| 11. Cargo-Audit Fix and Doc Corrections | v1.0.1 | 1/1 | Complete | 2026-03-22 |
| 12. RBAC Foundation | 1/5 | In Progress|  | - |
| 13. Nuclei DAST Adapter | v1.0.2 | 0/? | Not started | - |
| 14. Scanner Configuration UI | v1.0.2 | 0/? | Not started | - |
| 15. Scan Profiles and Documentation | v1.0.2 | 0/? | Not started | - |
