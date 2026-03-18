# Technology Stack

**Project:** aipix-security-scanner
**Researched:** 2026-03-18

## Recommended Stack

### Core Runtime

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Python | 3.12.x | Orchestrator, API, reports | Most deployed production Python version in 2026. 3.13's free-threading and JIT are experimental and unnecessary here. 3.12-slim Docker image is the community standard base. | HIGH |
| Docker + Compose | Latest stable | Full containerization | Single `docker-compose up` requirement per PROJECT.md. Compose v2 is the standard. | HIGH |

### Security Scanning Tools (Layer 1)

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Semgrep CE | 1.156.0+ | Static analysis (PHP, C#, limited C++) | Industry standard open-source SAST. 30+ languages, custom rule authoring, SARIF output. Fall 2025 release added 3x perf with multicore. Community Edition is free and sufficient for self-hosted use. | HIGH |
| cppcheck | 2.19.0+ | C++ static analysis (Mediaserver) | Semgrep has limited C++ support (no dataflow analysis). cppcheck provides proper buffer overflow, memory leak, format string detection -- exactly what the Mediaserver needs. Open source, no license cost. | HIGH |
| Gitleaks | 8.24.x+ | Secrets detection in code and git history | Proven, stable, widely adopted. Regex + entropy-based detection. `--no-git` mode for directory scanning, `--report-format sarif` for integration. | HIGH |
| Trivy | 0.69.x+ | Container images, K8s manifests, CVE scanning | Swiss-army knife: scans Docker images, Kubernetes YAML, Helm charts, and filesystem for CVEs. SARIF output. Actively maintained by Aqua Security. Replaces the need for separate image and K8s scanners. | HIGH |
| Checkov | 3.2.x+ | IaC scanning (Helm, docker-compose, K8s) | 2,500+ built-in policies for Kubernetes, Docker, Helm. Graph-based analysis catches resource relationship issues. Complements Trivy's CVE focus with configuration/misconfiguration focus. SARIF output. | HIGH |

### AI Analysis (Layer 2)

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| anthropic (Python SDK) | 0.85.x+ | Claude API integration | Official SDK with async support, streaming, proper error handling. Required for claude-sonnet-4-6 semantic analysis. | HIGH |
| Claude claude-sonnet-4-6 | API | AI-powered security analysis | Good balance of cost vs capability for code analysis. At ~$3/1M input tokens, fits the $5/scan budget. Handles business logic analysis (RTSP auth, IDOR, webhook validation) that static tools miss. | HIGH |

### Web Framework & API

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| FastAPI | 0.135.x+ | REST API + dashboard | Async-native, auto-generates OpenAPI docs, built-in request validation via Pydantic. Modern Python standard for APIs. SSE support added recently for live scan progress streaming. | HIGH |
| Uvicorn | 0.42.x+ | ASGI server | Standard production server for FastAPI. Lightweight, fast, supports graceful shutdown. | HIGH |
| Pydantic | 2.x (bundled) | Data validation | Comes with FastAPI. V2 is significantly faster than V1. Use for scan configs, API request/response models, report data models. | HIGH |

### Report Generation (Layer 3)

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Jinja2 | 3.1.6 | HTML template engine | Mature, stable, well-documented. Used by Flask, Ansible, and most Python templating. Perfect for HTML report templates with code diffs. | HIGH |
| WeasyPrint | 68.1+ | HTML-to-PDF conversion | Renders HTML/CSS to PDF. No headless browser needed (unlike Playwright/Puppeteer). Smaller Docker footprint. CSS @page support for formal reports with headers/footers. Security fix in 68.1 -- use this version or later. | MEDIUM |

### Database

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| SQLite | 3.x (system) | Scan history storage | Per PROJECT.md constraint: single-file DB, zero config, easy backup/transfer. Sufficient for scan history workload (writes are infrequent, reads are dashboard queries). | HIGH |
| SQLAlchemy | 2.0.x+ | ORM / query builder | Type-safe query building, migration support via Alembic, async support via aiosqlite. Prevents raw SQL injection in dashboard queries. | HIGH |
| aiosqlite | 0.20.x+ | Async SQLite driver | Required for non-blocking SQLite access in async FastAPI. SQLAlchemy 2.0 supports `sqlite+aiosqlite:///` connection string natively. | HIGH |
| Alembic | 1.x+ | Database migrations | Schema evolution without manual SQL. Essential for upgrading deployed scanners without data loss. | HIGH |

### Notifications

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| httpx | 0.27.x+ | HTTP client (Slack webhooks, API calls) | Async-native HTTP client. Better than requests for async FastAPI context. Used for Slack webhook POSTs and Bitbucket API calls. | HIGH |
| aiosmtplib | 3.x+ | Async email sending | Async SMTP client for email notifications. Lightweight, no heavy dependencies. | MEDIUM |

### Testing & Quality

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| pytest | 8.x+ | Test framework | Standard Python test framework. Rich plugin ecosystem. | HIGH |
| pytest-asyncio | 0.24.x+ | Async test support | Required for testing FastAPI async endpoints and async scan orchestration. | HIGH |
| httpx (TestClient) | -- | API integration tests | FastAPI recommends httpx for async test client. | HIGH |
| ruff | 0.9.x+ | Linter + formatter | Replaces flake8 + black + isort. 10-100x faster (Rust-based). Single tool for all Python code quality. | HIGH |
| mypy | 1.x+ | Type checking | Catches type errors before runtime. Essential for a security tool where correctness matters. | MEDIUM |

### Configuration & CLI

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| PyYAML | 6.x | Config file parsing | `config.yml` for scanner settings, thresholds, notification toggles. YAML is human-readable for ops teams. | HIGH |
| python-dotenv | 1.x | Environment variable loading | `.env` file support for local development. Secrets stay in env vars per PROJECT.md constraint. | HIGH |
| typer | 0.15.x+ | CLI interface | Modern CLI framework built on Click. Auto-generates help, type-safe args. For `scanner scan --repo-url ...` style commands. | MEDIUM |

### Data Exchange Format

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| SARIF 2.1.0 | -- | Standardized scan output | Industry standard for static analysis results. Semgrep, Trivy, Checkov, and Gitleaks all support SARIF output. Use as the internal interchange format between Layer 1 tools and the aggregator. Enables future integration with GitHub/GitLab/Bitbucket code scanning. | HIGH |

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Secrets detection | Gitleaks 8.x | Betterleaks 1.x | Betterleaks launched March 2026 by the Gitleaks creator. BPE tokenization is promising (98.6% vs 70.4% recall). However, it is brand new with no production track record. Gitleaks is battle-tested. **Revisit in 6 months** -- Betterleaks may become the better choice once it stabilizes. |
| Secrets detection | Gitleaks 8.x | TruffleHog | TruffleHog is heavier, slower, more opinionated. Gitleaks is lighter and sufficient for the scan-time budget. |
| Static analysis | Semgrep CE | SonarQube CE | SonarQube requires a running server (Java), is heavier to containerize, and Community Edition has limited language support. Semgrep CE is CLI-first, lighter, and supports custom rules more easily. |
| Static analysis | Semgrep CE | CodeQL | CodeQL requires compilation database setup, is GitHub-centric, and has restrictive licensing for non-GitHub use. Semgrep is more portable. |
| IaC scanning | Checkov | tfsec / KICS | Checkov covers Helm + docker-compose + K8s in one tool. tfsec is Terraform-focused (less relevant here). KICS works but Checkov has broader policy coverage and better Python integration. |
| Container scanning | Trivy | Grype + Syft | Trivy handles images + K8s + filesystem in one binary. Grype + Syft requires two tools for the same coverage. Trivy's SARIF output is more mature. |
| PDF generation | WeasyPrint | Playwright/wkhtmltopdf | WeasyPrint is pure Python (no headless browser). Smaller Docker image. wkhtmltopdf is deprecated. Playwright adds ~400MB to the Docker image for browser binaries. |
| PDF generation | WeasyPrint | ReportLab | ReportLab requires programmatic PDF construction (no HTML/CSS). WeasyPrint lets you write reports as HTML templates and convert to PDF -- much faster development. |
| Web framework | FastAPI | Flask | Flask lacks native async, auto-generated OpenAPI docs, and request validation. FastAPI is the modern standard for Python APIs. |
| HTTP client | httpx | aiohttp | httpx has a cleaner API, is recommended by FastAPI docs, and supports both sync and async. aiohttp is heavier. |
| HTTP client | httpx | requests | requests is sync-only. In an async FastAPI app, blocking HTTP calls would stall the event loop. |
| Python version | 3.12 | 3.13 | 3.13's free-threading (no-GIL) and JIT are experimental, behind flags, and not production-ready. 3.12 has the broadest library compatibility and is the most deployed version. |
| Linter | ruff | flake8 + black + isort | ruff replaces all three in a single Rust-based tool. 10-100x faster. Fewer dev dependencies. Industry momentum is strongly toward ruff in 2025-2026. |
| ORM | SQLAlchemy 2.0 | Tortoise ORM | SQLAlchemy has the largest ecosystem, best documentation, and Alembic for migrations. Tortoise is newer with smaller community. |
| CLI | typer | argparse | typer provides auto-generated help, type validation, and cleaner code. argparse is verbose and error-prone for complex CLIs. |

## What NOT to Use

| Technology | Why Not |
|------------|---------|
| PostgreSQL/MySQL | PROJECT.md constraint: SQLite only for portability |
| SonarQube | Too heavy for containerized pipeline; requires persistent server |
| Bandit | Overlaps with Semgrep for Python. Semgrep has broader language coverage and better custom rules |
| wkhtmltopdf | Deprecated, unmaintained, known security issues |
| requests (as primary HTTP client) | Sync-only, blocks async event loop |
| flake8/black/isort separately | ruff replaces all three, faster and simpler |
| Celery | Overkill for scan job queuing. Use Python asyncio with background tasks. Scans are triggered individually, not at high volume. |
| Redis | No need for external cache/queue. SQLite handles scan state. asyncio handles concurrency. |
| Node.js/React for dashboard | Over-engineered for an internal tool dashboard. Use FastAPI + Jinja2 server-rendered HTML with HTMX for interactivity. |
| HTMX | Worth considering for dashboard interactivity, but keep as optional enhancement. Start with server-rendered HTML and add if needed. |

## Docker Architecture

```
aipix-security-scanner/
  Dockerfile           # Single multi-stage image
  docker-compose.yml   # Single-container + volume mounts
```

**Base image:** `python:3.12-slim` (Debian Bookworm based, ~45MB compressed)

**Tool installation strategy:**
- Semgrep: `pip install semgrep` (Python package, installs OCaml binary)
- cppcheck: `apt-get install cppcheck` (system package)
- Gitleaks: Download Go binary from GitHub releases
- Trivy: Download binary from GitHub releases (or use aquasec apt repo)
- Checkov: `pip install checkov` (Python package)
- WeasyPrint: `apt-get install` system deps (libpango, libcairo) + `pip install weasyprint`

**Image size estimate:** ~1.5-2GB (Semgrep alone is ~500MB due to OCaml runtime)

**Optimization:** Multi-stage build where tool binaries are compiled/downloaded in builder stage, then copied to slim runtime stage.

## Installation

```bash
# Core application
pip install fastapi[standard] uvicorn[standard] pydantic

# Security scanning tools (Python-based)
pip install semgrep checkov

# AI analysis
pip install anthropic

# Database
pip install sqlalchemy[asyncio] aiosqlite alembic

# Report generation
pip install jinja2 weasyprint

# HTTP client & notifications
pip install httpx aiosmtplib

# Configuration
pip install pyyaml python-dotenv typer

# Dev dependencies
pip install -D pytest pytest-asyncio ruff mypy httpx
```

```bash
# System packages (Dockerfile apt-get)
apt-get install -y cppcheck git

# Binary tools (Dockerfile wget/curl)
# Gitleaks - download from https://github.com/gitleaks/gitleaks/releases
# Trivy - download from https://github.com/aquasecurity/trivy/releases
```

## Version Pinning Strategy

Pin **major.minor** in requirements, allow patch updates:

```
# requirements.txt
fastapi>=0.135,<1.0
uvicorn>=0.42,<1.0
semgrep>=1.156,<2.0
anthropic>=0.85,<1.0
sqlalchemy>=2.0,<3.0
aiosqlite>=0.20,<1.0
jinja2>=3.1,<4.0
weasyprint>=68.1,<69.0
checkov>=3.2,<4.0
httpx>=0.27,<1.0
pyyaml>=6.0,<7.0
typer>=0.15,<1.0
ruff>=0.9
```

Pin **exact versions** for security scanning binaries in Dockerfile (reproducible builds):
```dockerfile
ARG GITLEAKS_VERSION=8.24.3
ARG TRIVY_VERSION=0.69.3
ARG CPPCHECK_VERSION=2.19
```

## Sources

- [Semgrep releases](https://github.com/semgrep/semgrep/releases) -- v1.156.0 confirmed March 2026
- [Semgrep CE Fall 2025 release](https://semgrep.dev/blog/2025/semgrep-community-edition-fall-release-2025/) -- multicore performance
- [Gitleaks GitHub](https://github.com/gitleaks/gitleaks) -- v8.30.0 Nov 2025
- [Betterleaks announcement](https://www.aikido.dev/blog/betterleaks-gitleaks-successor) -- March 2026, too new
- [Trivy releases](https://github.com/aquasecurity/trivy/releases) -- v0.69.3 March 2026
- [Checkov PyPI](https://pypi.org/project/checkov/) -- v3.2.509
- [cppcheck releases](https://github.com/danmar/cppcheck/releases) -- v2.19.0 Jan 2026
- [FastAPI releases](https://github.com/fastapi/fastapi/releases) -- v0.135.1 March 2026
- [Anthropic Python SDK](https://pypi.org/project/anthropic/) -- v0.85.0 March 2026
- [WeasyPrint changelog](https://doc.courtbouillon.org/weasyprint/stable/changelog.html) -- v68.1 Jan 2026
- [Jinja2 PyPI](https://pypi.org/project/Jinja2/) -- v3.1.6 March 2025
- [Uvicorn PyPI](https://pypi.org/project/uvicorn/) -- v0.42.0 March 2026
- [Python Docker base images guide](https://pythonspeed.com/articles/base-image-python-docker-images/) -- recommends 3.12-slim
- [SARIF standard](https://www.sonarsource.com/resources/library/sarif/) -- v2.1.0 industry standard
