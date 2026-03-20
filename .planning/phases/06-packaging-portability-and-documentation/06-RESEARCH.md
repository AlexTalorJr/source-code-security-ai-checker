# Phase 6: Packaging, Portability, and Documentation - Research

**Researched:** 2026-03-20
**Domain:** Docker multi-arch builds, Makefile automation, SQLite backup/restore, bilingual documentation
**Confidence:** HIGH

## Summary

Phase 6 transforms the scanner from a development project into a distributable product. The work falls into four distinct areas: (1) Makefile automation wrapping docker-compose and utility commands, (2) multi-arch Docker builds via buildx, (3) backup/restore tooling for SQLite-based migration, and (4) comprehensive bilingual documentation restructuring.

The technical risk is low. All components use well-established tools (GNU Make, docker buildx, tar/gzip, Alembic). The primary effort is documentation -- updating 8 existing English docs to reflect Phases 2-5 features, then translating all to Russian. The existing docs are Phase 1 era (~875 lines total) and need substantial expansion.

**Primary recommendation:** Structure work as Makefile+packaging first (enables testing everything else), then backup/restore, then multi-arch Docker, then documentation update+translation, then meta files (LICENSE, CONTRIBUTING, CHANGELOG).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- `make install` -- runs `docker-compose build` (Docker-first model)
- `make run` -- runs `docker-compose up -d`
- `make test` -- runs test suite
- `make package` -- produces `aipix-security-scanner-{version}.tar.gz` tarball containing: Dockerfile, docker-compose.yml, config.yml.example, .env.example, docs/, README.md, LICENSE, src/, pyproject.toml, alembic/, alembic.ini
- `make migrate` -- runs `alembic upgrade head`
- `make backup` -- copies SQLite DB + config to timestamped archive
- `make restore BACKUP=file` -- restores from backup archive
- `make clean` -- removes build artifacts, __pycache__, .pyc files
- Version number read from pyproject.toml (single source of truth for tarball naming)
- Export format: SQLite file copy; `make backup` produces tar.gz with scanner.db, reports/, config.yml
- Import: `make restore BACKUP=file` replaces DB, reports, config
- Schema version mismatches handled by Alembic -- on restore, run `alembic upgrade head`
- Transfer guide includes onboarding checklist and complete SCANNER_* environment variables reference
- Move existing `docs/*.md` (8 files) into `docs/en/`
- Create matching `docs/ru/` with full Russian translations
- Update English docs first to reflect Phases 2-5, then translate to Russian
- Russian documentation uses technical formal style (formal "vy", professional terminology)
- Split README.md into README.md (English) + README.ru.md (Russian)
- `make docker-multiarch` uses `docker buildx build --platform linux/amd64,linux/arm64`
- `make install` stays single-arch (local development)
- `make docker-multiarch` saves locally as tar export (no registry required)
- `make docker-push` pushes to configured registry (optional)
- Current Dockerfile base (python:3.12-slim) is ARM64-compatible
- LICENSE: Apache 2.0
- CONTRIBUTING.md: new file
- CHANGELOG.md: update with all phase completions
- .env.example: verify completeness

### Claude's Discretion
- Makefile syntax and variable conventions
- Exact backup archive structure and restore script implementation
- CONTRIBUTING.md content and contribution workflow
- CHANGELOG.md format and level of detail
- buildx builder configuration details
- Docker registry target configuration approach
- Doc update depth -- how much to expand each existing doc

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| INFRA-02 | Docker images support x86_64 and ARM64 architectures | docker buildx with --platform linux/amd64,linux/arm64; OCI export for local tar |
| INFRA-06 | Makefile with targets: install, run, test, migrate, backup, restore, package | GNU Make wrapping docker-compose, alembic, tar commands |
| INFRA-07 | Migration scripts for moving scan history between environments | make backup/restore with SQLite file copy + Alembic schema migration |
| INFRA-08 | make package creates distributable archive | tar.gz with version from pyproject.toml |
| DOC-01 | README.md with quick start (5 minutes to first scan) | Split bilingual README into English README.md + README.ru.md |
| DOC-02 | docs/en/architecture.md and docs/ru/architecture.md | Move + update existing docs/architecture.md, create Russian translation |
| DOC-03 | docs/en/database-schema.md | Move + update existing, add Mermaid ER diagram |
| DOC-04 | docs/en/user-guide.md | Move + update to cover reports, AI findings, quality gate |
| DOC-05 | docs/en/admin-guide.md | Move + update to cover all config options from Phases 1-5 |
| DOC-06 | docs/en/devops-guide.md | Move + update to cover Docker, Jenkins, backups, multi-arch |
| DOC-07 | docs/en/api.md | Move + update to cover all REST API endpoints from Phase 5 |
| DOC-08 | docs/en/transfer-guide.md | Move + update with onboarding checklist, env vars reference |
| DOC-09 | docs/en/custom-rules.md | Move + update existing |
| DOC-10 | All docs available in Russian (docs/ru/) | Translate all 8 English docs to Russian |
| DOC-11 | CHANGELOG.md, LICENSE (Apache 2.0), CONTRIBUTING.md, .env.example | Create LICENSE, CONTRIBUTING.md; update CHANGELOG.md, verify .env.example |
</phase_requirements>

