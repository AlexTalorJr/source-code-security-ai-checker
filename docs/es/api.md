# Referencia de API

## URL Base

```
http://localhost:8000
```

## Autenticación

Todos los endpoints de la API excepto `/api/health` requieren una clave API en el encabezado `X-API-Key`. La clave se establece mediante la variable de entorno `SCANNER_API_KEY` y se valida usando comparación segura en tiempo constante (`secrets.compare_digest`).

```bash
curl -H "X-API-Key: your-key" http://localhost:8000/api/scans
```

Las solicitudes sin una clave válida reciben una respuesta `401 Unauthorized`.

## Endpoints

### GET /api/health

Endpoint de verificación de salud. No requiere autenticación.

**Respuesta 200:**

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime_seconds": 3600.5,
  "database": "ok"
}
```

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `status` | string | `"healthy"` o `"degraded"` |
| `version` | string | Versión del escáner desde pyproject.toml |
| `uptime_seconds` | float | Segundos desde el inicio de la aplicación |
| `database` | string | `"ok"` o `"error"` |

**Ejemplo:**

```bash
curl http://localhost:8000/api/health
```

---

### POST /api/scans

Inicia un nuevo escaneo de seguridad. El escaneo se encola y se ejecuta de forma asíncrona en segundo plano.

**Cuerpo de la solicitud:**

```json
{
  "path": "/path/to/local/code",
  "repo_url": "https://github.com/org/repo.git",
  "branch": "main"
}
```

| Campo | Tipo | Requerido | Descripción |
|-------|------|----------|-------------|
| `path` | string | No | Ruta del sistema de archivos local a escanear |
| `repo_url` | string | No | URL del repositorio Git para clonar y escanear |
| `branch` | string | No | Rama a verificar (por defecto: rama predeterminada del repositorio) |

Proporcione `path` o `repo_url`. Si se proporciona `repo_url`, el escáner clona el repositorio antes de escanearlo.

**Respuesta 202:**

```json
{
  "id": 1,
  "status": "queued"
}
```

**Códigos de estado:** `202` Creado, `401` No autorizado, `422` Error de validación

**Ejemplo:**

```bash
curl -X POST http://localhost:8000/api/scans \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/org/repo.git", "branch": "main"}'
```

---

### GET /api/scans

Lista todos los escaneos, ordenados por fecha de creación (más recientes primero).

**Respuesta 200:**

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

**Ejemplo:**

```bash
curl -H "X-API-Key: your-key" http://localhost:8000/api/scans
```

---

### GET /api/scans/{id}

Obtiene los resultados detallados del escaneo incluyendo los hallazgos.

**Parámetros de ruta:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `id` | integer | ID del escaneo |

**Respuesta 200:**

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

**Códigos de estado:** `200` OK, `401` No autorizado, `404` Escaneo no encontrado

**Ejemplo:**

```bash
curl -H "X-API-Key: your-key" http://localhost:8000/api/scans/1
```

---

### POST /api/scans/{scan_id}/findings/{finding_id}/suppress

Suprime un hallazgo (lo marca como falso positivo).

**Parámetros de ruta:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `scan_id` | integer | ID del escaneo |
| `finding_id` | integer | ID del hallazgo |

**Cuerpo de la solicitud:**

```json
{
  "reason": "False positive: test fixture data"
}
```

**Respuesta 200:**

```json
{
  "status": "suppressed",
  "finding_id": 1,
  "reason": "False positive: test fixture data"
}
```

**Ejemplo:**

```bash
curl -X POST http://localhost:8000/api/scans/1/findings/5/suppress \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"reason": "False positive: test fixture"}'
```

---

### DELETE /api/scans/{scan_id}/findings/{finding_id}/suppress

Elimina la supresión de un hallazgo.

**Parámetros de ruta:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `scan_id` | integer | ID del escaneo |
| `finding_id` | integer | ID del hallazgo |

**Respuesta 200:**

```json
{
  "status": "unsuppressed",
  "finding_id": 1
}
```

**Ejemplo:**

```bash
curl -X DELETE http://localhost:8000/api/scans/1/findings/5/suppress \
  -H "X-API-Key: your-key"
```

---

### GET /api/trends

Obtiene las tendencias de hallazgos a lo largo del tiempo para los gráficos de tendencias.

**Respuesta 200:**

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

**Ejemplo:**

```bash
curl -H "X-API-Key: your-key" http://localhost:8000/api/trends
```

## Panel de Control

Un panel de control web está disponible en `/dashboard` que proporciona una interfaz gráfica para el escáner:

| Ruta | Descripción |
|-------|-------------|
| `GET /dashboard/login` | Página de inicio de sesión |
| `POST /dashboard/login` | Autenticación con clave API |
| `GET /dashboard/` | Resumen del historial de escaneos |
| `GET /dashboard/scans/{id}` | Detalle del escaneo con hallazgos |
| `GET /dashboard/trends` | Gráficos de tendencias a lo largo del tiempo |

El panel de control utiliza la misma clave API para la autenticación, almacenada en una cookie de sesión tras el inicio de sesión. La supresión y desupresión de hallazgos están disponibles directamente desde la página de detalle del escaneo.

## Respuestas de Error

Todas las respuestas de error siguen un formato estándar:

```json
{
  "detail": "Description of the error"
}
```

**Códigos de estado comunes:**

| Código | Significado |
|------|---------|
| `401` | Clave API faltante o inválida |
| `404` | Recurso no encontrado (ID de escaneo, ID de hallazgo) |
| `422` | Error de validación (cuerpo de solicitud inválido) |

## Documentación OpenAPI

FastAPI genera automáticamente documentación interactiva de la API:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json
