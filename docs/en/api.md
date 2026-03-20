# API Reference

## Base URL

```
http://localhost:8000/api
```

## Authentication

All endpoints except health check require an API key in the `X-API-Key` header. The key is validated using timing-safe comparison (`secrets.compare_digest`).

```bash
curl -H "X-API-Key: your-key" http://localhost:8000/api/scans
```

## Endpoints

### Health Check

```
GET /api/health
```

Checks application and database health. No authentication required.

**Response 200:**

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime_seconds": 123.45,
  "database": "ok"
}
```

| Field | Type | Description |
|-------|------|-------------|
| status | string | `"healthy"` or `"degraded"` |
| version | string | Scanner version |
| uptime_seconds | float | Seconds since startup |
| database | string | `"ok"` or `"error"` |

### Trigger Scan

```
POST /api/scans
```

Start a new security scan. Returns immediately with scan ID; scan runs asynchronously.

**Request body:**

```json
{
  "repo_url": "https://github.com/org/repo.git",
  "branch": "main"
}
```

**Response 202:**

```json
{
  "id": 1,
  "status": "pending",
  "repo_url": "https://github.com/org/repo.git",
  "branch": "main"
}
```

### List Scans

```
GET /api/scans
```

Returns all scans ordered by creation date (newest first).

### Get Scan Details

```
GET /api/scans/{id}
```

Returns scan metadata, severity counts, and quality gate result.

### Get Scan Findings

```
GET /api/scans/{id}/findings
```

Returns all findings for a scan, including AI analysis and fix suggestions.

### Download HTML Report

```
GET /api/scans/{id}/report/html
```

Returns the interactive HTML report for a completed scan.

### Download PDF Report

```
GET /api/scans/{id}/report/pdf
```

Returns the PDF report for a completed scan.

### Quality Gate Result

```
GET /api/scans/{id}/gate
```

Returns the quality gate evaluation result for a scan.

### Create Suppression

```
POST /api/suppressions
```

Mark a finding fingerprint as a false positive.

**Request body:**

```json
{
  "fingerprint": "abc123...",
  "reason": "False positive: test fixture"
}
```

### Delete Suppression

```
DELETE /api/suppressions/{fingerprint}
```

Remove a suppression to re-enable the finding.

## OpenAPI Documentation

FastAPI auto-generates interactive API documentation:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json