## Standard Stack

### Core
| Tool | Purpose | Why Standard |
|------|---------|--------------|
| GNU Make | Build automation | Universal on Linux, self-documenting targets, no dependencies |
| docker buildx | Multi-arch image builds | Official Docker tool for cross-platform builds |
| tar + gzip | Package archive creation | Standard Unix tools, no extra dependencies |
| Alembic | Schema migration on restore | Already in project, handles version mismatches |

### Supporting
| Tool | Purpose | When to Use |
|------|---------|-------------|
| docker compose | Service orchestration | Wrapped by Makefile targets |
| grep/sed | Version extraction from pyproject.toml | In Makefile for tarball naming |
| python -c | Version extraction alternative | More reliable than grep for TOML parsing |

### No New Dependencies
This phase requires NO new Python packages. All work is Makefile automation, Docker configuration, and documentation files.

## Architecture Patterns

### Recommended Project Structure After Phase 6
```
naveksoft-security/
+-- Makefile                    # NEW: build automation
+-- LICENSE                     # NEW: Apache 2.0
+-- CONTRIBUTING.md             # NEW: contribution guide
+-- CHANGELOG.md                # UPDATED: all phases
+-- README.md                   # UPDATED: English only
+-- README.ru.md                # NEW: Russian README
+-- .env.example                # VERIFIED: completeness
+-- config.yml.example
+-- Dockerfile
+-- docker-compose.yml
+-- pyproject.toml
+-- alembic.ini
+-- alembic/
+-- src/scanner/
+-- tests/
+-- docs/
    +-- en/                     # NEW: moved from docs/
    |   +-- architecture.md
    |   +-- database-schema.md
    |   +-- user-guide.md
    |   +-- admin-guide.md
    |   +-- devops-guide.md
    |   +-- api.md
    |   +-- transfer-guide.md
    |   +-- custom-rules.md
    +-- ru/                     # NEW: Russian translations
        +-- architecture.md
        +-- database-schema.md
        +-- user-guide.md
        +-- admin-guide.md
        +-- devops-guide.md
        +-- api.md
        +-- transfer-guide.md
        +-- custom-rules.md
```

### Pattern 1: Makefile Version Extraction from pyproject.toml
**What:** Extract version from pyproject.toml without external tools
**When to use:** For `make package` tarball naming
**Example:**
```makefile
VERSION := $(shell python3 -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])" 2>/dev/null || grep -m1 'version' pyproject.toml | cut -d'"' -f2)
PACKAGE_NAME := aipix-security-scanner-$(VERSION)
```

### Pattern 2: Makefile with .PHONY and Help Target
**What:** Self-documenting Makefile with help
**When to use:** Standard practice for project Makefiles
**Example:**
```makefile
.PHONY: help install run test migrate backup restore package clean docker-multiarch docker-push

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Build Docker images
	docker compose build

run: ## Start scanner in background
	docker compose up -d

stop: ## Stop scanner
	docker compose down

test: ## Run test suite
	docker compose run --rm scanner python -m pytest tests/ -v

migrate: ## Run database migrations
	docker compose exec scanner alembic upgrade head
```

### Pattern 3: Backup Archive Structure
**What:** Timestamped tar.gz with DB, config, reports
**When to use:** `make backup` target
**Example:**
```makefile
BACKUP_DIR := backups
TIMESTAMP := $(shell date +%Y%m%d_%H%M%S)

backup: ## Backup database, config, and reports
	@mkdir -p $(BACKUP_DIR)
	docker compose exec scanner tar czf - /data/scanner.db /app/config.yml 2>/dev/null > $(BACKUP_DIR)/backup-$(TIMESTAMP).tar.gz
	@echo "Backup saved: $(BACKUP_DIR)/backup-$(TIMESTAMP).tar.gz"
```
Note: The exact mechanism may use `docker cp` or volume-mounted paths instead of exec+tar. Implementation should handle the case where the container is stopped.

