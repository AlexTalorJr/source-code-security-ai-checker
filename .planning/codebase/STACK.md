# Technology Stack

**Analysis Date:** 2026-03-20

## Languages

**Primary:**
- Python 3.12 - All application code (API, CLI, core logic, adapters, notifications, reports)

**Secondary:**
- Jinja2 HTML templates - Report and email rendering (`src/scanner/reports/templates/`, `src/scanner/notifications/templates/`)
- Groovy - Jenkins CI pipeline integration (`Jenkinsfile.security`)

## Runtime

**Environment:**
- Python 3.12 (CPython)
- Async-first: `asyncio` used throughout; all I/O operations are async

**Package Manager:**
- `pip` with `hatchling` build backend
- Build definition: `pyproject.toml`
- Lockfile: Not present (no `requirements.lock` or `uv.lock`)

## Frameworks

**Core:**
- FastAPI (standard extras) - REST API server and HTTP layer (`src/scanner/api/`, `src/scanner/main.py`)
- Pydantic v2 - Data validation and schemas throughout (`src/scanner/schemas/`, `src/scanner/api/schemas.py`)
- pydantic-settings[yaml] - Configuration management with YAML + env var override (`src/scanner/config.py`)
- Typer[all] - CLI interface (`src/scanner/cli/main.py`)

**Database:**
- SQLAlchemy 2.0+ (async) - ORM and query layer (`src/scanner/db/`, `src/scanner/models/`)
- aiosqlite - Async SQLite driver used by SQLAlchemy
- Alembic - Database migrations (`alembic/`, `alembic.ini`)

**Testing:**
- pytest - Test runner (`pyproject.toml` test config)
- pytest-asyncio - Async test support (`asyncio_mode = "auto"`)
- httpx - HTTP client for API integration tests

**Build/Dev:**
- hatchling - Build backend for wheel packaging
- uvicorn - ASGI server (production entry point in `Dockerfile`)

## Key Dependencies

**Critical:**
- `anthropic>=0.86.0` - Claude AI API client; used for security finding analysis and compound risk correlation (`src/scanner/ai/analyzer.py`)
- `fastapi[standard]` - Web framework; drives all REST API behavior
- `sqlalchemy>=2.0` + `aiosqlite` - Async SQLite persistence; scan results, findings, suppressions

**Infrastructure:**
- `httpx` - Async HTTP client; used for Slack webhook delivery (`src/scanner/notifications/slack.py`)
- `jinja2>=3.1.6` - Template engine; powers HTML/PDF reports and email notifications
- `weasyprint>=68.0` - HTML-to-PDF renderer; requires system libs `libpango`, `libharfbuzz` (installed in `Dockerfile`)
- `matplotlib>=3.10.0` - Chart generation for severity pie and tool bar charts in reports (`src/scanner/reports/charts.py`); uses `Agg` (non-GUI) backend
- `rich` - Terminal output formatting for CLI (`src/scanner/cli/main.py`)
- `defusedxml>=0.7.1` - Safe XML parsing; guards against XML injection in scanner output parsing
- `typer[all]` - CLI framework with completion support

**External CLI Tools (bundled in Docker image):**
- `semgrep` (pip-installed) - SAST scanner (`src/scanner/adapters/semgrep.py`)
- `cppcheck` (apt package) - C/C++ static analysis (`src/scanner/adapters/cppcheck.py`)
- `gitleaks v8.30.0` (binary, GitHub release) - Secret scanning (`src/scanner/adapters/gitleaks.py`)
- `trivy v0.69.3` (binary, GitHub release) - Container/dependency vulnerability scan (`src/scanner/adapters/trivy.py`)
- `checkov` (pip-installed) - IaC security scan (`src/scanner/adapters/checkov.py`)

## Configuration

**Environment:**
- Config file: `config.yml` (lowest priority; template at `config.yml.example`)
- Environment variables: `SCANNER_*` prefix, `SCANNER__` nested delimiter
- Priority order: constructor args > env vars > dotenv > file secrets > YAML
- Config class: `ScannerSettings` in `src/scanner/config.py`

**Key env vars required:**
- `SCANNER_API_KEY` - REST API authentication key
- `SCANNER_CLAUDE_API_KEY` - Anthropic API key for AI analysis
- `SCANNER_SLACK_WEBHOOK_URL` - Optional Slack webhook
- `SCANNER_EMAIL_SMTP_HOST` - Optional SMTP host
- `SCANNER_GIT_TOKEN` - Optional HTTPS git auth token
- `SCANNER_CONFIG_PATH` - Override config file path (default: `config.yml`)

**Build:**
- `pyproject.toml` - Project metadata, dependencies, pytest config
- `Dockerfile` - Multi-step image; Python 3.12-slim base; installs apt deps, pip tools, binary tools
- `docker-compose.yml` - Single-service deployment with named volume `scanner_data` at `/data`

## Platform Requirements

**Development:**
- Python 3.12+
- External scanner tools must be installed and on `PATH`: `semgrep`, `cppcheck`, `gitleaks`, `trivy`, `checkov`
- System libs for WeasyPrint: `libpango`, `libpangoft2`, `libharfbuzz-subset0`

**Production:**
- Docker (recommended); image built from `Dockerfile`
- Deployed as single container via `docker-compose.yml`
- ASGI server: `uvicorn` on port 8000
- Persistent SQLite DB at `/data/scanner.db` (Docker named volume)

---

*Stack analysis: 2026-03-20*
