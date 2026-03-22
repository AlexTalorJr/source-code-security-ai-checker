# Guía DevOps

## Despliegue con Docker

### Inicio Rápido

```bash
cp config.yml.example config.yml
cp .env.example .env
# Edit .env with real secrets
make install   # builds Docker images
make run       # starts scanner in background
```

O directamente con Docker Compose:

```bash
docker compose up -d --build
```

### Configuración del Contenedor

El archivo `docker-compose.yml` define un único servicio `scanner`:

```yaml
services:
  scanner:
    build: .
    ports:
      - "${SCANNER_PORT:-8000}:8000"
    volumes:
      - scanner_data:/data           # Persistent DB and reports
      - ./config.yml:/app/config.yml:ro  # Read-only config mount
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    restart: unless-stopped

volumes:
  scanner_data:  # Named volume for SQLite persistence
```

- **Volumen `scanner_data`** se monta en `/data` dentro del contenedor -- almacena la base de datos SQLite y los informes generados. Los datos sobreviven a los reinicios y reconstrucciones del contenedor.
- **Montaje de configuración** enlaza `config.yml` en solo lectura dentro del contenedor en `/app/config.yml`.
- **Mapeo de puertos** por defecto es `8000`, pero puede cambiarse mediante la variable de entorno `SCANNER_PORT`.
- **Política de reinicio** `unless-stopped` asegura que el escáner se reinicie después de reinicios del host.

## Dockerfile

La imagen esta basada en `python:3.12-slim` e incluye las 12 herramientas de escaneo:

1. **Dependencias del sistema** -- `curl` (healthcheck), `libpango` y `libharfbuzz` (generacion de PDF con WeasyPrint), `ruby` (Brakeman)
2. **Usuario sin privilegios root** -- se crea el usuario y grupo `scanner` por seguridad; el directorio `/data` es propiedad de este usuario
3. **Binarios de escaneres** -- consulte la seccion Binarios de escaneres a continuacion para la lista completa
4. **Flujo de instalacion** -- se copian `pyproject.toml` y `src/`, luego `pip install --no-cache-dir .` usando el backend de compilacion hatchling
5. **Archivos de la aplicacion** -- se copian `alembic.ini`, las migraciones `alembic/` y `config.yml.example` (como `config.yml` por defecto)
6. **Entrypoint** -- `uvicorn scanner.main:app --host 0.0.0.0 --port 8000`

## Binarios de escaneres

Las 12 herramientas de escaneo se instalan dentro de la imagen Docker:

| Escaner | Metodo de instalacion | Notas |
|---------|----------------------|-------|
| **Semgrep** | `pip install semgrep` | Paquete Python, instalado junto con la aplicacion |
| **cppcheck** | `apt-get install cppcheck` | Paquete del sistema |
| **Gitleaks** | Binario precompilado de GitHub releases | Descargado a `/usr/local/bin`, soporta amd64/arm64 |
| **Trivy** | Binario precompilado de GitHub releases | Descargado a `/usr/local/bin`, soporta amd64/arm64 |
| **Checkov** | `pip install checkov` | Paquete Python, instalado con `--no-cache-dir` |
| **Psalm** | `composer global require vimeo/psalm` | Paquete PHP Composer, requiere `php-cli` |
| **Enlightn** | `composer global require enlightn/enlightn` | Paquete PHP Composer |
| **PHP Security Checker** | Binario precompilado de GitHub releases | Descargado a `/usr/local/bin` |
| **gosec** | Binario precompilado de GitHub releases | Descargado a `/usr/local/bin`, soporta amd64/arm64 |
| **Bandit** | `pip install bandit` | Paquete Python, instalado junto con Semgrep y Checkov |
| **Brakeman** | `gem install brakeman` | Ruby gem, requiere el paquete `ruby` (~80 MB) |
| **cargo-audit** | Binario precompilado de GitHub releases | Descargado a `/usr/local/bin`, soporta amd64/arm64 |

### Verificacion de disponibilidad de escaneres

Despues de construir la imagen Docker, verifique que todos los escaneres estan correctamente instalados:

```bash
make verify-scanners
```

Este objetivo ejecuta un smoke test dentro del contenedor, verificando que cada uno de los 12 binarios de escaneres esta disponible y responde a comandos version/help. Uselo despues de cualquier cambio en el Dockerfile para asegurar que ningun escaner se rompio.

## Variables de Entorno

Toda la configuración puede establecerse mediante variables de entorno con el prefijo `SCANNER_`. Pase los secretos mediante el archivo `.env` (no confirmado en git).

