# Руководство по переносу

## Обзор

Данное руководство охватывает миграцию Security AI Scanner на новый сервер, передачу проекта новой команде или настройку свежей установки.

**Что переносится:**
- База данных SQLite (история сканирований, находки, подавления)
- Файлы конфигурации (`config.yml`, `.env`)
- Сгенерированные отчёты (HTML/PDF)

**Что НЕ переносится:**
- Docker-образы -- пересобираются на целевом хосте из исходного кода
- Виртуальные окружения Python -- пересоздаются при `make install`

## Предварительные требования

На целевом хосте необходимы:

- Docker Engine 20.10+
- Docker Compose v2+
- GNU Make
- Git (для клонирования репозитория)
- Минимум 2 ГБ оперативной памяти
- 10 ГБ дискового пространства

## Экспорт с исходного сервера

Создайте архив резервной копии на исходном сервере:

```bash
cd /path/to/naveksoft-security

# Создание резервной копии с меткой времени (БД + отчёты + конфигурация)
make backup
# Результат: backups/backup-YYYYMMDD_HHMMSS.tar.gz
```

Скопируйте архив на целевой хост:

```bash
scp backups/backup-*.tar.gz user@target-server:/tmp/
```

## Импорт на целевой сервер

### Свежая установка (клонирование Git)

```bash
# На целевом сервере
git clone https://github.com/AlexTalorJr/naveksoft-security.git
cd naveksoft-security

# Настройка
cp .env.example .env
# Отредактируйте .env, указав реальные значения (см. Справочник переменных окружения ниже)

cp config.yml.example config.yml
# Отредактируйте config.yml при необходимости

# Сборка и запуск
make install
make run

# Выполнение миграций
make migrate

# Проверка
curl http://localhost:8000/api/health
```

### Восстановление данных из резервной копии

Если у вас есть архив резервной копии с исходного сервера:

```bash
# После make install и make run:
make restore BACKUP=/tmp/backup-20260320_143000.tar.gz

# Перезапуск для применения восстановленных данных
docker compose restart

# Проверка
curl http://localhost:8000/api/health
```

## Контрольный список для новых пользователей

Выполните эти шаги для запуска новой установки:

1. Установите Docker и Docker Compose на целевом хосте
2. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/AlexTalorJr/naveksoft-security.git
   cd naveksoft-security
   ```
3. Скопируйте шаблоны конфигурации:
   ```bash
   cp config.yml.example config.yml
   cp .env.example .env
   ```
4. Задайте `SCANNER_API_KEY` -- сгенерируйте безопасный ключ:
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
5. Задайте `SCANNER_CLAUDE_API_KEY` -- получите в [Anthropic Console](https://console.anthropic.com/)
6. Настройте уведомления при необходимости:
   - Slack: укажите `SCANNER_SLACK_WEBHOOK_URL` в `.env`
   - Email: укажите `SCANNER_EMAIL_SMTP_HOST`, `SCANNER_NOTIFICATIONS__EMAIL__SMTP_USER`, `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PASSWORD` и `SCANNER_NOTIFICATIONS__EMAIL__RECIPIENTS` в `.env`
7. Соберите Docker-образы:
   ```bash
   make install
   ```
8. Запустите сканер:
   ```bash
   make run
   ```
9. Выполните миграции базы данных:
   ```bash
   make migrate
   ```
10. Проверьте эндпоинт состояния:
    ```bash
    curl http://localhost:8000/api/health
    # Ожидаемый ответ: {"status": "healthy", ...}
    ```
11. Запустите первое сканирование:
    ```bash
    curl -X POST http://localhost:8000/api/scans \
      -H "Authorization: Bearer nvsec_your_token" \
      -H "Content-Type: application/json" \
      -d '{"path": "/path/to/code"}'
    ```

## Справочник переменных окружения

Все переменные используют префикс `SCANNER_`. Задайте их в файле `.env`.

| Переменная | Обязательная | По умолчанию | Описание | Пример |
|-----------|-------------|-------------|----------|--------|
| `SCANNER_API_KEY` | Да | -- | API-ключ для аутентификации REST API | `dGhpcyBpcyBhIHRlc3Q` |
| `SCANNER_CLAUDE_API_KEY` | Да | -- | API-ключ Anthropic для ИИ-анализа | `sk-ant-api03-...` |
| `SCANNER_PORT` | Нет | `8000` | Внешний порт сканера | `9000` |
| `SCANNER_DB_PATH` | Нет | `/data/scanner.db` | Путь к файлу базы данных SQLite | `/data/scanner.db` |
| `SCANNER_CONFIG_PATH` | Нет | `config.yml` | Путь к YAML-файлу конфигурации | `config.yml` |
| `SCANNER_GIT_TOKEN` | Нет | -- | Токен для клонирования приватных репозиториев | `ghp_xxxxxxxxxxxx` |
| `SCANNER_SLACK_WEBHOOK_URL` | Нет | -- | Вебхук Slack для уведомлений | `https://hooks.slack.com/...` |
| `SCANNER_EMAIL_SMTP_HOST` | Нет | -- | SMTP-сервер для email-уведомлений | `smtp.gmail.com` |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PORT` | Нет | `587` | Порт SMTP | `587` |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_USER` | Нет | -- | Имя пользователя SMTP | `alerts@example.com` |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PASSWORD` | Нет | -- | Пароль SMTP | -- |
| `SCANNER_NOTIFICATIONS__EMAIL__RECIPIENTS` | Нет | `[]` | JSON-массив получателей email | `["dev@example.com"]` |

## Устранение неполадок

### Контейнер не запускается

```bash
docker compose logs scanner
```

Распространённые причины:
- Порт уже занят -- измените `SCANNER_PORT` в `.env`
- Отсутствует файл `.env` -- скопируйте из `.env.example`
- Docker не запущен -- запустите демон Docker

### Эндпоинт состояния возвращает ошибку

```bash
curl http://localhost:8000/api/health
# {"status": "degraded", "database": "error"}
```

Убедитесь, что `SCANNER_DB_PATH` указывает на доступную для записи директорию внутри контейнера. По умолчанию `/data/scanner.db` требует монтирования тома `scanner_data`.

### Сканирования завершаются с ошибкой или по таймауту

- Убедитесь, что все 12 инструментов сканирования (semgrep, cppcheck, gitleaks, trivy, checkov, psalm, enlightn, php-security-checker, gosec, bandit, brakeman, cargo-audit) доступны внутри Docker-образа. Запустите `make verify-scanners` для подтверждения
- Увеличьте `scan_timeout` в `config.yml` для больших репозиториев
- Для приватных репозиториев убедитесь, что задан `SCANNER_GIT_TOKEN`

### Ошибки блокировки базы данных

База данных использует режим WAL для параллельного чтения. Если вы видите ошибки "database is locked":
- Убедитесь, что запущен только один контейнер сканера
- Не обращайтесь к файлу SQLite напрямую, пока контейнер запущен
- Используйте `make backup` для безопасного копирования базы данных

### Ошибка доступа к /data

Контейнер работает от непривилегированного пользователя `scanner`. Убедитесь, что Docker-том имеет правильные права:

```bash
docker compose down
docker volume rm naveksoft-security_scanner_data
docker compose up -d  # Пересоздаёт том с правильными правами
```

Внимание: это удалит существующие данные сканирований. Сначала создайте резервную копию с помощью `make backup`.
