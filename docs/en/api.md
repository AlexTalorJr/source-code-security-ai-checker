# API Reference

## Base URL

```
http://localhost:8000
```

## Authentication

All API endpoints except `/api/health` require an API key passed in the `X-API-Key` header. The key is set via the `SCANNER_API_KEY` environment variable and validated using timing-safe comparison (`secrets.compare_digest`).

```bash
curl -H "X-API-Key: your-key" http://localhost:8000/api/scans
```

Requests without a valid key receive a `401 Unauthorized` response.

## Endpoints

### GET /api/health

Health check endpoint. No authentication required.

**Response 200:**

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime_seconds": 3600.5,
  "database": "ok"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `"healthy"` or `"degraded"` |
| `version` | string | Scanner version from pyproject.toml |
| `uptime_seconds` | float | Seconds since application startup |
| `database` | string | `"ok"` or `"error"` |

**Example:**

```bash
curl http://localhost:8000/api/health
```

---

### POST /api/scans

Trigger a new security scan. The scan is queued and runs asynchronously in the background.

**Request body:**

```json
{
  "path": "/path/to/local/code",
  "repo_url": "https://github.com/org/repo.git",
  "branch": "main"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `path` | string | No | Local filesystem path to scan |
| `repo_url` | string | No | Git repository URL to clone and scan |
| `branch` | string | No | Branch to checkout (default: repository default branch) |

Provide either `path` or `repo_url`. If `repo_url` is given, the scanner clones the repository before scanning.

**Response 202:**

```json
{
  "id": 1,
  "status": "queued"
}
```

**Status codes:** `202` Created, `401` Unauthorized, `422` Validation error

**Example:**

```bash
curl -X POST http://localhost:8000/api/scans \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/org/repo.git", "branch": "main"}'
```

---

### GET /api/scans

List all scans, ordered by creation date (newest first).

**Response 200:**

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

**Example:**

```bash
curl -H "X-API-Key: your-key" http://localhost:8000/api/scans
```

---

### GET /api/scans/{id}

Get detailed scan results including findings.

**Path parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | integer | Scan ID |

**Response 200:**

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

**Status codes:** `200` OK, `401` Unauthorized, `404` Scan not found

**Example:**

```bash
curl -H "X-API-Key: your-key" http://localhost:8000/api/scans/1
```

---

### POST /api/scans/{scan_id}/findings/{finding_id}/suppress

Suppress a finding (mark as false positive).

**Path parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `scan_id` | integer | Scan ID |
| `finding_id` | integer | Finding ID |

**Request body:**

```json
{
  "reason": "False positive: test fixture data"
}
```

**Response 200:**

```json
{
  "status": "suppressed",
  "finding_id": 1,
  "reason": "False positive: test fixture data"
}
```

**Example:**

```bash
curl -X POST http://localhost:8000/api/scans/1/findings/5/suppress \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"reason": "False positive: test fixture"}'
```

---

### DELETE /api/scans/{scan_id}/findings/{finding_id}/suppress

Remove suppression from a finding.

**Path parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `scan_id` | integer | Scan ID |
| `finding_id` | integer | Finding ID |

**Response 200:**

```json
{
  "status": "unsuppressed",
  "finding_id": 1
}
```

**Example:**

```bash
curl -X DELETE http://localhost:8000/api/scans/1/findings/5/suppress \
  -H "X-API-Key: your-key"
```

---

### GET /api/scanners

List all registered scanners with their configuration. Requires authentication.

**Response 200:**

```json
[
  {
    "name": "semgrep",
    "enabled": true,
    "languages": ["python", "php", "javascript", "typescript", "go", "java", "kotlin", "ruby", "csharp", "rust"],
    "adapter_class": "scanner.adapters.semgrep.SemgrepAdapter"
  },
  {
    "name": "gosec",
    "enabled": "auto",
    "languages": ["go"],
    "adapter_class": "scanner.adapters.gosec.GosecAdapter"
  },
  {
    "name": "bandit",
    "enabled": "auto",
    "languages": ["python"],
    "adapter_class": "scanner.adapters.bandit.BanditAdapter"
  },
  {
    "name": "brakeman",
    "enabled": "auto",
    "languages": ["ruby"],
    "adapter_class": "scanner.adapters.brakeman.BrakemanAdapter"
  },
  {
    "name": "cargo_audit",
    "enabled": "auto",
    "languages": ["rust"],
    "adapter_class": "scanner.adapters.cargo_audit.CargoAuditAdapter"
  }
]
```

The response includes all 12 registered scanners. The example above shows a subset for brevity.

**Example:**

```bash
curl -H "X-API-Key: your-key" http://localhost:8000/api/scanners
```

---

### GET /api/trends

Get finding trends over time for trend charts.

**Response 200:**

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

**Example:**

```bash
curl -H "X-API-Key: your-key" http://localhost:8000/api/trends
```

## Dashboard

A web dashboard is available at `/dashboard` providing a graphical interface for the scanner:

| Route | Description |
|-------|-------------|
| `GET /dashboard/login` | Login page |
| `POST /dashboard/login` | Authenticate with API key |
| `GET /dashboard/` | Scan history overview |
| `GET /dashboard/scans/{id}` | Scan detail with findings |
| `GET /dashboard/trends` | Trend charts over time |

The dashboard uses the same API key for authentication, stored in a session cookie after login. Finding suppression and unsuppression are available directly from the scan detail page.

## Error Responses

All error responses follow a standard format:

```json
{
  "detail": "Description of the error"
}
```

**Common status codes:**

| Code | Meaning |
|------|---------|
| `401` | Missing or invalid API key |
| `404` | Resource not found (scan ID, finding ID) |
| `422` | Validation error (invalid request body) |

## OpenAPI Documentation

FastAPI auto-generates interactive API documentation:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json
