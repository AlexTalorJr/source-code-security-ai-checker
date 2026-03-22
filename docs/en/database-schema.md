# Database Schema

## Overview

SQLite database with WAL (Write-Ahead Logging) mode for concurrent read access. Managed by SQLAlchemy 2.0 async ORM with Alembic migrations.

## ER Diagram

```mermaid
erDiagram
    scans ||--o{ findings : "has many"
    scans ||--o{ compound_risks : "has many"
    compound_risks ||--o{ compound_risk_findings : "linked via"

    scans {
        int id PK "autoincrement"
        varchar target_path "nullable -- local path"
        varchar repo_url "nullable -- git URL"
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
        float ai_cost_usd "nullable"
        datetime created_at "auto"
    }

    findings {
        int id PK "autoincrement"
        int scan_id FK "references scans.id, indexed"
        varchar fingerprint "SHA-256 hex, 64 chars, indexed"
        varchar tool "semgrep/cppcheck/gitleaks/trivy/checkov/psalm/enlightn/php_security_checker/gosec/bandit/brakeman/cargo_audit"
        varchar rule_id "tool-specific rule identifier"
        varchar file_path "path in scanned repo"
        int line_start "nullable"
        int line_end "nullable"
        text snippet "nullable -- code fragment"
        int severity "1=INFO, 2=LOW, 3=MEDIUM, 4=HIGH, 5=CRITICAL"
        varchar title "short description"
        text description "nullable -- detailed explanation"
        text recommendation "nullable -- fix suggestion"
        text ai_analysis "nullable -- Claude AI analysis"
        text ai_fix_suggestion "nullable -- AI fix code"
        int false_positive "0=no, 1=yes"
        datetime created_at "auto"
    }

    compound_risks {
        int id PK "autoincrement"
        int scan_id FK "references scans.id, indexed"
        varchar title "short description"
        text description "detailed explanation"
        int severity "1=INFO to 5=CRITICAL"
        varchar risk_category "nullable -- e.g. auth_bypass, data_leak"
        text recommendation "nullable"
    }

    compound_risk_findings {
        int compound_risk_id FK "references compound_risks.id"
        varchar finding_fingerprint "SHA-256 fingerprint"
    }

    suppressions {
        int id PK "autoincrement"
        varchar fingerprint "SHA-256, unique, indexed"
        text reason "nullable"
        varchar suppressed_by "default api"
        datetime created_at "auto"
    }
```

## Models

### ScanResult

Tracks a single scan execution from trigger to completion. Stores aggregate severity counts for fast dashboard queries. The `gate_passed` field records whether the quality gate passed (1), failed (0), or was not evaluated (NULL).

### Finding

A normalized security vulnerability found by one of the twelve scanner tools. Each finding has a deterministic `fingerprint` (SHA-256 of normalized path + rule_id + snippet) for cross-scan deduplication. AI enrichment fields (`ai_analysis`, `ai_fix_suggestion`) are populated after Claude analysis.

### CompoundRisk

An AI-identified compound risk that spans multiple individual findings. For example, an authentication bypass in one component combined with an IDOR in another. Linked to related findings via the `compound_risk_findings` association table using fingerprints.

### Suppression

Tracks fingerprints that have been marked as false positives. When a finding's fingerprint matches a suppression record, it is excluded from quality gate evaluation and report counts.

## Severity Levels

| Value | Name | Action Required |
|-------|------|-----------------|
| 5 | CRITICAL | Fix immediately, blocks deployment |
| 4 | HIGH | Fix before release |
| 3 | MEDIUM | Fix in current sprint |
| 2 | LOW | Fix when convenient |
| 1 | INFO | Informational, no action needed |

## Indexes

| Table | Column(s) | Purpose |
|-------|-----------|---------|
| findings | scan_id | Fast lookup of findings by scan |
| findings | fingerprint | Deduplication and suppression queries |
| compound_risks | scan_id | Fast lookup of compound risks by scan |
| suppressions | fingerprint | Fast suppression matching (unique constraint) |

## SQLite Configuration

Applied on every connection via SQLAlchemy event listeners:

```sql
PRAGMA journal_mode=WAL;      -- Write-Ahead Logging for concurrent reads
PRAGMA synchronous=NORMAL;     -- Balance between safety and speed
PRAGMA foreign_keys=ON;        -- Enforce FK constraints
```

## Database Location

| Environment | Path |
|-------------|------|
| Docker | `/data/scanner.db` (named volume `scanner_data`) |
| Local dev | Configured via `SCANNER_DB_PATH` env var or `db_path` in `config.yml` |

## Migrations

Alembic is configured for schema migrations. Tables are auto-created on application startup via `Base.metadata.create_all()` in the FastAPI lifespan handler.

```bash
# Generate a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```
