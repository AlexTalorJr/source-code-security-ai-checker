# Схема базы данных

## Обзор

База данных SQLite с режимом WAL (Write-Ahead Logging) для параллельного чтения. Управляется асинхронным ORM SQLAlchemy 2.0 с миграциями Alembic.

## ER-диаграмма

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

## Модели

### ScanResult

Отслеживает одно выполнение сканирования от запуска до завершения. Хранит агрегированные счётчики по уровням серьёзности для быстрых запросов панели управления. Поле `gate_passed` фиксирует результат шлюза качества: пройден (1), не пройден (0) или не оценивался (NULL).

### Finding

Нормализованная уязвимость безопасности, обнаруженная одним из пяти инструментов сканирования. Каждая находка имеет детерминированный `fingerprint` (SHA-256 от нормализованного пути + rule_id + фрагмента кода) для кросс-скановой дедупликации. Поля ИИ-обогащения (`ai_analysis`, `ai_fix_suggestion`) заполняются после анализа Claude.

### CompoundRisk

Составной риск, выявленный ИИ, который охватывает несколько отдельных находок. Например, обход аутентификации в одном компоненте в сочетании с IDOR в другом. Связан с соответствующими находками через ассоциативную таблицу `compound_risk_findings` по fingerprint.

### Suppression

Отслеживает fingerprint-ы, помеченные как ложные срабатывания. Когда fingerprint находки совпадает с записью подавления, она исключается из оценки шлюза качества и счётчиков отчётов.

## Уровни серьёзности

| Значение | Название | Требуемое действие |
|---------|----------|-------------------|
| 5 | CRITICAL | Немедленное исправление, блокирует развёртывание |
| 4 | HIGH | Исправить до релиза |
| 3 | MEDIUM | Исправить в текущем спринте |
| 2 | LOW | Исправить при возможности |
| 1 | INFO | Информационное, действий не требуется |

## Индексы

| Таблица | Столбец(ы) | Назначение |
|---------|-----------|-----------|
| findings | scan_id | Быстрый поиск находок по сканированию |
| findings | fingerprint | Запросы дедупликации и подавления |
| compound_risks | scan_id | Быстрый поиск составных рисков по сканированию |
| suppressions | fingerprint | Быстрое сопоставление подавлений (уникальное ограничение) |

## Конфигурация SQLite

Применяется к каждому соединению через обработчики событий SQLAlchemy:

```sql
PRAGMA journal_mode=WAL;      -- Write-Ahead Logging для параллельного чтения
PRAGMA synchronous=NORMAL;     -- Баланс между безопасностью и скоростью
PRAGMA foreign_keys=ON;        -- Принудительное соблюдение ограничений FK
```

## Расположение базы данных

| Окружение | Путь |
|----------|------|
| Docker | `/data/scanner.db` (именованный том `scanner_data`) |
| Локальная разработка | Настраивается через переменную `SCANNER_DB_PATH` или `db_path` в `config.yml` |

## Миграции

Alembic настроен для миграций схемы. Таблицы автоматически создаются при запуске приложения через `Base.metadata.create_all()` в обработчике жизненного цикла FastAPI.

```bash
# Создание новой миграции
alembic revision --autogenerate -m "description"

# Применение миграций
alembic upgrade head
```
