# Admin Guide / Руководство администратора

## Configuration / Конфигурация

### Config Sources (Priority Order) / Источники конфигурации (по приоритету)

1. **Constructor arguments** — programmatic overrides / программные значения
2. **Environment variables** — `SCANNER_*` prefix / переменные окружения с префиксом `SCANNER_`
3. **Dotenv file** — `.env` file / файл `.env`
4. **File secrets** — Docker/K8s secrets
5. **YAML config file** — `config.yml` (lowest priority / наименьший приоритет)

### Configuration File / Файл конфигурации

Copy the example and customize / Скопируйте пример и настройте:

```bash
cp config.yml.example config.yml
```

```yaml
# config.yml
host: "0.0.0.0"          # Listen address / Адрес прослушивания
port: 8000                # Listen port / Порт
db_path: "/data/scanner.db"  # SQLite database path / Путь к БД
api_key: ""               # Use env var! / Используйте переменную окружения!
claude_api_key: ""        # Use env var! / Используйте переменную окружения!
slack_webhook_url: ""     # Slack notifications / Уведомления Slack
email_smtp_host: ""       # Email notifications / Уведомления email
log_level: "info"         # debug/info/warning/error
scan_timeout: 600         # Max scan duration in seconds / Макс. время скана в секундах
```

### Environment Variables / Переменные окружения

All settings can be overridden with `SCANNER_` prefix:

Все настройки можно переопределить с префиксом `SCANNER_`:

| Variable | Description | Default |
|----------|-------------|---------|
| `SCANNER_HOST` | Listen address | `0.0.0.0` |
| `SCANNER_PORT` | Listen port | `8000` |
| `SCANNER_DB_PATH` | SQLite DB path | `/data/scanner.db` |
| `SCANNER_API_KEY` | API authentication key | `""` (empty) |
| `SCANNER_CLAUDE_API_KEY` | Claude API key for AI analysis | `""` (empty) |
| `SCANNER_SLACK_WEBHOOK_URL` | Slack webhook for notifications | `""` |
| `SCANNER_EMAIL_SMTP_HOST` | SMTP host for email notifications | `""` |
| `SCANNER_LOG_LEVEL` | Log level | `info` |
| `SCANNER_SCAN_TIMEOUT` | Scan timeout (seconds) | `600` |
| `SCANNER_CONFIG_PATH` | Path to YAML config file | `config.yml` |

### Secrets Management / Управление секретами

**Never store secrets in config.yml or commit them to git!**

**Никогда не храните секреты в config.yml и не коммитьте их в git!**

```bash
# Set secrets via environment / Установите секреты через окружение:
export SCANNER_API_KEY="your-secure-key"
export SCANNER_CLAUDE_API_KEY="sk-ant-..."

# Or in docker-compose via .env file / Или в docker-compose через .env файл:
echo "SCANNER_API_KEY=your-secure-key" >> .env
echo "SCANNER_CLAUDE_API_KEY=sk-ant-..." >> .env
```

## Database Management / Управление базой данных

### Location / Расположение

- Docker: `/data/scanner.db` (persistent volume `scanner_data`)
- Local: configurable via `SCANNER_DB_PATH`

### WAL Mode

SQLite runs in WAL (Write-Ahead Logging) mode for concurrent read performance. This is set automatically on every connection.

SQLite работает в режиме WAL для параллельного чтения. Устанавливается автоматически при каждом соединении.

### Backup / Резервное копирование

```bash
# Stop scanner (optional, WAL mode allows hot backup)
# Остановите сканер (необязательно, WAL позволяет горячий бэкап)

# Docker
docker compose exec scanner cp /data/scanner.db /data/scanner.db.backup

# Or from host / Или с хоста
docker cp naveksoft-security-scanner-1:/data/scanner.db ./backup/
```

## Monitoring / Мониторинг

### Health Check

```bash
curl http://localhost:8000/api/health
```

Docker Compose performs automatic health checks every 30 seconds.
Docker Compose выполняет автоматические проверки каждые 30 секунд.

### Container Status

```bash
docker compose ps    # Should show "(healthy)"
docker compose logs scanner --tail 50
```

## Tuning / Настройка производительности

*(Phase 2+ — scanners not yet implemented / сканеры ещё не реализованы)*

Future tuning parameters will include:
- Scan timeout thresholds
- Severity thresholds for quality gate
- Tool-specific configurations
- Notification filters
