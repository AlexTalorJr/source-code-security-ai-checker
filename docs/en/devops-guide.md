# DevOps Guide

## Docker Deployment

### Quick Start

```bash
cp config.yml.example config.yml
cp .env.example .env
# Edit .env with real secrets
make install   # builds Docker images
make run       # starts scanner in background
```

Or directly with Docker Compose:

```bash
docker compose up -d --build
```

### Container Configuration

The `docker-compose.yml` defines a single `scanner` service:

```yaml
services:
  scanner:
    build: .
    ports:
      - "${SCANNER_PORT:-8000}:8000"
    volumes:
      - scanner_data:/data           # Persistent DB and reports
      - ./config.yml:/app/config.yml:ro  # Read-only config mount
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    restart: unless-stopped

volumes:
  scanner_data:  # Named volume for SQLite persistence
```

- **Volume `scanner_data`** mounts at `/data` inside the container -- stores the SQLite database and generated reports. Data survives container restarts and rebuilds.
- **Config mount** binds `config.yml` read-only into the container at `/app/config.yml`.
- **Port mapping** defaults to `8000` but can be changed via `SCANNER_PORT` environment variable.
- **Restart policy** `unless-stopped` ensures the scanner restarts after host reboots.

## Dockerfile

The image is based on `python:3.12-slim` and includes all 12 scanner tools:

1. **System dependencies** -- `curl` (healthcheck), `libpango` and `libharfbuzz` (WeasyPrint PDF generation), `ruby` (Brakeman)
2. **Non-root user** -- `scanner` user and group created for security; `/data` directory owned by this user
3. **Scanner binaries** -- see Scanner Binaries section below for the full list
4. **Install workflow** -- `pyproject.toml` and `src/` copied, then `pip install --no-cache-dir .` using the hatchling build backend
5. **App files** -- `alembic.ini`, `alembic/` migrations, and `config.yml.example` (as default `config.yml`) copied in
6. **Entrypoint** -- `uvicorn scanner.main:app --host 0.0.0.0 --port 8000`

## Scanner Binaries

All 12 scanner tools are installed inside the Docker image:

| Scanner | Install Method | Notes |
|---------|---------------|-------|
| **Semgrep** | `pip install semgrep` | Python package, installed alongside application |
| **cppcheck** | `apt-get install cppcheck` | System package |
| **Gitleaks** | Pre-built binary from GitHub releases | Downloaded to `/usr/local/bin`, supports amd64/arm64 |
| **Trivy** | Pre-built binary from GitHub releases | Downloaded to `/usr/local/bin`, supports amd64/arm64 |
| **Checkov** | `pip install checkov` | Python package, installed with `--no-cache-dir` |
| **Psalm** | `composer global require vimeo/psalm` | PHP Composer package, requires `php-cli` |
| **Enlightn** | `composer global require enlightn/enlightn` | PHP Composer package |
| **PHP Security Checker** | Pre-built binary from GitHub releases | Downloaded to `/usr/local/bin` |
| **gosec** | Pre-built binary from GitHub releases | Downloaded to `/usr/local/bin`, supports amd64/arm64 |
| **Bandit** | `pip install bandit` | Python package, installed alongside Semgrep and Checkov |
| **Brakeman** | `gem install brakeman` | Ruby gem, requires `ruby` apt package (~80MB) |
| **cargo-audit** | Pre-built binary from GitHub releases | Downloaded to `/usr/local/bin`, supports amd64/arm64 |

All binary downloads (Gitleaks, Trivy, gosec, cargo-audit, PHP Security Checker) use architecture detection (`dpkg --print-architecture` / `uname -m`) to download the correct binary for amd64 or arm64 platforms.

### Verifying Scanner Availability

After building the Docker image, verify all scanners are correctly installed:

```bash
make verify-scanners
```

This target runs a smoke test inside the container, checking that each of the 12 scanner binaries is available and responds to version/help commands. Use this after any Dockerfile changes to ensure no scanner was broken.

## Environment Variables

All configuration can be set via environment variables with the `SCANNER_` prefix. Pass secrets via the `.env` file (not committed to git).

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SCANNER_API_KEY` | Yes | -- | API key for authenticating REST API requests |
| `SCANNER_CLAUDE_API_KEY` | Yes | -- | Anthropic API key for AI analysis |
| `SCANNER_PORT` | No | `8000` | External port for the scanner service |
| `SCANNER_DB_PATH` | No | `/data/scanner.db` | Path to SQLite database file |
| `SCANNER_CONFIG_PATH` | No | `config.yml` | Path to YAML configuration file |
| `SCANNER_GIT_TOKEN` | No | -- | Token for cloning private Git repositories |
| `SCANNER_SLACK_WEBHOOK_URL` | No | -- | Slack incoming webhook URL for notifications |
| `SCANNER_EMAIL_SMTP_HOST` | No | -- | SMTP server hostname for email notifications |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PORT` | No | `587` | SMTP server port |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_USER` | No | -- | SMTP authentication username |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PASSWORD` | No | -- | SMTP authentication password |
| `SCANNER_NOTIFICATIONS__EMAIL__RECIPIENTS` | No | `[]` | JSON array of email recipients |

