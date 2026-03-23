# Справочник API

## Базовый URL

```
http://localhost:8000
```

## Аутентификация

Все эндпоинты API, кроме `/api/health`, требуют Bearer-токен в заголовке Authorization. Сгенерируйте токены в панели управления (`/dashboard/tokens`) или через API управления токенами.

```bash
curl -H "Authorization: Bearer nvsec_your_token_here" http://localhost:8000/api/scans
```

Запросы без валидного токена получают ответ `401 Unauthorized`.

## Эндпоинты

### GET /api/health

Эндпоинт проверки состояния. Аутентификация не требуется.

**Ответ 200:**

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime_seconds": 3600.5,
  "database": "ok"
}
```

| Поле | Тип | Описание |
|------|-----|----------|
| `status` | string | `"healthy"` или `"degraded"` |
| `version` | string | Версия сканера из pyproject.toml |
| `uptime_seconds` | float | Секунды с момента запуска приложения |
| `database` | string | `"ok"` или `"error"` |

**Пример:**

```bash
curl http://localhost:8000/api/health
```

---

### POST /api/scans

Запуск нового сканирования безопасности. Сканирование ставится в очередь и выполняется асинхронно.

**Тело запроса:**

```json
{
  "path": "/path/to/local/code",
  "repo_url": "https://github.com/org/repo.git",
  "branch": "main",
  "target_url": "https://example.com",
  "profile": "quick_scan"
}
```

| Поле | Тип | Обязательное | Описание |
|------|-----|-------------|----------|
| `path` | string | Нет | Локальный путь для сканирования |
| `repo_url` | string | Нет | URL Git-репозитория для клонирования и сканирования |
| `branch` | string | Нет | Ветка для checkout (по умолчанию: основная ветка) |
| `target_url` | string | Нет | URL для DAST-сканирования (взаимоисключающий с `path`/`repo_url`) |
| `profile` | string | Нет | Имя профиля сканирования (должен существовать в конфигурации) |
| `skip_ai` | boolean | Нет | Пропустить ИИ-анализ (по умолчанию: false) |

Укажите `path`, `repo_url` или `target_url`. Параметр `target_url` запускает DAST-сканирование и не может комбинироваться с `path` или `repo_url`.

**Ответ 202:**

```json
{
  "id": 1,
  "status": "queued"
}
```

**Коды статуса:** `202` Создано, `400` Невалидный профиль, `401` Не авторизован, `422` Ошибка валидации

**Примеры:**

```bash
# SAST-сканирование
curl -X POST http://localhost:8000/api/scans \
  -H "Authorization: Bearer nvsec_your_token" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/org/repo.git", "branch": "main"}'

# SAST-сканирование с профилем
curl -X POST http://localhost:8000/api/scans \
  -H "Authorization: Bearer nvsec_your_token" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/org/repo.git", "profile": "quick_scan"}'

# DAST-сканирование
curl -X POST http://localhost:8000/api/scans \
  -H "Authorization: Bearer nvsec_your_token" \
  -H "Content-Type: application/json" \
  -d '{"target_url": "https://example.com"}'
