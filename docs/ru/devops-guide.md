# Руководство по DevOps

## Развёртывание Docker

### Быстрый старт

```bash
cp config.yml.example config.yml
cp .env.example .env
# Отредактируйте .env, указав реальные секреты
make install   # сборка Docker-образов
make run       # запуск сканера в фоновом режиме
```

Или напрямую через Docker Compose:

```bash
docker compose up -d --build
```

### Конфигурация контейнера

Файл `docker-compose.yml` определяет один сервис `scanner`:

```yaml
services:
  scanner:
    build: .
    ports:
      - "${SCANNER_PORT:-8000}:8000"
    volumes:
      - scanner_data:/data           # Постоянное хранилище БД и отчётов
      - ./config.yml:/app/config.yml:ro  # Монтирование конфигурации только для чтения
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    restart: unless-stopped

volumes:
  scanner_data:  # Именованный том для хранения SQLite
```

- **Том `scanner_data`** монтируется в `/data` внутри контейнера -- хранит базу данных SQLite и сгенерированные отчёты. Данные сохраняются при перезапуске и пересборке контейнера.
- **Монтирование конфигурации** привязывает `config.yml` в режиме только для чтения в контейнер по пути `/app/config.yml`.
- **Проброс порта** по умолчанию `8000`, но может быть изменён через переменную окружения `SCANNER_PORT`.
- **Политика перезапуска** `unless-stopped` обеспечивает перезапуск сканера после перезагрузки хоста.

## Dockerfile

Образ основан на `python:3.12-slim`:

1. **Системные зависимости** -- `curl` (healthcheck), `libpango` и `libharfbuzz` (генерация PDF через WeasyPrint)
2. **Непривилегированный пользователь** -- пользователь и группа `scanner` созданы для безопасности; директория `/data` принадлежит этому пользователю
3. **Процесс установки** -- `pyproject.toml` и `src/` копируются, затем `pip install --no-cache-dir .` с использованием бэкенда сборки hatchling
4. **Файлы приложения** -- `alembic.ini`, директория `alembic/` с миграциями и `config.yml.example` (как `config.yml` по умолчанию) копируются
5. **Точка входа** -- `uvicorn scanner.main:app --host 0.0.0.0 --port 8000`

## Переменные окружения

Вся конфигурация может быть задана через переменные окружения с префиксом `SCANNER_`. Секреты передаются через файл `.env` (не коммитится в git).

| Переменная | Обязательная | По умолчанию | Описание |
|-----------|-------------|-------------|----------|
| `SCANNER_API_KEY` | Да | -- | API-ключ для аутентификации REST API запросов |
| `SCANNER_CLAUDE_API_KEY` | Да | -- | API-ключ Anthropic для ИИ-анализа |
| `SCANNER_PORT` | Нет | `8000` | Внешний порт сервиса сканера |
| `SCANNER_DB_PATH` | Нет | `/data/scanner.db` | Путь к файлу базы данных SQLite |
| `SCANNER_CONFIG_PATH` | Нет | `config.yml` | Путь к YAML-файлу конфигурации |
| `SCANNER_GIT_TOKEN` | Нет | -- | Токен для клонирования приватных Git-репозиториев |
| `SCANNER_SLACK_WEBHOOK_URL` | Нет | -- | URL входящего вебхука Slack для уведомлений |
| `SCANNER_EMAIL_SMTP_HOST` | Нет | -- | Имя хоста SMTP-сервера для email-уведомлений |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PORT` | Нет | `587` | Порт SMTP-сервера |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_USER` | Нет | -- | Имя пользователя для аутентификации SMTP |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PASSWORD` | Нет | -- | Пароль для аутентификации SMTP |
| `SCANNER_NOTIFICATIONS__EMAIL__RECIPIENTS` | Нет | `[]` | JSON-массив получателей email |

## Интеграция с Jenkins

Проект включает `Jenkinsfile.security` для интеграции сканирования безопасности в пайплайн Jenkins. Используется плагин Jenkins `httpRequest` для API-вызовов.

### Настройка

1. Установите плагин **HTTP Request** в Jenkins
2. Добавьте `SCANNER_URL` (например, `http://scanner:8000`) как учётные данные Jenkins или переменную окружения
3. Добавьте `SCANNER_API_KEY` как секретное текстовое учётное данное Jenkins

