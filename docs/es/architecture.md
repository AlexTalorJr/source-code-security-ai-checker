# Arquitectura

## Descripción General

Security AI Scanner es un pipeline de seguridad multicapa para la plataforma VSaaS de aipix.ai. Analiza repositorios de codigo fuente en busca de vulnerabilidades utilizando doce herramientas de escaneo de seguridad en paralelo, enriquece los hallazgos con analisis impulsado por IA a traves de Claude, y produce informes accionables con sugerencias de correccion. Los escaneres se cargan dinamicamente a traves de un registro de plugins basado en la configuracion. Un quality gate configurable puede bloquear despliegues cuando se encuentran problemas criticos.

## Diagrama de Componentes

```mermaid
graph TB
    subgraph Docker Container
        API[FastAPI API Server<br/>:8000]

        subgraph Core
            CFG[Config System<br/>YAML + Env vars]
            FP[Fingerprint Module<br/>SHA-256 dedup]
            QUEUE[Scan Queue<br/>asyncio.Queue]
        end

        subgraph Scanner Orchestrator
            ORCH[Orchestrator<br/>parallel execution]
            REG[ScannerRegistry<br/>config-driven loading]
            SEM[Semgrep Adapter]
            CPP[cppcheck Adapter]
            GLK[Gitleaks Adapter]
            TRV[Trivy Adapter]
            CHK[Checkov Adapter]
            PSA[Psalm Adapter]
            ENL[Enlightn Adapter]
            PSC[PHP Security Checker]
            GSC[gosec Adapter]
            BND[Bandit Adapter]
            BRK[Brakeman Adapter]
            CGA[cargo-audit Adapter]
        end

        subgraph AI Analysis
            AI[AI Analyzer<br/>Claude API]
            CR[Compound Risk<br/>Detection]
        end

        subgraph Reports
            HTML[HTML Report<br/>Jinja2 template]
            PDF[PDF Report<br/>WeasyPrint]
            CHARTS[Charts<br/>matplotlib]
        end

        subgraph Quality Gate
            GATE[Gate Evaluator<br/>severity thresholds]
        end

        subgraph Dashboard
            DASH[Web Dashboard<br/>scan history + controls]
        end

        subgraph Notifications
            NOTIF[Notification Dispatcher]
            SLACK[Slack Webhook]
            EMAIL[Email SMTP]
        end

        subgraph Persistence
            ORM[SQLAlchemy ORM<br/>async sessions]
            DB[(SQLite<br/>WAL mode)]
            ALM[Alembic<br/>Migrations]
        end

        API --> CFG
        API --> QUEUE
        QUEUE --> ORCH
        ORCH --> REG
        REG --> SEM
        REG --> CPP
        REG --> GLK
        REG --> TRV
        REG --> CHK
        REG --> PSA
        REG --> ENL
        REG --> PSC
        REG --> GSC
        REG --> BND
        REG --> BRK
        REG --> CGA
        ORCH --> AI
        AI --> CR
        ORCH --> GATE
        ORCH --> HTML
        ORCH --> PDF
        HTML --> CHARTS
        PDF --> CHARTS
        ORCH --> NOTIF
        NOTIF --> SLACK
        NOTIF --> EMAIL
        API --> DASH
        API --> ORM
        ORM --> DB
        ALM --> DB
    end

    User([User / Jenkins]) -->|HTTP| API
    CLI([CLI<br/>Typer]) -->|Direct call| ORCH

    style Docker Container fill:#f0f4ff,stroke:#3366cc
    style DB fill:#fff3cd,stroke:#ffc107
```

## Flujo de Datos

El ciclo de vida del escaneo desde el disparador de la API hasta la notificación:

