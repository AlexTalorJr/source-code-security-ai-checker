# API Reference

## Base URL

```
http://localhost:8000
```

## Authentication

All API endpoints except `/api/health` require a Bearer token in the Authorization header. Generate tokens from the dashboard (`/dashboard/tokens`) or via the token management API.

```bash
curl -H "Authorization: Bearer nvsec_your_token_here" http://localhost:8000/api/scans
```

Requests without a valid token receive a `401 Unauthorized` response.

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
  "branch": "main",
  "target_url": "https://example.com",
  "profile": "quick_scan"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `path` | string | No | Local filesystem path to scan |
| `repo_url` | string | No | Git repository URL to clone and scan |
| `branch` | string | No | Branch to checkout (default: repository default branch) |
| `target_url` | string | No | URL for DAST scanning (exclusive with `path`/`repo_url`) |
| `profile` | string | No | Name of scan profile to use (must exist in config) |
| `skip_ai` | boolean | No | Skip AI analysis (default: false) |

Provide either `path`, `repo_url`, or `target_url`. The `target_url` field triggers a DAST scan and cannot be combined with `path` or `repo_url`.

**Response 202:**

```json
{
  "id": 1,
  "status": "queued"
}
```

**Status codes:** `202` Created, `400` Invalid profile, `401` Unauthorized, `422` Validation error

**Examples:**

```bash
# SAST scan
curl -X POST http://localhost:8000/api/scans \
  -H "Authorization: Bearer nvsec_your_token" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/org/repo.git", "branch": "main"}'

# SAST scan with profile
curl -X POST http://localhost:8000/api/scans \
  -H "Authorization: Bearer nvsec_your_token" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/org/repo.git", "profile": "quick_scan"}'

# DAST scan
curl -X POST http://localhost:8000/api/scans \
  -H "Authorization: Bearer nvsec_your_token" \
  -H "Content-Type: application/json" \
  -d '{"target_url": "https://example.com"}'
```

---

### GET /api/scans

List all scans with pagination, ordered by creation date (newest first).

**Query parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number |
| `page_size` | integer | 20 | Results per page |

**Response 200:**

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

**Example:**

```bash
curl -H "Authorization: Bearer nvsec_your_token" http://localhost:8000/api/scans
```

---

### GET /api/scans/{id}

Get detailed scan results.

**Path parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | integer | Scan ID |

**Response 200:**

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

**Status codes:** `200` OK, `401` Unauthorized, `404` Scan not found

**Example:**

```bash
curl -H "Authorization: Bearer nvsec_your_token" http://localhost:8000/api/scans/1
```

---

### GET /api/scans/{scan_id}/findings

Get paginated findings for a specific scan.

**Path parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `scan_id` | integer | Scan ID |

**Query parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number |
| `page_size` | integer | 50 | Results per page |

**Response 200:**

```json
{
  "items": [
    {
      "fingerprint": "abc123...",
      "tool": "semgrep",
      "rule_id": "python.lang.security.audit.exec-detected",
      "file_path": "src/app.py",
      "line_start": 42,
      "line_end": 42,
      "snippet": "exec(user_input)",
      "severity": "HIGH",
      "title": "Use of exec() detected",
      "description": "Detected use of exec()...",
      "recommendation": "Avoid using exec()...",
      "ai_analysis": "This is a true positive...",
      "ai_fix_suggestion": "Replace exec() with...",
      "suppressed": false
    }
  ],
  "total": 15,
  "page": 1,
  "page_size": 50,
  "pages": 1
}
```

**Example:**

```bash
curl -H "Authorization: Bearer nvsec_your_token" http://localhost:8000/api/scans/1/findings
```

---

### POST /api/scans/{scan_id}/findings/{finding_id}/suppress

Suppress a finding (mark as false positive).

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
  -H "Authorization: Bearer nvsec_your_token" \
  -H "Content-Type: application/json" \
  -d '{"reason": "False positive: test fixture"}'
```

---

### DELETE /api/scans/{scan_id}/findings/{finding_id}/suppress

Remove suppression from a finding.

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
  -H "Authorization: Bearer nvsec_your_token"
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
  }
]
```

The response includes all 13 registered scanners. The example above shows one for brevity.

**Example:**

```bash
curl -H "Authorization: Bearer nvsec_your_token" http://localhost:8000/api/scanners
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
curl -H "Authorization: Bearer nvsec_your_token" http://localhost:8000/api/trends
```

---

## Configuration Endpoints

### GET /api/config

Get full scanner configuration as JSON. Admin only.

**Response 200:**

```json
{
  "scanners": { "...": "..." },
  "profiles": { "...": "..." },
  "ai": { "...": "..." },
  "gate": { "...": "..." }
}
```

