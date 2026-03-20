# Transfer Guide

## Overview

This guide covers migrating aipix-security-scanner to a new server, handing the project to a new team, or setting up a fresh installation.

**What gets transferred:**
- SQLite database (scan history, findings, suppressions)
- Configuration files (`config.yml`, `.env`)
- Generated reports (HTML/PDF)

**What does NOT get transferred:**
- Docker images -- rebuilt on the target host from source
- Python virtual environments -- recreated during `make install`

## Prerequisites

The target host needs:

- Docker Engine 20.10+
- Docker Compose v2+
- GNU Make
- Git (for cloning the repository)
- 2 GB RAM minimum
- 10 GB disk space

## Export from Source

Create a backup archive on the source server:

```bash
cd /path/to/naveksoft-security

# Create timestamped backup (DB + reports + config)
make backup
# Output: backups/backup-YYYYMMDD_HHMMSS.tar.gz
```

Copy the archive to the target host:

```bash
scp backups/backup-*.tar.gz user@target-server:/tmp/
```

## Import to Target

### Fresh Installation (Git Clone)

```bash
# On target server
git clone https://github.com/AlexTalorJr/naveksoft-security.git
cd naveksoft-security

# Configure
cp .env.example .env
# Edit .env with real values (see Environment Variables Reference below)

cp config.yml.example config.yml
# Edit config.yml if needed

# Build and start
make install
make run

# Run migrations
make migrate

# Verify
curl http://localhost:8000/api/health
```

### Restoring Data from Backup

If you have a backup archive from the source server:

```bash
# After make install and make run:
make restore BACKUP=/tmp/backup-20260320_143000.tar.gz

# Restart to pick up restored data
docker compose restart

# Verify
curl http://localhost:8000/api/health
```

## Onboarding Checklist

Follow these steps to get a new installation running:

1. Install Docker and Docker Compose on the target host
2. Clone the repository:
   ```bash
   git clone https://github.com/AlexTalorJr/naveksoft-security.git
   cd naveksoft-security
   ```
3. Copy configuration templates:
   ```bash
   cp config.yml.example config.yml
   cp .env.example .env
   ```
4. Set `SCANNER_API_KEY` -- generate a secure key:
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
5. Set `SCANNER_CLAUDE_API_KEY` -- obtain from the [Anthropic Console](https://console.anthropic.com/)
6. Configure notification settings if needed:
   - Slack: set `SCANNER_SLACK_WEBHOOK_URL` in `.env`
   - Email: set `SCANNER_EMAIL_SMTP_HOST`, `SCANNER_NOTIFICATIONS__EMAIL__SMTP_USER`, `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PASSWORD`, and `SCANNER_NOTIFICATIONS__EMAIL__RECIPIENTS` in `.env`
7. Build Docker images:
   ```bash
   make install
   ```
8. Start the scanner:
   ```bash
   make run
   ```
9. Run database migrations:
   ```bash
   make migrate
   ```
10. Verify the health endpoint:
    ```bash
    curl http://localhost:8000/api/health
    # Expected: {"status": "healthy", ...}
    ```
11. Run your first scan:
    ```bash
    curl -X POST http://localhost:8000/api/scans \
      -H "X-API-Key: your-key" \
      -H "Content-Type: application/json" \
      -d '{"path": "/path/to/code"}'
    ```

## Environment Variables Reference

All variables use the `SCANNER_` prefix. Set them in the `.env` file.

| Variable | Required | Default | Description | Example |
|----------|----------|---------|-------------|---------|
| `SCANNER_API_KEY` | Yes | -- | API key for REST API authentication | `dGhpcyBpcyBhIHRlc3Q` |
| `SCANNER_CLAUDE_API_KEY` | Yes | -- | Anthropic API key for AI analysis | `sk-ant-api03-...` |
| `SCANNER_PORT` | No | `8000` | External port for the scanner | `9000` |
| `SCANNER_DB_PATH` | No | `/data/scanner.db` | SQLite database file path | `/data/scanner.db` |
| `SCANNER_CONFIG_PATH` | No | `config.yml` | Path to YAML config file | `config.yml` |
| `SCANNER_GIT_TOKEN` | No | -- | Token for cloning private repos | `ghp_xxxxxxxxxxxx` |
| `SCANNER_SLACK_WEBHOOK_URL` | No | -- | Slack webhook for notifications | `https://hooks.slack.com/...` |
| `SCANNER_EMAIL_SMTP_HOST` | No | -- | SMTP server for email notifications | `smtp.gmail.com` |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PORT` | No | `587` | SMTP port | `587` |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_USER` | No | -- | SMTP username | `alerts@example.com` |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PASSWORD` | No | -- | SMTP password | -- |
| `SCANNER_NOTIFICATIONS__EMAIL__RECIPIENTS` | No | `[]` | JSON array of recipient emails | `["dev@example.com"]` |

## Troubleshooting

### Container Won't Start

```bash
docker compose logs scanner
```

Common causes:
- Port already in use -- change `SCANNER_PORT` in `.env`
- Missing `.env` file -- copy from `.env.example`
- Docker not running -- start Docker daemon

### Health Endpoint Returns Error

```bash
curl http://localhost:8000/api/health
# {"status": "degraded", "database": "error"}
```

Check that `SCANNER_DB_PATH` points to a writable location inside the container. The default `/data/scanner.db` requires the `scanner_data` volume to be mounted.

### Scans Fail or Timeout

- Check that scanner tools (semgrep, trivy, etc.) are available inside the Docker image
- Increase `scan_timeout` in `config.yml` for large repositories
- For private repos, ensure `SCANNER_GIT_TOKEN` is set

### Database Locked Errors

The database uses WAL mode for concurrent read access. If you see "database is locked" errors:
- Ensure only one scanner container is running
- Do not access the SQLite file directly while the container is running
- Use `make backup` for safe database copies

### Permission Denied on /data

The container runs as a non-root `scanner` user. Ensure the Docker volume has correct ownership:

```bash
docker compose down
docker volume rm naveksoft-security_scanner_data
docker compose up -d  # Recreates volume with correct permissions
```

Note: This removes existing scan data. Back up first with `make backup`.
