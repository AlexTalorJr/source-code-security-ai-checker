# External Integrations

**Analysis Date:** 2026-03-20

## APIs & External Services

**AI / LLM:**
- Anthropic Claude API - Core AI analysis of security findings and cross-component risk correlation
  - SDK/Client: `anthropic>=0.86.0` (`AsyncAnthropic` in `src/scanner/ai/analyzer.py`)
  - Auth: `SCANNER_CLAUDE_API_KEY` env var
  - Model: configurable; default `claude-sonnet-4-6` (set in `config.yml` `ai.model`)
  - Usage: tool-use API calls for `security_analysis` and `cross_component_correlation` tools; pre-flight `count_tokens` for budget enforcement
  - Cost guard: `ai.max_cost_per_scan` (default $5.00 USD per scan)

**Slack:**
- Slack Incoming Webhooks - Post-scan notifications with Block Kit messages
  - Client: `httpx.AsyncClient` (no SDK) (`src/scanner/notifications/slack.py`)
  - Auth: `SCANNER_SLACK_WEBHOOK_URL` env var
  - Trigger: on scan completion, if `notifications.slack.enabled = true`
  - Errors are swallowed; never interrupt scan pipeline

**Git Hosting (any HTTPS/SSH provider):**
- Remote git repositories - Source target for repo-URL scan mode
  - Client: system `git` binary via `asyncio.create_subprocess_exec` (`src/scanner/core/git.py`)
  - Auth: `SCANNER_GIT_TOKEN` env var (HTTPS token via `GIT_ASKPASS` script; avoids token in process args)
  - Supports: any HTTPS or SSH git URL

## Data Storage

**Databases:**
- SQLite - Primary and only data store
  - Location: `/data/scanner.db` (configurable via `SCANNER_DB_PATH`)
  - Connection string: `sqlite+aiosqlite:///{db_path}`
  - Client: SQLAlchemy 2.0 async ORM + aiosqlite driver (`src/scanner/db/session.py`)
  - Mode: WAL (Write-Ahead Logging) with `synchronous=NORMAL`, `foreign_keys=ON`
  - Migrations: Alembic (`alembic/`, `alembic.ini`) + inline column-addition fallback in `src/scanner/main.py`

**File Storage:**
- Local filesystem only
  - Scan reports (HTML, PDF) written to local paths
  - Git repos cloned to `tempfile.mkdtemp()` directories and cleaned up after each scan
  - Suppression rules: persisted in SQLite `suppressions` table

**Caching:**
- None

## Authentication & Identity

**API Authentication:**
- Custom static API key - `X-API-Key` header required on all `/api/*` endpoints
  - Implementation: `src/scanner/api/auth.py` (`require_api_key` FastAPI dependency)
  - Comparison: `secrets.compare_digest` (timing-safe)
  - Key source: `SCANNER_API_KEY` env var
  - Error: 503 if not configured, 401 if invalid

**Dashboard Authentication:**
- Custom session-based auth - Web dashboard at `/dashboard`
  - Implementation: `src/scanner/dashboard/auth.py`

## Monitoring & Observability

**Error Tracking:**
- None (no Sentry, Datadog, etc.)

**Logs:**
- Python stdlib `logging` module throughout
  - Level configurable via `log_level` setting (default: `info`)
  - Structured as module-level loggers (`logging.getLogger(__name__)`)
  - Notification failures logged as `WARNING` with `exc_info=True`

**Health Check:**
- HTTP endpoint: `GET /api/health` (`src/scanner/api/health.py`)
- Docker healthcheck polls this endpoint every 30s

## CI/CD & Deployment

**Hosting:**
- Docker container via `docker-compose.yml`
- Single-service deployment; no orchestration (no Kubernetes manifests)

**CI Pipeline:**
- Jenkins integration provided as a drop-in stage (`Jenkinsfile.security`)
  - Triggers scan via `POST /api/scans` with workspace path
  - Polls `GET /api/scans/{id}` for completion (max 15 minutes, 10s intervals)
  - Fails build if `gate_passed = false`
  - Requires Jenkins credentials: `scanner-url`, `scanner-api-key`

## Environment Configuration

**Required env vars:**
- `SCANNER_API_KEY` - API authentication key (503 returned if missing)
- `SCANNER_CLAUDE_API_KEY` - Anthropic API key (AI analysis disabled if missing)

**Optional env vars:**
- `SCANNER_SLACK_WEBHOOK_URL` - Enables Slack notifications
- `SCANNER_EMAIL_SMTP_HOST` - Enables email notifications
- `SCANNER_GIT_TOKEN` - HTTPS auth for private git repositories
- `SCANNER_DB_PATH` - SQLite DB file path (default: `/data/scanner.db`)
- `SCANNER_CONFIG_PATH` - YAML config file path (default: `config.yml`)
- `SCANNER_PORT` - Host port binding in docker-compose (default: `8000`)

**Secrets location:**
- All secrets must be provided as environment variables; never hardcoded
- `config.yml` documents secrets as empty strings with comments pointing to env vars

## Webhooks & Callbacks

**Incoming:**
- None (the scanner itself is not a webhook receiver)

**Outgoing:**
- Slack Incoming Webhook: `POST {SCANNER_SLACK_WEBHOOK_URL}` with `{"blocks": [...]}` JSON payload
  - Sent after each scan completes when Slack notifications are enabled
  - Implemented in `src/scanner/notifications/slack.py`

## Scanner Tool Integrations

These are local CLI tool integrations, not external APIs, but are critical external dependencies:

**Semgrep:**
- Type: Static analysis (SAST), multi-language
- Invocation: subprocess via `src/scanner/adapters/semgrep.py`
- Input: JSON output (`--json`)
- Installation: pip in Docker image

**Cppcheck:**
- Type: C/C++ static analysis
- Invocation: subprocess via `src/scanner/adapters/cppcheck.py`
- Input: XML output (`--xml`); `defusedxml` used for safe parsing
- Installation: apt package in Docker image

**Gitleaks:**
- Type: Secret/credential scanning
- Invocation: subprocess via `src/scanner/adapters/gitleaks.py`
- Input: JSON output
- Installation: binary downloaded from GitHub releases (v8.30.0)

**Trivy:**
- Type: Container image and dependency vulnerability scanning
- Invocation: subprocess via `src/scanner/adapters/trivy.py`
- Input: JSON output
- Installation: binary downloaded from GitHub releases (v0.69.3)

**Checkov:**
- Type: Infrastructure-as-Code (IaC) security scanning
- Invocation: subprocess via `src/scanner/adapters/checkov.py`
- Input: JSON output
- Installation: pip in Docker image

---

*Integration audit: 2026-03-20*
