# Architecture / Архитектура

## Overview / Обзор

aipix-security-scanner is a multi-layer security scanning pipeline. It scans source code for vulnerabilities using static analysis tools, enriches findings with AI analysis, and produces reports with fix suggestions.

aipix-security-scanner — многоуровневый конвейер сканирования безопасности. Сканирует исходный код на уязвимости с помощью инструментов статического анализа, обогащает результаты ИИ-анализом и генерирует отчёты с предложениями по исправлению.

## Component Diagram / Диаграмма компонентов

```mermaid
graph TB
    subgraph Docker Container
        API[FastAPI API Server<br/>:8000]
        subgraph Core
            CFG[Config System<br/>YAML + Env vars]
            FP[Fingerprint Module<br/>SHA-256 dedup]
        end
        subgraph Schemas
            SEV[Severity Enum<br/>CRITICAL..INFO]
            FS[FindingSchema]
            SS[ScanResultSchema]
        end
        subgraph Persistence
            ORM[SQLAlchemy ORM<br/>Finding, ScanResult]
            DB[(SQLite<br/>WAL mode)]
            ALM[Alembic<br/>Migrations]
        end
        API --> CFG
        API --> ORM
        ORM --> DB
        FS --> SEV
        ORM --> FS
    end

    User([User / Jenkins]) -->|HTTP| API
    API -->|GET /api/health| DB

    style Docker Container fill:#f0f4ff,stroke:#3366cc
    style DB fill:#fff3cd,stroke:#ffc107
```

## Data Flow / Поток данных

```mermaid
sequenceDiagram
    participant U as User/Jenkins
    participant API as FastAPI
    participant DB as SQLite

    Note over API: Planned for Phase 2+
    U->>API: POST /api/scans (trigger scan)
    API->>DB: Create ScanResult (status=pending)
    Note over API: Run scanner tools in parallel
    API->>DB: Insert Finding records
    API->>DB: Update ScanResult (status=completed)
    U->>API: GET /api/scans/{id}
    API->>DB: Query results
    API-->>U: ScanResult + Findings

    Note over U,DB: Currently implemented (Phase 1)
    U->>API: GET /api/health
    API->>DB: SELECT 1 (probe)
    API-->>U: {"status": "healthy"}
```

## Layered Scanning Approach / Многоуровневый подход

| Layer / Уровень | Tools / Инструменты | Time / Время | Status / Статус |
|-------|-------|------|--------|
| 1 — Static Analysis | Semgrep, cppcheck, Gitleaks, Trivy, Checkov | 2-4 min | Planned (Phase 2) |
| 2 — AI Analysis | Claude API (semantic review) | 1-2 min | Planned (Phase 3) |
| 3 — Reporting | Jinja2 + WeasyPrint (HTML/PDF) | <30s | Planned (Phase 4) |
| Quality Gate | Severity threshold check | <1s | Planned (Phase 5) |

## Current State (Phase 1) / Текущее состояние (Фаза 1)

Implemented / Реализовано:
- **Config system** — YAML file + environment variable overrides (SCANNER_* prefix)
- **Pydantic schemas** — FindingSchema, ScanResultSchema, Severity enum
- **Fingerprint module** — deterministic SHA-256 hashing for finding deduplication
- **SQLAlchemy ORM** — Finding and ScanResult models with async SQLite/WAL
- **FastAPI** — application factory with health endpoint (`GET /api/health`)
- **Alembic** — migration skeleton (tables auto-created on startup for now)
- **Docker** — single `docker compose up` deployment

## Key Design Decisions / Ключевые архитектурные решения

| Decision / Решение | Rationale / Обоснование |
|---------|-----------|
| SQLite over PostgreSQL | Portability — single file, no external dependencies / Портативность — один файл, без внешних зависимостей |
| WAL mode | Allows concurrent reads during writes / Параллельное чтение при записи |
| Async SQLAlchemy | Non-blocking DB operations for FastAPI / Неблокирующие операции с БД |
| Pydantic v2 schemas | Validation at API boundary, separate from ORM models / Валидация на границе API, отдельно от ORM |
| Deterministic fingerprints | Dedup findings across scans by normalizing path+rule+snippet / Дедупликация находок между сканами |
| Non-root Docker user | Security best practice / Практика безопасности |
