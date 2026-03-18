# Transfer Guide / Руководство по миграции

## Overview / Обзор

This guide covers migrating aipix-security-scanner to a new server or datacenter. The scanner is fully self-contained in Docker, making transfers straightforward.

Это руководство описывает миграцию aipix-security-scanner на новый сервер или в новый дата-центр. Сканер полностью автономен в Docker, что делает перенос простым.

## Prerequisites on Target Server / Требования к целевому серверу

- Docker Engine 20.10+
- Docker Compose v2+
- 2 GB RAM minimum / минимум
- 10 GB disk space / дискового пространства

## Step-by-Step Migration / Пошаговая миграция

### Step 1: Backup on Source Server / Шаг 1: Бэкап на исходном сервере

```bash
# On source server / На исходном сервере
cd /path/to/naveksoft-security

# Stop scanner (ensures clean DB state)
# Остановите сканер (чистое состояние БД)
docker compose down

# Create transfer archive / Создать архив для переноса
mkdir -p /tmp/scanner-transfer
cp -r . /tmp/scanner-transfer/source/
docker cp naveksoft-security-scanner-1:/data/scanner.db /tmp/scanner-transfer/ 2>/dev/null || true

# If scanner was already stopped, extract from volume
# Если сканер уже остановлен, извлечь из volume
docker run --rm -v naveksoft-security_scanner_data:/data -v /tmp/scanner-transfer:/backup \
  alpine cp /data/scanner.db /backup/

tar czf /tmp/scanner-transfer.tar.gz -C /tmp scanner-transfer/
```

### Step 2: Transfer to Target / Шаг 2: Перенос на целевой сервер

```bash
# Copy archive to target server / Скопировать архив на целевой сервер
scp /tmp/scanner-transfer.tar.gz user@target-server:/tmp/
```

### Step 3: Deploy on Target / Шаг 3: Деплой на целевом сервере

```bash
# On target server / На целевом сервере
cd /opt  # or preferred location
tar xzf /tmp/scanner-transfer.tar.gz
mv scanner-transfer/source naveksoft-security
cd naveksoft-security

# Restore database / Восстановить базу данных
mkdir -p /tmp/scanner-data
cp /tmp/scanner-transfer/scanner.db /tmp/scanner-data/ 2>/dev/null || true

# Configure / Настроить
cp config.yml.example config.yml
# Edit config.yml as needed / Отредактируйте config.yml

# Set environment / Установить окружение
cat > .env << 'EOF'
SCANNER_API_KEY=your-api-key
SCANNER_CLAUDE_API_KEY=sk-ant-...
EOF

# Build and start / Собрать и запустить
docker compose up -d --build

# Verify / Проверить
curl http://localhost:8000/api/health
```

### Step 4: Restore Database / Шаг 4: Восстановить БД

```bash
# Copy database into container volume
# Скопировать БД в volume контейнера
docker cp /tmp/scanner-data/scanner.db naveksoft-security-scanner-1:/data/scanner.db

# Restart to pick up restored data
# Перезапустить для подхвата данных
docker compose restart

# Verify data / Проверить данные
curl http://localhost:8000/api/health
```

### Step 5: Cleanup Source / Шаг 5: Очистка исходного сервера

After verifying the target works / После проверки работы на целевом сервере:

```bash
# On source server / На исходном сервере
docker compose down -v  # Removes volumes too / Удаляет и volumes
rm -rf /tmp/scanner-transfer*
```

## Files to Transfer / Файлы для переноса

| File/Dir | Required | Description / Описание |
|----------|----------|----------------------|
| `docker-compose.yml` | Yes | Service definition / Определение сервиса |
| `Dockerfile` | Yes | Build instructions / Инструкции сборки |
| `src/` | Yes | Application source / Исходный код |
| `pyproject.toml` | Yes | Python dependencies / Зависимости |
| `config.yml` | Yes | Configuration / Конфигурация |
| `.env` | Yes | Secrets (create new!) / Секреты (создать новый!) |
| `alembic/` | Yes | Database migrations / Миграции БД |
| `alembic.ini` | Yes | Alembic config / Конфиг Alembic |
| `scanner.db` | Optional | Existing scan data / Существующие данные |
| `tests/` | Optional | Test suite / Тесты |
| `docs/` | Optional | Documentation / Документация |

## Quick Transfer (Git-based) / Быстрый перенос (через Git)

If the target has internet access / Если на целевом сервере есть интернет:

```bash
git clone https://github.com/AlexTalorJr/naveksoft-security.git
cd naveksoft-security
cp config.yml.example config.yml
# Configure .env with secrets
docker compose up -d
```

Database must still be transferred separately.
Базу данных всё равно нужно перенести отдельно.

## Troubleshooting / Устранение проблем

| Problem | Solution |
|---------|----------|
| Port 8000 in use | Change `SCANNER_PORT` in `.env` |
| Permission denied on `/data` | Check Docker volume permissions |
| Health returns "degraded" | Check DB path and file permissions |
| Container keeps restarting | Check `docker compose logs scanner` |