### Pattern 4: Multi-Arch Build with Local OCI Export
**What:** Build for amd64+arm64, save as local tar
**When to use:** `make docker-multiarch` target
**Example:**
```makefile
REGISTRY ?= localhost
IMAGE_NAME ?= aipix-security-scanner

docker-multiarch: ## Build multi-arch images (amd64+arm64)
	docker buildx create --name multiarch --use 2>/dev/null || docker buildx use multiarch
	docker buildx build --platform linux/amd64,linux/arm64 \
		-t $(REGISTRY)/$(IMAGE_NAME):$(VERSION) \
		--output type=oci,dest=$(PACKAGE_NAME)-multiarch.tar .

docker-push: ## Push multi-arch images to registry
	docker buildx build --platform linux/amd64,linux/arm64 \
		-t $(REGISTRY)/$(IMAGE_NAME):$(VERSION) --push .
```

### Pattern 5: Package Tarball
**What:** Distributable archive with everything needed to deploy
**When to use:** `make package` target
**Example:**
```makefile
package: ## Create distributable archive
	tar czf $(PACKAGE_NAME).tar.gz \
		--transform 's,^,$(PACKAGE_NAME)/,' \
		Dockerfile docker-compose.yml config.yml.example .env.example \
		README.md LICENSE CONTRIBUTING.md \
		src/ pyproject.toml alembic/ alembic.ini docs/
```

### Anti-Patterns to Avoid
- **Hardcoded version in Makefile:** Always read from pyproject.toml
- **Backup requiring running container:** Support backup from stopped state via volume path
- **Missing .PHONY declarations:** All targets should be declared .PHONY since none produce files
- **Tabs vs spaces:** Makefile recipes MUST use tabs, not spaces

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Multi-arch builds | Custom cross-compilation | docker buildx | Handles QEMU emulation, manifest lists |
| Schema migration | Manual SQL scripts | Alembic (already in project) | Handles version ordering, rollback |
| Archive creation | Custom Python packager | GNU tar + gzip | Standard, predictable, no dependencies |
| License text | Paraphrased license | Official Apache 2.0 text from apache.org | Legal requirement for exact text |

## Common Pitfalls

### Pitfall 1: docker buildx Builder Not Configured
**What goes wrong:** `docker buildx build --platform linux/amd64,linux/arm64` fails with "multiple platforms not supported"
**Why it happens:** Default docker builder only supports native platform; need docker-container driver
**How to avoid:** Create a buildx builder with docker-container driver before multi-arch build
**Warning signs:** Error message mentioning "multiple platforms feature requires"
```makefile
docker-multiarch:
	docker buildx create --name multiarch --driver docker-container --use 2>/dev/null || docker buildx use multiarch
```

### Pitfall 2: Makefile Tabs vs Spaces
**What goes wrong:** `Makefile:X: *** missing separator. Stop.`
**Why it happens:** Makefile recipes require literal tab characters, editors may insert spaces
**How to avoid:** Use `.editorconfig` or editor settings; always use tabs in recipe lines
**Warning signs:** Build failure on first `make` invocation

### Pitfall 3: Backup with Running SQLite (WAL Mode)
**What goes wrong:** Backup captures inconsistent database state
**Why it happens:** SQLite WAL mode uses -wal and -shm files alongside main DB
**How to avoid:** Use SQLite `.backup` command or ensure WAL checkpoint before copy. Alternatively, copy scanner.db + scanner.db-wal + scanner.db-shm together.
**Warning signs:** Restored database has missing recent data or corruption

### Pitfall 4: tar --transform Portability
**What goes wrong:** `--transform` flag doesn't work on macOS (BSD tar)
**Why it happens:** GNU tar extension, not POSIX
**How to avoid:** Since target is Linux (Docker deployment), this is acceptable. Document as GNU tar requirement. Alternatively, use a staging directory.
**Warning signs:** Package creation fails on macOS developer machines

