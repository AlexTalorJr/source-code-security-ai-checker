# Phase 10: Infrastructure and Documentation - Research

**Researched:** 2026-03-22
**Domain:** Docker packaging, multi-arch builds, multilingual documentation
**Confidence:** HIGH

## Summary

Phase 10 extends the existing Docker image with 4 new scanner binaries (gosec, Bandit, Brakeman, cargo-audit), ensures multi-arch builds work for x86_64 and ARM64, adds a `make verify-scanners` smoke test target, and updates all 40 documentation files (8 files x 5 languages) plus 5 READMEs to reflect 12 scanners and the plugin registry architecture.

The Dockerfile already has well-established patterns for every installation method needed: binary tarballs (gitleaks, trivy), pip packages (semgrep, checkov), and apt+gem (PHP tools). The new scanners map directly onto these patterns. gosec and cargo-audit have confirmed pre-built Linux binaries for both amd64 and arm64. Bandit installs via pip alongside existing Python packages. Brakeman requires ruby + gem install.

**Primary recommendation:** Follow existing Dockerfile patterns exactly -- binary download for gosec/cargo-audit, pip for Bandit, apt+gem for Brakeman. Documentation updates are the bulk of the work: 45 files total need scanner count and plugin registry references updated.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- gosec: pre-built binary from GitHub releases, same pattern as gitleaks and trivy (download tarball, extract to /usr/local/bin)
- Bandit: `pip install bandit` alongside semgrep and checkov -- same Python package pattern
- Brakeman: `apt-get install ruby` + `gem install brakeman` -- adds ~80MB but straightforward, consistent with PHP tools pattern already in Dockerfile
- cargo-audit: pre-built binary from GitHub releases, same pattern as gosec/gitleaks/trivy
- All 4 new tools must handle multi-arch (x86_64 and ARM64) download URLs with architecture detection
- Update admin-guide.md with new "Plugin Registry" section (no separate plugin-guide.md)
- Update ALL 8 doc files across all 5 languages to reflect 12 scanners and plugin registry
- User-guide: per-scanner cards format -- each scanner gets: name, language, what it detects, example finding
- Admin-guide: plugin registry config, scanner management, config.yml format with adapter_class
- DevOps-guide: Docker changes, new binaries, build process
- Architecture, API, custom-rules, database-schema, transfer-guide: update scanner references for consistency
- Full professional quality translations for all 5 languages (EN, RU, FR, ES, IT)
- Formal register across all languages (formal "vy" for RU, formal "vous" for FR, "usted" for ES, "Lei" for IT)
- Technical terms stay in English where standard (Docker, API, SAST, SCA, etc.)
- README updated for all 5 language variants
- Smoke test with sample projects: include tiny sample projects (Go file, Python file, Ruby file, Rust Cargo.toml) and run each scanner against them inside Docker
- `make verify-scanners` Makefile target runs all scanner smoke tests inside the container
- CI matrix build for multi-arch

### Claude's Discretion
- Exact binary version pinning for gosec and cargo-audit releases
- Dockerfile layer ordering and optimization for cache efficiency
- Sample project file contents for smoke tests
- Architecture detection sed patterns for binary downloads
- CI configuration details (GitHub Actions matrix structure)
- Doc update depth per file -- how much to expand each section beyond scanner count updates

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| INFRA-01 | Docker image includes gosec, Bandit, Brakeman, and cargo-audit binaries | Verified binary availability for all 4 tools; established Dockerfile patterns for each install method; version numbers confirmed |
| INFRA-02 | Multi-arch build (x86_64, ARM64) works with new scanner binaries | Confirmed gosec and cargo-audit have arm64 Linux binaries; Bandit (pip) and Brakeman (gem) are architecture-independent; existing buildx infrastructure in Makefile |
| DOCS-01 | Bilingual documentation updated with new scanners and plugin architecture (EN, RU, FR, ES, IT) | Identified all 45 files to update; current docs reference "five scanners" -- must become 12; admin-guide needs Plugin Registry section; user-guide needs 4 new scanner cards |

</phase_requirements>

## Standard Stack

