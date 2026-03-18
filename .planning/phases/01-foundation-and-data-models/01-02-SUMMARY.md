---
phase: 01-foundation-and-data-models
plan: 02
subsystem: database, api
tags: [sqlalchemy, aiosqlite, sqlite-wal, fastapi, alembic, orm, async-engine]

# Dependency graph
requires:
  - phase: 01-01
    provides: "Pydantic schemas (FindingSchema, ScanResultSchema, Severity), ScannerSettings config, project skeleton"
provides:
  - "Finding and ScanResult SQLAlchemy ORM models with async SQLite persistence"
  - "Async engine factory with WAL mode, foreign keys, and synchronous=NORMAL"
  - "Async session factory (async_sessionmaker)"
  - "FastAPI app factory with lifespan (create_app)"
  - "Health endpoint at GET /api/health with DB connectivity check"
  - "Alembic migration skeleton with async engine support"
affects: [01-03, 02-scanner-integration, 03-ai-analysis, 04-quality-gates, 05-reporting]

# Tech tracking
tech-stack:
  added: []
  patterns: [sqlalchemy-async-sqlite-wal, fastapi-app-factory-lifespan, orm-declarative-base, async-session-factory, health-check-db-connectivity]

key-files:
  created:
    - src/scanner/models/__init__.py
    - src/scanner/models/base.py
    - src/scanner/models/finding.py
    - src/scanner/models/scan.py
    - src/scanner/db/__init__.py
    - src/scanner/db/session.py
    - src/scanner/api/__init__.py
    - src/scanner/api/router.py
    - src/scanner/api/health.py
    - src/scanner/main.py
    - alembic.ini
    - alembic/env.py
    - alembic/script.py.mako
    - alembic/versions/.gitkeep
    - tests/test_models.py
    - tests/test_health.py
  modified: []

key-decisions:
  - "Lifespan-managed test client: ASGITransport does not trigger lifespan events, so tests manually invoke app.router.lifespan_context"
  - "Tables created via Base.metadata.create_all in lifespan (Phase 1); Alembic migrations for later phases"

patterns-established:
  - "DB Session: create_engine(db_path) + create_session_factory(engine) for async SQLite with WAL"
  - "Health Check: GET /api/health returns status/version/uptime_seconds/database with DB SELECT 1 probe"
  - "App Factory: create_app() returns FastAPI with lifespan managing engine lifecycle"
  - "Test Client: _lifespan_client() context manager for proper lifespan + httpx AsyncClient setup"

requirements-completed: [SCAN-02, API-04, INFRA-05]

# Metrics
duration: 4min
completed: 2026-03-18
---

# Phase 01 Plan 02: ORM and API Summary

**SQLAlchemy ORM models (Finding, ScanResult) with async SQLite WAL mode, FastAPI app factory with health endpoint, and Alembic migration skeleton -- 15 passing tests**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-18T20:10:49Z
- **Completed:** 2026-03-18T20:14:34Z
- **Tasks:** 2
- **Files modified:** 16

## Accomplishments
- Finding and ScanResult ORM models persisting to async SQLite with WAL mode and foreign key enforcement
- FastAPI app factory with lifespan managing engine creation, table setup, and cleanup
- Health endpoint returning status, version, uptime, and DB connectivity probe
- Alembic skeleton ready for future schema migrations with async engine support
- 15 tests across models (9) and health endpoint (6)

## Task Commits

Each task was committed atomically:

1. **Task 1: SQLAlchemy ORM models, DB session with WAL mode, and Alembic skeleton** - `8185bdb` (feat)
2. **Task 2: FastAPI application factory with health endpoint** - `b410c43` (feat)

## Files Created/Modified
- `src/scanner/models/base.py` - DeclarativeBase for all ORM models
- `src/scanner/models/scan.py` - ScanResult ORM with status, counts, metadata columns
- `src/scanner/models/finding.py` - Finding ORM with ForeignKey to scans, severity, AI fields
- `src/scanner/models/__init__.py` - Exports Base, Finding, ScanResult
- `src/scanner/db/__init__.py` - DB package init
- `src/scanner/db/session.py` - Async engine factory with WAL/FK pragmas, session factory
- `src/scanner/api/__init__.py` - API package init
- `src/scanner/api/health.py` - HealthResponse model and GET /health endpoint
- `src/scanner/api/router.py` - API router aggregator
- `src/scanner/main.py` - App factory with lifespan, table creation, router inclusion
- `alembic.ini` - Alembic configuration with src layout prepend
- `alembic/env.py` - Async migration environment with target_metadata from Base
- `alembic/script.py.mako` - Migration template
- `alembic/versions/.gitkeep` - Empty versions directory
- `tests/test_models.py` - 9 tests for models, pragmas, CRUD, persistence
- `tests/test_health.py` - 6 tests for health endpoint and app startup

## Decisions Made
- ASGITransport does not trigger FastAPI lifespan events, so tests use `app.router.lifespan_context` directly to manage startup/shutdown -- this pattern is reusable for all future integration tests
- Tables created via `Base.metadata.create_all` during lifespan startup (Phase 1 simplicity); Alembic migrations will take over in later phases

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed ASGI test client lifespan management**
- **Found during:** Task 2 (health endpoint tests)
- **Issue:** httpx AsyncClient with ASGITransport does not send ASGI lifespan startup events, so app.state.session_factory was never initialized, causing health endpoint to report database=error
- **Fix:** Created `_lifespan_client()` async context manager that manually invokes `app.router.lifespan_context(app)` before creating the test client
- **Files modified:** tests/test_health.py
- **Verification:** All 6 health tests pass with status=healthy and database=ok
- **Committed in:** b410c43 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Fix necessary for test correctness. No scope creep.

## Issues Encountered
None beyond the lifespan fix documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- ORM models and DB session ready for Plan 03 (Docker) and Phase 2 (scanner tool integration)
- Health endpoint available for Docker healthcheck configuration
- App factory pattern established for all future endpoint additions

---
*Phase: 01-foundation-and-data-models*
*Completed: 2026-03-18*

## Self-Check: PASSED

All 16 files verified present. Both commit hashes (8185bdb, b410c43) confirmed in git log. 15/15 tests passing.
