# Requirements: Source Code Security AI Scanner

**Defined:** 2026-03-22
**Core Value:** Every code change is automatically scanned for security vulnerabilities before deployment

## v1.0.2 Requirements

### RBAC & Authentication

- [x] **AUTH-01**: Admin can create user accounts with username and password
- [x] **AUTH-02**: User can log in to dashboard with username and password
- [x] **AUTH-03**: User can generate and revoke personal API tokens for CI/CD
- [x] **AUTH-04**: Admin role has full access to all endpoints and dashboard pages
- [x] **AUTH-05**: Viewer role can view scan results and reports but cannot trigger scans or change settings
- [x] **AUTH-06**: Scanner role can trigger scans and view results via API only (no dashboard config access)
- [x] **AUTH-07**: Unauthenticated requests to API return 401

### Scanner Configuration

- [ ] **CONF-01**: Admin can enable/disable individual scanners from the dashboard
- [ ] **CONF-02**: Admin can edit per-scanner settings (timeout, extra args) from the dashboard
- [ ] **CONF-03**: Admin can edit config.yml via web-based YAML editor with syntax highlighting
- [ ] **CONF-04**: Admin can create and save named scan profiles (e.g. "Quick scan", "Full audit")
- [ ] **CONF-05**: User can select a scan profile when triggering a scan via API or dashboard

### DAST (Nuclei)

- [ ] **DAST-01**: Nuclei adapter scans target URLs using templates and produces FindingSchema-compatible results
- [ ] **DAST-02**: Scan API accepts optional target_url field for DAST scans
- [x] **DAST-03**: Nuclei binary installed in Docker image with multi-arch support
- [ ] **DAST-04**: Nuclei findings appear in HTML/PDF reports alongside SAST findings

### Infrastructure

- [x] **INFRA-03**: SQLite busy_timeout configured to prevent write contention
- [ ] **INFRA-04**: Bilingual documentation updated with RBAC, scanner config UI, and DAST features (EN, RU, FR, ES, IT)

## Future Requirements

### SARIF & Tier 2 (v1.0.3+)
- **SARIF-01**: Shared parse_sarif() helper for SARIF-capable tools
- **SCAN-05**: Grype adapter for SCA with EPSS+KEV risk scoring
- **SCAN-06**: security-code-scan adapter for C# SAST

### Incremental Scanning (v1.0.3+)
- **INCR-01**: Opt-in incremental scanning for tools supporting file-list input
- **DEDUP-01**: Cross-tool deduplication layer

### Advanced DAST (v1.0.3+)
- **DAST-05**: DAST target management (save/edit target URLs)
- **DAST-06**: DAST-specific report section with URL-based grouping
- **DAST-07**: Scheduled DAST scans

### Advanced Auth (v1.0.3+)
- **AUTH-08**: OAuth/SSO/LDAP integration
- **AUTH-09**: User self-registration with admin approval
- **AUTH-10**: Audit log of user actions

## Out of Scope

| Feature | Reason |
|---------|--------|
| OAuth/SSO/LDAP integration | Simple local auth only for v1.0.2 |
| User self-registration | Admin creates accounts |
| Full DAST pipeline (target management, scheduling) | Nuclei adapter only for v1.0.2 |
| Legacy X-API-Key backward compatibility | Clean break to new token auth |
| PostgreSQL/MySQL support | SQLite only for portability |
| Commercial/paid scanner integration | Open-source tools only |
| ZAP (DAST) | Nuclei preferred — 30MB vs 500MB+ |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 | Phase 12 | Complete |
| AUTH-02 | Phase 12 | Complete |
| AUTH-03 | Phase 12 | Complete |
| AUTH-04 | Phase 12 | Complete |
| AUTH-05 | Phase 12 | Complete |
| AUTH-06 | Phase 12 | Complete |
| AUTH-07 | Phase 12 | Complete |
| CONF-01 | Phase 14 | Pending |
| CONF-02 | Phase 14 | Pending |
| CONF-03 | Phase 14 | Pending |
| CONF-04 | Phase 15 | Pending |
| CONF-05 | Phase 15 | Pending |
| DAST-01 | Phase 13 | Pending |
| DAST-02 | Phase 13 | Pending |
| DAST-03 | Phase 13 | Complete |
| DAST-04 | Phase 13 | Pending |
| INFRA-03 | Phase 12 | Complete |
| INFRA-04 | Phase 15 | Pending |

**Coverage:**
- v1.0.2 requirements: 18 total
- Mapped to phases: 18
- Unmapped: 0

---
*Requirements defined: 2026-03-22*
