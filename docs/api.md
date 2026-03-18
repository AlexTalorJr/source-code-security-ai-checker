# API Reference / Справочник API

## Base URL

```
http://localhost:8000/api
```

## Endpoints / Эндпоинты

### Health Check / Проверка состояния

```
GET /api/health
```

Checks application and database health.
Проверяет состояние приложения и базы данных.

**Authentication:** None required / Аутентификация не требуется

**Response 200:**

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime_seconds": 123.45,
  "database": "ok"
}
```

**Response fields / Поля ответа:**

| Field | Type | Description (EN) | Описание (RU) |
|-------|------|-------------------|---------------|
| status | string | `"healthy"` or `"degraded"` | `"healthy"` или `"degraded"` |
| version | string | Scanner version | Версия сканера |
| uptime_seconds | float | Seconds since startup | Секунды с момента запуска |
| database | string | `"ok"` or `"error"` | `"ok"` или `"error"` |

**Status logic / Логика статуса:**
- `healthy` — application running, database accessible / приложение работает, БД доступна
- `degraded` — application running, database unreachable / приложение работает, БД недоступна

**Example / Пример:**

```bash
curl -s http://localhost:8000/api/health | python3 -m json.tool
```

---

## Planned Endpoints (Phase 2+) / Планируемые эндпоинты (Фаза 2+)

These endpoints will be implemented in future phases.
Эти эндпоинты будут реализованы в следующих фазах.

### Scans / Сканирования

| Method | Endpoint | Description | Phase |
|--------|----------|-------------|-------|
| POST | `/api/scans` | Trigger a new scan | 2 |
| GET | `/api/scans` | List all scans | 2 |
| GET | `/api/scans/{id}` | Get scan details | 2 |
| GET | `/api/scans/{id}/findings` | Get findings for a scan | 2 |

### Reports / Отчёты

| Method | Endpoint | Description | Phase |
|--------|----------|-------------|-------|
| GET | `/api/scans/{id}/report/html` | Download HTML report | 4 |
| GET | `/api/scans/{id}/report/pdf` | Download PDF report | 4 |

### Quality Gate / Контроль качества

| Method | Endpoint | Description | Phase |
|--------|----------|-------------|-------|
| GET | `/api/scans/{id}/gate` | Get quality gate result | 5 |

## Authentication / Аутентификация

API key authentication will be added in Phase 5.
Аутентификация по API-ключу будет добавлена в Фазе 5.

```bash
# Future usage / Будущее использование:
curl -H "X-API-Key: your-key" http://localhost:8000/api/scans
```

## OpenAPI / Swagger

FastAPI auto-generates OpenAPI documentation:
FastAPI автоматически генерирует документацию OpenAPI:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json