### Core (Already in Project)
| Tool | Version | Purpose | Install Pattern |
|------|---------|---------|-----------------|
| gosec | v2.25.0 | Go SAST scanner | Binary tarball from GitHub releases |
| Bandit | 1.9.4 | Python SAST scanner | `pip install --no-cache-dir bandit` |
| Brakeman | 8.0.4 | Ruby/Rails SAST scanner | `apt-get install ruby` + `gem install brakeman` |
| cargo-audit | 0.22.1 | Rust SCA scanner | Binary tarball from GitHub releases |
| Docker Buildx | (existing) | Multi-arch image builds | Already configured in Makefile |

### Version Verification
- gosec v2.25.0: Released 2026-03-19, confirmed via GitHub API. Linux assets: `gosec_2.25.0_linux_amd64.tar.gz`, `gosec_2.25.0_linux_arm64.tar.gz`
- Bandit 1.9.4: Confirmed via `pip index versions bandit`. Pure Python, arch-independent.
- Brakeman 8.0.4: Released 2026-02-27 per RubyGems. Requires Ruby >= 3.2.0. Pure Ruby gem, arch-independent.
- cargo-audit 0.22.1: Released 2025-02-04. Linux assets: `cargo-audit-x86_64-unknown-linux-gnu-v0.22.1.tgz`, `cargo-audit-aarch64-unknown-linux-gnu-v0.22.1.tgz`

## Architecture Patterns

### Dockerfile Extension Pattern

Each new scanner follows an existing pattern already in the Dockerfile:

**Pattern A: Binary tarball (gosec, cargo-audit)** -- matches gitleaks/trivy pattern
```dockerfile
# Install gosec
RUN ARCH=$(dpkg --print-architecture | sed 's/amd64/amd64/;s/arm64/arm64/') && \
    curl -sSL "https://github.com/securego/gosec/releases/download/v2.25.0/gosec_2.25.0_linux_${ARCH}.tar.gz" \
    | tar xz -C /usr/local/bin gosec

# Install cargo-audit
RUN ARCH=$(uname -m | sed 's/x86_64/x86_64-unknown-linux-gnu/;s/aarch64/aarch64-unknown-linux-gnu/') && \
    curl -sSL "https://github.com/rustsec/rustsec/releases/download/cargo-audit%2Fv0.22.1/cargo-audit-${ARCH}-v0.22.1.tgz" \
    | tar xz -C /usr/local/bin
```

**Pattern B: pip install (Bandit)** -- matches semgrep/checkov pattern
```dockerfile
# Install bandit via pip (alongside existing semgrep line, or separate RUN)
RUN pip install --no-cache-dir bandit
```

**Pattern C: apt + gem (Brakeman)** -- matches PHP tools pattern
```dockerfile
# Ruby is needed for Brakeman (already have apt-get pattern from PHP block)
# Option: add ruby to existing PHP apt-get block, or separate RUN
RUN apt-get update && apt-get install -y --no-install-recommends ruby && \
    rm -rf /var/lib/apt/lists/* && \
    gem install brakeman --no-document
```

### Recommended Layer Ordering (Claude's Discretion)

For cache efficiency, add new scanner installs BEFORE the non-root user creation and source copy:

```
Dockerfile order:
1. FROM python:3.12-slim
2. apt-get (system deps + cppcheck) -- EXTEND with ruby here
3. pip install semgrep -- ADD bandit here
4. gitleaks binary download
5. trivy binary download
6. pip install checkov
7. PHP tools block (apt + composer + psalm + php-security-checker)
8. NEW: gosec binary download
9. NEW: cargo-audit binary download
10. NEW: gem install brakeman (ruby already installed in step 2 or 7 area)
11. Non-root user creation
12. COPY source, pip install app
13. Entrypoint
```

Grouping the pip installs (semgrep + bandit + checkov) into fewer RUN commands reduces layers. However, keeping them separate preserves cache when only one version changes. Recommend adding bandit to the semgrep pip line for simplicity.

### Smoke Test Architecture

