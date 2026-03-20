# Roadmap: aipix-security-scanner

## Overview

This roadmap delivers a fully containerized, multi-tool security scanning pipeline for the aipix VSaaS platform. The build follows the natural dependency chain: data models and config foundation first, then scanner execution, AI enrichment, report generation with quality gate, full API/CI integration, and finally packaging with documentation. After Phase 2, the scanner is independently useful. After Phase 4, it is production-ready for CI. Phases 5-6 add operational maturity and portability.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation and Data Models** - Config system, unified Finding model with dedup keys, SQLite persistence, FastAPI skeleton with health endpoint, Docker base image (completed 2026-03-18)
- [ ] **Phase 2: Scanner Adapters and Orchestration** - Five scanner adapters running in parallel with timeouts, finding normalization and cross-tool deduplication, dual-mode scan input
- [ ] **Phase 3: AI Analysis** - Claude API integration for semantic analysis, fix suggestions, cross-tool correlation, token budgeting, graceful degradation
- [ ] **Phase 4: Reports and Quality Gate** - Interactive HTML report, formal PDF report, configurable quality gate with exit codes, scan history storage and delta comparison
- [x] **Phase 5: API, Dashboard, CI, and Notifications** - Full REST API for scan lifecycle, live dashboard, Jenkins pipeline integration, Slack/email notifications, false positive management (completed 2026-03-19)
- [ ] **Phase 6: Packaging, Portability, and Documentation** - Multi-arch Docker builds, Makefile automation, migration tooling, distributable archive, complete bilingual documentation suite

## Phase Details

### Phase 1: Foundation and Data Models
**Goal**: Establish the project skeleton with config loading, unified data models, database persistence, and a running API server -- so all subsequent phases build on stable foundations
**Depends on**: Nothing (first phase)
**Requirements**: SCAN-02, API-04, INFRA-01, INFRA-03, INFRA-04, INFRA-05
**Success Criteria** (what must be TRUE):
  1. Running `docker-compose up` starts a FastAPI server that responds to GET /api/health with status information
  2. Configuration loads from config.yml with environment variable overrides for secrets, and no credentials exist in committed code
  3. Finding and ScanResult data models exist with unified severity levels (Critical/High/Medium/Low/Info) and deterministic deduplication fingerprints
  4. SQLite database is created in a mounted volume with WAL mode enabled, and persists across container restarts
**Plans**: 3 plans

Plans:
- [ ] 01-01-PLAN.md -- Project skeleton, config system, Pydantic schemas, fingerprint module
- [ ] 01-02-PLAN.md -- SQLAlchemy ORM models, DB session with WAL mode, FastAPI app with health endpoint
- [ ] 01-03-PLAN.md -- Docker packaging (Dockerfile, docker-compose.yml) with smoke test

### Phase 2: Scanner Adapters and Orchestration
**Goal**: Users can trigger a scan that runs all five security tools in parallel, producing normalized and deduplicated findings with unified severity
**Depends on**: Phase 1
**Requirements**: SCAN-01, SCAN-03, SCAN-04, SCAN-05, SCAN-06, SCAN-07
**Success Criteria** (what must be TRUE):
  1. A scan against a local filesystem path runs Semgrep, cppcheck, Gitleaks, Trivy, and Checkov in parallel and produces a unified list of findings
  2. A scan against a git repository URL clones the repo and produces the same unified findings
  3. Duplicate findings across tools are collapsed into single entries with source tool attribution
  4. If any scanner tool hangs or crashes, the scan completes with partial results and a warning (no scan-level failure)
  5. Total scan time for a typical aipix release branch stays under 10 minutes
**Plans**: 3 plans

Plans:
- [ ] 02-01-PLAN.md -- Base adapter ABC, config extension, git clone module, test fixtures
- [ ] 02-02-PLAN.md -- Five scanner adapters (Semgrep, cppcheck, Gitleaks, Trivy, Checkov)
- [ ] 02-03-PLAN.md -- Orchestrator (parallel exec, dedup, persistence) and CLI scan command

### Phase 3: AI Analysis
**Goal**: Scan findings are enriched with AI-powered semantic analysis that identifies business logic risks and provides actionable fix suggestions
**Depends on**: Phase 2
**Requirements**: AI-01, AI-02, AI-03, AI-04, AI-05
**Success Criteria** (what must be TRUE):
  1. Claude analyzes aggregated findings and flags business logic vulnerabilities (auth bypass, tenant isolation, IDOR) that static tools miss
  2. Each finding includes an AI-generated fix suggestion with before/after code diffs
  3. Related findings across tools are correlated into compound risk entries
  4. AI analysis cost stays under $5 per release scan (tracked and logged)
  5. When the Claude API is unavailable, the scan completes without AI enrichment and the report clearly indicates AI analysis was skipped
**Plans**: 3 plans

Plans:
- [ ] 03-01-PLAN.md -- AI config, response schemas, prompts, cost module, compound risk DB models
- [ ] 03-02-PLAN.md -- AIAnalyzer class with component batching, budget control, and correlation
- [ ] 03-03-PLAN.md -- Orchestrator integration, graceful degradation, CLI update, quality gate

