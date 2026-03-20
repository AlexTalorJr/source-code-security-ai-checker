# Phase 6: Packaging, Portability, and Documentation - Context

**Gathered:** 2026-03-20
**Status:** Ready for planning

<domain>
## Phase Boundary

The scanner becomes a distributable, self-contained package that any team can deploy and operate using comprehensive documentation. Covers multi-arch Docker builds, Makefile automation, migration tooling, distributable archive, and complete bilingual documentation suite (English + Russian).

</domain>

<decisions>
## Implementation Decisions

### Makefile targets & packaging
- `make install` — runs `docker-compose build` (Docker-first model)
- `make run` — runs `docker-compose up -d`
- `make test` — runs test suite
- `make package` — produces `aipix-security-scanner-{version}.tar.gz` tarball containing: Dockerfile, docker-compose.yml, config.yml.example, .env.example, docs/, README.md, LICENSE, src/, pyproject.toml, alembic/, alembic.ini
- `make migrate` — runs `alembic upgrade head`
- `make backup` — copies SQLite DB + config to timestamped archive
- `make restore BACKUP=file` — restores from backup archive
- `make clean` — removes build artifacts, __pycache__, .pyc files
- Version number read from pyproject.toml (single source of truth for tarball naming)

### Migration & portability
- Export format: SQLite file copy — `make backup` produces tar.gz with scanner.db, reports/, config.yml
- Import: `make restore BACKUP=file` replaces DB, reports, config
- Schema version mismatches handled by Alembic — on restore, run `alembic upgrade head` to migrate imported DB to current schema
- Transfer guide includes: onboarding checklist (prerequisites, env setup, first scan, verify results) and complete SCANNER_* environment variables reference

### Doc restructuring & bilingual strategy
- Move existing `docs/*.md` (8 files) into `docs/en/`
- Create matching `docs/ru/` with full Russian translations of all 8 docs
- Update English docs first to reflect Phases 2-5 features (current docs are Phase 1 era), then translate complete versions to Russian
- Russian documentation uses technical formal style (formal "вы", professional terminology)
- Split README.md into README.md (English) + README.ru.md (Russian) — no longer bilingual in single file

### Multi-arch Docker builds
- `make docker-multiarch` — uses `docker buildx build --platform linux/amd64,linux/arm64`
- `make install` stays single-arch (local development)
- `make docker-multiarch` saves locally as tar export (no registry required)
- `make docker-push` pushes to configured registry (optional, for teams with registry infra)
- Current Dockerfile base (python:3.12-slim) is ARM64-compatible — no arch-specific Dockerfile changes expected

### Meta files
- LICENSE — Apache 2.0 (per PROJECT.md key decisions)
- CONTRIBUTING.md — new file
- CHANGELOG.md — already exists, update with all phase completions
- .env.example — already exists, verify completeness

### Claude's Discretion
- Makefile syntax and variable conventions
- Exact backup archive structure and restore script implementation
- CONTRIBUTING.md content and contribution workflow
- CHANGELOG.md format and level of detail
- buildx builder configuration details
- Docker registry target configuration approach
- Doc update depth — how much to expand each existing doc

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — Phase 6 covers INFRA-02, INFRA-06, INFRA-07, INFRA-08, DOC-01 through DOC-11
- `.planning/PROJECT.md` — Scanner tech stack, architecture layers, constraints (Apache 2.0 license, self-hosted, SQLite only, bilingual docs)

### Phase scope
- `.planning/ROADMAP.md` — Phase 6 goal and 5 success criteria

### Prior phase context
- `.planning/phases/05-api-dashboard-ci-and-notifications/05-CONTEXT.md` — API/dashboard/notification decisions (docs must cover these features)
- `.planning/phases/04-reports-and-quality-gate/04-CONTEXT.md` — Report and quality gate decisions (docs must cover these features)

### Existing code (integration points)
- `Dockerfile` — Current single-stage build, python:3.12-slim, non-root user (extend for multi-arch)
- `docker-compose.yml` — Service definition with volumes, env vars, healthcheck
- `config.yml.example` — Configuration template (verify completeness for docs)
- `.env.example` — Environment variables template (verify completeness for transfer guide)
- `README.md` — Current bilingual README (will be split into en/ru)
- `docs/*.md` — 8 existing English docs (architecture, user-guide, admin-guide, devops-guide, api, database-schema, transfer-guide, custom-rules)
- `alembic/` + `alembic.ini` — Migration infrastructure (used by make migrate and restore workflow)
- `CHANGELOG.md` — Existing changelog (update with phase completions)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `Dockerfile` — Working single-stage build with all system deps (pango, harfbuzz for WeasyPrint)
- `docker-compose.yml` — Service definition with volume mounts, healthcheck, env var passthrough
- `alembic/` — Migration infrastructure already set up for schema version management
- `config.yml.example` — Configuration template with scanner, AI, notification settings
- `.env.example` — Environment variable template
- Existing `docs/` — 8 English docs covering architecture, guides, API reference, custom rules

### Established Patterns
- Docker-first deployment (single docker-compose up)
- Config via ScannerSettings with SCANNER_ env prefix + config.yml YAML source
- SQLite in mounted volume (/data/scanner.db) for persistence
- Alembic for schema migrations
- Non-root scanner user in Docker

### Integration Points
- Makefile wraps existing docker-compose commands (build, up, down)
- Backup/restore targets operate on /data volume (scanner.db) and config files
- Multi-arch build extends existing Dockerfile with buildx
- Documentation references existing config.yml.example and .env.example for accuracy
- Transfer guide describes the Docker + volume + env var deployment model

</code_context>

<specifics>
## Specific Ideas

- `make package` should produce a "just works" archive — untar, set env vars, `docker-compose up`
- Migration is simple file-level backup/restore with Alembic handling version differences
- Docs should be fully updated to reflect all 5 completed phases before translation
- README split keeps English as primary (README.md), Russian as README.ru.md

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 06-packaging-portability-and-documentation*
*Context gathered: 2026-03-20*
