# Requirements: aipix-security-scanner

**Defined:** 2026-03-18
**Core Value:** Every release branch is automatically scanned for security vulnerabilities before deployment, and no code with Critical or High severity findings reaches production.

## v1 Requirements

### Scanning Engine

- [ ] **SCAN-01**: Scanner runs Semgrep, cppcheck, Gitleaks, Trivy, and Checkov in parallel on target codebase
- [ ] **SCAN-02**: All tool findings normalized to unified severity (Critical/High/Medium/Low/Info)
- [ ] **SCAN-03**: Findings deduplicated across tools using stable fingerprints (file + rule + snippet hash)
- [ ] **SCAN-04**: Scanner accepts local filesystem path as scan target
- [ ] **SCAN-05**: Scanner accepts git repository URL + branch as scan target and clones automatically
- [ ] **SCAN-06**: Each scanner tool has configurable timeout with graceful degradation on failure
- [ ] **SCAN-07**: Total scan time under 10 minutes for a typical aipix release branch

### AI Analysis

- [ ] **AI-01**: Claude API analyzes aggregated findings for business logic vulnerabilities (auth bypass, tenant isolation, IDOR)
- [ ] **AI-02**: Claude generates code-level fix suggestions (before/after diffs) for each finding
- [ ] **AI-03**: Claude correlates findings across tools to identify compound risks
- [ ] **AI-04**: AI analysis cost stays under $5 per release scan
- [ ] **AI-05**: Scanner functions correctly when Claude API is unavailable (graceful degradation)

### Reports

- [ ] **RPT-01**: HTML interactive report with findings grouped by severity, filterable by component/tool
- [ ] **RPT-02**: HTML report shows code context with line numbers and AI fix suggestions
- [ ] **RPT-03**: PDF formal report with executive summary, severity breakdown, and finding details
- [ ] **RPT-04**: Reports include scan metadata (date, branch, commit, duration, tool versions)

### Quality Gate

- [ ] **GATE-01**: Scanner returns non-zero exit code when Critical or High findings exist
- [ ] **GATE-02**: Severity thresholds configurable in config.yml
- [ ] **GATE-03**: Quality gate decision included in scan output and reports

### Notifications

- [ ] **NOTF-01**: Slack webhook notification on scan completion with severity summary
- [ ] **NOTF-02**: Email notification on scan completion with severity summary
- [ ] **NOTF-03**: Both notification channels independently configurable (enable/disable via config.yml)

### Scan History

- [ ] **HIST-01**: All scan results stored in SQLite database with full finding details
- [ ] **HIST-02**: Delta comparison between current and previous scan (new/fixed/persisting findings)
- [ ] **HIST-03**: User can mark findings as false positive, suppressed across future scans
- [ ] **HIST-04**: Scan history queryable via API (list scans, get scan details, get finding trends)

### API & Dashboard

- [ ] **API-01**: FastAPI REST API to trigger scans (POST /api/scans with path or repo URL)
- [ ] **API-02**: API returns scan status and results (GET /api/scans/{id})
- [ ] **API-03**: API authenticated via API key in header
- [ ] **API-04**: Health check endpoint (GET /api/health)
- [ ] **API-05**: Live web dashboard showing scan history, finding trends, release comparison
- [ ] **API-06**: Dashboard accessible via browser with API key authentication

### CI Integration

- [ ] **CI-01**: Jenkinsfile.security stage ready to drop into existing pipelines
- [ ] **CI-02**: Jenkins stage passes local workspace path to scanner
- [ ] **CI-03**: Quality gate result determines Jenkins stage pass/fail

### Infrastructure

- [ ] **INFRA-01**: Entire stack runs via single docker-compose up
- [ ] **INFRA-02**: Docker images support x86_64 and ARM64 architectures
- [ ] **INFRA-03**: All configuration via environment variables and config.yml
- [ ] **INFRA-04**: No hardcoded paths, hostnames, or credentials in codebase
- [ ] **INFRA-05**: SQLite database in mounted volume for persistence
- [ ] **INFRA-06**: Makefile with targets: install, run, test, migrate, backup, restore, package
- [ ] **INFRA-07**: Migration scripts for moving scan history between environments
- [ ] **INFRA-08**: make package creates distributable archive

### Documentation

- [ ] **DOC-01**: README.md with quick start (5 minutes to first scan)
- [ ] **DOC-02**: docs/en/architecture.md and docs/ru/architecture.md — system design with diagrams
- [ ] **DOC-03**: docs/en/database-schema.md — SQLite schema with Mermaid ER diagram
- [ ] **DOC-04**: docs/en/user-guide.md — how to read reports, interpret findings
- [ ] **DOC-05**: docs/en/admin-guide.md — configuration, thresholds, rule management
- [ ] **DOC-06**: docs/en/devops-guide.md — deployment, Docker, Jenkins integration, backups
- [ ] **DOC-07**: docs/en/api.md — REST API reference
- [ ] **DOC-08**: docs/en/transfer-guide.md — migration to new server, onboarding checklist
- [ ] **DOC-09**: docs/en/custom-rules.md — writing custom Semgrep rules
- [ ] **DOC-10**: All docs available in Russian (docs/ru/) as separate files
- [ ] **DOC-11**: CHANGELOG.md, LICENSE (Apache 2.0), CONTRIBUTING.md, .env.example

