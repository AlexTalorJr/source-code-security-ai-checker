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
git clone https://github.com/AlexTalorJr/source-code-security-ai-checker.git
cd source-code-security-ai-checker

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

## Web Dashboard

The scanner includes a built-in web interface at `http://localhost:8000/dashboard/`.

**Login:** use the API key set in `SCANNER_API_KEY`.

### Starting a scan from the dashboard

1. Open **Scan History** (`/dashboard/history`)
2. Click **"Start New Scan"** — the form expands
3. Fill in either **Local Path** or **Repository URL** + **Branch**
4. Optionally check **"Skip AI Analysis"** to run without Claude API (faster, no cost)
5. Click **"Start Scan"**

The scan runs in the background. The detail page shows real-time progress with live polling, and results appear automatically when complete.

### Dashboard pages

| Page | URL | Description |
|------|-----|-------------|
| Scan History | `/dashboard/history` | List of all scans + start new scan form |
| Scan Detail | `/dashboard/scans/{id}` | Findings, severity breakdown, suppression controls |
| Trends | `/dashboard/trends` | Charts: severity over time, tool distribution |

### Run a Scan via API

```bash
curl -X POST http://localhost:8000/api/scans \
  -H "X-API-Key: $SCANNER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/your-org/your-repo.git", "branch": "main"}'
```

To skip AI analysis for a specific scan:

```bash
curl -X POST http://localhost:8000/api/scans \
  -H "X-API-Key: $SCANNER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/your-org/repo.git", "branch": "main", "skip_ai": true}'
```

## Jenkins Pipeline Integration

Add the scanner as a stage in your `Jenkinsfile` to block deployments with Critical/High findings.

### Basic Jenkinsfile stage

```groovy
pipeline {
    agent any

    environment {
        SCANNER_URL = 'http://scanner-host:8000'
        SCANNER_API_KEY = credentials('scanner-api-key')
    }

    stages {
        stage('Security Scan') {
            steps {
                script {
                    // Trigger scan
                    def response = httpRequest(
                        url: "${SCANNER_URL}/api/scans",
                        httpMode: 'POST',
                        contentType: 'APPLICATION_JSON',
                        customHeaders: [[name: 'X-API-Key', value: "${SCANNER_API_KEY}"]],
                        requestBody: """{"repo_url": "${env.GIT_URL}", "branch": "${env.GIT_BRANCH}"}"""
                    )

                    def scan = readJSON text: response.content
                    def scanId = scan.id
                    echo "Scan started: #${scanId}"

                    // Poll until complete
                    def status = 'queued'
                    while (status == 'queued' || status == 'running') {
                        sleep 10
                        def progress = httpRequest(
                            url: "${SCANNER_URL}/api/scans/${scanId}/progress",
                            httpMode: 'GET'
                        )
                        status = readJSON(text: progress.content).stage
                    }

                    // Check quality gate
                    def result = httpRequest(
                        url: "${SCANNER_URL}/api/scans/${scanId}",
                        httpMode: 'GET',
                        customHeaders: [[name: 'X-API-Key', value: "${SCANNER_API_KEY}"]]
                    )
                    def scanResult = readJSON text: result.content

                    if (!scanResult.gate_passed) {
                        error "Security scan FAILED: ${scanResult.critical_count} Critical, ${scanResult.high_count} High findings"
                    }

                    echo "Security scan PASSED (${scanResult.total_findings} findings, gate passed)"
                }
            }
        }
    }
}
```

### Key points

- **Quality gate** blocks the build if Critical or High findings are detected (configurable in `config.yml` under `gate.fail_on`)
- **Scan via local path** — if Jenkins and the scanner share a filesystem, use `"path": "${WORKSPACE}"` instead of `repo_url`
- **Skip AI analysis** — add `"skip_ai": true` to the request body for faster scans without Claude API costs
- **Notifications** — configure Slack/email in `config.yml` to get alerts on scan completion
- **Reports** — HTML and PDF reports are generated automatically, accessible via `/api/scans/{id}/report` or the dashboard

See [DevOps Guide](docs/en/devops-guide.md) for full Jenkins integration details including pipeline examples with parallel stages.

## Features

- **8 security scanners with auto-detection** -- scanners are enabled automatically based on project languages
- **Multi-language support** -- Python, PHP/Laravel, C/C++, JavaScript/TypeScript, Go, Rust, Java, C#, Ruby
- **AI-powered analysis** -- Claude reviews findings for context, compound risks, and fix suggestions
- **Interactive HTML and PDF reports** -- filterable findings with code context and charts
- **Configurable quality gate** -- block deployments on Critical/High severity findings
- **Web dashboard** -- scan management, real-time progress, history, suppression controls
- **REST API** -- trigger scans, fetch results, manage findings programmatically
- **Slack and email notifications** -- real-time alerts with scan target identification
- **Jenkins CI integration** -- pipeline stage with quality gate checks
- **Scan history with delta comparison** -- track new, fixed, and persisting findings
- **Skip AI per scan** -- run without Claude API when speed or cost matters

## Supported Scanners

Scanners are enabled automatically based on detected languages (`enabled: auto`). Override per scanner in `config.yml`.

| Scanner | Languages | What it finds |
|---------|-----------|---------------|
| **Semgrep** | Python, PHP, JS/TS, Go, Java, Ruby, C#, Rust | SAST — injection, auth issues, insecure patterns |
| **cppcheck** | C/C++ | Memory safety, buffer overflows, undefined behavior |
| **Gitleaks** | Any | Hardcoded secrets, API keys, tokens in code and git history |
| **Trivy** | Docker, Terraform, K8s | CVEs in container images and IaC misconfigurations |
| **Checkov** | Docker, Terraform, CI configs | Infrastructure-as-code security best practices |
| **Psalm** | PHP | Taint analysis — SQL injection, XSS via data flow tracking |
| **Enlightn** | Laravel | CSRF, mass assignment, debug mode, exposed .env (120+ checks) |
| **PHP Security Checker** | PHP (composer) | Known CVEs in composer dependencies |

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
| [Custom Rules](docs/en/custom-rules.md) | Writing custom Semgrep rules |

## Project Status

All v1.0 phases complete.

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Foundation & Data Models | Done |
| 2 | Scanner Adapters & Orchestration | Done |
| 3 | AI Analysis (Claude API) | Done |
| 4 | Report Generation (HTML/PDF) | Done |
| 5 | Dashboard, Notifications & Quality Gate | Done |
| 6 | Packaging, Portability & Documentation | Done |

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

Other languages: [Русский](README.ru.md) | [Français](README.fr.md) | [Español](README.es.md) | [Italiano](README.it.md)
