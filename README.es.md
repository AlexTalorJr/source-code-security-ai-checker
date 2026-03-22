# Source Code Security AI Scanner

Escáner de vulnerabilidades de seguridad en código fuente impulsado por inteligencia artificial.

## Inicio Rápido

Realice su primer escaneo en menos de 5 minutos.

### Requisitos Previos

- Docker y Docker Compose
- Una clave API de Anthropic (para el análisis con IA)

### Configuración

```bash
# 1. Clonar
git clone https://github.com/AlexTalorJr/source-code-security-ai-checker.git
cd source-code-security-ai-checker

# 2. Configurar
cp config.yml.example config.yml
cp .env.example .env

# 3. Establecer secretos en .env
#    SCANNER_API_KEY=<su-clave-api>
#    SCANNER_CLAUDE_API_KEY=<su-clave-anthropic>

# 4. Iniciar
docker compose up -d

# 5. Verificar
curl http://localhost:8000/api/health
```

Respuesta esperada:

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime_seconds": 5.23,
  "database": "ok"
}
```

## Panel de Control Web

El escáner incluye una interfaz web integrada en `http://localhost:8000/dashboard/`.

**Inicio de sesión:** utilice la clave API configurada en `SCANNER_API_KEY`.

### Iniciar un escaneo desde el panel de control

1. Abra **Historial de Escaneos** (`/dashboard/history`)
2. Haga clic en **"Start New Scan"** — el formulario se desplegará
3. Complete el campo **Local Path** o **Repository URL** + **Branch**
4. Opcionalmente marque **"Skip AI Analysis"** para ejecutar sin la API de Claude (más rápido, sin costo)
5. Haga clic en **"Start Scan"**

El escaneo se ejecuta en segundo plano. La página de detalle muestra el progreso en tiempo real con actualización automática, y los resultados aparecen automáticamente al completarse.

### Páginas del panel de control

| Página | URL | Descripción |
|--------|-----|-------------|
| Historial de Escaneos | `/dashboard/history` | Lista de todos los escaneos + formulario para iniciar uno nuevo |
| Detalle del Escaneo | `/dashboard/scans/{id}` | Hallazgos, desglose por severidad, controles de supresión |
| Tendencias | `/dashboard/trends` | Gráficos: severidad a lo largo del tiempo, distribución por herramienta |

### Ejecutar un Escaneo vía API

```bash
curl -X POST http://localhost:8000/api/scans \
  -H "X-API-Key: $SCANNER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/your-org/your-repo.git", "branch": "main"}'
```

Para omitir el análisis con IA en un escaneo específico:

```bash
curl -X POST http://localhost:8000/api/scans \
  -H "X-API-Key: $SCANNER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/your-org/repo.git", "branch": "main", "skip_ai": true}'
```

## Integración con Jenkins Pipeline

Agregue el escáner como una etapa en su `Jenkinsfile` para bloquear despliegues con hallazgos de severidad Critical o High.

### Etapa básica de Jenkinsfile

```groovy
pipeline {
    agent any

    environment {
        SCANNER_URL = 'http://scanner-host:8000'
        SCANNER_API_KEY = credentials('scanner-api-key')
    }

    stages {
        stage('Security Scan') {
            steps {
                script {
                    // Trigger scan
                    def response = httpRequest(
                        url: "${SCANNER_URL}/api/scans",
                        httpMode: 'POST',
                        contentType: 'APPLICATION_JSON',
                        customHeaders: [[name: 'X-API-Key', value: "${SCANNER_API_KEY}"]],
                        requestBody: """{"repo_url": "${env.GIT_URL}", "branch": "${env.GIT_BRANCH}"}"""
                    )

                    def scan = readJSON text: response.content
                    def scanId = scan.id
                    echo "Scan started: #${scanId}"

                    // Poll until complete
                    def status = 'queued'
                    while (status == 'queued' || status == 'running') {
                        sleep 10
                        def progress = httpRequest(
                            url: "${SCANNER_URL}/api/scans/${scanId}/progress",
                            httpMode: 'GET'
                        )
                        status = readJSON(text: progress.content).stage
                    }

                    // Check quality gate
                    def result = httpRequest(
                        url: "${SCANNER_URL}/api/scans/${scanId}",
                        httpMode: 'GET',
                        customHeaders: [[name: 'X-API-Key', value: "${SCANNER_API_KEY}"]]
                    )
                    def scanResult = readJSON text: result.content

                    if (!scanResult.gate_passed) {
                        error "Security scan FAILED: ${scanResult.critical_count} Critical, ${scanResult.high_count} High findings"
                    }

                    echo "Security scan PASSED (${scanResult.total_findings} findings, gate passed)"
                }
            }
        }
    }
}
```

### Puntos clave

- **Quality gate** bloquea el build si se detectan hallazgos Critical o High (configurable en `config.yml` bajo `gate.fail_on`)
- **Escaneo vía ruta local** — si Jenkins y el escáner comparten un sistema de archivos, use `"path": "${WORKSPACE}"` en lugar de `repo_url`
- **Omitir análisis con IA** — agregue `"skip_ai": true` al cuerpo de la solicitud para escaneos más rápidos sin costos de la API de Claude
- **Notificaciones** — configure Slack/email en `config.yml` para recibir alertas al completarse un escaneo
- **Informes** — los informes HTML y PDF se generan automáticamente y son accesibles vía `/api/scans/{id}/report` o el panel de control