## Jenkins Integration

The project includes `Jenkinsfile.security` for integrating security scans into a Jenkins pipeline. It uses the Jenkins `httpRequest` plugin for API calls.

### Setup

1. Install the **HTTP Request** plugin in Jenkins
2. Add `SCANNER_URL` (e.g., `http://scanner:8000`) as a Jenkins credential or environment variable
3. Add `SCANNER_API_KEY` as a Jenkins secret text credential

### Usage

Add the security scan stage to your existing `Jenkinsfile`:

```groovy
stage('Security Scan') {
    steps {
        script {
            def response = httpRequest(
                url: "${SCANNER_URL}/api/scans",
                httpMode: 'POST',
                customHeaders: [[name: 'X-API-Key', value: "${SCANNER_API_KEY}"]],
                contentType: 'APPLICATION_JSON',
                requestBody: """{"repo_url": "${GIT_URL}", "branch": "${GIT_BRANCH}"}"""
            )
            def scanResult = readJSON(text: response.content)
            def scanId = scanResult.id
            // Poll for completion, then check quality gate
        }
    }
}
```

### Quality Gate

The scanner evaluates a quality gate after each scan. Configure pass/fail criteria in `config.yml`:

```yaml
gate:
  fail_on:
    - critical
    - high
  include_compound_risks: true
```

If the gate fails, the Jenkins stage should fail the build. Query the scan result to check `gate_passed`.

## Backups

### Using Make Targets

```bash
# Create a timestamped backup (DB + reports + config)
make backup
# Output: backups/backup-20260320_143000.tar.gz

# Restore from a backup file
make restore BACKUP=backups/backup-20260320_143000.tar.gz
```

### What Gets Backed Up

- **SQLite database** -- backed up using `sqlite3 .backup` command (WAL-safe, no downtime required)
- **Reports** -- generated HTML/PDF reports from `/data/reports`
- **Configuration** -- `config.yml`

### WAL Mode Safety

The database runs in WAL (Write-Ahead Logging) mode. The `make backup` target uses SQLite's `.backup` command inside the container, which safely handles WAL checkpointing. Do not simply copy the `.db` file -- use the make target or `sqlite3 .backup` command.

### Recommended Schedule

Set up a daily cron job for automated backups:

```bash
# Daily at 2 AM
0 2 * * * cd /path/to/naveksoft-security && make backup
```

## Multi-Architecture Builds

Build Docker images for both `amd64` and `arm64` architectures using Docker Buildx.

### Prerequisites

- Docker Desktop 4.x+ (includes buildx) or manually installed `docker-buildx` plugin
- QEMU user-static for cross-platform emulation (Docker Desktop handles this automatically)

### Build Multi-Arch Images

```bash
# Build for amd64 + arm64, save as OCI archive
make docker-multiarch
# Output: Security AI Scanner-{version}-multiarch.tar

# Build and push to a container registry
make docker-push REGISTRY=your-registry.example.com
```

The `docker-multiarch` target creates a buildx builder named `multiarch` if it does not already exist.

All 12 scanner binary downloads (Gitleaks, Trivy, gosec, cargo-audit, PHP Security Checker) support both amd64 and arm64 architectures. Python packages (Semgrep, Checkov, Bandit) and Ruby gems (Brakeman) are platform-independent and work on both architectures without modification.

## Monitoring

### Health Endpoint

Poll the health endpoint to monitor scanner status:

```bash
curl http://localhost:8000/api/health
# {"status": "healthy", "version": "0.1.0", "uptime_seconds": 3600.5, "database": "ok"}
```

A `"degraded"` status or `"database": "error"` response indicates an issue with the database connection.

### Docker Healthcheck

The container includes a built-in healthcheck that runs every 30 seconds. Check container health status:

```bash
docker compose ps
# Shows "healthy" or "unhealthy" in the STATUS column
```

### Logs

```bash
# Follow logs in real time
docker compose logs -f scanner

# Last 100 lines
docker compose logs scanner --tail 100
```

Log level is configured in `config.yml` via the `log_level` field (default: `info`).

### Restart Policy

The container uses `restart: unless-stopped`, so it automatically restarts after crashes or host reboots. Only a manual `docker compose stop` or `docker compose down` will keep it stopped.

## Upgrading

1. Pull the latest code:
   ```bash
   git pull origin main
   ```

2. Rebuild and restart:
   ```bash
   make install   # rebuilds Docker image
   make run       # starts updated container
   ```

3. Run database migrations:
   ```bash
   make migrate
   ```

4. Verify the upgrade:
   ```bash
   curl http://localhost:8000/api/health
   ```

If the health endpoint returns the new version number and `"status": "healthy"`, the upgrade is complete.
