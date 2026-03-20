# Codebase Structure

**Analysis Date:** 2026-03-20

## Directory Layout

```
naveksoft-security/
├── src/
│   └── scanner/                    # Main Python package (installed as 'scanner')
│       ├── __init__.py
│       ├── __main__.py             # Entry point: python -m scanner
│       ├── main.py                 # FastAPI app factory and lifespan
│       ├── config.py               # ScannerSettings (pydantic-settings + YAML)
│       ├── adapters/               # External scanner tool wrappers
│       │   ├── base.py             # ScannerAdapter abstract class
│       │   ├── semgrep.py
│       │   ├── cppcheck.py
│       │   ├── gitleaks.py
│       │   ├── trivy.py
│       │   └── checkov.py
│       ├── ai/                     # Claude AI enrichment layer
│       │   ├── analyzer.py         # AIAnalyzer class
│       │   ├── cost.py             # Token budget helpers
│       │   ├── prompts.py          # Prompt builders and tool specs
│       │   └── schemas.py          # AI response schemas
│       ├── api/                    # REST JSON API (FastAPI routers)
│       │   ├── router.py           # Aggregates sub-routers
│       │   ├── scans.py            # /api/scans endpoints
│       │   ├── findings.py         # /api/findings endpoints
│       │   ├── health.py           # /api/health endpoint
│       │   ├── auth.py             # API key dependency
│       │   └── schemas.py          # API request/response Pydantic models
│       ├── cli/
│       │   └── main.py             # Typer CLI (scanner scan command)
│       ├── core/                   # Business logic and cross-cutting utilities
│       │   ├── orchestrator.py     # run_scan(), deduplication, AI call
│       │   ├── scan_queue.py       # ScanQueue async worker
│       │   ├── fingerprint.py      # SHA-256 fingerprint computation
│       │   ├── git.py              # clone_repo(), cleanup_clone()
│       │   ├── suppression.py      # Suppression CRUD functions
│       │   └── exceptions.py       # ScannerError hierarchy
│       ├── dashboard/              # Server-rendered HTML UI (Jinja2)
│       │   ├── router.py           # All page handlers and form actions
│       │   ├── auth.py             # Cookie session helpers
│       │   └── templates/          # Jinja2 HTML templates (.html.j2)
│       │       ├── base.html.j2
│       │       ├── login.html.j2
│       │       ├── history.html.j2
│       │       ├── detail.html.j2
│       │       └── trends.html.j2
│       ├── db/
│       │   └── session.py          # Async SQLAlchemy engine + session factory
│       ├── models/                 # SQLAlchemy ORM models
│       │   ├── base.py             # Declarative base
│       │   ├── scan.py             # ScanResult
│       │   ├── finding.py          # Finding
│       │   ├── compound_risk.py    # CompoundRisk + association table
│       │   └── suppression.py      # Suppression
│       ├── notifications/          # Post-scan notification channels
│       │   ├── service.py          # Dispatcher (notify_scan_complete)
│       │   ├── slack.py            # Slack webhook sender
│       │   ├── email_sender.py     # SMTP email sender
│       │   └── templates/
│       │       └── email.html.j2   # Email HTML template
│       ├── reports/                # Report generation (HTML + PDF)
│       │   ├── html_report.py      # generate_html_report()
│       │   ├── pdf_report.py       # generate_pdf_report()
│       │   ├── charts.py           # Matplotlib chart helpers
│       │   ├── delta.py            # compute_delta() finding comparison
│       │   ├── models.py           # ReportData, DeltaResult dataclasses
│       │   └── templates/
│       │       ├── report.html.j2
│       │       └── report_pdf.html.j2
│       └── schemas/                # Pydantic in-memory data contracts
│           ├── finding.py          # FindingSchema
│           ├── scan.py             # ScanResultSchema
│           ├── compound_risk.py    # CompoundRiskSchema
│           └── severity.py         # Severity IntEnum
├── tests/
│   ├── phase_01/                   # Foundation and data model tests
│   ├── phase_02/                   # Adapter and orchestrator tests (+ fixtures/)
│   ├── phase_03/                   # AI analysis tests
│   ├── phase_04/                   # Report generation tests
│   ├── phase_05/                   # API, dashboard, notifications, CI tests
│   └── phase_06/                   # Packaging, docs, backup/restore tests
├── alembic/                        # Database migration tooling
│   ├── env.py
│   └── versions/                   # Migration scripts (001_add_skip_ai_to_scans.py)
├── docs/                           # Bilingual documentation
│   ├── en/                         # English docs (api.md, architecture.md, etc.)
│   ├── es/                         # Spanish
│   ├── fr/                         # French
│   ├── it/                         # Italian
│   └── ru/                         # Russian
├── reports/                        # Default output directory for CLI-generated reports
├── backups/                        # Database backup directory (root-owned)
├── .planning/                      # GSD planning artifacts (not shipped)
│   ├── codebase/                   # Codebase analysis documents
│   ├── phases/                     # Per-phase implementation plans
│   └── research/                   # Research notes
├── Dockerfile                      # Single-stage Python 3.12 image
├── docker-compose.yml              # Service + volume definition
├── Makefile                        # Developer task runner
├── pyproject.toml                  # Package manifest (hatchling build)
├── config.yml                      # Runtime configuration (loaded by ScannerSettings)
├── config.yml.example              # Example config template
├── alembic.ini                     # Alembic migration configuration
├── Jenkinsfile.security            # Jenkins CI pipeline
├── CHANGELOG.md                    # Version history
├── CONTRIBUTING.md
└── README.md / README.*.md         # Multilingual READMEs
```

