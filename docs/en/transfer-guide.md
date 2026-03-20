# Transfer Guide

## Overview

This guide covers migrating aipix-security-scanner to a new server or datacenter. The scanner is fully self-contained in Docker, making transfers straightforward.

## Prerequisites on Target Server

- Docker Engine 20.10+
- Docker Compose v2+
- 2 GB RAM minimum
- 10 GB disk space

## Step-by-Step Migration

### Step 1: Backup on Source Server

```bash
# On source server
cd /path/to/naveksoft-security

# Stop scanner (ensures clean DB state)
docker compose down

# Create transfer archive
mkdir -p /tmp/scanner-transfer
cp -r . /tmp/scanner-transfer/source/
docker cp naveksoft-security-scanner-1:/data/scanner.db /tmp/scanner-transfer/ 2>/dev/null || true

# If scanner was already stopped, extract from volume
docker run --rm -v naveksoft-security_scanner_data:/data -v /tmp/scanner-transfer:/backup \
  alpine cp /data/scanner.db /backup/

tar czf /tmp/scanner-transfer.tar.gz -C /tmp scanner-transfer/
```

### Step 2: Transfer to Target

```bash
# Copy archive to target server
scp /tmp/scanner-transfer.tar.gz user@target-server:/tmp/
```

### Step 3: Deploy on Target

```bash
# On target server
cd /opt  # or preferred location
tar xzf /tmp/scanner-transfer.tar.gz
mv scanner-transfer/source naveksoft-security
cd naveksoft-security

# Restore database
mkdir -p /tmp/scanner-data
cp /tmp/scanner-transfer/scanner.db /tmp/scanner-data/ 2>/dev/null || true

# Configure
cp config.yml.example config.yml
# Edit config.yml as needed

# Set environment
cat > .env << 'EOF'
SCANNER_API_KEY=your-api-key
SCANNER_CLAUDE_API_KEY=sk-ant-...
EOF

# Build and start
docker compose up -d --build

# Verify
curl http://localhost:8000/api/health
```

### Step 4: Restore Database

```bash
# Copy database into container volume
docker cp /tmp/scanner-data/scanner.db naveksoft-security-scanner-1:/data/scanner.db

# Restart to pick up restored data
docker compose restart

# Verify data
curl http://localhost:8000/api/health
```

### Step 5: Cleanup Source

After verifying the target works:

```bash
# On source server
docker compose down -v  # Removes volumes too
rm -rf /tmp/scanner-transfer*
```

## Files to Transfer

| File/Dir | Required | Description |
|----------|----------|-------------|
| `docker-compose.yml` | Yes | Service definition |
| `Dockerfile` | Yes | Build instructions |
| `src/` | Yes | Application source |
| `pyproject.toml` | Yes | Python dependencies |
| `config.yml` | Yes | Configuration |
| `.env` | Yes | Secrets (create new!) |
| `alembic/` | Yes | Database migrations |
| `alembic.ini` | Yes | Alembic config |
| `scanner.db` | Optional | Existing scan data |
| `tests/` | Optional | Test suite |
| `docs/` | Optional | Documentation |

## Quick Transfer (Git-based)

If the target has internet access:

```bash
git clone https://github.com/AlexTalorJr/naveksoft-security.git
cd naveksoft-security
cp config.yml.example config.yml
# Configure .env with secrets
docker compose up -d
```

Database must still be transferred separately.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Port 8000 in use | Change `SCANNER_PORT` in `.env` |
| Permission denied on `/data` | Check Docker volume permissions |
| Health returns "degraded" | Check DB path and file permissions |
| Container keeps restarting | Check `docker compose logs scanner` |