### Phase 4: Reports and Quality Gate
**Goal**: Every scan produces professional reports and an automated pass/fail decision that can block deployment
**Depends on**: Phase 3
**Requirements**: RPT-01, RPT-02, RPT-03, RPT-04, GATE-01, GATE-02, GATE-03, HIST-01, HIST-02
**Success Criteria** (what must be TRUE):
  1. An interactive HTML report displays findings grouped by severity, filterable by component and tool, with code context and AI fix suggestions
  2. A PDF report contains an executive summary, severity breakdown chart, and detailed findings suitable for management review
  3. Reports include scan metadata (date, branch, commit hash, duration, tool versions)
  4. The scanner returns exit code 0 when no Critical/High findings exist and non-zero when they do, with thresholds configurable in config.yml
  5. Scan results are stored in SQLite with delta comparison showing new, fixed, and persisting findings relative to the previous scan of the same branch
**Plans**: 4 plans

Plans:
- [ ] 04-01-PLAN.md -- Configurable quality gate, delta comparison module, data contracts
- [ ] 04-02-PLAN.md -- Interactive HTML report with sidebar filters and AI fix diffs
- [ ] 04-03-PLAN.md -- PDF report with charts and executive summary
- [ ] 04-04-PLAN.md -- CLI integration, Docker deps, end-to-end wiring

### Phase 5: API, Dashboard, CI, and Notifications
**Goal**: The scanner is fully operational as both a CI pipeline stage and a standalone service with web dashboard and notifications
**Depends on**: Phase 4
**Requirements**: API-01, API-02, API-03, API-05, API-06, CI-01, CI-02, CI-03, NOTF-01, NOTF-02, NOTF-03, HIST-03, HIST-04
**Success Criteria** (what must be TRUE):
  1. POST /api/scans triggers a scan and returns a scan ID; GET /api/scans/{id} returns status and results; all API endpoints require API key authentication
  2. A web dashboard shows scan history, finding trends over time, and release-to-release comparison
  3. A Jenkinsfile.security stage can be dropped into an existing pipeline, passes the workspace path to the scanner, and fails the build when the quality gate fails
  4. Slack and email notifications fire on scan completion with severity summary, and each channel is independently configurable
  5. Users can mark findings as false positive via the API, and suppressed findings are excluded from future scan results and quality gate decisions
**Plans**: 4 plans

Plans:
- [ ] 05-01-PLAN.md -- API auth, scan lifecycle endpoints, background queue, suppression, config extension
- [ ] 05-02-PLAN.md -- Slack/email notifications, dispatcher service, Jenkinsfile.security
- [ ] 05-03-PLAN.md -- Server-rendered Jinja2 dashboard (login, history, detail, trends)
- [ ] 05-04-PLAN.md -- Gap closure: fix notify_scan_complete call site bug + regression test

### Phase 6: Packaging, Portability, and Documentation
**Goal**: The scanner is a distributable, self-contained package that any team can deploy and operate using comprehensive documentation
**Depends on**: Phase 5
**Requirements**: INFRA-02, INFRA-06, INFRA-07, INFRA-08, DOC-01, DOC-02, DOC-03, DOC-04, DOC-05, DOC-06, DOC-07, DOC-08, DOC-09, DOC-10, DOC-11
**Success Criteria** (what must be TRUE):
  1. Docker images build and run on both x86_64 and ARM64 architectures
  2. `make package` produces a distributable archive; `make install && make run` starts the scanner on a fresh Linux host
  3. Scan history can be exported from one environment, transferred, and imported into another using migration scripts
  4. A new user can go from zero to first scan in under 5 minutes following only the README
  5. Complete documentation exists in both English (docs/en/) and Russian (docs/ru/) covering architecture, user guide, admin guide, DevOps guide, API reference, transfer guide, and custom rules
**Plans**: 4 plans

Plans:
- [ ] 06-01-PLAN.md -- Makefile automation (install, run, test, backup, restore, package, multi-arch) and Wave 0 tests
- [ ] 06-02-PLAN.md -- Doc restructuring: move to docs/en/, rewrite README.md, update 5 English docs
- [ ] 06-03-PLAN.md -- Update remaining 3 English docs, create LICENSE, CONTRIBUTING.md, update CHANGELOG.md
- [ ] 06-04-PLAN.md -- Russian translations: README.ru.md and 8 docs in docs/ru/

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation and Data Models | 3/3 | Complete   | 2026-03-18 |
| 2. Scanner Adapters and Orchestration | 1/3 | In Progress|  |
| 3. AI Analysis | 0/3 | Not started | - |
| 4. Reports and Quality Gate | 3/4 | In Progress|  |
| 5. API, Dashboard, CI, and Notifications | 3/4 | Gap closure | 2026-03-19 |
| 6. Packaging, Portability, and Documentation | 1/4 | In Progress|  |