### Использование

Добавьте этап сканирования безопасности в ваш `Jenkinsfile`:

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

### Шлюз качества

Сканер оценивает шлюз качества после каждого сканирования. Настройте критерии прохождения/непрохождения в `config.yml`:

```yaml
gate:
  fail_on:
    - critical
    - high
  include_compound_risks: true
```

Если шлюз не пройден, этап Jenkins должен завершить сборку с ошибкой. Запросите результат сканирования для проверки `gate_passed`.

## Резервное копирование

### Использование Make-целей

```bash
# Создание резервной копии с меткой времени (БД + отчёты + конфигурация)
make backup
# Результат: backups/backup-20260320_143000.tar.gz

# Восстановление из файла резервной копии
make restore BACKUP=backups/backup-20260320_143000.tar.gz
```

### Что сохраняется

- **База данных SQLite** -- резервная копия создаётся командой `sqlite3 .backup` (безопасно для WAL, без простоя)
- **Отчёты** -- сгенерированные HTML/PDF-отчёты из `/data/reports`
- **Конфигурация** -- `config.yml`

### Безопасность режима WAL

База данных работает в режиме WAL (Write-Ahead Logging). Цель `make backup` использует команду SQLite `.backup` внутри контейнера, которая безопасно обрабатывает чекпоинтинг WAL. Не копируйте файл `.db` напрямую -- используйте make-цель или команду `sqlite3 .backup`.

### Рекомендуемое расписание

Настройте ежедневное задание cron для автоматического резервного копирования:

```bash
# Ежедневно в 2:00
0 2 * * * cd /path/to/naveksoft-security && make backup
```

## Мультиархитектурные сборки

Сборка Docker-образов для архитектур `amd64` и `arm64` с использованием Docker Buildx.

### Предварительные требования

- Docker Desktop 4.x+ (включает buildx) или вручную установленный плагин `docker-buildx`
- QEMU user-static для кросс-платформенной эмуляции (Docker Desktop обрабатывает это автоматически)

### Сборка мультиархитектурных образов

```bash
# Сборка для amd64 + arm64, сохранение как OCI-архив
make docker-multiarch
# Результат: Security AI Scanner-{version}-multiarch.tar

# Сборка и отправка в реестр контейнеров
make docker-push REGISTRY=your-registry.example.com
```

Цель `docker-multiarch` создаёт сборщик buildx с именем `multiarch`, если он ещё не существует.

## Мониторинг

### Эндпоинт проверки состояния

Опрашивайте эндпоинт проверки состояния для мониторинга сканера:

```bash
curl http://localhost:8000/api/health
# {"status": "healthy", "version": "0.1.0", "uptime_seconds": 3600.5, "database": "ok"}
```

Ответ со статусом `"degraded"` или `"database": "error"` указывает на проблему с подключением к базе данных.

### Healthcheck Docker

Контейнер включает встроенную проверку состояния, выполняемую каждые 30 секунд. Проверка состояния контейнера:

```bash
docker compose ps
# Показывает "healthy" или "unhealthy" в столбце STATUS
```

### Логи

```bash
# Просмотр логов в реальном времени
docker compose logs -f scanner

# Последние 100 строк
docker compose logs scanner --tail 100
```

Уровень логирования настраивается в `config.yml` через поле `log_level` (по умолчанию: `info`).

### Политика перезапуска

Контейнер использует `restart: unless-stopped`, поэтому автоматически перезапускается после сбоев или перезагрузки хоста. Только ручная команда `docker compose stop` или `docker compose down` остановит его.

## Обновление

1. Получите последний код:
   ```bash
   git pull origin main
   ```

2. Пересоберите и перезапустите:
   ```bash
   make install   # пересборка Docker-образа
   make run       # запуск обновлённого контейнера
   ```

3. Выполните миграции базы данных:
   ```bash
   make migrate
   ```

4. Проверьте обновление:
   ```bash
   curl http://localhost:8000/api/health
   ```

Если эндпоинт проверки состояния возвращает новый номер версии и `"status": "healthy"`, обновление завершено.
