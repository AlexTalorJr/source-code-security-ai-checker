# Source Code Security AI Scanner

AI-powered security vulnerability scanner for source code analysis.

## Quick Start

Get your first scan running in under 5 minutes.

### Prerequisites

- Docker & Docker Compose
- An Anthropic API key (for AI analysis)

### Setup

```bash
# 1. Clone
git clone https://github.com/AlexTalorJr/naveksoft-security.git
cd naveksoft-security

# 2. Configure
cp config.yml.example config.yml
cp .env.example .env

# 3. Set secrets in .env
#    SCANNER_API_KEY=<your-api-key>
#    SCANNER_CLAUDE_API_KEY=<your-anthropic-key>

# 4. Launch
docker compose up -d

# 5. Verify
curl http://localhost:8000/api/health
```

Expected response:

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime_seconds": 5.23,
  "database": "ok"
}
```

### Run a Scan

```bash
curl -X POST http://localhost:8000/api/scans \
  -H "X-API-Key: $SCANNER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/your-org/your-repo.git", "branch": "main"}'
```

## Features

- **5 parallel security scanners** -- Semgrep, cppcheck, Gitleaks, Trivy, Checkov
- **AI-powered analysis** -- Claude reviews findings for context, compound risks, and fix suggestions
- **Interactive HTML and PDF reports** -- filterable findings with code context and charts
- **Configurable quality gate** -- block deployments on Critical/High severity findings
- **REST API with web dashboard** -- scan management, history, suppression controls
- **Slack and email notifications** -- real-time alerts on scan completion
- **Jenkins CI integration** -- pipeline stage with quality gate checks
- **Scan history with delta comparison** -- track new, fixed, and persisting findings

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/en/architecture.md) | System design, component diagram, data flow |
| [Database Schema](docs/en/database-schema.md) | SQLite schema, ER diagram, indexes |
| [API Reference](docs/en/api.md) | REST API endpoints and authentication |
| [User Guide](docs/en/user-guide.md) | Reports, findings, quality gate, suppressions |
| [Admin Guide](docs/en/admin-guide.md) | Configuration, environment variables, tuning |
| [DevOps Guide](docs/en/devops-guide.md) | Docker deployment, Jenkins, backups |
| [Transfer Guide](docs/en/transfer-guide.md) | Server migration procedures |
| [Custom Rules](docs/en/custom-rules.md) | Writing Semgrep rules for aipix |

## Project Status

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Foundation & Data Models | Done |
| 2 | Scanner Adapters & Orchestration | Done |
| 3 | AI Analysis (Claude API) | Done |
| 4 | Report Generation (HTML/PDF) | Done |
| 5 | Dashboard, Notifications & Quality Gate | Done |
| 6 | Packaging, Portability & Documentation | In Progress |

## Tech Stack

- **Python 3.12** -- core language
- **FastAPI** -- REST API and web dashboard
- **SQLAlchemy 2.0** -- async ORM with SQLite
- **SQLite (WAL mode)** -- embedded database
- **Pydantic v2** -- data validation and settings
- **Docker** -- containerization
- **Alembic** -- database migrations
- **Anthropic Claude** -- AI-powered vulnerability analysis
- **WeasyPrint** -- PDF report generation
- **Jinja2** -- HTML templating for reports and dashboard
- **Typer** -- CLI interface

## License

Apache 2.0

---

Russian documentation: [README.ru.md](README.ru.md)