### Pitfall 5: doc/ Path References After Restructuring
**What goes wrong:** README and cross-doc links point to `docs/architecture.md` instead of `docs/en/architecture.md`
**Why it happens:** Moving docs to `docs/en/` breaks all existing links
**How to avoid:** Update ALL references in README.md, README.ru.md, and cross-references within docs themselves
**Warning signs:** 404s when clicking documentation links

### Pitfall 6: Missing git in Docker for Buildx
**What goes wrong:** Multi-arch build fails because git is needed for cloning repos (scanner feature)
**Why it happens:** Current Dockerfile does not install git explicitly (relies on base image or docker compose context)
**How to avoid:** Verify Dockerfile installs git -- currently it does NOT install git in the apt-get line. This needs to be checked. Looking at the Dockerfile, `git` is mentioned in comments but NOT in the `apt-get install` line.
**Warning signs:** Scanner fails to clone repos in multi-arch built images

### Pitfall 7: .env.example Missing New Variables
**What goes wrong:** New users miss environment variables added in Phases 2-5
**Why it happens:** .env.example wasn't updated as new features were added
**How to avoid:** Cross-reference ScannerSettings fields with .env.example; add SCANNER_GIT_TOKEN, notification vars, etc.
**Warning signs:** Scanner fails on fresh deployment due to missing config

## Code Examples

### Makefile Complete Structure
```makefile
# aipix-security-scanner Makefile
# Wraps Docker Compose and utility commands

VERSION := $(shell python3 -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])" 2>/dev/null || grep -m1 'version' pyproject.toml | cut -d'"' -f2)
PACKAGE_NAME := aipix-security-scanner-$(VERSION)
REGISTRY ?= localhost
IMAGE_NAME ?= aipix-security-scanner
BACKUP_DIR := backups

.DEFAULT_GOAL := help

.PHONY: help install run stop test migrate backup restore package clean docker-multiarch docker-push

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Build Docker images
	docker compose build

run: ## Start scanner (detached)
	docker compose up -d

stop: ## Stop scanner
	docker compose down

test: ## Run test suite
	python -m pytest tests/ -v

migrate: ## Run Alembic database migrations
	docker compose exec scanner alembic upgrade head

backup: ## Backup DB + config to timestamped archive
	# implementation here

restore: ## Restore from backup (usage: make restore BACKUP=path/to/file.tar.gz)
	# implementation here

package: ## Create distributable archive
	tar czf $(PACKAGE_NAME).tar.gz \
		--transform 's,^,$(PACKAGE_NAME)/,' \
		Dockerfile docker-compose.yml config.yml.example .env.example \
		README.md LICENSE CONTRIBUTING.md \
		src/ pyproject.toml alembic/ alembic.ini docs/

clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true
	rm -f $(PACKAGE_NAME).tar.gz

docker-multiarch: ## Build multi-arch images (amd64 + arm64)
	docker buildx create --name multiarch --driver docker-container --use 2>/dev/null || docker buildx use multiarch
	docker buildx build --platform linux/amd64,linux/arm64 \
		-t $(IMAGE_NAME):$(VERSION) \
		--output type=oci,dest=$(PACKAGE_NAME)-multiarch.tar .

docker-push: ## Push multi-arch images to registry
	docker buildx build --platform linux/amd64,linux/arm64 \
		-t $(REGISTRY)/$(IMAGE_NAME):$(VERSION) --push .
```

### SQLite Safe Backup Pattern
```bash
# Safe backup approach for WAL-mode SQLite
# Option A: Use sqlite3 .backup command (safest)
docker compose exec scanner sqlite3 /data/scanner.db ".backup '/tmp/scanner_backup.db'"

# Option B: Checkpoint WAL then copy
docker compose exec scanner sqlite3 /data/scanner.db "PRAGMA wal_checkpoint(TRUNCATE);"
docker cp scanner:/data/scanner.db ./backup/scanner.db
```

