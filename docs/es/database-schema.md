# Esquema de Base de Datos

## Descripción General

Base de datos SQLite en modo WAL (Write-Ahead Logging) para acceso de lectura concurrente. Gestionada por el ORM asíncrono de SQLAlchemy 2.0 con migraciones de Alembic.

## Diagrama ER

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
        varchar tool "semgrep/gitleaks/trivy/cppcheck/checkov"
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

## Modelos

### ScanResult

Registra una ejecución individual de escaneo desde su inicio hasta su finalización. Almacena recuentos agregados de severidad para consultas rápidas en el panel de control. El campo `gate_passed` indica si el quality gate pasó (1), falló (0), o no fue evaluado (NULL).

### Finding

Una vulnerabilidad de seguridad normalizada encontrada por una de las cinco herramientas de escaneo. Cada hallazgo tiene un `fingerprint` determinístico (SHA-256 de ruta normalizada + rule_id + fragmento) para deduplicación entre escaneos. Los campos de enriquecimiento con IA (`ai_analysis`, `ai_fix_suggestion`) se completan tras el análisis con Claude.

### CompoundRisk

Un riesgo compuesto identificado por IA que abarca múltiples hallazgos individuales. Por ejemplo, una omisión de autenticación en un componente combinada con un IDOR en otro. Se vincula a los hallazgos relacionados a través de la tabla de asociación `compound_risk_findings` usando fingerprints.

### Suppression

Registra los fingerprints que han sido marcados como falsos positivos. Cuando el fingerprint de un hallazgo coincide con un registro de supresión, este queda excluido de la evaluación del quality gate y de los recuentos en los informes.

## Niveles de Severidad

| Valor | Nombre | Acción Requerida |
|-------|------|-----------------|
| 5 | CRITICAL | Corregir de inmediato, bloquea el despliegue |
| 4 | HIGH | Corregir antes del lanzamiento |
| 3 | MEDIUM | Corregir en el sprint actual |
| 2 | LOW | Corregir cuando sea conveniente |
| 1 | INFO | Informativo, no requiere acción |

## Índices

| Tabla | Columna(s) | Propósito |
|-------|-----------|---------|
| findings | scan_id | Búsqueda rápida de hallazgos por escaneo |
| findings | fingerprint | Consultas de deduplicación y supresión |
| compound_risks | scan_id | Búsqueda rápida de riesgos compuestos por escaneo |
| suppressions | fingerprint | Coincidencia rápida de supresiones (restricción única) |

## Configuración de SQLite

Aplicada en cada conexión mediante event listeners de SQLAlchemy:

```sql
PRAGMA journal_mode=WAL;      -- Write-Ahead Logging for concurrent reads
PRAGMA synchronous=NORMAL;     -- Balance between safety and speed
PRAGMA foreign_keys=ON;        -- Enforce FK constraints
```

## Ubicación de la Base de Datos

| Entorno | Ruta |
|-------------|------|
| Docker | `/data/scanner.db` (volumen con nombre `scanner_data`) |
| Desarrollo local | Configurado vía variable de entorno `SCANNER_DB_PATH` o `db_path` en `config.yml` |

## Migraciones

Alembic está configurado para las migraciones del esquema. Las tablas se crean automáticamente al iniciar la aplicación mediante `Base.metadata.create_all()` en el manejador del lifespan de FastAPI.

```bash
# Generate a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```
