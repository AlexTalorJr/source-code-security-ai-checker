# Source Code Security AI Scanner

## What This Is

A multi-language security scanning platform that analyzes source code using 8 parallel scanners with AI-powered analysis. Auto-detects project languages (Python, PHP/Laravel, C/C++, JavaScript, Go, Rust, Java, C#, Ruby) and enables relevant scanners. Generates HTML/PDF reports with fix suggestions, blocks deployments via configurable quality gate, and integrates with Jenkins CI + Slack/email notifications. Fully self-contained via Docker.

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

### Active (v2.0)

- [x] Research security scanner ecosystem — tools, configurations, best practices per language — Validated in Phase 7
- [ ] Scanner plugin architecture — add/configure scanners without code changes
- [ ] Advanced scanner configuration UI — manage scanner settings from dashboard
- [ ] DAST (dynamic application security testing) capabilities
- [ ] Role-based access control (admin, viewer, scanner roles)

## Current Milestone: v2.0 Scanner Ecosystem

**Goal:** Research and improve the security scanning capabilities — discover which tools work best for each language, how to configure them optimally, and how to make scanner management extensible.

**Phase 7 (research) — COMPLETE:** Produced 1416-line scanner ecosystem report covering 9 languages, 13 tools evaluated, 9 recommended across 3 priority tiers. Key outcomes: config-driven plugin registry, optional SARIF helper, incremental scanning pattern. Implementation roadmap: Phase 8 (Tier 1 tools), Phase 9 (SARIF + Tier 2), Phase 10 (incremental + DAST).

### Out of Scope

- PostgreSQL/MySQL support — SQLite only for portability
- SaaS-hosted scanner — fully self-hosted only
- Real-time code monitoring — scan-on-demand and CI-triggered only
- Windows host support — Linux containers only

## Context

**v1.0 shipped** — 6 phases, 21 plans, 150 commits, 5400+ LOC Python, 320 tests passing.

**Scanner tech stack:**
- Python 3.12 (orchestrator, FastAPI, reports)
- 8 scanners: Semgrep, cppcheck, Gitleaks, Trivy, Checkov, Psalm, Enlightn, PHP Security Checker
- Claude API (AI semantic analysis)
- Jinja2 + WeasyPrint (HTML/PDF reports)
- SQLite/WAL (scan history)
- Docker + docker-compose (containerization)

**Architecture — layered scanning:**
- Layer 1: Language auto-detection → enable relevant scanners
- Layer 2: Parallel scanner execution (8 tools)
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
| `--config auto` for Semgrep | Covers all languages automatically | ✓ Confirmed v1.2 |
| Language auto-detection | Scanners enable/disable based on project content | ✓ Confirmed v1.2 |
| PHP scanners (Psalm, Enlightn, php-security-checker) | Laravel/PHP platform needs dedicated tools | ✓ Confirmed v1.2 |
| Apache 2.0 license | Enterprise/partner sharing | ✓ Confirmed |
| Separate bilingual doc files | docs/{en,ru,fr,es,it}/ — clean separation | ✓ Confirmed |
| Skip AI per scan | Cost control, faster scans when AI not needed | ✓ Confirmed |

---
*Last updated: 2026-03-20 — Phase 7 complete. Scanner ecosystem research delivered.*
