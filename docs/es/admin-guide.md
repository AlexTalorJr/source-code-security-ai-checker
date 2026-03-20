# Guía de Administración

## Configuración

### Fuentes de Configuración (Orden de Prioridad)

1. **Argumentos del constructor** -- anulaciones programáticas
2. **Variables de entorno** -- prefijo `SCANNER_*`
3. **Archivo dotenv** -- archivo `.env`
4. **Secretos de archivos** -- secretos de Docker/K8s
5. **Archivo de configuración YAML** -- `config.yml` (menor prioridad)

### Archivo de Configuración

Copie el ejemplo y personalícelo:

```bash
cp config.yml.example config.yml
```

## Configuración de los Escáneres

Cada una de las cinco herramientas de escaneo puede habilitarse de forma independiente, configurarse con un tiempo de espera y recibir argumentos adicionales:

```yaml
scanners:
  semgrep:
    enabled: true
    timeout: 180
    extra_args: []
  cppcheck:
    enabled: true
    timeout: 120
    extra_args: []
  gitleaks:
    enabled: true
    timeout: 120
    extra_args: []
  trivy:
    enabled: true
    timeout: 120
    extra_args: []
  checkov:
    enabled: true
    timeout: 120
    extra_args: []
```

- **enabled** -- establezca en `false` para omitir completamente una herramienta
- **timeout** -- tiempo máximo en segundos antes de que la herramienta sea terminada
- **extra_args** -- argumentos CLI adicionales pasados a la herramienta

## Configuración de IA

```yaml
ai:
  max_cost_per_scan: 5.0
  model: "claude-sonnet-4-6"
  max_findings_per_batch: 50
  max_tokens_per_response: 4096
```

| Parámetro | Descripción | Valor por Defecto |
|---------|-------------|---------|
| `max_cost_per_scan` | Gasto máximo en USD en análisis con IA por escaneo | `5.0` |
| `model` | Identificador del modelo Claude | `claude-sonnet-4-6` |
| `max_findings_per_batch` | Máximo de hallazgos enviados a Claude en una solicitud | `50` |
| `max_tokens_per_response` | Máximo de tokens de respuesta de Claude | `4096` |

## Configuración del Quality Gate

```yaml
gate:
  fail_on:
    - critical
    - high
  include_compound_risks: true
```

- **fail_on** -- lista de niveles de severidad que causan que el gate falle
- **include_compound_risks** -- cuando es `true`, los riesgos compuestos con severidad coincidente también hacen fallar el gate

## Configuración de Notificaciones

### Slack

```yaml
notifications:
  slack:
    enabled: false
```

Establezca la URL del webhook en el nivel superior:

```yaml
slack_webhook_url: "https://hooks.slack.com/services/T.../B.../xxx"
```

O mediante variable de entorno: `SCANNER_SLACK_WEBHOOK_URL`

### Email

```yaml
notifications:
  email:
    enabled: false
    recipients: ["security@example.com"]
    smtp_port: 587
    smtp_user: ""
    smtp_password: ""  # Use env var instead
    use_tls: true
```

Establezca el host SMTP en el nivel superior:

```yaml
email_smtp_host: "smtp.example.com"
```

O mediante variable de entorno: `SCANNER_EMAIL_SMTP_HOST`

La contraseña SMTP debe usar la variable de entorno anidada: `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PASSWORD`

### URL del Panel de Control

```yaml
dashboard_url: ""  # e.g., http://scanner:8000/dashboard
```

Se utiliza en los mensajes de notificación para enlazar de vuelta a los resultados del escaneo. Si está vacío, se deriva automáticamente del host y el puerto.

## Variables de Entorno

Todos los parámetros pueden anularse con el prefijo `SCANNER_`:

