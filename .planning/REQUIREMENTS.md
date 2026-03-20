# Requirements: aipix-security-scanner

**Defined:** 2026-03-18
**Core Value:** Every release branch is automatically scanned for security vulnerabilities before deployment, and no code with Critical or High severity findings reaches production.

## v1 Requirements

### Scanning Engine

- [x] **SCAN-01**: Scanner runs Semgrep, cppcheck, Gitleaks, Trivy, and Checkov in parallel on target codebase
- [x] **SCAN-02**: All tool findings normalized to unified severity (Critical/High/Medium/Low/Info)
- [x] **SCAN-03**: Findings deduplicated across tools using stable fingerprints (file + rule + snippet hash)
- [x] **SCAN-04**: Scanner accepts local filesystem path as scan target
- [x] **SCAN-05**: Scanner accepts git repository URL + branch as scan target and clones automatically
- [x] **SCAN-06**: Each scanner tool has configurable timeout with graceful degradation on failure
- [x] **SCAN-07**: Total scan time under 10 minutes for a typical aipix release branch

### AI Analysis

- [x] **AI-01**: Claude API analyzes aggregated findings for business logic vulnerabilities (auth bypass, tenant isolation, IDOR)
- [x] **AI-02**: Claude generates code-level fix suggestions (before/after diffs) for each finding
- [x] **AI-03**: Claude correlates findings across tools to identify compound risks
- [x] **AI-04**: AI analysis cost stays under $5 per release scan
- [x] **AI-05**: Scanner functions correctly when Claude API is unavailable (graceful degradation)

### Reports

- [x] **RPT-01**: HTML interactive report with findings grouped by severity, filterable by component/tool
- [x] **RPT-02**: HTML report shows code context with line numbers and AI fix suggestions
- [x] **RPT-03**: PDF formal report with executive summary, severity breakdown, and finding details
- [x] **RPT-04**: Reports include scan metadata (date, branch, commit, duration, tool versions)

### Quality Gate

- [x] **GATE-01**: Scanner returns non-zero exit code when Critical or High findings exist
- [x] **GATE-02**: Severity thresholds configurable in config.yml
- [x] **GATE-03**: Quality gate decision included in scan output and reports

### Notifications

- [x] **NOTF-01**: Slack webhook notification on scan completion with severity summary
- [x] **NOTF-02**: Email notification on scan completion with severity summary
- [x] **NOTF-03**: Both notification channels independently configurable (enable/disable via config.yml)

### Scan History

- [x] **HIST-01**: All scan results stored in SQLite database with full finding details
- [x] **HIST-02**: Delta comparison between current and previous scan (new/fixed/persisting findings)
- [x] **HIST-03**: User can mark findings as false positive, suppressed across future scans
- [x] **HIST-04**: Scan history queryable via API (list scans, get scan details, get finding trends)

### API & Dashboard

- [x] **API-01**: FastAPI REST API to trigger scans (POST /api/scans with path or repo URL)
- [x] **API-02**: API returns scan status and results (GET /api/scans/{id})
- [x] **API-03**: API authenticated via API key in header
- [x] **API-04**: Health check endpoint (GET /api/health)
- [x] **API-05**: Live web dashboard showing scan history, finding trends, release comparison
- [x] **API-06**: Dashboard accessible via browser with API key authentication

### CI Integration

- [x] **CI-01**: Jenkinsfile.security stage ready to drop into existing pipelines
- [x] **CI-02**: Jenkins stage passes local workspace path to scanner
- [x] **CI-03**: Quality gate result determines Jenkins stage pass/fail

### Infrastructure

- [x] **INFRA-01**: Entire stack runs via single docker-compose up
- [x] **INFRA-02**: Docker images support x86_64 and ARM64 architectures
- [x] **INFRA-03**: All configuration via environment variables and config.yml
- [x] **INFRA-04**: No hardcoded paths, hostnames, or credentials in codebase
- [x] **INFRA-05**: SQLite database in mounted volume for persistence
- [x] **INFRA-06**: Makefile with targets: install, run, test, migrate, backup, restore, package
- [x] **INFRA-07**: Migration scripts for moving scan history between environments
- [x] **INFRA-08**: make package creates distributable archive

