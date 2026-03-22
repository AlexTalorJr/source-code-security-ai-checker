# Phase 10: Infrastructure and Documentation - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning

<domain>
## Phase Boundary

The complete platform ships as a single Docker image with all 12 scanners (8 existing + 4 new from Phase 9) and up-to-date documentation in all 5 languages (EN, RU, FR, ES, IT). Covers Dockerfile updates for new scanner binaries, multi-arch builds, documentation updates across all doc files, and scanner verification tooling.

</domain>

<decisions>
## Implementation Decisions

### Docker packaging
- gosec: pre-built binary from GitHub releases, same pattern as gitleaks and trivy (download tarball, extract to /usr/local/bin)
- Bandit: `pip install bandit` alongside semgrep and checkov — same Python package pattern
- Brakeman: `apt-get install ruby` + `gem install brakeman` — adds ~80MB but straightforward, consistent with PHP tools pattern already in Dockerfile
- cargo-audit: pre-built binary from GitHub releases, same pattern as gosec/gitleaks/trivy
- All 4 new tools must handle multi-arch (x86_64 and ARM64) download URLs with architecture detection

### Documentation scope
- Update admin-guide.md with new "Plugin Registry" section (no separate plugin-guide.md) — scanner config already documented there, natural home for registry docs
- Update ALL 8 doc files across all 5 languages to reflect 12 scanners and plugin registry
- User-guide: per-scanner cards format — each scanner gets: name, language, what it detects, example finding. Consistent format for all 12 scanners
- Admin-guide: plugin registry config, scanner management, config.yml format with adapter_class
- DevOps-guide: Docker changes, new binaries, build process
- Architecture, API, custom-rules, database-schema, transfer-guide: update scanner references for consistency

### Documentation translation
- Full professional quality translations for all 5 languages (EN, RU, FR, ES, IT)
- Formal register across all languages — consistent with Phase 6 decision (formal "вы" for RU, formal "vous" for FR, "usted" for ES, "Lei" for IT)
- Technical terms stay in English where standard (Docker, API, SAST, SCA, etc.)
- README updated for all 5 languages: README.md (EN), README.ru.md (RU), README.fr.md (FR), README.es.md (ES), README.it.md (IT)

### Verification approach
- Smoke test with sample projects: include tiny sample projects (Go file, Python file, Ruby file, Rust Cargo.toml) and run each scanner against them inside Docker
- `make verify-scanners` Makefile target runs all scanner smoke tests inside the container — quick validation after build
- CI matrix build for multi-arch: build and test on both amd64 and arm64 in CI to catch arch-specific issues automatically

### Claude's Discretion
- Exact binary version pinning for gosec and cargo-audit releases
- Dockerfile layer ordering and optimization for cache efficiency
- Sample project file contents for smoke tests
- Architecture detection sed patterns for binary downloads
- CI configuration details (GitHub Actions matrix structure)
- Doc update depth per file — how much to expand each section beyond scanner count updates

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Docker infrastructure
- `Dockerfile` — Current single-stage build with 8 scanner installs. Extend with gosec, Bandit, Brakeman, cargo-audit
- `docker-compose.yml` — Service definition, volume mounts, healthcheck
- `Makefile` — Existing targets (install, run, test, package, docker-multiarch). Add verify-scanners target

### Scanner configuration
- `config.yml` — All 12 scanners registered with adapter_class and languages (Phase 8+9 output)
- `src/scanner/adapters/` — All adapter implementations including 4 new from Phase 9

### Documentation (all files to update)
- `docs/en/*.md` — 8 English doc files (admin-guide, user-guide, devops-guide, architecture, api, custom-rules, database-schema, transfer-guide)
- `docs/ru/*.md` — 8 Russian doc files
- `docs/fr/*.md` — 8 French doc files
- `docs/es/*.md` — 8 Spanish doc files
- `docs/it/*.md` — 8 Italian doc files
- `README.md` — English README
- `README.ru.md` — Russian README

### Prior phase context
- `.planning/phases/06-packaging-portability-and-documentation/06-CONTEXT.md` — Original Docker/docs decisions: multi-arch buildx, bilingual strategy, Makefile targets, formal RU tone
- `.planning/phases/08-plugin-registry-architecture/08-CONTEXT.md` — Plugin registry design: config-driven, adapter_class, /api/scanners endpoint
- `.planning/phases/09-tier-1-scanner-adapters/09-CONTEXT.md` — Adapter implementations, severity mapping, output parsing details

### Requirements
- `.planning/REQUIREMENTS.md` — INFRA-01 (Docker binaries), INFRA-02 (multi-arch), DOCS-01 (bilingual docs)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `Dockerfile`: Working single-stage build with established patterns for binary downloads (gitleaks, trivy), pip installs (semgrep, checkov), and apt+gem patterns (PHP tools)
- `Makefile`: Existing targets including `docker-multiarch` with buildx
- `docs/` structure: All 5 language directories with 8 files each — established file naming and structure
- Architecture detection patterns: `dpkg --print-architecture` and `uname -m` sed transforms already in Dockerfile

### Established Patterns
- Binary install: curl + tar to /usr/local/bin (gitleaks, trivy)
- pip install: single RUN line with --no-cache-dir (semgrep, checkov)
- apt + runtime: apt-get install + package manager install (PHP: php-cli + composer + psalm gem)
- Multi-arch: `docker buildx build --platform linux/amd64,linux/arm64`
- Doc structure: docs/{lang}/{doc-name}.md with matching file sets per language

### Integration Points
- Dockerfile: add 4 new RUN blocks following existing patterns
- Makefile: add `verify-scanners` target
- docs/: update all 40 doc files (8 files × 5 languages) + 5 READMEs
- CI: extend build matrix for multi-arch testing

</code_context>

<specifics>
## Specific Ideas

- Smoke tests are preferred over simple version checks — they catch runtime issues, not just binary existence
- All 5 README language variants should exist (expanding from current EN+RU pair)
- Per-scanner cards in user-guide should have consistent format across all 12 scanners

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 10-infrastructure-and-documentation*
*Context gathered: 2026-03-22*