**Example:**

```bash
curl -H "Authorization: Bearer nvsec_your_token" http://localhost:8000/api/config
```

---

### GET /api/config/yaml

Get raw `config.yml` content as plain text. Admin only.

**Response 200:** Raw YAML text (`text/plain`).

**Example:**

```bash
curl -H "Authorization: Bearer nvsec_your_token" http://localhost:8000/api/config/yaml
```

---

### PATCH /api/config/scanners/{scanner_name}

Update settings for a single scanner. Admin only.

**Path parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `scanner_name` | string | Scanner identifier (e.g., `semgrep`, `nuclei`) |

**Request body:**

```json
{
  "enabled": true,
  "timeout": 300,
  "extra_args": ["--exclude", ".venv"]
}
```

All fields are optional. Only provided fields are updated.

| Field | Type | Description |
|-------|------|-------------|
| `enabled` | bool/string | `true`, `false`, or `"auto"` |
| `timeout` | integer | 30-900 seconds |
| `extra_args` | string[] | Additional CLI arguments |

**Response 200:**

```json
{
  "status": "ok",
  "scanner": "semgrep"
}
```

**Example:**

```bash
curl -X PATCH http://localhost:8000/api/config/scanners/semgrep \
  -H "Authorization: Bearer nvsec_your_token" \
  -H "Content-Type: application/json" \
  -d '{"timeout": 300}'
```

---

### PUT /api/config/yaml

Replace the entire `config.yml` with new YAML content. Admin only. The YAML is validated before writing.

**Request body:** Raw YAML text (`text/plain` or `application/octet-stream`).

**Response 200:**

```json
{
  "status": "ok"
}
```

**Example:**

```bash
curl -X PUT http://localhost:8000/api/config/yaml \
  -H "Authorization: Bearer nvsec_your_token" \
  -H "Content-Type: text/plain" \
  --data-binary @config.yml
```

---

## Profile Management Endpoints

### GET /api/config/profiles

List all scan profiles. Admin only.

**Response 200:**

```json
{
  "profiles": {
    "quick_scan": {
      "description": "Fast scan with essential tools only",
      "scanners": {
        "semgrep": {},
        "gitleaks": {}
      }
    },
    "full_audit": {
      "description": "Comprehensive scan with all tools",
      "scanners": {
        "semgrep": {},
        "gitleaks": {},
        "trivy": {},
        "checkov": {}
      }
    }
  }
}
```

**Example:**

```bash
curl -H "Authorization: Bearer nvsec_your_token" http://localhost:8000/api/config/profiles
```

---

### POST /api/config/profiles

Create a new scan profile. Admin only.

**Request body:**

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

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Profile name (letters, numbers, hyphens, underscores) |
| `description` | string | No | Human-readable description |
| `scanners` | object | Yes | Map of scanner names to settings overrides |

The `scanners` field must contain at least one scanner. Each scanner entry can optionally include settings overrides (e.g., `{"timeout": 300}`), or be empty (`{}`) to use default settings.

**Response 201:**

```json
{
  "status": "ok",
  "profile": "quick_scan"
}
```

**Status codes:** `201` Created, `400` Max profiles reached, `409` Profile already exists, `422` Validation error

**Example:**

```bash
curl -X POST http://localhost:8000/api/config/profiles \
  -H "Authorization: Bearer nvsec_your_token" \
  -H "Content-Type: application/json" \
  -d '{"name": "quick_scan", "description": "Fast scan", "scanners": {"semgrep": {}, "gitleaks": {}}}'
```

---

### GET /api/config/profiles/{name}

Get a single scan profile by name. Admin only.

**Response 200:**

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

**Status codes:** `200` OK, `404` Profile not found

**Example:**

```bash
curl -H "Authorization: Bearer nvsec_your_token" http://localhost:8000/api/config/profiles/quick_scan
```

---

### PUT /api/config/profiles/{name}

Update an existing scan profile. Admin only.

**Request body:**

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

All fields are optional. Only provided fields are updated.

**Response 200:**

```json
{
  "status": "ok",
  "profile": "quick_scan"
}
```

**Status codes:** `200` OK, `404` Profile not found, `422` Validation error

**Example:**

```bash
curl -X PUT http://localhost:8000/api/config/profiles/quick_scan \
  -H "Authorization: Bearer nvsec_your_token" \
  -H "Content-Type: application/json" \
  -d '{"scanners": {"semgrep": {}, "gitleaks": {}, "trivy": {}}}'
```

---

### DELETE /api/config/profiles/{name}

Delete a scan profile. Admin only.

**Response 200:**

