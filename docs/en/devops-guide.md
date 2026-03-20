# DevOps Guide / Руководство по деплою

## Docker Deployment / Деплой через Docker

### Quick Start / Быстрый старт

```bash
cp config.yml.example config.yml
docker compose up -d
```

### Dockerfile

Multi-stage build based on `python:3.12-slim`:
- Non-root user `scanner` for security / Пользователь `scanner` (не root) для безопасности
- `curl` installed for health checks / `curl` для проверок состояния
- Package installed via `pip install .` with hatchling / Пакет установлен через `pip install .`

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

### Environment Variables / Переменные окружения

Pass secrets via `.env` file (not committed to git):
Передавайте секреты через `.env` файл (не коммитится в git):

```bash
# .env
SCANNER_API_KEY=your-api-key
SCANNER_CLAUDE_API_KEY=sk-ant-...
SCANNER_PORT=8000
```

### Health Checks / Проверки состояния

Docker health check runs every 30 seconds:

```bash
# Check container health / Проверить здоровье контейнера
docker compose ps

# Manual check / Ручная проверка
curl http://localhost:8000/api/health
```

### Logs / Логи

```bash
# Tail logs / Просмотр логов
docker compose logs -f scanner

# Last 100 lines / Последние 100 строк
docker compose logs scanner --tail 100
```

### Rebuild / Пересборка

```bash
docker compose down
docker compose up -d --build
```

### Data Persistence / Сохранение данных

SQLite database is stored in a named Docker volume `scanner_data` mounted at `/data`. Data survives container restarts and rebuilds.

БД SQLite хранится в именованном Docker volume `scanner_data`, примонтированном к `/data`. Данные сохраняются при перезапусках и пересборках контейнера.

```bash
# Inspect volume / Информация о volume
docker volume inspect naveksoft-security_scanner_data

# Backup / Резервное копирование
docker cp naveksoft-security-scanner-1:/data/scanner.db ./backup/scanner.db

# Restore / Восстановление
docker cp ./backup/scanner.db naveksoft-security-scanner-1:/data/scanner.db
docker compose restart
```

### Port Configuration / Настройка порта

```bash
# Change external port / Изменить внешний порт
SCANNER_PORT=9000 docker compose up -d
```

## Jenkins Integration / Интеграция с Jenkins

*(Phase 6 — planned / планируется)*

Will be added as a Jenkins pipeline stage that triggers scans and checks the quality gate.

Будет добавлено как стадия Jenkins pipeline, запускающая сканирование и проверяющая quality gate.

## Backup Strategy / Стратегия резервного копирования

### Automated Backup Script / Скрипт автоматического бэкапа

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

Add to cron / Добавить в cron:
```bash
0 2 * * * /path/to/backup-scanner.sh
```

## Local Development / Локальная разработка

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run all tests / Запуск всех тестов
python -m pytest tests/ -v

# Run specific phase / Тесты конкретной фазы
python -m pytest tests/phase_01/ -v

# Start dev server / Запуск dev-сервера
SCANNER_DB_PATH=./dev.db uvicorn scanner.main:app --reload
```
