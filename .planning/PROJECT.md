# aipix-security-scanner

## What This Is

An automated security scanning pipeline for the aipix.ai VSaaS (Video Surveillance as a Service) platform. It scans source code of release and pre-release branches for security vulnerabilities using a multi-layer approach — static analysis, secrets detection, infrastructure scanning, and AI-powered semantic analysis — then generates detailed HTML/PDF reports with fix suggestions and blocks deployment on Critical/High findings. Fully self-contained and portable via Docker, designed to be transferred to other teams and partners with minimal setup effort.

## Core Value

Every release branch is automatically scanned for security vulnerabilities before deployment, and no code with Critical or High severity findings reaches production.

## Requirements

### Validated

- [x] Full Docker containerization with single docker-compose up — *Validated in Phase 01: Foundation and Data Models*
- [x] SQLite local scan history database — *Validated in Phase 01: Foundation and Data Models (async SQLite/WAL)*
- [x] Health check endpoint — *Validated in Phase 01: Foundation and Data Models*

### Active

- [x] Multi-tool security scanning (Semgrep, Gitleaks, Trivy, Checkov, cppcheck) — *Validated in Phase 02: Scanner Adapters and Orchestration*
- [x] AI-powered semantic analysis via Claude API (business logic, authorization, fix suggestions) — *Validated in Phase 03: AI Analysis*
- [ ] HTML interactive reports with code diffs and fix examples
- [ ] PDF formal reports for management and telecom operators
- [x] Quality Gate — block Jenkins builds on Critical/High findings — *Validated in Phase 02: Scanner Adapters and Orchestration (CLI exit code)*
- [ ] FastAPI REST API for triggering scans and fetching reports
- [ ] Live web dashboard with scan history and release comparison
- [ ] Jenkins pipeline integration as a stage
- [ ] Configurable Slack and email notifications on findings
- [x] Full Docker containerization with single docker-compose up
- [x] SQLite local scan history database
- [ ] Custom Semgrep rules for aipix platform (RTSP auth, VMS API, webhooks)
- [x] Dual-mode scan input — local path (Jenkins) or repo URL (API-triggered) — *Validated in Phase 02: git clone module*
- [ ] Multi-arch support (Linux x86_64, ARM64)
- [ ] Bilingual documentation suite (Russian/English, separate files)
- [ ] Portability — migration scripts, backup/restore, packaging
- [x] Health check endpoint
- [ ] API key authentication for API/dashboard access

### Out of Scope

- PostgreSQL/MySQL support — SQLite only for portability
- SaaS-hosted scanner — fully self-hosted only
- Real-time code monitoring — scan-on-demand and CI-triggered only
- DAST (dynamic application security testing) — static analysis only for v1
- Mobile app scanning (Flutter/Dart analysis) — deferred, focus on server-side first
- Windows host support — Linux containers only (Docker Desktop not targeted)

## Context

**Platform being scanned:**
- PHP/Laravel — VMS (Video Management System), REST API, user portal
- C++ — Mediaserver (RTSP/RTP/HLS/ONVIF streaming server)
- C# — Windows desktop client
- Flutter — mobile apps (iOS/Android)
- Kubernetes + Helm, Docker Compose — infrastructure
- MinIO S3, InfluxDB, Prometheus — supporting services

**Key security concerns for this platform:**
- Unauthorized RTSP stream access (camera feed theft)
- API token exposure and hardcoded secrets in configs
- Broken authorization in VMS multi-tenant user portal
- Webhook endpoint validation (no signature verification)
- Kubernetes misconfigurations (exposed services, weak RBAC)
- C++ Mediaserver memory safety (buffer overflows, format strings)
- Insecure direct object references on video archive endpoints

**Scanner tech stack:**
- Python 3.11+ (orchestrator, report generator, FastAPI web server)
- Semgrep (static analysis — PHP, C#, C++)
- cppcheck (dedicated C++ static analysis for Mediaserver)
- Gitleaks (secrets detection in code and git history)
- Trivy (Docker images, K8s manifests, CVE scanning)
- Checkov (IaC — Helm charts, docker-compose)
- Claude API claude-sonnet-4-6 (AI semantic analysis)
- Jinja2 + WeasyPrint (HTML/PDF reports)
- FastAPI (REST API + live dashboard)
- SQLite (local scan history)
- Jenkins + Bitbucket (CI/CD integration)
- Docker + docker-compose (full containerization)

**Architecture — layered scanning approach:**
- Layer 1 (parallel): Semgrep + cppcheck + Gitleaks + Trivy + Checkov — 2-4 min
- Layer 2: Claude AI analysis on aggregated findings — semantic business logic review
- Layer 3: Report generation (HTML, PDF) + notifications
- Quality Gate: final pass/fail decision based on severity thresholds

## Constraints

- **CI time**: Must not slow down Jenkins CI more than 10 minutes total
- **AI cost**: Claude API cost target under $5 per release scan
- **Database**: SQLite only — no external DB dependencies
- **Secrets**: All secrets via environment variables, never in committed config files
- **Dependencies**: No SaaS dependencies — runs entirely on self-hosted infrastructure
- **Portability**: Single docker-compose up to start entire stack
- **License**: Apache 2.0
- **Auth**: API key-based authentication for REST API and dashboard

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| FastAPI over Flask | Async support, auto OpenAPI docs, modern Python — fits REST API + dashboard well | Confirmed — Phase 01 |
| cppcheck alongside Semgrep for C++ | Semgrep has limited C++ support; cppcheck provides proper static analysis for Mediaserver | Confirmed — Phase 02 |
| SQLite over PostgreSQL | Simplifies portability — single file, no external DB, easy backup/transfer | Confirmed — Phase 01 |
| Dual-mode scan input (path + URL) | Local path for Jenkins pipeline, repo URL for API-triggered standalone scans | Confirmed — Phase 02 |
| Separate bilingual doc files | docs/en/ + docs/ru/ — clean separation, easier maintenance | — Pending |
| Apache 2.0 license | Patent protection, explicit contributor terms — better for enterprise/partner sharing | — Pending |
| API key auth | Simple shared secret in env var — appropriate for internal tool, Jenkins passes in headers | — Pending |
| Configurable notifications | Slack and email both optional via config.yml toggles — teams choose what fits | — Pending |

---
*Last updated: 2026-03-19 — Phase 03 complete: AI-powered semantic analysis with Claude API, component batching, budget control, cross-tool correlation, graceful degradation*