## v2 Requirements

### Custom Rules

- **RULES-01**: Custom Semgrep rules for Laravel VMS (SQL injection, XSS, insecure deserialization, route/middleware issues)
- **RULES-02**: Custom Semgrep rules for C++ Mediaserver (RTSP auth bypass, buffer overflows, format strings, unsafe string functions)
- **RULES-03**: Custom Semgrep rules for webhook signature validation
- **RULES-04**: Custom Semgrep rules for video archive IDOR patterns

### Advanced Features

- **ADV-01**: SARIF output format for integration with GitHub/Azure DevOps
- **ADV-02**: Bilingual HTML/PDF reports (language selection per scan)
- **ADV-03**: Compliance framework tagging (CWE IDs on findings)
- **ADV-04**: Bitbucket PR comments with inline finding annotations

## Out of Scope

| Feature | Reason |
|---------|--------|
| DAST (dynamic testing) | Requires running application and network access — different architecture entirely |
| SaaS-hosted scanner | Violates self-hosted constraint; portability is core value |
| IDE integration / real-time monitoring | Scanner is batch-oriented (CI/on-demand), not an IDE plugin |
| User management / RBAC | API key auth sufficient for internal tool; add reverse proxy with SSO if needed |
| CVE database maintenance | Trivy handles vulnerability DB updates |
| Jira / issue tracker integration | Export as JSON/SARIF; manual ticket creation sufficient for v1 |
| Auto-remediation / auto-fix PRs | AI suggestions in reports are safer than auto-commits |
| Windows host support | Linux containers only; Windows users use WSL2 |
| Flutter/Dart scanning | Immature tooling; focus on server-side first |
| PostgreSQL/MySQL | SQLite is the right choice for portability |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SCAN-01 | Phase 2 | Pending |
| SCAN-02 | Phase 1 | Pending |
| SCAN-03 | Phase 2 | Pending |
| SCAN-04 | Phase 2 | Pending |
| SCAN-05 | Phase 2 | Pending |
| SCAN-06 | Phase 2 | Pending |
| SCAN-07 | Phase 2 | Pending |
| AI-01 | Phase 3 | Pending |
| AI-02 | Phase 3 | Pending |
| AI-03 | Phase 3 | Pending |
| AI-04 | Phase 3 | Pending |
| AI-05 | Phase 3 | Pending |
| RPT-01 | Phase 4 | Pending |
| RPT-02 | Phase 4 | Pending |
| RPT-03 | Phase 4 | Pending |
| RPT-04 | Phase 4 | Pending |
| GATE-01 | Phase 4 | Pending |
| GATE-02 | Phase 4 | Pending |
| GATE-03 | Phase 4 | Pending |
| NOTF-01 | Phase 5 | Pending |
| NOTF-02 | Phase 5 | Pending |
| NOTF-03 | Phase 5 | Pending |
| HIST-01 | Phase 4 | Pending |
| HIST-02 | Phase 4 | Pending |
| HIST-03 | Phase 5 | Pending |
| HIST-04 | Phase 5 | Pending |
| API-01 | Phase 5 | Pending |
| API-02 | Phase 5 | Pending |
| API-03 | Phase 5 | Pending |
| API-04 | Phase 1 | Pending |
| API-05 | Phase 5 | Pending |
| API-06 | Phase 5 | Pending |
| CI-01 | Phase 5 | Pending |
| CI-02 | Phase 5 | Pending |
| CI-03 | Phase 5 | Pending |
| INFRA-01 | Phase 1 | Pending |
| INFRA-02 | Phase 6 | Pending |
| INFRA-03 | Phase 1 | Pending |
| INFRA-04 | Phase 1 | Pending |
| INFRA-05 | Phase 1 | Pending |
| INFRA-06 | Phase 6 | Pending |
| INFRA-07 | Phase 6 | Pending |
| INFRA-08 | Phase 6 | Pending |
| DOC-01 | Phase 6 | Pending |
| DOC-02 | Phase 6 | Pending |
| DOC-03 | Phase 6 | Pending |
| DOC-04 | Phase 6 | Pending |
| DOC-05 | Phase 6 | Pending |
| DOC-06 | Phase 6 | Pending |
| DOC-07 | Phase 6 | Pending |
| DOC-08 | Phase 6 | Pending |
| DOC-09 | Phase 6 | Pending |
| DOC-10 | Phase 6 | Pending |
| DOC-11 | Phase 6 | Pending |

**Coverage:**
- v1 requirements: 54 total
- Mapped to phases: 54
- Unmapped: 0

---
*Requirements defined: 2026-03-18*
*Last updated: 2026-03-18 after roadmap creation*