```
tests/smoke/
  go_sample/          # main.go with a known gosec issue (e.g., G101 hardcoded credential)
  python_sample/      # vuln.py with a known bandit issue (e.g., B105 hardcoded password)
  ruby_sample/        # Gemfile + app.rb for brakeman (e.g., SQL injection pattern)
  rust_sample/        # Cargo.toml with a known vulnerable dependency
```

The `make verify-scanners` target should:
1. Build or use existing Docker image
2. Copy sample projects into container (or mount)
3. Run each of the 12 scanners against its sample project
4. Verify non-zero findings (smoke test passes if scanner finds expected vulnerability)
5. Report pass/fail per scanner

### Documentation Update Matrix

| Doc File | Key Updates |
|----------|-------------|
| user-guide.md | Change "five" to "twelve" scanners; add 7 new scanner cards (4 new + 3 PHP that may be missing cards); per-scanner card format: name, language, what it detects, example finding |
| admin-guide.md | Update scanner config YAML to show all 12; add Plugin Registry section with adapter_class, /api/scanners endpoint; update "five scanner tools" references |
| devops-guide.md | Update Dockerfile description to mention all 12 scanners; add new binary install details; update multi-arch notes; add verify-scanners target docs |
| architecture.md | Update mermaid diagram to show all 12 adapters; update text from "five" to "twelve" |
| api.md | Add /api/scanners endpoint if not present; update scanner references |
| custom-rules.md | Update scanner references if any |
| database-schema.md | Minimal -- update scanner name references if present |
| transfer-guide.md | Update scanner references |
| README.md (x5) | Update scanner count, add new language coverage mentions |

### Anti-Patterns to Avoid
- **Separate Dockerfiles per arch:** Use buildx with single Dockerfile and architecture detection at build time
- **Installing cargo/rustc for cargo-audit:** Use pre-built binary, not `cargo install` (would add 1GB+ to image)
- **Translating technical terms:** Keep Docker, API, SAST, SCA, JSON, YAML, etc. in English across all languages
- **Inconsistent scanner counts:** Search-and-replace "five" / "cinq" / "cinco" etc. is error-prone; grep thoroughly for old counts

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Multi-arch builds | Custom build scripts per arch | `docker buildx build --platform linux/amd64,linux/arm64` | Buildx handles QEMU emulation, manifest lists |
| Architecture detection | Complex if/else bash | `dpkg --print-architecture` + `sed` transforms | Already proven in existing Dockerfile |
| Ruby runtime for Brakeman | Compile Ruby from source | `apt-get install ruby` | Debian packages are tested, maintained |
| Scanner verification | Manual docker exec commands | `make verify-scanners` with structured output | Repeatable, CI-friendly |

## Common Pitfalls

### Pitfall 1: cargo-audit URL encoding
**What goes wrong:** The GitHub release tag for cargo-audit is `cargo-audit/v0.22.1` with a slash. curl must URL-encode the slash as `%2F` in the download URL.
**Why it happens:** GitHub release tags can contain slashes; the download URL path uses the literal tag.
**How to avoid:** Use the exact URL format: `https://github.com/rustsec/rustsec/releases/download/cargo-audit%2Fv0.22.1/cargo-audit-{arch}-v0.22.1.tgz`
**Warning signs:** 404 errors during Docker build.

### Pitfall 2: Ruby gem install as non-root
**What goes wrong:** If `gem install brakeman` runs after the USER scanner directive, it fails with permission errors.
**Why it happens:** Gem install needs write access to system gem directory.
**How to avoid:** Install brakeman BEFORE the `USER scanner` line in Dockerfile.
**Warning signs:** Permission denied errors during build.