| Variable | Requerida | Por Defecto | Descripción |
|----------|----------|---------|-------------|
| `SCANNER_API_KEY` | Sí | -- | Clave API para autenticar solicitudes REST API |
| `SCANNER_CLAUDE_API_KEY` | Sí | -- | Clave API de Anthropic para análisis con IA |
| `SCANNER_PORT` | No | `8000` | Puerto externo para el servicio del escáner |
| `SCANNER_DB_PATH` | No | `/data/scanner.db` | Ruta al archivo de base de datos SQLite |
| `SCANNER_CONFIG_PATH` | No | `config.yml` | Ruta al archivo de configuración YAML |
| `SCANNER_GIT_TOKEN` | No | -- | Token para clonar repositorios Git privados |
| `SCANNER_SLACK_WEBHOOK_URL` | No | -- | URL del webhook entrante de Slack para notificaciones |
| `SCANNER_EMAIL_SMTP_HOST` | No | -- | Nombre de host del servidor SMTP para notificaciones por email |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PORT` | No | `587` | Puerto del servidor SMTP |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_USER` | No | -- | Nombre de usuario de autenticación SMTP |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PASSWORD` | No | -- | Contraseña de autenticación SMTP |
| `SCANNER_NOTIFICATIONS__EMAIL__RECIPIENTS` | No | `[]` | Array JSON de destinatarios de email |

## Integración con Jenkins

El proyecto incluye `Jenkinsfile.security` para integrar escaneos de seguridad en un pipeline de Jenkins. Utiliza el plugin `httpRequest` de Jenkins para las llamadas a la API.

### Configuración

1. Instale el plugin **HTTP Request** en Jenkins
2. Agregue `SCANNER_URL` (p. ej., `http://scanner:8000`) como credencial o variable de entorno de Jenkins
3. Agregue `SCANNER_API_KEY` como credencial de texto secreto en Jenkins

### Uso

Agregue la etapa de escaneo de seguridad a su `Jenkinsfile` existente:

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

### Quality Gate

El escáner evalúa un quality gate después de cada escaneo. Configure los criterios de aprobación/fallo en `config.yml`:

```yaml
gate:
  fail_on:
    - critical
    - high
  include_compound_risks: true
```

Si el gate falla, la etapa de Jenkins debe hacer fallar el build. Consulte el resultado del escaneo para verificar `gate_passed`.

## Copias de Seguridad

### Usando los Objetivos de Make

```bash
# Create a timestamped backup (DB + reports + config)
make backup
# Output: backups/backup-20260320_143000.tar.gz

# Restore from a backup file
make restore BACKUP=backups/backup-20260320_143000.tar.gz
```

### Qué se Incluye en la Copia de Seguridad

- **Base de datos SQLite** -- respaldada usando el comando `sqlite3 .backup` (seguro con WAL, sin tiempo de inactividad)
- **Informes** -- informes HTML/PDF generados desde `/data/reports`
- **Configuración** -- `config.yml`

### Seguridad del Modo WAL

La base de datos se ejecuta en modo WAL (Write-Ahead Logging). El objetivo `make backup` usa el comando `.backup` de SQLite dentro del contenedor, que maneja de forma segura el checkpointing de WAL. No copie simplemente el archivo `.db` -- use el objetivo de make o el comando `sqlite3 .backup`.

### Programación Recomendada

Configure un cron job diario para copias de seguridad automatizadas:

```bash
# Daily at 2 AM
0 2 * * * cd /path/to/naveksoft-security && make backup
```

## Compilaciones Multi-Arquitectura

Compile imágenes Docker para las arquitecturas `amd64` y `arm64` usando Docker Buildx.

### Requisitos Previos

- Docker Desktop 4.x+ (incluye buildx) o el plugin `docker-buildx` instalado manualmente
- QEMU user-static para emulación multiplataforma (Docker Desktop lo gestiona automáticamente)

### Compilar Imágenes Multi-Arquitectura

```bash
# Build for amd64 + arm64, save as OCI archive
make docker-multiarch
# Output: Security AI Scanner-{version}-multiarch.tar

# Build and push to a container registry
make docker-push REGISTRY=your-registry.example.com
```

El objetivo `docker-multiarch` crea un builder de buildx llamado `multiarch` si no existe ya.

## Monitorización

### Endpoint de Salud

Consulte el endpoint de salud para monitorizar el estado del escáner:

```bash
curl http://localhost:8000/api/health
# {"status": "healthy", "version": "0.1.0", "uptime_seconds": 3600.5, "database": "ok"}
```

Un estado `"degraded"` o una respuesta `"database": "error"` indica un problema con la conexión a la base de datos.

### Healthcheck de Docker

El contenedor incluye un healthcheck integrado que se ejecuta cada 30 segundos. Verifique el estado de salud del contenedor:

```bash
docker compose ps
# Shows "healthy" or "unhealthy" in the STATUS column
```

### Logs

```bash
# Follow logs in real time
docker compose logs -f scanner

# Last 100 lines
docker compose logs scanner --tail 100
```

El nivel de log se configura en `config.yml` mediante el campo `log_level` (por defecto: `info`).

### Política de Reinicio

El contenedor usa `restart: unless-stopped`, por lo que se reinicia automáticamente tras fallos o reinicios del host. Solo un `docker compose stop` o `docker compose down` manual lo mantendrá detenido.

## Actualización

1. Obtenga el código más reciente:
   ```bash
   git pull origin main
   ```

2. Reconstruya y reinicie:
   ```bash
   make install   # rebuilds Docker image
   make run       # starts updated container
   ```

3. Ejecute las migraciones de la base de datos:
   ```bash
   make migrate
   ```

4. Verifique la actualización:
   ```bash
   curl http://localhost:8000/api/health
   ```

Si el endpoint de salud devuelve el nuevo número de versión y `"status": "healthy"`, la actualización está completa.
