# Phase 1: Foundation and Data Models - Research

**Researched:** 2026-03-18
**Domain:** Python/FastAPI project bootstrap, config management, data models, SQLite persistence, Docker containerization
**Confidence:** HIGH

## Summary

Phase 1 establishes the entire project skeleton for a FastAPI-based security scanner. The core work is: (1) project structure and packaging, (2) config loading from YAML with env var overrides for secrets, (3) Pydantic data models for Finding and ScanResult with deterministic dedup fingerprints, (4) SQLite persistence with WAL mode, (5) FastAPI health endpoint, and (6) Docker/docker-compose setup.

The Python ecosystem has mature, well-documented solutions for every component. FastAPI 0.135+ with Pydantic v2 is the standard. pydantic-settings with its built-in YamlConfigSettingsSource handles YAML+env var config natively. SQLAlchemy 2.0 with aiosqlite provides async SQLite access. The key design decision is getting the Finding model and fingerprint algorithm right -- this is the core data contract consumed by every subsequent phase.

**Primary recommendation:** Use FastAPI + Pydantic v2 + pydantic-settings[yaml] for config, SQLAlchemy 2.0 + aiosqlite for async SQLite with WAL mode, and SHA-256 fingerprints composed from (file_path + rule_id + code_snippet_normalized) for deterministic deduplication.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
None -- all areas deferred to Claude's discretion.

### Claude's Discretion
All areas in this phase are technical foundation decisions fully determined by the requirements. No user vision input needed -- Claude has full discretion on:
- Config structure -- config.yml organization, env var override mechanism, default values
- Finding model fields -- Field selection, severity enum, dedup fingerprint algorithm
- Project layout -- Python package structure, module organization
- Docker setup -- Base image, multi-stage build, scanner tool installation
- Database schema -- SQLite table design, WAL mode config, migration approach
- API skeleton -- FastAPI app structure, health endpoint response format

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SCAN-02 | All tool findings normalized to unified severity (Critical/High/Medium/Low/Info) | Pydantic enum for severity levels; Finding model with tool-agnostic fields; severity mapping table pattern |
| API-04 | Health check endpoint (GET /api/health) | FastAPI router with health endpoint returning status, version, DB connectivity, uptime |
| INFRA-01 | Entire stack runs via single docker-compose up | Docker Compose with python:3.12-slim base, volume mounts, port mapping |
| INFRA-03 | All configuration via environment variables and config.yml | pydantic-settings[yaml] with YamlConfigSettingsSource + env var overrides (env takes priority) |
| INFRA-04 | No hardcoded paths, hostnames, or credentials in codebase | Config model validation; .env.example with placeholder values; secrets only via env vars |
| INFRA-05 | SQLite database in mounted volume for persistence | SQLAlchemy + aiosqlite with WAL mode; Docker volume mount for /data; DB path configurable |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| fastapi | 0.135.1 | Web framework + REST API | Async, auto OpenAPI docs, Pydantic-native, production-proven |
| pydantic | 2.12.5 | Data validation and models | V2 is 5-50x faster than V1; native to FastAPI |
| pydantic-settings[yaml] | 2.13.1 | Config from YAML + env vars | Built-in YamlConfigSettingsSource, env override, type validation |
| sqlalchemy | 2.0.48 | ORM and database toolkit | Async support, declarative models, migration ecosystem |
| aiosqlite | 0.22.1 | Async SQLite driver | Required for SQLAlchemy async + SQLite; single-thread safety |
| uvicorn | 0.42.0 | ASGI server | Standard FastAPI production server |
| pyyaml | (via pydantic-settings[yaml]) | YAML parsing | Installed as dependency of pydantic-settings[yaml] extra |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| alembic | latest | Database migrations | Schema evolution across versions |
| python-dotenv | latest | .env file loading | Local development convenience |
| httpx | latest | Async HTTP client | Health check self-test, future webhook calls |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| SQLAlchemy | raw aiosqlite | Less boilerplate but no ORM, no migration support, manual SQL |
| pydantic-settings | dynaconf | dynaconf more flexible but adds unnecessary dependency; pydantic-settings is native to FastAPI |
| alembic | manual SQL migrations | Simpler initially but unscalable; alembic is standard for SQLAlchemy |

