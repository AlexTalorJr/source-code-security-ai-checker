# Referencia de API

## URL Base

```
http://localhost:8000
```

## Autenticacion

Todos los endpoints de la API excepto `/api/health` requieren un token Bearer en el encabezado Authorization. Genere tokens desde el panel de control (`/dashboard/tokens`) o via la API de gestion de tokens.

```bash
curl -H "Authorization: Bearer nvsec_your_token_here" http://localhost:8000/api/scans
```

Las solicitudes sin un token valido reciben una respuesta `401 Unauthorized`.

## Endpoints

### GET /api/health

Endpoint de verificacion de salud. No requiere autenticacion.

**Respuesta 200:**

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime_seconds": 3600.5,
  "database": "ok"
}
```

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| `status` | string | `"healthy"` o `"degraded"` |
| `version` | string | Version del escaner desde pyproject.toml |
| `uptime_seconds` | float | Segundos desde el inicio de la aplicacion |
| `database` | string | `"ok"` o `"error"` |

---

### POST /api/scans

Iniciar un nuevo escaneo de seguridad. El escaneo se encola y se ejecuta de forma asincrona.

**Cuerpo de la solicitud:**

```json
{
  "path": "/path/to/local/code",
  "repo_url": "https://github.com/org/repo.git",
  "branch": "main",
  "target_url": "https://example.com",
  "profile": "quick_scan"
}
```

| Campo | Tipo | Requerido | Descripcion |
|-------|------|----------|-------------|
| `path` | string | No | Ruta local a escanear |
| `repo_url` | string | No | URL del repositorio Git a clonar y escanear |
| `branch` | string | No | Rama a verificar (por defecto: rama predeterminada) |
| `target_url` | string | No | URL para escaneo DAST (exclusivo con `path`/`repo_url`) |
| `profile` | string | No | Nombre del perfil de escaneo a usar |
| `skip_ai` | boolean | No | Omitir analisis IA (por defecto: false) |

Proporcione `path`, `repo_url` o `target_url`. El campo `target_url` inicia un escaneo DAST y no puede combinarse con `path` o `repo_url`.

**Respuesta 202:**

```json
{
  "id": 1,
  "status": "queued"
}
```

**Codigos de estado:** `202` Creado, `400` Perfil invalido, `401` No autorizado, `422` Error de validacion

**Ejemplos:**

```bash
# Escaneo SAST
curl -X POST http://localhost:8000/api/scans \
  -H "Authorization: Bearer nvsec_your_token" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/org/repo.git", "branch": "main"}'

# Escaneo SAST con perfil
curl -X POST http://localhost:8000/api/scans \
  -H "Authorization: Bearer nvsec_your_token" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/org/repo.git", "profile": "quick_scan"}'

# Escaneo DAST
curl -X POST http://localhost:8000/api/scans \
  -H "Authorization: Bearer nvsec_your_token" \
  -H "Content-Type: application/json" \
  -d '{"target_url": "https://example.com"}'
