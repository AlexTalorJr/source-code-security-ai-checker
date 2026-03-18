# Database Schema / Схема базы данных

## Overview / Обзор

SQLite database with WAL (Write-Ahead Logging) mode for concurrent read access. Managed by SQLAlchemy ORM with Alembic migrations.

База данных SQLite с режимом WAL для параллельного чтения. Управляется через SQLAlchemy ORM с миграциями Alembic.

## ER Diagram / ER-диаграмма

```mermaid
erDiagram
    scans ||--o{ findings : "has many"

    scans {
        int id PK "autoincrement"
        varchar target_path "nullable — local path"
        varchar repo_url "nullable — git URL"
        varchar branch "nullable"
        varchar commit_hash "nullable, 40 chars"
        varchar status "pending/running/completed/failed"
        datetime started_at "nullable"
        datetime completed_at "nullable"
        float duration_seconds "nullable"
        int total_findings "default 0"
        int critical_count "default 0"
        int high_count "default 0"
        int medium_count "default 0"
        int low_count "default 0"
        int info_count "default 0"
        int gate_passed "0=fail, 1=pass, NULL=not evaluated"
        varchar scanner_version "nullable"
        text tool_versions "nullable, JSON"
        text error_message "nullable"
        datetime created_at "auto"
    }

    findings {
        int id PK "autoincrement"
        int scan_id FK "references scans.id, indexed"
        varchar fingerprint "SHA-256 hex, 64 chars, indexed"
        varchar tool "semgrep/gitleaks/trivy/cppcheck/checkov"
        varchar rule_id "tool-specific rule identifier"
        varchar file_path "path in scanned repo"
        int line_start "nullable"
        int line_end "nullable"
        text snippet "nullable — code fragment"
        int severity "1=INFO, 2=LOW, 3=MEDIUM, 4=HIGH, 5=CRITICAL"
        varchar title "short description"
        text description "nullable — detailed explanation"
        text recommendation "nullable — fix suggestion"
        text ai_analysis "nullable — Claude AI analysis (Phase 3)"
        text ai_fix_suggestion "nullable — AI fix code (Phase 3)"
        int false_positive "0=no, 1=yes (Phase 5)"
        datetime created_at "auto"
    }
```

## Severity Levels / Уровни серьёзности

| Value | Name | Description (EN) | Описание (RU) |
|-------|------|-------------------|---------------|
| 5 | CRITICAL | Immediate exploitation risk | Непосредственный риск эксплуатации |
| 4 | HIGH | Serious vulnerability | Серьёзная уязвимость |
| 3 | MEDIUM | Moderate risk | Умеренный риск |
| 2 | LOW | Minor issue | Незначительная проблема |
| 1 | INFO | Informational finding | Информационная находка |

## SQLite Pragmas / Настройки SQLite

Applied on every connection / Применяются при каждом соединении:

```sql
PRAGMA journal_mode=WAL;      -- Write-Ahead Logging for concurrent reads
PRAGMA synchronous=NORMAL;     -- Balance between safety and speed
PRAGMA foreign_keys=ON;        -- Enforce FK constraints
```

## Indexes / Индексы

| Table | Column | Purpose / Назначение |
|-------|--------|---------------------|
| findings | scan_id | Fast lookup by scan / Быстрый поиск по скану |
| findings | fingerprint | Deduplication queries / Запросы дедупликации |

## Database Location / Расположение БД

| Environment | Path |
|-------------|------|
| Docker | `/data/scanner.db` (named volume `scanner_data`) |
| Local dev | Configured via `SCANNER_DB_PATH` env var or `config.yml` |

## Migrations / Миграции

Alembic is configured but not yet active. In Phase 1, tables are auto-created on application startup via `Base.metadata.create_all()`. Full Alembic migrations will be used starting from Phase 2.

Alembic настроен, но пока не активен. В Фазе 1 таблицы создаются автоматически при запуске через `Base.metadata.create_all()`. Полноценные миграции Alembic будут использоваться начиная с Фазы 2.

```bash
# Future usage / Будущее использование:
alembic revision --autogenerate -m "description"
alembic upgrade head
```