**Installation:**
```bash
pip install "fastapi[standard]" "pydantic-settings[yaml]" sqlalchemy aiosqlite alembic
```

Note: `fastapi[standard]` includes uvicorn, httpx, and other standard dependencies.

## Architecture Patterns

### Recommended Project Structure
```
aipix-security-scanner/
├── docker-compose.yml
├── Dockerfile
├── config.yml.example          # Template config (no secrets)
├── .env.example                # Template env vars (no real values)
├── pyproject.toml              # Project metadata + dependencies
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/
├── src/
│   └── scanner/
│       ├── __init__.py
│       ├── main.py             # FastAPI app factory
│       ├── config.py           # Settings model (pydantic-settings)
│       ├── api/
│       │   ├── __init__.py
│       │   ├── router.py       # API router aggregator
│       │   └── health.py       # GET /api/health
│       ├── models/
│       │   ├── __init__.py
│       │   ├── base.py         # SQLAlchemy declarative base
│       │   ├── finding.py      # Finding ORM model
│       │   └── scan.py         # ScanResult ORM model
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── finding.py      # Finding Pydantic schemas
│       │   ├── scan.py         # ScanResult Pydantic schemas
│       │   └── severity.py     # Severity enum
│       ├── db/
│       │   ├── __init__.py
│       │   └── session.py      # Async engine + session factory
│       └── core/
│           ├── __init__.py
│           └── fingerprint.py  # Dedup fingerprint logic
└── tests/
    ├── conftest.py
    ├── test_config.py
    ├── test_health.py
    ├── test_models.py
    └── test_fingerprint.py
```

### Pattern 1: Pydantic Settings with YAML + Env Var Override
**What:** Load base config from config.yml, allow env vars to override any value (especially secrets).
**When to use:** Always -- this is the primary config mechanism.
**Example:**
```python
# src/scanner/config.py
from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)


class ScannerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        yaml_file="config.yml",
        env_prefix="SCANNER_",
        env_nested_delimiter="__",
    )

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    db_path: str = "/data/scanner.db"

    # API
    api_key: str = Field(default="", description="API key for authentication")

    # AI (secrets -- MUST come from env vars)
    claude_api_key: str = Field(default="", description="Claude API key")

    # Notifications (optional)
    slack_webhook_url: str = ""
    email_smtp_host: str = ""

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,           # Env vars override YAML
            dotenv_settings,
            file_secret_settings,
            YamlConfigSettingsSource(settings_cls),  # YAML is lowest priority
        )
```
**Source:** [Pydantic Settings docs](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)

**Key point:** The tuple order defines priority. First source wins. Env vars MUST be higher priority than YAML so secrets are never in config files.

### Pattern 2: Severity Enum with Ordering
**What:** Unified severity levels with comparison support for quality gate logic.
**When to use:** Every finding, every report, every quality gate check.
**Example:**
```python
# src/scanner/schemas/severity.py
from enum import IntEnum


class Severity(IntEnum):
    """Unified severity levels. IntEnum enables comparison operators."""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    INFO = 1
```

Using IntEnum means `Severity.CRITICAL > Severity.HIGH` works naturally, which is essential for quality gate threshold comparisons in Phase 4.

### Pattern 3: Deterministic Fingerprint for Dedup
**What:** SHA-256 hash of normalized (file_path, rule_id, code_snippet) to deduplicate findings across tools and scans.
**When to use:** Every finding gets a fingerprint at creation time.
**Example:**
```python
# src/scanner/core/fingerprint.py
import hashlib
import re


def compute_fingerprint(
    file_path: str,
    rule_id: str,
    snippet: str,
) -> str:
    """Deterministic fingerprint for finding deduplication.

    Normalizes inputs before hashing:
    - file_path: forward slashes, no leading ./
    - rule_id: lowercase, stripped
    - snippet: whitespace-collapsed, stripped
    """
    norm_path = file_path.replace("\\", "/").lstrip("./").strip()
    norm_rule = rule_id.lower().strip()
    norm_snippet = re.sub(r"\s+", " ", snippet).strip()

    content = f"{norm_path}:{norm_rule}:{norm_snippet}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
```