### Documentation

- [x] **DOC-01**: README.md with quick start (5 minutes to first scan)
- [x] **DOC-02**: docs/en/architecture.md and docs/ru/architecture.md — system design with diagrams
- [x] **DOC-03**: docs/en/database-schema.md — SQLite schema with Mermaid ER diagram
- [x] **DOC-04**: docs/en/user-guide.md — how to read reports, interpret findings
- [x] **DOC-05**: docs/en/admin-guide.md — configuration, thresholds, rule management
- [x] **DOC-06**: docs/en/devops-guide.md — deployment, Docker, Jenkins integration, backups
- [x] **DOC-07**: docs/en/api.md — REST API reference
- [x] **DOC-08**: docs/en/transfer-guide.md — migration to new server, onboarding checklist
- [x] **DOC-09**: docs/en/custom-rules.md — writing custom Semgrep rules
- [ ] **DOC-10**: All docs available in Russian (docs/ru/) as separate files
- [x] **DOC-11**: CHANGELOG.md, LICENSE (Apache 2.0), CONTRIBUTING.md, .env.example

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
| SCAN-01 | Phase 2 | Complete |
| SCAN-02 | Phase 1 | Complete |
| SCAN-03 | Phase 2 | Complete |
| SCAN-04 | Phase 2 | Complete |
| SCAN-05 | Phase 2 | Complete |
| SCAN-06 | Phase 2 | Complete |
| SCAN-07 | Phase 2 | Complete |
| AI-01 | Phase 3 | Complete |
| AI-02 | Phase 3 | Complete |
| AI-03 | Phase 3 | Complete |
| AI-04 | Phase 3 | Complete |
| AI-05 | Phase 3 | Complete |
| RPT-01 | Phase 4 | Complete |
| RPT-02 | Phase 4 | Complete |
| RPT-03 | Phase 4 | Complete |
| RPT-04 | Phase 4 | Complete |
| GATE-01 | Phase 4 | Complete |
| GATE-02 | Phase 4 | Complete |
| GATE-03 | Phase 4 | Complete |
| NOTF-01 | Phase 5 | Complete |
| NOTF-02 | Phase 5 | Complete |
| NOTF-03 | Phase 5 | Complete |
| HIST-01 | Phase 4 | Complete |
| HIST-02 | Phase 4 | Complete |
| HIST-03 | Phase 5 | Complete |
| HIST-04 | Phase 5 | Complete |
| API-01 | Phase 5 | Complete |
| API-02 | Phase 5 | Complete |
| API-03 | Phase 5 | Complete |
| API-04 | Phase 1 | Complete |
| API-05 | Phase 5 | Complete |
| API-06 | Phase 5 | Complete |
| CI-01 | Phase 5 | Complete |
| CI-02 | Phase 5 | Complete |
| CI-03 | Phase 5 | Complete |
| INFRA-01 | Phase 1 | Complete |
| INFRA-02 | Phase 6 | Complete |
| INFRA-03 | Phase 1 | Complete |
| INFRA-04 | Phase 1 | Complete |
| INFRA-05 | Phase 1 | Complete |
| INFRA-06 | Phase 6 | Complete |
| INFRA-07 | Phase 6 | Complete |
| INFRA-08 | Phase 6 | Complete |
| DOC-01 | Phase 6 | Complete |
| DOC-02 | Phase 6 | Complete |
| DOC-03 | Phase 6 | Complete |
| DOC-04 | Phase 6 | Complete |
| DOC-05 | Phase 6 | Complete |
| DOC-06 | Phase 6 | Complete |
| DOC-07 | Phase 6 | Complete |
| DOC-08 | Phase 6 | Complete |
| DOC-09 | Phase 6 | Complete |
| DOC-10 | Phase 6 | Pending |
| DOC-11 | Phase 6 | Complete |

**Coverage:**
- v1 requirements: 54 total
- Mapped to phases: 54
- Unmapped: 0

---
*Requirements defined: 2026-03-18*
*Last updated: 2026-03-18 after roadmap creation*