### Pitfall 3: Stale scanner counts in translations
**What goes wrong:** Updating English docs but forgetting to update the count in other languages (e.g., "cinq outils" in French stays as 5).
**Why it happens:** Scanner counts are embedded in prose text, not just config references.
**How to avoid:** Grep all doc files for numeric scanner counts (5, five, cinq, cinco, cinque, pyat') before marking docs complete.
**Warning signs:** Inconsistent numbers between language versions.

### Pitfall 4: Brakeman needs a Gemfile or Rails structure
**What goes wrong:** Brakeman exits with error if the target directory has no Gemfile or Rails-like structure.
**Why it happens:** Brakeman is specifically a Rails scanner.
**How to avoid:** Smoke test sample must include minimal Gemfile and Rails-like directory structure (app/controllers/).
**Warning signs:** Brakeman returns exit code 1 with "No Rails application detected" message.

### Pitfall 5: cargo-audit binary linked against glibc
**What goes wrong:** The `cargo-audit-*-unknown-linux-gnu-*` binary requires glibc, which is available in python:3.12-slim (Debian-based) but would fail on Alpine.
**Why it happens:** GNU binaries link against glibc dynamically.
**How to avoid:** Confirm base image is Debian-based (python:3.12-slim is). Use `-gnu` variant, not `-musl`.
**Warning signs:** "not found" or segfault when running cargo-audit inside container.

### Pitfall 6: Bandit pip conflict with existing packages
**What goes wrong:** Bandit's dependencies could conflict with semgrep or checkov versions.
**Why it happens:** All three are Python packages sharing the same pip environment.
**How to avoid:** Test `pip install --no-cache-dir bandit` in the existing image to verify no conflicts. Bandit has minimal dependencies (stevedore, PyYAML, rich) that are common.
**Warning signs:** pip resolver errors during Docker build.

## Code Examples

### gosec Dockerfile block
```dockerfile
# Source: https://github.com/securego/gosec/releases
# Matches existing gitleaks pattern in this Dockerfile
RUN ARCH=$(dpkg --print-architecture) && \
    curl -sSL "https://github.com/securego/gosec/releases/download/v2.25.0/gosec_2.25.0_linux_${ARCH}.tar.gz" \
    | tar xz -C /usr/local/bin gosec
```

### cargo-audit Dockerfile block
```dockerfile
# Source: https://github.com/rustsec/rustsec/releases
# Note: tag contains slash, URL-encoded as %2F
RUN ARCH=$(uname -m | sed 's/x86_64/x86_64-unknown-linux-gnu/;s/aarch64/aarch64-unknown-linux-gnu/') && \
    curl -sSL "https://github.com/rustsec/rustsec/releases/download/cargo-audit%2Fv0.22.1/cargo-audit-${ARCH}-v0.22.1.tgz" \
    | tar xz -C /usr/local/bin
```

### Bandit pip install
```dockerfile
# Add to existing semgrep pip line or as separate RUN
RUN pip install --no-cache-dir bandit
```

### Brakeman install
```dockerfile
# Ruby + Brakeman (add ruby to existing apt-get block or separate)
RUN apt-get update && apt-get install -y --no-install-recommends ruby && \
    rm -rf /var/lib/apt/lists/* && \
    gem install brakeman --no-document
```

### Makefile verify-scanners target
```makefile
verify-scanners: ## Smoke-test all 12 scanners inside Docker container
	@echo "Verifying scanners..."
	docker compose exec scanner semgrep --version
	docker compose exec scanner cppcheck --version
	docker compose exec scanner gitleaks version
	docker compose exec scanner trivy --version
	docker compose exec scanner checkov --version
	docker compose exec scanner psalm --version
	docker compose exec scanner local-php-security-checker --help
	docker compose exec scanner gosec --version 2>&1 | head -1
	docker compose exec scanner bandit --version
	docker compose exec scanner brakeman --version
	docker compose exec scanner cargo-audit --version
	@echo "All 12 scanners verified."
```

Note: The above is version-check only. The full smoke test with sample projects would be more involved -- running each scanner against a sample file and checking for expected findings.

### Scanner card format for user-guide
```markdown
### gosec (Go)

**Language:** Go
**Type:** SAST (static analysis)
**What it detects:** Hardcoded credentials, SQL injection, insecure crypto, unsafe file permissions, HTTP request smuggling
**Example finding:**
> G101: Potential hardcoded credentials in variable `apiKey` at `main.go:15`

**Enabled:** Automatically when Go files (`.go`) are detected in the repository.
```

## State of the Art

| Old State (Phase 6) | Current State (Phase 10) | Impact |
|----------------------|--------------------------|--------|
| 5 base scanners | 12 scanners (8 existing + 4 new) | Dockerfile must install 4 more tools |
| Hard-coded scanner list | Config-driven plugin registry (Phase 8) | Docs must explain adapter_class config |
| 2 languages (EN, RU) | 5 languages (EN, RU, FR, ES, IT) | 40 doc files + 5 READMEs to update |
| No scanner verification | `make verify-scanners` smoke tests | New Makefile target, sample projects |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (existing) |
| Config file | pyproject.toml (existing) |
| Quick run command | `python -m pytest tests/phase_10/ -x -v` |
| Full suite command | `python -m pytest tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INFRA-01 | Docker image contains all 12 scanner binaries | smoke | `make verify-scanners` (Docker required) | No -- Wave 0 |
| INFRA-02 | Multi-arch build succeeds for amd64 and arm64 | integration | `make docker-multiarch` (Docker + buildx required) | No -- Wave 0 |
| DOCS-01 | All doc files reference 12 scanners consistently | unit | `python -m pytest tests/phase_10/test_docs_consistency.py -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/phase_10/ -x -v`
- **Per wave merge:** `python -m pytest tests/ -v`
- **Phase gate:** Full suite green + `make verify-scanners` inside Docker

### Wave 0 Gaps
- [ ] `tests/phase_10/test_docs_consistency.py` -- grep-based test that all doc files reference correct scanner count and all 12 scanner names
- [ ] `tests/phase_10/conftest.py` -- shared fixtures (doc file paths, scanner name list)
- [ ] `tests/phase_10/__init__.py` -- package init
- [ ] `tests/smoke/` -- sample project files for scanner verification (Go, Python, Ruby, Rust)
- [ ] Makefile `verify-scanners` target -- scanner binary availability and smoke test

Note: INFRA-01 and INFRA-02 require Docker to validate. The pytest-based test for DOCS-01 can verify documentation consistency without Docker.

## Open Questions

1. **Ruby version in python:3.12-slim**
   - What we know: `apt-get install ruby` on Debian Bookworm (python:3.12-slim base) installs Ruby 3.1.x. Brakeman 8.0.4 requires Ruby >= 3.2.0.
   - What's unclear: Whether the Debian Bookworm ruby package meets Brakeman 8.0.4's minimum version requirement.
   - Recommendation: Test `apt-get install ruby && gem install brakeman` during implementation. If Ruby 3.1 is too old, use `apt-get install ruby3.2` from backports or install Ruby from a PPA. Alternatively, pin Brakeman to 7.x which supports Ruby 3.1.

2. **Enlightn scanner card in docs**
   - What we know: Enlightn is one of the 8 existing scanners but might not have a detailed card in user-guide.
   - What's unclear: Whether all 8 existing scanners already have cards, or only the original 5.
   - Recommendation: During implementation, audit existing scanner cards and add any missing ones to reach full 12-scanner coverage.

## Sources

### Primary (HIGH confidence)
- GitHub API: `securego/gosec` releases -- confirmed v2.25.0 with `linux_amd64` and `linux_arm64` tarballs
- GitHub API: `rustsec/rustsec` releases -- confirmed cargo-audit v0.22.1 with `x86_64-unknown-linux-gnu` and `aarch64-unknown-linux-gnu` tarballs
- pip index: Bandit 1.9.4 confirmed as latest
- Project files: Dockerfile, Makefile, docker-compose.yml, config.yml, docs/ -- read directly

### Secondary (MEDIUM confidence)
- RubyGems: Brakeman 8.0.4 (2026-02-27), requires Ruby >= 3.2.0
- Brakeman docs: https://brakemanscanner.org/docs/install/

### Tertiary (LOW confidence)
- Ruby version in Debian Bookworm apt repos -- needs validation during implementation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all versions confirmed via package registries and GitHub API
- Architecture: HIGH -- follows established patterns already working in Dockerfile
- Pitfalls: HIGH -- based on direct examination of release assets and Dockerfile constraints
- Documentation scope: HIGH -- all 45 files enumerated, current content reviewed

**Research date:** 2026-03-22
**Valid until:** 2026-04-15 (stable tools, pinned versions)