## Directory Purposes

**`src/scanner/adapters/`:**
- Purpose: One file per external scanner tool; each implements `ScannerAdapter`
- Contains: Tool invocation, output parsing, `FindingSchema` normalization
- Key files: `src/scanner/adapters/base.py` (contract), `src/scanner/adapters/__init__.py` (exports `ALL_ADAPTERS` list)

**`src/scanner/ai/`:**
- Purpose: All Anthropic Claude integration code isolated here
- Contains: Analyzer orchestration, prompt building, cost/budget math, response schemas
- Key files: `src/scanner/ai/analyzer.py` (primary), `src/scanner/ai/prompts.py` (tool specs), `src/scanner/ai/cost.py`

**`src/scanner/api/`:**
- Purpose: REST endpoints only; no business logic — delegates to core orchestrator
- Contains: FastAPI routers, API-layer Pydantic schemas, auth dependency
- Key files: `src/scanner/api/scans.py` (scan lifecycle), `src/scanner/api/auth.py`

**`src/scanner/core/`:**
- Purpose: All domain logic; adapters and AI are called from here
- Contains: Scan execution, queuing, fingerprinting, git operations, suppression
- Key files: `src/scanner/core/orchestrator.py` (central), `src/scanner/core/scan_queue.py`

**`src/scanner/dashboard/`:**
- Purpose: Human-facing web UI; reads from DB, renders Jinja2 templates
- Contains: Route handlers, form actions, cookie auth, Jinja2 environment
- Key files: `src/scanner/dashboard/router.py`, `src/scanner/dashboard/templates/`

**`src/scanner/models/`:**
- Purpose: Database schema definition (SQLAlchemy declarative); one file per table
- Contains: ORM model classes only; no query logic (queries live in the layer that needs them)
- Key files: `src/scanner/models/base.py`, `src/scanner/models/scan.py`, `src/scanner/models/finding.py`

**`src/scanner/schemas/`:**
- Purpose: In-memory Pydantic contracts; separate from ORM models
- Contains: `FindingSchema`, `ScanResultSchema`, `CompoundRiskSchema`, `Severity`
- Key files: `src/scanner/schemas/finding.py`, `src/scanner/schemas/severity.py`

**`src/scanner/reports/`:**
- Purpose: Standalone report generation; no side effects beyond writing files or returning HTML
- Contains: HTML/PDF generators, chart builders, delta logic, data contracts
- Key files: `src/scanner/reports/models.py` (input contract), `src/scanner/reports/html_report.py`

**`src/scanner/notifications/`:**
- Purpose: Outbound notifications after scan completion; isolated for testability
- Contains: Dispatcher, Slack webhook, SMTP email, Jinja2 email template
- Key files: `src/scanner/notifications/service.py`

**`tests/phase_NN/`:**
- Purpose: Autonomous test suite per development phase; each phase is self-contained
- Contains: `conftest.py`, test modules, and `fixtures/` with JSON/XML tool output samples
- Key files: `tests/phase_02/fixtures/` (real scanner output files for adapter tests)

**`docs/<lang>/`:**
- Purpose: Bilingual documentation; maintained in five languages (en, es, fr, it, ru)
- Contains: api.md, architecture.md, user-guide.md, admin-guide.md, devops-guide.md, custom-rules.md, database-schema.md, transfer-guide.md

## Key File Locations

**Entry Points:**
- `src/scanner/main.py`: FastAPI `app` object (`create_app()`) and lifespan
- `src/scanner/__main__.py`: CLI dispatch (`python -m scanner`)
- `src/scanner/cli/main.py`: Typer CLI command definitions

**Configuration:**
- `src/scanner/config.py`: All settings classes
- `config.yml`: Runtime configuration file (loaded at startup)
- `config.yml.example`: Documentation of all available settings
- `.env.example`: Documents required environment variable overrides

**Core Logic:**
- `src/scanner/core/orchestrator.py`: `run_scan()` — central execution function
- `src/scanner/core/scan_queue.py`: `ScanQueue` — background worker
- `src/scanner/adapters/__init__.py`: `ALL_ADAPTERS` list — registry of enabled tools

**Database:**
- `src/scanner/db/session.py`: Engine creation with WAL mode
- `src/scanner/models/base.py`: SQLAlchemy `Base`
- `alembic/versions/`: Migration scripts