Consulte la [Guía DevOps](docs/es/devops-guide.md) para obtener todos los detalles de integración con Jenkins, incluyendo ejemplos de pipelines con etapas paralelas.

## Características

- **12 escaneres de seguridad con deteccion automatica** -- los escaneres se activan automaticamente segun los lenguajes del proyecto a traves de un registro de plugins basado en la configuracion
- **Soporte multilenguaje** -- Python, PHP/Laravel, C/C++, JavaScript/TypeScript, Go, Rust, Java, C#, Ruby, Kotlin
- **Análisis impulsado por IA** -- Claude revisa los hallazgos para evaluar contexto, riesgos compuestos y sugerencias de corrección
- **Informes interactivos HTML y PDF** -- hallazgos filtrables con contexto de código y gráficos
- **Quality gate configurable** -- bloquea despliegues ante hallazgos de severidad Critical o High
- **Panel de control web** -- gestión de escaneos, progreso en tiempo real, historial, controles de supresión
- **REST API** -- dispare escaneos, obtenga resultados y gestione hallazgos de forma programática
- **Notificaciones por Slack y email** -- alertas en tiempo real con identificación del objetivo del escaneo
- **Integración con CI de Jenkins** -- etapa de pipeline con verificaciones de quality gate
- **Historial de escaneos con comparación delta** -- rastree hallazgos nuevos, corregidos y persistentes
- **Omitir IA por escaneo** -- ejecute sin la API de Claude cuando la velocidad o el costo sean prioritarios

## Escáneres Soportados

Los escáneres se activan automáticamente según los lenguajes detectados (`enabled: auto`). Se puede modificar individualmente en `config.yml`.

| Escáner | Lenguajes | Qué detecta |
|---------|-----------|-------------|
| **Semgrep** | Python, PHP, JS/TS, Go, Java, Ruby, C#, Rust | SAST — inyecciones, problemas de autenticación, patrones inseguros |
| **cppcheck** | C/C++ | Seguridad de memoria, desbordamientos de búfer, comportamiento indefinido |
| **Gitleaks** | Cualquiera | Secretos codificados, claves API, tokens en el código e historial de git |
| **Trivy** | Docker, Terraform, K8s | CVEs en imágenes de contenedor y configuraciones incorrectas de IaC |
| **Checkov** | Docker, Terraform, CI configs | Mejores prácticas de seguridad para Infrastructure-as-code |
| **Psalm** | PHP | Análisis de contaminación — inyección SQL, XSS mediante rastreo del flujo de datos |
| **Enlightn** | Laravel | CSRF, mass assignment, modo debug, .env expuesto (más de 120 verificaciones) |
| **PHP Security Checker** | PHP (composer) | CVEs conocidos en dependencias de composer |
| **gosec** | Go | Credenciales codificadas, inyeccion SQL, criptografia insegura, permisos de archivo inseguros |
| **Bandit** | Python | Contrasenas codificadas, inyeccion SQL, eval, criptografia debil |
| **Brakeman** | Ruby/Rails | Inyeccion SQL, XSS, mass assignment, inyeccion de comandos |
| **cargo-audit** | Rust | Dependencias vulnerables conocidas a traves de la base de datos RustSec |

## Documentacion

| Documento | Descripción |
|-----------|-------------|
| [Arquitectura](docs/es/architecture.md) | Diseño del sistema, diagrama de componentes, flujo de datos |
| [Esquema de Base de Datos](docs/es/database-schema.md) | Esquema SQLite, diagrama ER, índices |
| [Referencia de API](docs/es/api.md) | Endpoints REST API y autenticación |
| [Guía de Usuario](docs/es/user-guide.md) | Informes, hallazgos, quality gate, supresiones |
| [Guía de Administración](docs/es/admin-guide.md) | Configuración, variables de entorno, ajuste |
| [Guía DevOps](docs/es/devops-guide.md) | Despliegue con Docker, Jenkins, copias de seguridad |
| [Guía de Transferencia](docs/es/transfer-guide.md) | Procedimientos de migración de servidor |
| [Reglas Personalizadas](docs/es/custom-rules.md) | Escritura de reglas Semgrep personalizadas |

## Estado del Proyecto

Todas las fases de v1.0 completadas.

| Fase | Descripción | Estado |
|------|-------------|--------|
| 1 | Fundación y Modelos de Datos | Listo |
| 2 | Adaptadores de Escáner y Orquestación | Listo |
| 3 | Análisis con IA (Claude API) | Listo |
| 4 | Generación de Informes (HTML/PDF) | Listo |
| 5 | Panel de Control, Notificaciones y Quality Gate | Listo |
| 6 | Empaquetado, Portabilidad y Documentación | Listo |

## Stack Tecnológico

- **Python 3.12** -- lenguaje principal
- **FastAPI** -- REST API y panel de control web
- **SQLAlchemy 2.0** -- ORM asíncrono con SQLite
- **SQLite (modo WAL)** -- base de datos embebida
- **Pydantic v2** -- validación de datos y configuración
- **Docker** -- contenedorización
- **Alembic** -- migraciones de base de datos
- **Anthropic Claude** -- análisis de vulnerabilidades impulsado por IA
- **WeasyPrint** -- generación de informes PDF
- **Jinja2** -- plantillas HTML para informes y panel de control
- **Typer** -- interfaz de línea de comandos (CLI)

## Licencia

Apache 2.0

---

Documentacion en otros idiomas: [English](README.md) | [Русский](README.ru.md) | [Francais](README.fr.md) | [Italiano](README.it.md)
