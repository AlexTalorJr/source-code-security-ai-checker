# Architecture

## Overview

Security AI Scanner is a multi-layer security scanning pipeline for the aipix.ai VSaaS platform. It scans source code repositories for vulnerabilities using five parallel static analysis tools, enriches findings with AI-powered analysis via Claude, and produces actionable reports with fix suggestions. A configurable quality gate can block deployments when critical issues are found.

## Component Diagram

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
            SEM[Semgrep Adapter]
            CPP[cppcheck Adapter]
            GLK[Gitleaks Adapter]
            TRV[Trivy Adapter]
            CHK[Checkov Adapter]
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
        ORCH --> SEM
        ORCH --> CPP
        ORCH --> GLK
        ORCH --> TRV
        ORCH --> CHK
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

## Data Flow

The scan lifecycle from API trigger to notification:

```mermaid
sequenceDiagram
    participant U as User/Jenkins
    participant API as FastAPI
    participant Q as Scan Queue
    participant O as Orchestrator
    participant S as Scanners (x5)
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
    O->>S: Run 5 tools in parallel (asyncio.gather)
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

## Technology Choices

| Technology | Purpose | Rationale |
|-----------|---------|-----------|
| SQLite (WAL) | Database | Portability -- single file, no external dependencies, concurrent reads |
| Async SQLAlchemy | ORM | Non-blocking DB operations for FastAPI async handlers |
| Pydantic v2 | Validation | Strict typing at API boundary, separate from ORM models |
| FastAPI | API + Dashboard | Async support, auto-generated OpenAPI docs, dependency injection |
| asyncio.gather | Scanner parallelism | Run 5 tools concurrently without threading overhead |
| Fingerprinting | Dedup | SHA-256 hash of path+rule+snippet for cross-scan deduplication |
| WeasyPrint | PDF generation | Pure Python, CSS-based layout for report PDFs |
| Jinja2 PackageLoader | Templates | Discover templates within installed scanner package |
| matplotlib (Agg) | Charts | Headless server-side chart rendering as base64 PNG data URIs |
| Typer | CLI | Subcommand-based CLI for direct scan execution |

## Security Model

- **API key authentication** -- all scan endpoints require `X-API-Key` header, validated with `secrets.compare_digest` for timing-safe comparison
- **Non-root Docker user** -- the `scanner` user runs the application inside the container
- **Secrets via environment** -- API keys and SMTP passwords are never stored in config files; they use `SCANNER_*` environment variables
- **Read-only config mount** -- `config.yml` is mounted as read-only in Docker

## Configuration

All settings follow a priority chain: constructor arguments > environment variables (`SCANNER_*` prefix) > `.env` file > Docker secrets > `config.yml` (lowest priority).

Key environment variables:

| Variable | Purpose |
|----------|---------|
| `SCANNER_API_KEY` | API authentication key |
| `SCANNER_CLAUDE_API_KEY` | Anthropic API key for AI analysis |
| `SCANNER_DB_PATH` | SQLite database file path |
| `SCANNER_PORT` | Server listen port |
| `SCANNER_CONFIG_PATH` | Path to YAML config file |

See the [Admin Guide](admin-guide.md) for complete configuration reference.
