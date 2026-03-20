# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Phase 6: Packaging, Portability, and Documentation
#### Added
- Makefile with build automation targets (install, run, test, backup, restore, package)
- Multi-arch Docker builds (amd64 + arm64)
- Apache 2.0 LICENSE file
- CONTRIBUTING.md
- Complete English documentation in docs/en/
- Complete Russian documentation in docs/ru/
- README.ru.md (Russian README)

## [0.1.0] - 2026-03-18

### Phase 5: API, Dashboard, CI, and Notifications
#### Added
- REST API for scan lifecycle (POST /api/scans, GET /api/scans/{id})
- API key authentication with timing-safe comparison
- Background scan queue (asyncio.Queue-based)
- Web dashboard with scan history, detail views, trend charts
- Dashboard authentication with session cookies
- Slack webhook notifications on scan completion
- Email notifications with HTML template and inline CSS
- Jenkins pipeline integration (Jenkinsfile.security)
- Finding suppression (false positive management) via API and dashboard
- CSS-only tab switcher for dashboard finding views

### Phase 4: Reports and Quality Gate
#### Added
- Interactive HTML report with severity filters, code context, AI fix suggestions
- PDF report with executive summary, severity breakdown charts (matplotlib)
- Configurable quality gate (fail on Critical/High, compound risks)
- Scan history storage with delta comparison (new/fixed/persisting findings)
- Base64 PNG chart embedding in HTML templates
- PackageLoader for Jinja2 template discovery

### Phase 3: AI Analysis
#### Added
- Claude API integration for semantic vulnerability analysis
- AI-generated fix suggestions with before/after code diffs
- Cross-tool finding correlation into compound risk entries
- Token budgeting and cost tracking per scan
- Graceful degradation when Claude API unavailable
- Component framework mapping for batch analysis

### Phase 2: Scanner Adapters and Orchestration
#### Added
- Scanner adapter ABC with configurable timeout and extra_args
- Semgrep adapter for SAST scanning
- cppcheck adapter for C/C++ analysis
- Gitleaks adapter for secret detection
- Trivy adapter for container/dependency scanning
- Checkov adapter for IaC security
- Parallel scan orchestration with asyncio.gather
- Git repository cloning with branch selection
- Cross-tool finding deduplication
- CLI scan command via Typer

### Phase 1: Foundation and Data Models
#### Added
- Project skeleton with pyproject.toml and hatchling build
- Configuration system (YAML + env var overrides with SCANNER_ prefix)
- Pydantic schemas (FindingSchema, ScanResultSchema, Severity enum)
- Fingerprint module for deterministic finding deduplication
- SQLAlchemy ORM models with async SQLite and WAL mode
- FastAPI application with health endpoint
- Alembic migration infrastructure
- Docker packaging (python:3.12-slim, non-root user, docker-compose)

#### Fixed
- Dockerfile: source code must be copied before `pip install .` (was causing ModuleNotFoundError at runtime)