### CONTRIBUTING.md Template
```markdown
# Contributing to aipix-security-scanner

## Development Setup

1. Clone the repository
2. Install development dependencies: `pip install -e ".[dev]"`
3. Run tests: `make test`

## Code Style

- Python 3.12+
- Type hints required
- Tests in `tests/phase_XX/` directories

## Pull Request Process

1. Create a feature branch from `main`
2. Add tests for new functionality
3. Ensure `make test` passes
4. Update documentation if needed
5. Submit PR with clear description
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| docker build for single arch | docker buildx for multi-arch | Docker Desktop 4.x+ | Single command builds for amd64+arm64 |
| Manual DB dump/load | SQLite file copy + Alembic | N/A (project-specific) | Simple backup = file copy |
| Single bilingual README | Separate language files | Common practice | Cleaner maintenance, git diff |

## Open Questions

1. **Git installation in Dockerfile**
   - What we know: The Dockerfile apt-get line does NOT include `git`, but the scanner needs git for repo cloning (SCAN-05)
   - What's unclear: How is git currently available? Possibly from python:3.12-slim base or a later layer?
   - Recommendation: Verify `git` availability in current Docker image; add to apt-get if missing

2. **Backup from stopped container**
   - What we know: `docker compose exec` requires a running container
   - What's unclear: Whether backup should work when scanner is stopped
   - Recommendation: Use volume mount path directly if container is stopped, or require running container with clear error message

3. **Config.yml in backup/restore**
   - What we know: config.yml is bind-mounted from host (`./config.yml:/app/config.yml:ro`)
   - What's unclear: Whether backup should include host-side config.yml or container-side
   - Recommendation: Backup host-side config.yml since that's the user's actual config

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `python -m pytest tests/phase_06/ -x -v` |
| Full suite command | `python -m pytest tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INFRA-06 | Makefile targets exist and have correct help text | unit | `python -m pytest tests/phase_06/test_makefile.py -x` | No - Wave 0 |
| INFRA-08 | make package produces correct tarball with expected files | integration | `python -m pytest tests/phase_06/test_package.py -x` | No - Wave 0 |
| INFRA-07 | Backup creates archive, restore extracts correctly | integration | `python -m pytest tests/phase_06/test_backup_restore.py -x` | No - Wave 0 |
| INFRA-02 | Dockerfile builds for multi-arch (buildx syntax validation) | manual-only | N/A (requires Docker daemon with buildx) | N/A |
| DOC-01 | README.md contains quick start, README.ru.md exists | unit | `python -m pytest tests/phase_06/test_docs.py::test_readme -x` | No - Wave 0 |
| DOC-02-09 | All 8 docs exist in docs/en/ and docs/ru/ | unit | `python -m pytest tests/phase_06/test_docs.py::test_docs_structure -x` | No - Wave 0 |
| DOC-10 | Russian docs exist for all English docs | unit | `python -m pytest tests/phase_06/test_docs.py::test_russian_docs -x` | No - Wave 0 |
| DOC-11 | LICENSE, CONTRIBUTING.md, CHANGELOG.md, .env.example exist | unit | `python -m pytest tests/phase_06/test_docs.py::test_meta_files -x` | No - Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/phase_06/ -x -v`
- **Per wave merge:** `python -m pytest tests/ -v`
- **Phase gate:** Full suite green before verification

### Wave 0 Gaps
- [ ] `tests/phase_06/` directory and `__init__.py`
- [ ] `tests/phase_06/test_makefile.py` -- validates Makefile targets parse correctly
- [ ] `tests/phase_06/test_package.py` -- validates package tarball contents
- [ ] `tests/phase_06/test_backup_restore.py` -- validates backup/restore archive structure
- [ ] `tests/phase_06/test_docs.py` -- validates documentation structure and completeness

## Sources

### Primary (HIGH confidence)
- [Docker Multi-platform Docs](https://docs.docker.com/build/building/multi-platform/) -- buildx multi-arch patterns
- [Docker Exporters Docs](https://docs.docker.com/build/exporters/) -- OCI export for local tar
- [Apache License 2.0 Text](https://www.apache.org/licenses/LICENSE-2.0.txt) -- official license text
- Project codebase analysis -- Dockerfile, docker-compose.yml, pyproject.toml, config.py, existing docs

### Secondary (MEDIUM confidence)
- [Docker Blog: Multi-arch the simple way](https://www.docker.com/blog/multi-arch-build-and-images-the-simple-way/) -- verified patterns
- [Makefile + Docker patterns](https://www.codyhiar.com/blog/makefiles-and-docker-for-local-development/) -- community best practices

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- GNU Make, docker buildx, tar are well-understood tools
- Architecture: HIGH -- project structure is straightforward file reorganization
- Pitfalls: HIGH -- common issues are well-documented in Docker and SQLite communities
- Documentation content: MEDIUM -- depth of doc updates depends on feature complexity in Phases 2-5

**Research date:** 2026-03-20
**Valid until:** 2026-04-20 (stable tools, no fast-moving dependencies)