**Testing:**
- `tests/phase_02/fixtures/`: JSON and XML files with real scanner tool output (used in adapter unit tests)
- `tests/phase_NN/conftest.py`: Phase-specific pytest fixtures

## Naming Conventions

**Files:**
- All snake_case: `html_report.py`, `scan_queue.py`, `email_sender.py`
- Adapter files named after the tool: `semgrep.py`, `gitleaks.py`
- Test files prefixed `test_`: `test_orchestrator.py`, `test_adapter_semgrep.py`
- Jinja2 templates use `.html.j2` extension: `report.html.j2`, `detail.html.j2`
- Fixture files named after the tool they represent: `semgrep_output.json`

**Directories:**
- All lowercase snake_case: `scan_queue`, `compound_risk`, `email_sender`
- No plural directories (model not models, schema not schemas — exception: `models/`, `schemas/` are pluralised for package conventions)

**Classes:**
- PascalCase: `ScannerAdapter`, `AIAnalyzer`, `ScanQueue`, `ScannerSettings`
- Schema classes suffixed `Schema`: `FindingSchema`, `ScanResultSchema`
- ORM model classes match the concept without suffix: `Finding`, `ScanResult`, `CompoundRisk`
- Config classes suffixed `Config`: `AIConfig`, `GateConfig`, `ScannerToolConfig`
- Adapter classes suffixed `Adapter`: `SemgrepAdapter`, `TrivyAdapter`

**Functions:**
- All snake_case; async functions use plain names (no `async_` prefix)
- Orchestrator functions are module-level: `run_scan()`, `deduplicate_findings()`, `enrich_with_ai()`
- Internal helpers prefixed `_`: `_run_adapter()`, `_apply_schema_updates()`, `_on_tool_complete()`

## Where to Add New Code

**New Scanner Tool Adapter:**
- Implementation: `src/scanner/adapters/<toolname>.py` — subclass `ScannerAdapter`
- Register: Add to `ALL_ADAPTERS` list in `src/scanner/adapters/__init__.py`
- Config: Add `<toolname>: ScannerToolConfig` field to `ScannersConfig` in `src/scanner/config.py`
- Tests: `tests/phase_02/test_adapter_<toolname>.py` + fixture in `tests/phase_02/fixtures/<toolname>_output.json`

**New API Endpoint:**
- Implementation: New file or addition to existing router in `src/scanner/api/`
- Register: Include router in `src/scanner/api/router.py`
- Schemas: Add request/response models to `src/scanner/api/schemas.py`
- Tests: `tests/phase_05/test_<feature>.py`

**New Dashboard Page:**
- Route handler: Add to `src/scanner/dashboard/router.py`
- Template: `src/scanner/dashboard/templates/<page>.html.j2`
- Tests: `tests/phase_05/test_dashboard.py`

**New Database Table:**
- ORM model: `src/scanner/models/<name>.py` inheriting from `Base`
- Migration: `alembic/versions/<NNN>_<description>.py` OR inline in `main.py` `_apply_schema_updates()` for lightweight additions
- Schema: `src/scanner/schemas/<name>.py` for the Pydantic counterpart

**New Notification Channel:**
- Sender: `src/scanner/notifications/<channel>.py`
- Config: Add config model to `NotificationsConfig` in `src/scanner/config.py`
- Register: Add dispatch call in `src/scanner/notifications/service.py`
- Tests: `tests/phase_05/test_notifications.py`

**New Report Section:**
- Logic: Add to `src/scanner/reports/html_report.py` or `pdf_report.py`
- Data contract: Extend `ReportData` dataclass in `src/scanner/reports/models.py` if new input data needed
- Template: Update `src/scanner/reports/templates/report.html.j2` or `report_pdf.html.j2`
- Tests: `tests/phase_04/test_html_report.py` or `test_pdf_report.py`

**Utilities / Shared Helpers:**
- Domain utilities: `src/scanner/core/` (e.g., `fingerprint.py`, `suppression.py`)
- No generic `utils.py` pattern — place helpers in the module closest to their usage

## Special Directories

**`.planning/`:**
- Purpose: GSD planning artifacts — research, phase plans, codebase analysis
- Generated: No
- Committed: Yes (planning artifacts are versioned)

**`.venv/`:**
- Purpose: Python virtual environment
- Generated: Yes
- Committed: No (in `.gitignore`)

**`reports/`:**
- Purpose: Default output directory for CLI-generated HTML/PDF scan reports
- Generated: Yes (by `scanner scan` command)
- Committed: No

**`backups/`:**
- Purpose: Database backup files (root-owned, created by backup scripts)
- Generated: Yes
- Committed: No

**`alembic/versions/`:**
- Purpose: Alembic migration scripts for schema changes
- Generated: Partially (by `alembic revision`)
- Committed: Yes

---

*Structure analysis: 2026-03-20*
