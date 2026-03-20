# Руководство администратора

## Конфигурация

### Источники конфигурации (в порядке приоритета)

1. **Аргументы конструктора** -- программные переопределения
2. **Переменные окружения** -- префикс `SCANNER_*`
3. **Файл dotenv** -- файл `.env`
4. **Файловые секреты** -- секреты Docker/K8s
5. **YAML-файл конфигурации** -- `config.yml` (наименьший приоритет)

### Файл конфигурации

Скопируйте пример и настройте:

```bash
cp config.yml.example config.yml
```

## Настройка сканеров

Каждый из пяти инструментов сканирования может быть независимо включён/выключен, ему может быть задан таймаут и дополнительные аргументы:

```yaml
scanners:
  semgrep:
    enabled: true
    timeout: 180
    extra_args: []
  cppcheck:
    enabled: true
    timeout: 120
    extra_args: []
  gitleaks:
    enabled: true
    timeout: 120
    extra_args: []
  trivy:
    enabled: true
    timeout: 120
    extra_args: []
  checkov:
    enabled: true
    timeout: 120
    extra_args: []
```

- **enabled** -- установите `false` для полного пропуска инструмента
- **timeout** -- максимальное время выполнения в секундах до принудительной остановки
- **extra_args** -- дополнительные аргументы командной строки, передаваемые инструменту

## Настройка ИИ

```yaml
ai:
  max_cost_per_scan: 5.0
  model: "claude-sonnet-4-6"
  max_findings_per_batch: 50
  max_tokens_per_response: 4096
```

| Параметр | Описание | По умолчанию |
|---------|----------|-------------|
| `max_cost_per_scan` | Максимальные затраты в USD на ИИ-анализ за сканирование | `5.0` |
| `model` | Идентификатор модели Claude | `claude-sonnet-4-6` |
| `max_findings_per_batch` | Максимум находок, отправляемых Claude за один запрос | `50` |
| `max_tokens_per_response` | Максимум токенов ответа от Claude | `4096` |

## Настройка шлюза качества

```yaml
gate:
  fail_on:
    - critical
    - high
  include_compound_risks: true
```

- **fail_on** -- список уровней серьёзности, при которых шлюз не проходит
- **include_compound_risks** -- при значении `true` составные риски с соответствующей серьёзностью также приводят к непрохождению шлюза

## Настройка уведомлений

### Slack

```yaml
notifications:
  slack:
    enabled: false
```

Укажите URL вебхука на верхнем уровне:

```yaml
slack_webhook_url: "https://hooks.slack.com/services/T.../B.../xxx"
```

Или через переменную окружения: `SCANNER_SLACK_WEBHOOK_URL`

### Электронная почта

```yaml
notifications:
  email:
    enabled: false
    recipients: ["security@example.com"]
    smtp_port: 587
    smtp_user: ""
    smtp_password: ""  # Используйте переменную окружения
    use_tls: true
```

Укажите хост SMTP на верхнем уровне:

```yaml
email_smtp_host: "smtp.example.com"
```

Или через переменную окружения: `SCANNER_EMAIL_SMTP_HOST`

Пароль SMTP следует задавать через вложенную переменную окружения: `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PASSWORD`

### URL панели управления

```yaml
dashboard_url: ""  # Например, http://scanner:8000/dashboard
```

Используется в сообщениях уведомлений для ссылки на результаты сканирования. Если пусто, определяется автоматически из хоста и порта.

## Переменные окружения

Все настройки могут быть переопределены с помощью префикса `SCANNER_`:

| Переменная | Описание | По умолчанию |
|-----------|----------|-------------|
| `SCANNER_HOST` | Адрес прослушивания | `0.0.0.0` |
| `SCANNER_PORT` | Порт прослушивания | `8000` |
| `SCANNER_DB_PATH` | Путь к файлу базы данных SQLite | `/data/scanner.db` |
| `SCANNER_API_KEY` | Ключ аутентификации API | `""` (пусто) |
| `SCANNER_CLAUDE_API_KEY` | API-ключ Anthropic для ИИ-анализа | `""` (пусто) |
| `SCANNER_SLACK_WEBHOOK_URL` | URL вебхука Slack | `""` |
| `SCANNER_EMAIL_SMTP_HOST` | Имя хоста SMTP-сервера | `""` |
| `SCANNER_LOG_LEVEL` | Уровень логирования (debug/info/warning/error) | `info` |
| `SCANNER_SCAN_TIMEOUT` | Глобальный таймаут сканирования в секундах | `600` |
| `SCANNER_CONFIG_PATH` | Путь к YAML-файлу конфигурации | `config.yml` |

### Вложенные переменные окружения

Для вложенных разделов конфигурации используйте двойное подчёркивание:

| Переменная | Соответствует |
|-----------|-------------|
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PASSWORD` | `notifications.email.smtp_password` |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PORT` | `notifications.email.smtp_port` |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_USER` | `notifications.email.smtp_user` |
| `SCANNER_NOTIFICATIONS__SLACK__ENABLED` | `notifications.slack.enabled` |

## Управление секретами

Никогда не храните секреты в `config.yml` и не коммитьте их в git.

```bash
# Установка секретов через переменные окружения:
export SCANNER_API_KEY="your-secure-key"
export SCANNER_CLAUDE_API_KEY="sk-ant-..."

# Или в docker-compose через файл .env:
echo "SCANNER_API_KEY=your-secure-key" >> .env
echo "SCANNER_CLAUDE_API_KEY=sk-ant-..." >> .env
```

## Управление базой данных

### Расположение

- Docker: `/data/scanner.db` (постоянный том `scanner_data`)
- Локально: настраивается через `SCANNER_DB_PATH`

### Режим WAL

SQLite работает в режиме WAL (Write-Ahead Logging) для повышения производительности параллельного чтения. Режим устанавливается автоматически при каждом соединении через обработчики событий SQLAlchemy.

### Резервное копирование

```bash
# Режим WAL позволяет горячее копирование (без остановки сканера)
docker cp naveksoft-security-scanner-1:/data/scanner.db ./backup/
```

## Настройка порогов

### Шлюз качества

Настройте уровни серьёзности, при которых шлюз не проходит:

```yaml
gate:
  fail_on:
    - critical        # Блокировать только при критических (мягкая политика)
```

Или включите medium:

```yaml
gate:
  fail_on:
    - critical
    - high
    - medium           # Более строгая политика
```

### Управление инструментами сканирования

Отключите инструменты, не относящиеся к вашей кодовой базе:

```yaml
scanners:
  cppcheck:
    enabled: false     # Нет кода на C/C++
  checkov:
    enabled: false     # Нет файлов IaC
```

## Настройка производительности

### Таймауты

- `scan_timeout` (глобальный): максимальная общая продолжительность сканирования (по умолчанию: 600 с)
- `timeout` для каждого сканера: максимальное время выполнения инструмента (по умолчанию: 120-180 с)

Если сканирования завершаются по таймауту, увеличьте таймаут для медленного сканера, а не глобальный таймаут.

### Размер пакета ИИ

Для больших сканирований с множеством находок настройте:

```yaml
ai:
  max_findings_per_batch: 25   # Меньшие пакеты для более быстрых ответов
  max_tokens_per_response: 8192  # Больше места для детального анализа
```

### Мониторинг

```bash
# Проверка состояния
curl http://localhost:8000/api/health

# Статус контейнера
docker compose ps

# Логи
docker compose logs scanner --tail 50
```

Docker Compose выполняет автоматические проверки состояния каждые 30 секунд.
