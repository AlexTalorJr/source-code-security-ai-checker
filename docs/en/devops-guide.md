# DevOps Guide

## Docker Deployment

### Quick Start

```bash
cp config.yml.example config.yml
cp .env.example .env
# Edit .env with real secrets
docker compose up -d
```

### Dockerfile

Multi-stage build based on `python:3.12-slim`:
- Non-root user `scanner` for security
- `curl` installed for health checks
- Package installed via `pip install .` with hatchling build backend

### docker-compose.yml

```yaml
services:
  scanner:
    build: .
    ports:
      - "${SCANNER_PORT:-8000}:8000"
    volumes:
      - scanner_data:/data           # Persistent DB storage
      - ./config.yml:/app/config.yml:ro  # Read-only config
    environment:
      - SCANNER_DB_PATH=/data/scanner.db
      - SCANNER_API_KEY=${SCANNER_API_KEY:-}
      - SCANNER_CLAUDE_API_KEY=${SCANNER_CLAUDE_API_KEY:-}
      - SCANNER_CONFIG_PATH=/app/config.yml
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

### Environment Variables

Pass secrets via `.env` file (not committed to git):

```bash
# .env
SCANNER_API_KEY=your-api-key
SCANNER_CLAUDE_API_KEY=sk-ant-...
SCANNER_PORT=8000
```

### Health Checks

Docker health check runs every 30 seconds:

```bash
# Check container health
docker compose ps

# Manual check
curl http://localhost:8000/api/health
```

### Logs

```bash
# Tail logs
docker compose logs -f scanner

# Last 100 lines
docker compose logs scanner --tail 100
```

### Rebuild

```bash
docker compose down
docker compose up -d --build
```

### Data Persistence

SQLite database is stored in a named Docker volume `scanner_data` mounted at `/data`. Data survives container restarts and rebuilds.

```bash
# Inspect volume
docker volume inspect naveksoft-security_scanner_data

# Backup
docker cp naveksoft-security-scanner-1:/data/scanner.db ./backup/scanner.db

# Restore
docker cp ./backup/scanner.db naveksoft-security-scanner-1:/data/scanner.db
docker compose restart
```

### Port Configuration

```bash
# Change external port
SCANNER_PORT=9000 docker compose up -d
```

## Jenkins Integration

The scanner integrates with Jenkins pipelines via a Jenkinsfile stage that triggers a scan and checks the quality gate. Uses the Jenkins `httpRequest` plugin for API calls.

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
            def scanId = readJSON(text: response.content).id
            // Poll for completion, then check quality gate
        }
    }
}
```

## Backup Strategy

### Automated Backup Script

```bash
#!/bin/bash
# backup-scanner.sh
BACKUP_DIR="/backups/scanner/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# Copy database (WAL mode allows hot backup)
docker cp naveksoft-security-scanner-1:/data/scanner.db "$BACKUP_DIR/"
docker cp naveksoft-security-scanner-1:/data/scanner.db-wal "$BACKUP_DIR/" 2>/dev/null
docker cp naveksoft-security-scanner-1:/data/scanner.db-shm "$BACKUP_DIR/" 2>/dev/null

# Copy config
cp config.yml "$BACKUP_DIR/"

echo "Backup saved to $BACKUP_DIR"
```

Add to cron:
```bash
0 2 * * * /path/to/backup-scanner.sh
```

## Local Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run all tests
python -m pytest tests/ -v

# Run specific phase tests
python -m pytest tests/phase_01/ -v

# Start dev server
SCANNER_DB_PATH=./dev.db uvicorn scanner.main:app --reload
```