| Variable | Descripción | Valor por Defecto |
|----------|-------------|---------|
| `SCANNER_HOST` | Dirección de escucha | `0.0.0.0` |
| `SCANNER_PORT` | Puerto de escucha | `8000` |
| `SCANNER_DB_PATH` | Ruta al archivo de base de datos SQLite | `/data/scanner.db` |
| `SCANNER_API_KEY` | Clave de autenticación de la API | `""` (vacío) |
| `SCANNER_CLAUDE_API_KEY` | Clave API de Anthropic para el análisis con IA | `""` (vacío) |
| `SCANNER_SLACK_WEBHOOK_URL` | URL del webhook de Slack | `""` |
| `SCANNER_EMAIL_SMTP_HOST` | Nombre de host del servidor SMTP | `""` |
| `SCANNER_LOG_LEVEL` | Nivel de log (debug/info/warning/error) | `info` |
| `SCANNER_SCAN_TIMEOUT` | Tiempo de espera global del escaneo en segundos | `600` |
| `SCANNER_CONFIG_PATH` | Ruta al archivo de configuración YAML | `config.yml` |

### Variables de Entorno Anidadas

Para secciones de configuración anidadas, use doble guion bajo:

| Variable | Corresponde a |
|----------|---------|
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PASSWORD` | `notifications.email.smtp_password` |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PORT` | `notifications.email.smtp_port` |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_USER` | `notifications.email.smtp_user` |
| `SCANNER_NOTIFICATIONS__SLACK__ENABLED` | `notifications.slack.enabled` |

## Gestión de Secretos

Nunca almacene secretos en `config.yml` ni los confirme en git.

```bash
# Set secrets via environment:
export SCANNER_API_KEY="your-secure-key"
export SCANNER_CLAUDE_API_KEY="sk-ant-..."

# Or in docker-compose via .env file:
echo "SCANNER_API_KEY=your-secure-key" >> .env
echo "SCANNER_CLAUDE_API_KEY=sk-ant-..." >> .env
```

## Gestión de la Base de Datos

### Ubicación

- Docker: `/data/scanner.db` (volumen persistente `scanner_data`)
- Local: configurable vía `SCANNER_DB_PATH`

### Modo WAL

SQLite se ejecuta en modo WAL (Write-Ahead Logging) para rendimiento de lectura concurrente. Esto se establece automáticamente en cada conexión mediante event listeners de SQLAlchemy.

### Copia de Seguridad

```bash
# WAL mode allows hot backup (no need to stop scanner)
docker cp naveksoft-security-scanner-1:/data/scanner.db ./backup/
```

## Ajuste de Umbrales

### Quality Gate

Ajuste qué severidades hacen fallar el gate:

```yaml
gate:
  fail_on:
    - critical        # Only block on critical (relaxed)
```

O incluya medium:

```yaml
gate:
  fail_on:
    - critical
    - high
    - medium           # Stricter policy
```

### Gestión de Herramientas de Escaneo

Deshabilite las herramientas no relevantes para su código base:

```yaml
scanners:
  cppcheck:
    enabled: false     # No C/C++ code
  checkov:
    enabled: false     # No IaC files
```

## Ajuste de Rendimiento

### Tiempos de Espera

- `scan_timeout` (global): duración máxima total del escaneo (por defecto: 600s)
- `timeout` por escáner: tiempo máximo de ejecución por herramienta (por defecto: 120-180s)

Si los escaneos están agotando el tiempo de espera, aumente el timeout por herramienta para el escáner lento en lugar del timeout global.

### Tamaño del Lote de IA

Para escaneos grandes con muchos hallazgos, ajuste:

```yaml
ai:
  max_findings_per_batch: 25   # Smaller batches for faster responses
  max_tokens_per_response: 8192  # More room for detailed analysis
```

### Monitorización

```bash
# Health check
curl http://localhost:8000/api/health

# Container status
docker compose ps

# Logs
docker compose logs scanner --tail 50
```

Docker Compose realiza verificaciones de salud automáticas cada 30 segundos.
