# Справочник API

## Базовый URL

```
http://localhost:8000
```

## Аутентификация

Все эндпоинты API, кроме `/api/health`, требуют API-ключ, передаваемый в заголовке `X-API-Key`. Ключ задаётся через переменную окружения `SCANNER_API_KEY` и проверяется с использованием timing-safe сравнения (`secrets.compare_digest`).

```bash
curl -H "X-API-Key: your-key" http://localhost:8000/api/scans
```

Запросы без валидного ключа получают ответ `401 Unauthorized`.

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

Запуск нового сканирования безопасности. Сканирование ставится в очередь и выполняется асинхронно в фоновом режиме.

**Тело запроса:**

```json
{
  "path": "/path/to/local/code",
  "repo_url": "https://github.com/org/repo.git",
  "branch": "main"
}
```

| Поле | Тип | Обязательное | Описание |
|------|-----|-------------|----------|
| `path` | string | Нет | Локальный путь в файловой системе для сканирования |
| `repo_url` | string | Нет | URL Git-репозитория для клонирования и сканирования |
| `branch` | string | Нет | Ветка для checkout (по умолчанию: основная ветка репозитория) |

Укажите `path` или `repo_url`. Если указан `repo_url`, сканер клонирует репозиторий перед сканированием.

**Ответ 202:**

```json
{
  "id": 1,
  "status": "queued"
}
```

**Коды статуса:** `202` Created, `401` Unauthorized, `422` Validation error

**Пример:**

```bash
curl -X POST http://localhost:8000/api/scans \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/org/repo.git", "branch": "main"}'
```

---

### GET /api/scans

Список всех сканирований, упорядоченных по дате создания (сначала новые).

**Ответ 200:**

```json
[
  {
    "id": 1,
    "repo_url": "https://github.com/org/repo.git",
    "branch": "main",
    "status": "completed",
    "started_at": "2026-03-20T10:00:00Z",
    "completed_at": "2026-03-20T10:05:00Z",
    "gate_passed": true
  }
]
```

**Пример:**

```bash
curl -H "X-API-Key: your-key" http://localhost:8000/api/scans
```

---

### GET /api/scans/{id}

Получение детальных результатов сканирования, включая находки.

**Параметры пути:**

| Параметр | Тип | Описание |
|---------|-----|----------|
| `id` | integer | Идентификатор сканирования |

**Ответ 200:**

```json
{
  "id": 1,
  "repo_url": "https://github.com/org/repo.git",
  "branch": "main",
  "status": "completed",
  "started_at": "2026-03-20T10:00:00Z",
  "completed_at": "2026-03-20T10:05:00Z",
  "gate_passed": true,
  "findings": [
    {
      "id": 1,
      "tool": "semgrep",
      "rule_id": "python.lang.security.audit.exec-detected",
      "severity": "high",
      "file_path": "src/app.py",
      "line": 42,
      "message": "Use of exec() detected",
      "fingerprint": "abc123..."
    }
  ]
}
```

**Коды статуса:** `200` OK, `401` Unauthorized, `404` Scan not found

**Пример:**

```bash
curl -H "X-API-Key: your-key" http://localhost:8000/api/scans/1
```

---

### POST /api/scans/{scan_id}/findings/{finding_id}/suppress

Подавление находки (пометка как ложное срабатывание).

**Параметры пути:**

| Параметр | Тип | Описание |
|---------|-----|----------|
| `scan_id` | integer | Идентификатор сканирования |
| `finding_id` | integer | Идентификатор находки |

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

**Пример:**

```bash
curl -X POST http://localhost:8000/api/scans/1/findings/5/suppress \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"reason": "False positive: test fixture"}'
```

---

### DELETE /api/scans/{scan_id}/findings/{finding_id}/suppress

Снятие подавления с находки.

**Параметры пути:**

| Параметр | Тип | Описание |
|---------|-----|----------|
| `scan_id` | integer | Идентификатор сканирования |
| `finding_id` | integer | Идентификатор находки |

**Ответ 200:**

```json
{
  "status": "unsuppressed",
  "finding_id": 1
}
```

**Пример:**

```bash
curl -X DELETE http://localhost:8000/api/scans/1/findings/5/suppress \
  -H "X-API-Key: your-key"
```

---

### GET /api/trends

Получение трендов находок во времени для диаграмм трендов.

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

**Пример:**

```bash
curl -H "X-API-Key: your-key" http://localhost:8000/api/trends
```

## Панель управления

Веб-панель управления доступна по адресу `/dashboard` и предоставляет графический интерфейс для сканера:

| Маршрут | Описание |
|---------|----------|
| `GET /dashboard/login` | Страница входа |
| `POST /dashboard/login` | Аутентификация по API-ключу |
| `GET /dashboard/` | Обзор истории сканирований |
| `GET /dashboard/scans/{id}` | Детали сканирования с находками |
| `GET /dashboard/trends` | Диаграммы трендов во времени |

Панель управления использует тот же API-ключ для аутентификации, хранящийся в сессионном cookie после входа. Подавление и снятие подавления находок доступны непосредственно на странице деталей сканирования.

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
| `401` | Отсутствует или недействительный API-ключ |
| `404` | Ресурс не найден (идентификатор сканирования, идентификатор находки) |
| `422` | Ошибка валидации (невалидное тело запроса) |

## Документация OpenAPI

FastAPI автоматически генерирует интерактивную документацию API:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json