```

---

### GET /api/scans

Listar escaneos con paginacion, ordenados por fecha de creacion (mas recientes primero).

---

### GET /api/scans/{id}

Obtener informacion detallada de un escaneo.

---

### GET /api/scans/{scan_id}/findings

Hallazgos paginados para un escaneo especifico.

---

### POST /api/scans/{scan_id}/findings/{finding_id}/suppress

Suprimir un hallazgo (marcar como falso positivo).

**Cuerpo de la solicitud:**

```json
{
  "reason": "False positive: test fixture data"
}
```

---

### DELETE /api/scans/{scan_id}/findings/{finding_id}/suppress

Eliminar la supresion de un hallazgo.

---

### GET /api/scanners

Lista de todos los escaneres registrados con su configuracion.

---

### GET /api/trends

Tendencias de hallazgos a lo largo del tiempo para graficos.

---

## Endpoints de Configuracion

### GET /api/config

Configuracion completa del escaner en JSON. Solo admin.

```bash
curl -H "Authorization: Bearer nvsec_your_token" http://localhost:8000/api/config
```

---

### GET /api/config/yaml

Contenido bruto de `config.yml` como texto. Solo admin.

---

### PATCH /api/config/scanners/{scanner_name}

Actualizar parametros de un escaner individual. Solo admin.

**Cuerpo de la solicitud:**

```json
{
  "enabled": true,
  "timeout": 300,
  "extra_args": ["--exclude", ".venv"]
}
```

| Campo | Tipo | Descripcion |
|-------|------|-------------|
| `enabled` | bool/string | `true`, `false` o `"auto"` |
| `timeout` | integer | 30-900 segundos |
| `extra_args` | string[] | Argumentos CLI adicionales |

---

### PUT /api/config/yaml

Reemplazar `config.yml` con nuevo contenido YAML. Solo admin. El YAML se valida antes de escribir.

---

## Endpoints de Gestion de Perfiles

### GET /api/config/profiles

Lista de todos los perfiles de escaneo. Solo admin.

**Respuesta 200:**

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

Crear un nuevo perfil de escaneo. Solo admin.

**Cuerpo de la solicitud:**

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

**Codigos de estado:** `201` Creado, `400` Limite alcanzado, `409` Perfil existente, `422` Error de validacion

---

### GET /api/config/profiles/{name}

Obtener un perfil por nombre. Solo admin.

### PUT /api/config/profiles/{name}

Actualizar un perfil existente. Solo admin.

### DELETE /api/config/profiles/{name}

Eliminar un perfil de escaneo. Solo admin.

---

## Endpoints de Gestion de Usuarios

### GET /api/users

Lista de todos los usuarios. Solo admin.

### POST /api/users

Crear un nuevo usuario. Solo admin.

```json
{
  "username": "newuser",
  "password": "securepassword",
  "role": "viewer"
}
```

### GET /api/users/{id}

Obtener un usuario. Solo admin.

### PUT /api/users/{id}

Actualizar un usuario. Solo admin.

### DELETE /api/users/{id}

Desactivar un usuario. Solo admin.

---

## Endpoints de Gestion de Tokens

### GET /api/tokens

Lista de sus tokens API.

### POST /api/tokens

Crear un nuevo token API.

```json
{
  "name": "CI Pipeline",
  "expires_days": 90
}
```

### DELETE /api/tokens/{id}

Revocar un token API.

---

## Panel de Control

Un panel de control web esta disponible en `/dashboard`:

| Ruta | Descripcion |
|-------|-------------|
| `GET /dashboard/login` | Pagina de inicio de sesion |
| `POST /dashboard/login` | Autenticacion por nombre de usuario y contrasena |
| `GET /dashboard/` | Resumen del historial de escaneos |
| `GET /dashboard/scans/{id}` | Detalle del escaneo con hallazgos |
| `GET /dashboard/trends` | Graficos de tendencias |
| `GET /dashboard/users` | Gestion de usuarios (solo admin) |
| `GET /dashboard/tokens` | Gestion de tokens |
| `GET /dashboard/scanners` | Configuracion de escaneres (solo admin) |

El panel de control utiliza cookies de sesion para autenticacion (expiracion de 7 dias).

## Respuestas de Error

Todas las respuestas de error siguen un formato estandar:

```json
{
  "detail": "Description of the error"
}
```

**Codigos de estado comunes:**

| Codigo | Significado |
|------|---------|
| `401` | Token Bearer faltante o invalido |
| `403` | Permisos insuficientes (verificacion de rol fallida) |
| `404` | Recurso no encontrado (ID de escaneo, ID de hallazgo, nombre de perfil) |
| `422` | Error de validacion (cuerpo de solicitud invalido) |

## Documentacion OpenAPI

FastAPI genera automaticamente documentacion interactiva de la API:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json
