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

### Validated (v2.0)

- ✓ Research security scanner ecosystem — tools, configurations, best practices per language — v2.0

### Active

- ✓ Scanner plugin architecture — add/configure scanners without code changes — v1.0.1 Phase 8
- ✓ Tier 1 scanner integration — gosec, Brakeman, Bandit, cargo-audit — v1.0.1 Phase 9
- [ ] Advanced scanner configuration UI — manage scanner settings from dashboard
- [ ] DAST (dynamic application security testing) capabilities
- [ ] Role-based access control (admin, viewer, scanner roles)

## Current Milestone: v1.0.1 Scanner Plugin Registry

**Goal:** Implement the config-driven plugin registry architecture and integrate 4 Tier-1 scanners (gosec, Brakeman, Bandit, cargo-audit) as recommended by v2.0 research.

**Target features:**
- Config-driven scanner registration (adapter_class in config.yml)
- gosec adapter for Go SAST
- Brakeman adapter for Ruby/Rails SAST
- Bandit adapter for Python SAST
- cargo-audit adapter for Rust SCA
- Updated language detection for new scanners
- Docker image with new scanner binaries
- Updated documentation (bilingual)

### Out of Scope

- PostgreSQL/MySQL support — SQLite only for portability
- SaaS-hosted scanner — fully self-hosted only
- Real-time code monitoring — scan-on-demand and CI-triggered only
- Windows host support — Linux containers only
- Commercial/paid scanner integration — open-source tools only

## Context

**v1.0 shipped** — 6 phases, 21 plans, 150 commits, 5400+ LOC Python, 320 tests passing.
**v2.0 shipped** — 1 phase, 2 plans. Research-only milestone producing scanner ecosystem report with priority-ranked tool recommendations.

**Scanner tech stack:**
- Python 3.12 (orchestrator, FastAPI, reports)
- 12 scanners: Semgrep, cppcheck, Gitleaks, Trivy, Checkov, Psalm, Enlightn, PHP Security Checker, gosec, Bandit, Brakeman, cargo-audit
- Claude API (AI semantic analysis)
- Jinja2 + WeasyPrint (HTML/PDF reports)
- SQLite/WAL (scan history)
- Docker + docker-compose (containerization)

**Architecture — layered scanning:**
- Layer 1: Language auto-detection → enable relevant scanners
- Layer 2: Parallel scanner execution (8 tools)
- Layer 3: AI enrichment (Claude API) — optional per scan
- Layer 4: Report generation + quality gate + notifications

**Research outcomes (v2.0):**
- 9 new tools evaluated, 4 Tier-1 recommended: gosec, Brakeman, Bandit, cargo-audit
- Config-driven plugin registry architecture recommended
- SARIF helper pattern for 8/13 tools with native support
- Incremental scanning feasible for 5 tools (Semgrep, Bandit, gosec, Brakeman, Gitleaks)

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
| Config-driven plugin registry | Extends config.yml with adapter_class — no stevedore needed | ✓ Confirmed v2.0 |
| Keep Semgrep CE, monitor Opengrep | Opengrep fork immature, cross-function taint moved to commercial | ✓ Confirmed v2.0 |
| Keep Gitleaks over TruffleHog | Speed and simplicity win for CI/CD; TruffleHog as optional complement | ✓ Confirmed v2.0 |
| Nuclei over ZAP for DAST | CLI-friendly, template-based, 30MB vs 500MB+ | ✓ Confirmed v2.0 |

---
*Last updated: 2026-03-21 — Phase 9 complete: tier-1 scanner adapters (gosec, Bandit, Brakeman, cargo-audit)*