**Key design decisions:**
- Use SHA-256 (not MD5) for collision resistance
- Normalize whitespace in snippets so reformatting does not break dedup
- Normalize path separators for cross-platform consistency
- Fingerprint is deterministic: same input always produces same output
- Include rule_id so different tools flagging the same line for different reasons are separate findings

### Pattern 4: SQLAlchemy Async Engine with WAL Mode
**What:** Configure SQLAlchemy async engine for SQLite with WAL mode on connect.
**When to use:** Database initialization at app startup.
**Example:**
```python
# src/scanner/db/session.py
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import event


def _set_sqlite_pragmas(dbapi_conn, connection_record):
    """Enable WAL mode and other SQLite optimizations."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def create_engine(db_path: str):
    url = f"sqlite+aiosqlite:///{db_path}"
    engine = create_async_engine(url, echo=False)

    # Register PRAGMA on every new connection
    event.listen(engine.sync_engine, "connect", _set_sqlite_pragmas)

    return engine


def create_session_factory(engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)
```

**Source:** [SQLAlchemy SQLite docs](https://docs.sqlalchemy.org/en/21/dialects/sqlite.html)

**WAL mode benefits:**
- Readers do not block writers
- Writers do not block readers
- Better performance for concurrent read/write (FastAPI handles multiple requests)
- Crash recovery is more robust

### Pattern 5: FastAPI App Factory
**What:** Create FastAPI app in a factory function for testability.
**Example:**
```python
# src/scanner/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from scanner.config import ScannerSettings
from scanner.db.session import create_engine, create_session_factory
from scanner.api.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    settings = ScannerSettings()
    engine = create_engine(settings.db_path)

    # Create tables (Phase 1 only; alembic in later phases)
    async with engine.begin() as conn:
        from scanner.models.base import Base
        await conn.run_sync(Base.metadata.create_all)

    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)
    app.state.settings = settings

    yield

    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="aipix-security-scanner",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(api_router, prefix="/api")
    return app


app = create_app()
```

### Pattern 6: Health Check Endpoint
**What:** GET /api/health returning status, version, DB check, uptime.
**Example:**
```python
# src/scanner/api/health.py
import time
from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter()
_start_time = time.time()


class HealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: float
    database: str


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request):
    db_status = "ok"
    try:
        async with request.app.state.session_factory() as session:
            await session.execute("SELECT 1")
    except Exception:
        db_status = "error"

    return HealthResponse(
        status="healthy" if db_status == "ok" else "degraded",
        version="0.1.0",
        uptime_seconds=round(time.time() - _start_time, 2),
        database=db_status,
    )
```

### Anti-Patterns to Avoid
- **Global mutable settings singleton:** Use dependency injection via `app.state` or FastAPI `Depends()`, not module-level globals that are hard to test.
- **Synchronous SQLite in async FastAPI:** Always use aiosqlite driver. Synchronous sqlite3 blocks the event loop and kills concurrency.
- **Fingerprint including line numbers:** Line numbers shift with code changes. Use code snippet content instead for stability across commits.
- **Hardcoding config paths:** Make config.yml path configurable via env var (`SCANNER_CONFIG_PATH`) so Docker and tests can point to different files.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML config + env override | Custom YAML loader + os.environ merging | pydantic-settings[yaml] YamlConfigSettingsSource | Handles nested keys, type coercion, validation, env prefix, dotenv -- all built in |
| Database migrations | Manual ALTER TABLE scripts | Alembic | Auto-generates diffs, handles rollbacks, version tracking |
| ASGI server | asyncio.run + manual socket handling | Uvicorn | Production-hardened, graceful shutdown, logging, worker management |
| Data validation | Manual dict checking and type casting | Pydantic BaseModel | Automatic validation, serialization, OpenAPI schema generation |
| Async DB access | threading + sqlite3 | SQLAlchemy async + aiosqlite | Thread-safe, connection pooling, ORM, event system for PRAGMAs |

**Key insight:** Every component in Phase 1 has a mature, well-tested library. Hand-rolling any of these introduces bugs that the ecosystem solved years ago.

## Common Pitfalls

### Pitfall 1: SQLite WAL Mode Not Persisting
**What goes wrong:** WAL mode is set once but new connections revert to journal_mode=DELETE.
**Why it happens:** SQLite PRAGMAs are per-connection, not per-database (WAL is an exception -- it persists in the DB file, but SYNCHRONOUS does not).
**How to avoid:** Use SQLAlchemy `event.listen(engine.sync_engine, "connect", ...)` to set PRAGMAs on every new connection.
**Warning signs:** Slow writes under concurrent requests; `PRAGMA journal_mode` returns "delete".

### Pitfall 2: Config Secrets in YAML File
**What goes wrong:** Developer puts API keys in config.yml and commits them.
**Why it happens:** YAML file is convenient; easy to forget it's tracked by git.
**How to avoid:** (1) config.yml.example in repo with placeholder values, (2) actual config.yml in .gitignore, (3) secrets ONLY via env vars with clear naming (SCANNER_API_KEY, SCANNER_CLAUDE_API_KEY), (4) pydantic-settings validates that required secrets are present at startup.
**Warning signs:** Gitleaks (our own tool!) flagging credentials in the repo.

### Pitfall 3: Blocking the Async Event Loop
**What goes wrong:** Using synchronous sqlite3 or synchronous file I/O in async FastAPI endpoints.
**Why it happens:** Python stdlib sqlite3 is synchronous; easy to accidentally import and use directly.
**How to avoid:** Always use aiosqlite via SQLAlchemy async engine. Never import sqlite3 directly. Lint for it.
**Warning signs:** High latency under concurrent requests; event loop warnings in logs.

### Pitfall 4: Fingerprint Instability Across Platforms
**What goes wrong:** Same finding produces different fingerprints on Windows vs Linux.
**Why it happens:** Path separators (\ vs /), line endings (\r\n vs \n), locale-dependent whitespace.
**How to avoid:** Normalize all inputs before hashing: forward slashes, strip, collapse whitespace, UTF-8 encoding.
**Warning signs:** Duplicate findings appearing in scan history after running on different machines.

### Pitfall 5: Docker Volume Permissions
**What goes wrong:** SQLite DB file created as root inside container, then inaccessible or permission errors.
**Why it happens:** Docker runs as root by default; volume-mounted files get root ownership.
**How to avoid:** Create a non-root user in Dockerfile, ensure /data directory has correct ownership, use `USER` directive.
**Warning signs:** PermissionError on DB operations; file owned by root:root on host.

### Pitfall 6: Missing Foreign Key Enforcement in SQLite
**What goes wrong:** Foreign key constraints silently not enforced.
**Why it happens:** SQLite has foreign keys disabled by default for backward compatibility.
**How to avoid:** `PRAGMA foreign_keys=ON` on every connection (included in the connect event handler pattern above).
**Warning signs:** Orphaned records after deletes; referential integrity violations not raising errors.

## Code Examples

### Finding ORM Model
```python
# src/scanner/models/finding.py
from datetime import datetime
from sqlalchemy import (
    Column, DateTime, ForeignKey, Integer, String, Text,
)
from scanner.models.base import Base


class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=False, index=True)
    fingerprint = Column(String(64), nullable=False, index=True)  # SHA-256 hex

    # Source
    tool = Column(String(50), nullable=False)          # semgrep, gitleaks, trivy, etc.
    rule_id = Column(String(200), nullable=False)       # Tool-specific rule identifier

    # Location
    file_path = Column(String(500), nullable=False)
    line_start = Column(Integer, nullable=True)
    line_end = Column(Integer, nullable=True)
    snippet = Column(Text, nullable=True)               # Code context

    # Classification
    severity = Column(Integer, nullable=False)          # Maps to Severity IntEnum
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)

    # AI enrichment (Phase 3, nullable for now)
    ai_analysis = Column(Text, nullable=True)
    ai_fix_suggestion = Column(Text, nullable=True)

    # Metadata
    false_positive = Column(Integer, default=0)         # 0=no, 1=yes (Phase 5)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### ScanResult ORM Model
```python
# src/scanner/models/scan.py
from datetime import datetime
from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from scanner.models.base import Base


class ScanResult(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Target
    target_path = Column(String(500), nullable=True)    # Local path
    repo_url = Column(String(500), nullable=True)       # Git repo URL
    branch = Column(String(200), nullable=True)
    commit_hash = Column(String(40), nullable=True)

    # Status
    status = Column(String(20), nullable=False, default="pending")  # pending/running/completed/failed
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Results summary
    total_findings = Column(Integer, default=0)
    critical_count = Column(Integer, default=0)
    high_count = Column(Integer, default=0)
    medium_count = Column(Integer, default=0)
    low_count = Column(Integer, default=0)
    info_count = Column(Integer, default=0)

    # Quality gate
    gate_passed = Column(Integer, nullable=True)  # 0=fail, 1=pass, NULL=not evaluated

    # Metadata
    scanner_version = Column(String(20), nullable=True)
    tool_versions = Column(Text, nullable=True)   # JSON blob of tool versions
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Docker Compose
```yaml
# docker-compose.yml
version: "3.8"

services:
  scanner:
    build: .
    ports:
      - "${SCANNER_PORT:-8000}:8000"
    volumes:
      - scanner_data:/data
      - ./config.yml:/app/config.yml:ro
    environment:
      - SCANNER_DB_PATH=/data/scanner.db
      - SCANNER_API_KEY=${SCANNER_API_KEY:-}
      - SCANNER_CLAUDE_API_KEY=${SCANNER_CLAUDE_API_KEY:-}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

volumes:
  scanner_data:
```

### Dockerfile (Phase 1 minimal)
```dockerfile
FROM python:3.12-slim AS base

# System deps for scanner tools will be added in Phase 2
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user
RUN groupadd -r scanner && useradd -r -g scanner -d /app scanner
RUN mkdir -p /data && chown scanner:scanner /data

WORKDIR /app

# Python deps
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]" || pip install --no-cache-dir .

# App code
COPY src/ src/
COPY alembic.ini .
COPY alembic/ alembic/

USER scanner

EXPOSE 8000

CMD ["uvicorn", "scanner.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Pydantic V1 BaseSettings | pydantic-settings V2 (separate package) | Pydantic V2 (2023) | Must install pydantic-settings separately; new API for customise_sources |
| SQLAlchemy 1.x sync | SQLAlchemy 2.0 async with aiosqlite | SQLAlchemy 2.0 (2023) | Native async; new declarative syntax; must use async_sessionmaker |
| Flask for APIs | FastAPI with async | FastAPI mature (2024+) | Auto OpenAPI, native Pydantic, async by default |
| Manual config parsing | pydantic-settings[yaml] | pydantic-settings 2.x | Built-in YAML source, no custom code needed |

**Deprecated/outdated:**
- `pydantic.BaseSettings` (moved to `pydantic_settings.BaseSettings` in Pydantic V2)
- `SessionLocal = sessionmaker(...)` pattern (use `async_sessionmaker` for async)
- `@app.on_event("startup")` (use `lifespan` context manager instead -- on_event is deprecated in FastAPI)

## Open Questions

1. **Alembic with async SQLAlchemy**
   - What we know: Alembic supports async engines via `run_async` in env.py
   - What's unclear: Whether to set up alembic in Phase 1 or defer to Phase 2 when schema stabilizes
   - Recommendation: Create alembic skeleton in Phase 1 with initial migration, but keep it simple. Schema will evolve.

2. **Scanner tool installation in Docker**
   - What we know: Phase 1 Dockerfile is minimal; scanner tools (semgrep, trivy, gitleaks, cppcheck, checkov) are Phase 2
   - What's unclear: Whether to include tool stubs in Phase 1 Docker image for integration testing
   - Recommendation: Phase 1 Dockerfile should be Python-only. Phase 2 extends it with scanner tools. Keeps Phase 1 Docker builds fast.

3. **Config file path discovery**
   - What we know: pydantic-settings yaml_file can be a relative or absolute path
   - What's unclear: How to handle config.yml not found (first run, testing)
   - Recommendation: Make yaml_file path configurable via SCANNER_CONFIG_PATH env var. Fall back to defaults if file not found. pydantic-settings handles missing yaml_file gracefully (uses defaults + env vars).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio + httpx |
| Config file | pyproject.toml [tool.pytest.ini_options] |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v --tb=short` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SCAN-02 | Severity enum has 5 levels, IntEnum ordering works | unit | `pytest tests/test_models.py::test_severity_enum -x` | No -- Wave 0 |
| SCAN-02 | Finding model accepts all severity levels | unit | `pytest tests/test_models.py::test_finding_severity -x` | No -- Wave 0 |
| API-04 | GET /api/health returns 200 with status fields | integration | `pytest tests/test_health.py::test_health_endpoint -x` | No -- Wave 0 |
| INFRA-01 | docker-compose up starts server | smoke | `docker-compose up -d && curl -f http://localhost:8000/api/health` | No -- manual |
| INFRA-03 | Config loads from YAML, env vars override | unit | `pytest tests/test_config.py::test_yaml_loading -x` | No -- Wave 0 |
| INFRA-03 | Config env var overrides YAML value | unit | `pytest tests/test_config.py::test_env_override -x` | No -- Wave 0 |
| INFRA-04 | No secrets in default config | unit | `pytest tests/test_config.py::test_no_hardcoded_secrets -x` | No -- Wave 0 |
| INFRA-05 | SQLite created with WAL mode | integration | `pytest tests/test_models.py::test_sqlite_wal_mode -x` | No -- Wave 0 |
| INFRA-05 | DB persists data across session recreate | integration | `pytest tests/test_models.py::test_db_persistence -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/ -x -q`
- **Per wave merge:** `pytest tests/ -v --tb=short`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/conftest.py` -- shared fixtures (async engine, test DB, test client)
- [ ] `tests/test_config.py` -- config loading tests
- [ ] `tests/test_health.py` -- health endpoint test
- [ ] `tests/test_models.py` -- model and DB tests
- [ ] `tests/test_fingerprint.py` -- fingerprint determinism and normalization tests
- [ ] Framework install: `pip install pytest pytest-asyncio httpx` -- none detected in project

## Sources

### Primary (HIGH confidence)
- [Pydantic Settings docs](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) -- YamlConfigSettingsSource, settings_customise_sources, env var override priority
- [SQLAlchemy SQLite dialect docs](https://docs.sqlalchemy.org/en/21/dialects/sqlite.html) -- async engine, aiosqlite, PRAGMA configuration via events
- [FastAPI docs](https://fastapi.tiangolo.com/) -- lifespan, routers, dependency injection
- [PyPI](https://pypi.org/) -- verified current versions of all packages

### Secondary (MEDIUM confidence)
- [FastAPI best practices (zhanymkanov)](https://github.com/zhanymkanov/fastapi-best-practices) -- project structure patterns
- [FastAPI production guide](https://patrykgolabek.dev/guides/fastapi-production/health-checks/) -- health check patterns

### Tertiary (LOW confidence)
- None -- all findings verified against official documentation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries are well-established, versions verified on PyPI
- Architecture: HIGH -- FastAPI + SQLAlchemy + Pydantic is the dominant Python API stack
- Pitfalls: HIGH -- WAL mode, async gotchas, fingerprint stability are well-documented issues
- Data models: HIGH -- Finding/ScanResult schema follows standard security tool patterns (SARIF-adjacent)

**Research date:** 2026-03-18
**Valid until:** 2026-04-18 (stable ecosystem, 30-day validity)
