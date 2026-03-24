# Source Code Security AI Scanner

## What This Is

A multi-language security scanning platform that analyzes source code using 12 parallel scanners with AI-powered analysis. Auto-detects project languages (Python, PHP/Laravel, C/C++, JavaScript, Go, Rust, Java, C#, Ruby) and enables relevant scanners via config-driven plugin registry. Generates HTML/PDF reports with fix suggestions, blocks deployments via configurable quality gate, and integrates with Jenkins CI + Slack/email notifications. Fully self-contained via Docker.

## Core Value

Every code change is automatically scanned for security vulnerabilities before deployment, with AI-powered context analysis to reduce false positives and prioritize real risks.

## Requirements

### Validated (v1.0)

- ✓ Multi-tool security scanning (8 scanners with auto-detection) — v1.0
- ✓ AI-powered semantic analysis via Claude API — v1.0
- ✓ HTML interactive + PDF formal reports with delta comparison — v1.0
- ✓ Configurable quality gate (block on Critical/High) — v1.0
- ✓ FastAPI REST API + live web dashboard — v1.0
- ✓ Jenkins CI integration as pipeline stage — v1.0
- ✓ Slack and email notifications with scan identification — v1.0
- ✓ Full Docker containerization with all scanner tools — v1.0
- ✓ Multi-arch support (x86_64, ARM64) — v1.0
- ✓ Bilingual documentation (EN, RU, FR, ES, IT) — v1.0
- ✓ Backup/restore, packaging, migration tooling — v1.0
- ✓ Skip AI option per scan (API + dashboard) — v1.0
- ✓ Copy AI Prompt from scan results — v1.0
- ✓ PHP/Laravel scanners (Psalm, Enlightn, PHP Security Checker) — v1.0
- ✓ Auto-detect languages and enable scanners accordingly — v1.0

### Validated (v2.0)

- ✓ Research security scanner ecosystem — tools, configurations, best practices per language — v2.0

### Validated (v1.0.1)

- ✓ Scanner plugin architecture — add/configure scanners without code changes — v1.0.1
- ✓ Tier 1 scanner integration — gosec, Brakeman, Bandit, cargo-audit — v1.0.1
- ✓ Infrastructure & documentation — Docker with all 12 scanners, bilingual docs updated — v1.0.1
- ✓ Cargo-audit runtime fix and documentation corrections — v1.0.1

### Validated (v1.0.2)

- ✓ RBAC — user accounts, API tokens, role-based access (admin, scanner, viewer) — v1.0.2 Phase 12
- ✓ DAST — Nuclei adapter for template-based dynamic scanning — v1.0.2 Phase 13
- ✓ Scanner configuration UI — enable/disable scanners, per-scanner settings, YAML config editor — v1.0.2 Phase 14
- ✓ Scan profiles — named scanner configurations selectable via API and dashboard — v1.0.2 Phase 15
- ✓ Bilingual documentation (EN, RU, FR, ES, IT) updated for all v1.0.2 features — v1.0.2 Phase 15

### Active

(No active requirements — v1.0.2 milestone fully closed including gap closure)

## Current Milestone: v1.0.2 Scanner UI, DAST & RBAC

**Goal:** Add web-based scanner configuration, Nuclei DAST adapter, and token-based authentication with role-based access control.

**Target features:**
- Scanner configuration UI (enable/disable, settings, config editor, scan profiles)
- Nuclei DAST adapter (template-based dynamic application security testing)
- Token-based API authentication for CI/CD pipelines
- Role-based access control (admin, viewer, scanner roles)
- Dashboard access control per role

### Out of Scope

- PostgreSQL/MySQL support — SQLite only for portability
- SaaS-hosted scanner — fully self-hosted only
- Real-time code monitoring — scan-on-demand and CI-triggered only
- Windows host support — Linux containers only
- Commercial/paid scanner integration — open-source tools only
- OAuth/SSO/LDAP integration — simple local auth only for v1.0.2
- User self-registration — admin creates accounts
- Full DAST pipeline (target management, DAST-specific reports) — Nuclei adapter only for v1.0.2

## Context

**v1.0 shipped** — 6 phases, 21 plans, 150 commits, 5400+ LOC Python, 320 tests passing.
**v2.0 shipped** — 1 phase, 2 plans. Research-only milestone producing scanner ecosystem report.
**v1.0.1 shipped** — 4 phases, 8 plans, 28 commits. Plugin registry + 4 Tier-1 scanners + Docker + docs. 402 tests passing, ~6000 LOC Python.
**v1.0.2 shipped** — 5 phases, 14 plans. RBAC, Nuclei DAST, scanner config UI, scan profiles, bilingual docs, gap closure. 487+ tests passing.

**Scanner tech stack:**
- Python 3.12 (orchestrator, FastAPI, reports)
- 13 scanners: Semgrep, cppcheck, Gitleaks, Trivy, Checkov, Psalm, Enlightn, PHP Security Checker, gosec, Bandit, Brakeman, cargo-audit, Nuclei (DAST)
- Claude API (AI semantic analysis)
- Jinja2 + WeasyPrint (HTML/PDF reports)
- SQLite/WAL (scan history)
- Docker + docker-compose (containerization)

**Architecture — layered scanning:**
- Layer 1: Language auto-detection → enable relevant scanners
- Layer 2: Parallel scanner execution (12 tools via config-driven registry)
- Layer 3: AI enrichment (Claude API) — optional per scan
- Layer 4: Report generation + quality gate + notifications

## Constraints

- **CI time**: Under 10 minutes total scan time
- **AI cost**: Claude API target under $5 per scan
- **Database**: SQLite only — no external DB
- **Secrets**: All secrets via environment variables
- **Portability**: Single docker-compose up
- **License**: Apache 2.0

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| FastAPI over Flask | Async support, auto OpenAPI docs | ✓ Confirmed |
| SQLite over PostgreSQL | Portability — single file, easy backup | ✓ Confirmed |
| `--config auto` for Semgrep | Covers all languages automatically | ✓ Confirmed v1.0 |
| Language auto-detection | Scanners enable/disable based on project content | ✓ Confirmed v1.0 |
| PHP scanners (Psalm, Enlightn, php-security-checker) | Laravel/PHP platform needs dedicated tools | ✓ Confirmed v1.0 |
| Apache 2.0 license | Enterprise/partner sharing | ✓ Confirmed |
| Separate bilingual doc files | docs/{en,ru,fr,es,it}/ — clean separation | ✓ Confirmed |
| Skip AI per scan | Cost control, faster scans when AI not needed | ✓ Confirmed |
| Config-driven plugin registry | Extends config.yml with adapter_class — no stevedore needed | ✓ Confirmed v1.0.1 |
| Keep Semgrep CE, monitor Opengrep | Opengrep fork immature, cross-function taint moved to commercial | ✓ Confirmed v2.0 |
| Keep Gitleaks over TruffleHog | Speed and simplicity win for CI/CD; TruffleHog as optional complement | ✓ Confirmed v2.0 |
| Nuclei over ZAP for DAST | CLI-friendly, template-based, 30MB vs 500MB+ | ✓ Confirmed v2.0 |
| ScannerRegistry over ALL_ADAPTERS | Dynamic loading via importlib, config-driven | ✓ Confirmed v1.0.1 |
| Underscore convention for config keys | tool_name uses underscores to match config.yml keys | ✓ Confirmed v1.0.1 |

---
*Last updated: 2026-03-24 — Phase 16 v1.0.2 gap closure complete (dashboard target_url, schema migration, docs auth fix)*