```json
{
  "status": "ok"
}
```

**Status codes:** `200` OK, `404` Profile not found

**Example:**

```bash
curl -X DELETE http://localhost:8000/api/config/profiles/quick_scan \
  -H "Authorization: Bearer nvsec_your_token"
```

---

## User Management Endpoints

### GET /api/users

List all users. Admin only.

**Response 200:**

```json
[
  {
    "id": 1,
    "username": "admin",
    "role": "admin",
    "is_active": true,
    "created_at": "2026-03-20T10:00:00Z"
  }
]
```

**Example:**

```bash
curl -H "Authorization: Bearer nvsec_your_token" http://localhost:8000/api/users
```

---

### POST /api/users

Create a new user. Admin only.

**Request body:**

```json
{
  "username": "newuser",
  "password": "securepassword",
  "role": "viewer"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | string | Yes | Unique username |
| `password` | string | Yes | Minimum 8 characters |
| `role` | string | Yes | `admin`, `viewer`, or `scanner` |

**Response 201:**

```json
{
  "id": 2,
  "username": "newuser",
  "role": "viewer"
}
```

**Example:**

```bash
curl -X POST http://localhost:8000/api/users \
  -H "Authorization: Bearer nvsec_your_token" \
  -H "Content-Type: application/json" \
  -d '{"username": "newuser", "password": "securepassword", "role": "viewer"}'
```

---

### GET /api/users/{id}

Get a single user. Admin only.

**Response 200:**

```json
{
  "id": 1,
  "username": "admin",
  "role": "admin",
  "is_active": true,
  "created_at": "2026-03-20T10:00:00Z"
}
```

---

### PUT /api/users/{id}

Update a user. Admin only.

**Request body:**

```json
{
  "role": "admin",
  "password": "newpassword"
}
```

All fields are optional.

---

### DELETE /api/users/{id}

Deactivate a user. Admin only. The user is soft-deleted (marked inactive) rather than permanently removed.

**Response 200:**

```json
{
  "status": "ok"
}
```

---

## Token Management Endpoints

### GET /api/tokens

List your own API tokens. Returns token metadata (not the token value).

**Response 200:**

```json
[
  {
    "id": 1,
    "name": "CI Pipeline",
    "created_at": "2026-03-20T10:00:00Z",
    "expires_at": "2026-06-20T10:00:00Z",
    "last_used_at": "2026-03-21T15:30:00Z"
  }
]
```

**Example:**

```bash
curl -H "Authorization: Bearer nvsec_your_token" http://localhost:8000/api/tokens
```

---

### POST /api/tokens

Create a new API token. The token value is returned only once in the response.

**Request body:**

```json
{
  "name": "CI Pipeline",
  "expires_days": 90
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Human-readable token name |
| `expires_days` | integer | No | Days until expiry (30, 90, 365, or null for never) |

**Response 201:**

```json
{
  "id": 2,
  "name": "CI Pipeline",
  "token": "nvsec_a1b2c3d4e5f6...",
  "expires_at": "2026-06-20T10:00:00Z"
}
```

**Example:**

```bash
curl -X POST http://localhost:8000/api/tokens \
  -H "Authorization: Bearer nvsec_your_token" \
  -H "Content-Type: application/json" \
  -d '{"name": "CI Pipeline", "expires_days": 90}'
```

---

### DELETE /api/tokens/{id}

Revoke an API token. The token is immediately invalidated.

**Response 200:**

```json
{
  "status": "ok"
}
```

**Example:**

```bash
curl -X DELETE http://localhost:8000/api/tokens/1 \
  -H "Authorization: Bearer nvsec_your_token"
```

---

## Dashboard

A web dashboard is available at `/dashboard` providing a graphical interface for the scanner:

| Route | Description |
|-------|-------------|
| `GET /dashboard/login` | Login page |
| `POST /dashboard/login` | Authenticate with username and password |
| `GET /dashboard/` | Scan history overview |
| `GET /dashboard/scans/{id}` | Scan detail with findings |
| `GET /dashboard/trends` | Trend charts over time |
| `GET /dashboard/users` | User management (admin only) |
| `GET /dashboard/tokens` | Token management |
| `GET /dashboard/scanners` | Scanner configuration (admin only) |

The dashboard uses session cookies for authentication (7-day expiry). Finding suppression and unsuppression are available directly from the scan detail page.

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
| `401` | Missing or invalid Bearer token |
| `403` | Insufficient permissions (role check failed) |
| `404` | Resource not found (scan ID, finding ID, profile name) |
| `422` | Validation error (invalid request body) |

## OpenAPI Documentation

FastAPI auto-generates interactive API documentation:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json