```

---

### GET /api/scans

Список сканирований с пагинацией, упорядоченных по дате создания (сначала новые).

**Параметры запроса:**

| Параметр | Тип | По умолчанию | Описание |
|---------|-----|-------------|----------|
| `page` | integer | 1 | Номер страницы |
| `page_size` | integer | 20 | Результатов на страницу |

**Ответ 200:**

```json
{
  "items": [
    {
      "id": 1,
      "status": "completed",
      "repo_url": "https://github.com/org/repo.git",
      "branch": "main",
      "target_url": null,
      "profile_name": "quick_scan",
      "started_at": "2026-03-20T10:00:00Z",
      "completed_at": "2026-03-20T10:05:00Z",
      "total_findings": 15,
      "gate_passed": true
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "pages": 1
}
```

**Пример:**

```bash
curl -H "Authorization: Bearer nvsec_your_token" http://localhost:8000/api/scans
```

---

### GET /api/scans/{id}

Получение детальной информации о сканировании.

**Ответ 200:**

```json
{
  "id": 1,
  "status": "completed",
  "target_path": null,
  "repo_url": "https://github.com/org/repo.git",
  "branch": "main",
  "target_url": null,
  "profile_name": "quick_scan",
  "commit_hash": "abc123",
  "started_at": "2026-03-20T10:00:00Z",
  "completed_at": "2026-03-20T10:05:00Z",
  "duration_seconds": 300.5,
  "total_findings": 15,
  "critical_count": 1,
  "high_count": 3,
  "medium_count": 7,
  "low_count": 4,
  "info_count": 0,
  "gate_passed": true,
  "error_message": null,
  "ai_cost_usd": 0.12
}
```

**Коды статуса:** `200` OK, `401` Не авторизован, `404` Сканирование не найдено

---

### GET /api/scans/{scan_id}/findings

Постраничные находки для конкретного сканирования.

**Ответ 200:**

```json
{
  "items": [
    {
      "fingerprint": "abc123...",
      "tool": "semgrep",
      "rule_id": "python.lang.security.audit.exec-detected",
      "file_path": "src/app.py",
      "line_start": 42,
      "severity": "HIGH",
      "title": "Use of exec() detected",
      "suppressed": false
    }
  ],
  "total": 15,
  "page": 1,
  "page_size": 50,
  "pages": 1
}
```

---

### POST /api/scans/{scan_id}/findings/{finding_id}/suppress

Подавление находки (пометка как ложное срабатывание).

**Тело запроса:**

```json
{
  "reason": "False positive: test fixture data"
}
```

**Ответ 200:**

```json
{
  "status": "suppressed",
  "finding_id": 1,
  "reason": "False positive: test fixture data"
}
```

---

### DELETE /api/scans/{scan_id}/findings/{finding_id}/suppress

Снятие подавления с находки.

**Ответ 200:**

```json
{
  "status": "unsuppressed",
  "finding_id": 1
}
```

---

### GET /api/scanners

Список всех зарегистрированных сканеров с конфигурацией. Требуется аутентификация.

**Ответ 200:**

```json
[
  {
    "name": "semgrep",
    "enabled": true,
    "languages": ["python", "php", "javascript", "typescript", "go", "java", "kotlin", "ruby", "csharp", "rust"],
    "adapter_class": "scanner.adapters.semgrep.SemgrepAdapter"
  }
]
```

Ответ включает все 13 зарегистрированных сканеров.

---

### GET /api/trends

Тренды находок во времени для диаграмм.

**Ответ 200:**

```json
{
  "scans": [
    {
      "id": 1,
      "completed_at": "2026-03-20T10:05:00Z",
      "total_findings": 15,
      "critical": 1,
      "high": 3,
      "medium": 7,
      "low": 4
    }
  ]
}
```

---

## Эндпоинты конфигурации

### GET /api/config

Получение полной конфигурации сканера в формате JSON. Только для админов.

**Пример:**

```bash
curl -H "Authorization: Bearer nvsec_your_token" http://localhost:8000/api/config
```

---

### GET /api/config/yaml

Получение содержимого `config.yml` как текст. Только для админов.

**Пример:**

```bash
curl -H "Authorization: Bearer nvsec_your_token" http://localhost:8000/api/config/yaml
```

---

### PATCH /api/config/scanners/{scanner_name}

Обновление настроек одного сканера. Только для админов.

**Тело запроса:**

```json
{
  "enabled": true,
  "timeout": 300,
  "extra_args": ["--exclude", ".venv"]
}
```

Все поля опциональны. Обновляются только указанные поля.

| Поле | Тип | Описание |
|------|-----|----------|
| `enabled` | bool/string | `true`, `false` или `"auto"` |
| `timeout` | integer | 30-900 секунд |
| `extra_args` | string[] | Дополнительные аргументы CLI |

---

### PUT /api/config/yaml

Замена `config.yml` новым YAML-содержимым. Только для админов. YAML валидируется перед записью.

**Тело запроса:** Текст в формате YAML.

---

## Эндпоинты управления профилями

### GET /api/config/profiles

Список всех профилей сканирования. Только для админов.

**Ответ 200:**

```json
{
  "profiles": {
    "quick_scan": {
      "description": "Fast scan with essential tools only",
      "scanners": {
        "semgrep": {},
        "gitleaks": {}
      }
    }
  }
}
```

---

### POST /api/config/profiles

Создание нового профиля сканирования. Только для админов.

**Тело запроса:**

```json
{
  "name": "quick_scan",
  "description": "Fast scan with essential tools only",
  "scanners": {
    "semgrep": {},
    "gitleaks": {}
  }
}
```

| Поле | Тип | Обязательное | Описание |
|------|-----|-------------|----------|
| `name` | string | Да | Имя профиля (буквы, цифры, дефисы, подчёркивания) |
| `description` | string | Нет | Описание |
| `scanners` | object | Да | Словарь сканеров с параметрами |

**Коды статуса:** `201` Создано, `400` Достигнут лимит, `409` Профиль уже существует, `422` Ошибка валидации

---

### GET /api/config/profiles/{name}

Получение профиля по имени. Только для админов.

---

### PUT /api/config/profiles/{name}

Обновление существующего профиля. Только для админов.

**Тело запроса:**

```json
{
  "description": "Updated description",
  "scanners": {
    "semgrep": {},
    "gitleaks": {},
    "trivy": {}
  }
}
```

---

### DELETE /api/config/profiles/{name}

Удаление профиля сканирования. Только для админов.

---

## Эндпоинты управления пользователями

### GET /api/users

Список всех пользователей. Только для админов.

### POST /api/users

Создание нового пользователя. Только для админов.

**Тело запроса:**

```json
{
  "username": "newuser",
  "password": "securepassword",
  "role": "viewer"
}
```

### GET /api/users/{id}

Получение информации о пользователе. Только для админов.

### PUT /api/users/{id}

Обновление пользователя. Только для админов.

### DELETE /api/users/{id}

Деактивация пользователя. Только для админов.

---

## Эндпоинты управления токенами

### GET /api/tokens

Список ваших API-токенов. Возвращает метаданные токенов (не значение токена).

### POST /api/tokens

Создание нового API-токена. Значение токена возвращается только один раз.

**Тело запроса:**

```json
{
  "name": "CI Pipeline",
  "expires_days": 90
}
```

### DELETE /api/tokens/{id}

Отзыв API-токена. Токен немедленно аннулируется.

---

## Панель управления

Веб-панель управления доступна по адресу `/dashboard`:

| Маршрут | Описание |
|---------|----------|
| `GET /dashboard/login` | Страница входа |
| `POST /dashboard/login` | Аутентификация по имени пользователя и паролю |
| `GET /dashboard/` | Обзор истории сканирований |
| `GET /dashboard/scans/{id}` | Детали сканирования с находками |
| `GET /dashboard/trends` | Диаграммы трендов |
| `GET /dashboard/users` | Управление пользователями (только для админов) |
| `GET /dashboard/tokens` | Управление токенами |
| `GET /dashboard/scanners` | Настройка сканеров (только для админов) |

Панель управления использует сессионные cookie для аутентификации (срок действия 7 дней).

## Ответы об ошибках

Все ответы об ошибках следуют стандартному формату:

```json
{
  "detail": "Description of the error"
}
```

**Общие коды статуса:**

| Код | Значение |
|-----|----------|
| `401` | Отсутствует или недействительный Bearer-токен |
| `403` | Недостаточно прав (проверка роли не пройдена) |
| `404` | Ресурс не найден (ID сканирования, ID находки, имя профиля) |
| `422` | Ошибка валидации (невалидное тело запроса) |

## Документация OpenAPI

FastAPI автоматически генерирует интерактивную документацию API:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json