```mermaid
sequenceDiagram
    participant U as User/Jenkins
    participant API as FastAPI
    participant Q as Scan Queue
    participant O as Orchestrator
    participant S as Scanners (x12)
    participant AI as AI Analyzer
    participant G as Quality Gate
    participant R as Report Generator
    participant N as Notifications
    participant DB as SQLite

    U->>API: POST /api/scans (trigger scan)
    API->>DB: Create ScanResult (status=pending)
    API->>Q: Enqueue scan job
    API-->>U: 202 Accepted (scan_id)

    Q->>O: Dequeue and execute
    O->>DB: Update status=running
    O->>S: Run 12 tools in parallel (asyncio.gather)
    S-->>O: Raw findings per tool
    O->>O: Normalize + fingerprint + deduplicate
    O->>DB: Insert Finding records

    O->>AI: Send findings batch to Claude
    AI-->>O: AI analysis + fix suggestions + compound risks
    O->>DB: Update findings with AI data
    O->>DB: Insert CompoundRisk records

    O->>G: Evaluate quality gate
    G-->>O: pass/fail
    O->>DB: Update gate_passed, counts, status=completed

    O->>R: Generate HTML + PDF reports
    O->>N: Send Slack/email notifications

    U->>API: GET /api/scans/{id}
    API->>DB: Query results
    API-->>U: ScanResult + Findings + CompoundRisks
```

## Decisiones Tecnológicas

| Tecnología | Propósito | Justificación |
|-----------|---------|-----------|
| SQLite (WAL) | Base de datos | Portabilidad -- archivo único, sin dependencias externas, lecturas concurrentes |
| Async SQLAlchemy | ORM | Operaciones de BD no bloqueantes para los manejadores asíncronos de FastAPI |
| Pydantic v2 | Validación | Tipado estricto en la frontera de la API, separado de los modelos ORM |
| FastAPI | API + Dashboard | Soporte asíncrono, documentación OpenAPI autogenerada, inyección de dependencias |
| asyncio.gather | Paralelismo de escaneres | Ejecutar 12 herramientas concurrentemente sin overhead de hilos |
| Fingerprinting | Deduplicación | Hash SHA-256 de ruta+regla+fragmento para deduplicación entre escaneos |
| WeasyPrint | Generación de PDF | Python puro, diseño basado en CSS para los PDF de informes |
| Jinja2 PackageLoader | Plantillas | Descubre plantillas dentro del paquete del escáner instalado |
| matplotlib (Agg) | Gráficos | Renderizado de gráficos sin cabeza en el servidor como URI de datos PNG en base64 |
| Typer | CLI | CLI basada en subcomandos para ejecución directa de escaneos |

## Modelo de Seguridad

- **Autenticacion mediante token Bearer** -- todos los endpoints de la API (excepto /api/health) requieren un token Bearer valido en el encabezado Authorization; los tokens se generan por usuario desde el panel de control
- **Usuario Docker sin privilegios root** -- el usuario `scanner` ejecuta la aplicación dentro del contenedor
- **Secretos vía entorno** -- las claves API y contraseñas SMTP nunca se almacenan en archivos de configuración; se utilizan las variables de entorno `SCANNER_*`
- **Montaje de configuración en solo lectura** -- `config.yml` se monta como solo lectura en Docker

## Configuración

Todos los ajustes siguen una cadena de prioridad: argumentos del constructor > variables de entorno (prefijo `SCANNER_*`) > archivo `.env` > secretos de Docker > `config.yml` (menor prioridad).

Variables de entorno clave:

| Variable | Propósito |
|----------|---------|
| `SCANNER_API_KEY` | Clave de autenticación de la API |
| `SCANNER_CLAUDE_API_KEY` | Clave API de Anthropic para el análisis con IA |
| `SCANNER_DB_PATH` | Ruta al archivo de base de datos SQLite |
| `SCANNER_PORT` | Puerto de escucha del servidor |
| `SCANNER_CONFIG_PATH` | Ruta al archivo de configuración YAML |

Consulte la [Guía de Administración](admin-guide.md) para la referencia completa de configuración.
