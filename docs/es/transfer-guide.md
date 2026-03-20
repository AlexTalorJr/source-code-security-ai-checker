# Guía de Transferencia

## Descripción General

Esta guía cubre la migración de Security AI Scanner a un nuevo servidor, transferir el proyecto a un nuevo equipo o configurar una instalación nueva.

**Qué se transfiere:**
- Base de datos SQLite (historial de análisis, hallazgos, supresiones)
- Archivos de configuración (`config.yml`, `.env`)
- Reportes generados (HTML/PDF)

**Qué NO se transfiere:**
- Imágenes Docker -- se reconstruyen en el host de destino desde el código fuente
- Entornos virtuales de Python -- se recrean durante `make install`

## Requisitos Previos

El host de destino requiere:

- Docker Engine 20.10+
- Docker Compose v2+
- GNU Make
- Git (para clonar el repositorio)
- Mínimo 2 GB de RAM
- Espacio en disco de 10 GB

## Exportar desde la Fuente

Cree un archivo de respaldo en el servidor de origen:

```bash
cd /path/to/naveksoft-security

# Create timestamped backup (DB + reports + config)
make backup
# Output: backups/backup-YYYYMMDD_HHMMSS.tar.gz
```

Copie el archivo al host de destino:

```bash
scp backups/backup-*.tar.gz user@target-server:/tmp/
```

## Importar al Destino

### Instalación Nueva (Clonar Git)

```bash
# On target server
git clone https://github.com/AlexTalorJr/naveksoft-security.git
cd naveksoft-security

# Configure
cp .env.example .env
# Edit .env with real values (see Environment Variables Reference below)

cp config.yml.example config.yml
# Edit config.yml if needed

# Build and start
make install
make run

# Run migrations
make migrate

# Verify
curl http://localhost:8000/api/health
```

### Restaurar Datos desde Respaldo

Si tiene un archivo de respaldo del servidor de origen:

```bash
# After make install and make run:
make restore BACKUP=/tmp/backup-20260320_143000.tar.gz

# Restart to pick up restored data
docker compose restart

# Verify
curl http://localhost:8000/api/health
```

## Lista de Verificación de Incorporación

Siga estos pasos para ejecutar una nueva instalación:

1. Instale Docker y Docker Compose en el host de destino
2. Clone el repositorio:
   ```bash
   git clone https://github.com/AlexTalorJr/naveksoft-security.git
   cd naveksoft-security
   ```
3. Copie las plantillas de configuración:
   ```bash
   cp config.yml.example config.yml
   cp .env.example .env
   ```
4. Establezca `SCANNER_API_KEY` -- genere una clave segura:
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
5. Establezca `SCANNER_CLAUDE_API_KEY` -- obtenga desde la [Consola de Anthropic](https://console.anthropic.com/)
6. Configure opciones de notificación si es necesario:
   - Slack: establezca `SCANNER_SLACK_WEBHOOK_URL` en `.env`
   - Email: establezca `SCANNER_EMAIL_SMTP_HOST`, `SCANNER_NOTIFICATIONS__EMAIL__SMTP_USER`, `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PASSWORD` y `SCANNER_NOTIFICATIONS__EMAIL__RECIPIENTS` en `.env`
7. Construya imágenes Docker:
   ```bash
   make install
   ```
8. Inicie el scanner:
   ```bash
   make run
   ```
9. Ejecute migraciones de base de datos:
   ```bash
   make migrate
   ```
10. Verifique el punto final de estado:
    ```bash
    curl http://localhost:8000/api/health
    # Expected: {"status": "healthy", ...}
    ```
11. Ejecute su primer análisis:
    ```bash
    curl -X POST http://localhost:8000/api/scans \
      -H "X-API-Key: your-key" \
      -H "Content-Type: application/json" \
      -d '{"path": "/path/to/code"}'
    ```

## Referencia de Variables de Entorno

Todas las variables usan el prefijo `SCANNER_`. Establézcalas en el archivo `.env`.

| Variable | Requerida | Predeterminada | Descripción | Ejemplo |
|----------|-----------|----------------|-------------|---------|
| `SCANNER_API_KEY` | Sí | -- | Clave API para autenticación de API REST | `dGhpcyBpcyBhIHRlc3Q` |
| `SCANNER_CLAUDE_API_KEY` | Sí | -- | Clave API de Anthropic para análisis IA | `sk-ant-api03-...` |
| `SCANNER_PORT` | No | `8000` | Puerto externo para el scanner | `9000` |
| `SCANNER_DB_PATH` | No | `/data/scanner.db` | Ruta del archivo de base de datos SQLite | `/data/scanner.db` |
| `SCANNER_CONFIG_PATH` | No | `config.yml` | Ruta del archivo de configuración YAML | `config.yml` |
| `SCANNER_GIT_TOKEN` | No | -- | Token para clonar repositorios privados | `ghp_xxxxxxxxxxxx` |
| `SCANNER_SLACK_WEBHOOK_URL` | No | -- | Webhook de Slack para notificaciones | `https://hooks.slack.com/...` |
| `SCANNER_EMAIL_SMTP_HOST` | No | -- | Servidor SMTP para notificaciones por correo | `smtp.gmail.com` |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PORT` | No | `587` | Puerto SMTP | `587` |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_USER` | No | -- | Usuario SMTP | `alerts@example.com` |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PASSWORD` | No | -- | Contraseña SMTP | -- |
| `SCANNER_NOTIFICATIONS__EMAIL__RECIPIENTS` | No | `[]` | Array JSON de correos de destinatarios | `["dev@example.com"]` |

## Solución de Problemas

### El Contenedor No Se Inicia

```bash
docker compose logs scanner
```

Causas comunes:
- Puerto en uso -- cambie `SCANNER_PORT` en `.env`
- Archivo `.env` faltante -- copie desde `.env.example`
- Docker no ejecutándose -- inicie el demonio de Docker

### El Punto Final de Estado Devuelve un Error

```bash
curl http://localhost:8000/api/health
# {"status": "degraded", "database": "error"}
```

Verifique que `SCANNER_DB_PATH` apunte a una ubicación escribible dentro del contenedor. El predeterminado `/data/scanner.db` requiere que el volumen `scanner_data` esté montado.

### Los Análisis Fallan o Agotan el Tiempo

- Verifique que las herramientas del scanner (semgrep, trivy, etc.) estén disponibles dentro de la imagen Docker
- Aumente `scan_timeout` en `config.yml` para repositorios grandes
- Para repositorios privados, asegúrese de que `SCANNER_GIT_TOKEN` esté establecido

### Errores de Base de Datos Bloqueada

La base de datos utiliza modo WAL para acceso de lectura concurrente. Si ve errores de "database is locked":
- Asegúrese de que solo se está ejecutando un contenedor del scanner
- No acceda directamente al archivo SQLite mientras el contenedor está en ejecución
- Use `make backup` para copias seguras de la base de datos

### Permiso Denegado en /data

El contenedor se ejecuta como usuario no root `scanner`. Asegúrese de que el volumen de Docker tenga la propiedad correcta:

```bash
docker compose down
docker volume rm naveksoft-security_scanner_data
docker compose up -d  # Recreates volume with correct permissions
```

Nota: Esto elimina los datos de análisis existentes. Haga una copia de seguridad primero con `make backup`.
