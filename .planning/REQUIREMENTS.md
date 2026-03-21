# Requirements: Source Code Security AI Scanner

**Defined:** 2026-03-20
**Core Value:** Every code change is automatically scanned for security vulnerabilities before deployment

## v1.0.1 Requirements

### Plugin Architecture

- [x] **PLUG-01**: Scanner adapters can be registered via config.yml `adapter_class` field without code changes
- [ ] **PLUG-02**: Existing hard-coded ALL_ADAPTERS list migrated to config-driven registration
- [x] **PLUG-03**: Config validation warns on missing or invalid adapter_class references
- [ ] **PLUG-04**: SCANNER_LANGUAGES mapping extended for new scanner→language associations

### Scanner Integration

- [ ] **SCAN-01**: gosec adapter scans Go source code and produces FindingSchema-compatible results
- [ ] **SCAN-02**: Bandit adapter scans Python source code and produces FindingSchema-compatible results
- [ ] **SCAN-03**: Brakeman adapter scans Ruby/Rails applications and produces FindingSchema-compatible results
- [ ] **SCAN-04**: cargo-audit adapter scans Rust dependencies via Cargo.lock and produces FindingSchema-compatible results

### Infrastructure

- [ ] **INFRA-01**: Docker image includes gosec, Bandit, Brakeman, and cargo-audit binaries
- [ ] **INFRA-02**: Multi-arch build (x86_64, ARM64) works with new scanner binaries

### Documentation

- [ ] **DOCS-01**: Bilingual documentation updated with new scanners and plugin architecture (EN, RU, FR, ES, IT)

## Future Requirements

### SARIF & Tier 2 (v1.0.2)
- **SARIF-01**: Shared parse_sarif() helper for SARIF-capable tools
- **SCAN-05**: Grype adapter for SCA with EPSS+KEV risk scoring
- **SCAN-06**: security-code-scan adapter for C# SAST

### Incremental & DAST (v1.0.3)
- **INCR-01**: Opt-in incremental scanning for tools supporting file-list input
- **DAST-01**: Nuclei adapter for template-based DAST scanning
- **DEDUP-01**: Cross-tool deduplication layer

## Out of Scope

| Feature | Reason |
|---------|--------|
| Commercial/paid scanner integration | Open-source tools only |
| SpotBugs (Java) | Requires JVM + compiled .class files — high effort, defer |
| ZAP (DAST) | 500MB+ footprint, Nuclei preferred — defer to v1.0.3+ |
| eslint-plugin-security | Only 14 rules, Semgrep covers JS/TS better |
| OWASP Dependency-Check | Higher false positives than Trivy/Grype, XML-only |
| TruffleHog (as Gitleaks replacement) | Gitleaks faster/simpler for CI/CD |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PLUG-01 | Phase 8 | Complete |
| PLUG-02 | Phase 8 | Pending |
| PLUG-03 | Phase 8 | Complete |
| PLUG-04 | Phase 8 | Pending |
| SCAN-01 | Phase 9 | Pending |
| SCAN-02 | Phase 9 | Pending |
| SCAN-03 | Phase 9 | Pending |
| SCAN-04 | Phase 9 | Pending |
| INFRA-01 | Phase 10 | Pending |
| INFRA-02 | Phase 10 | Pending |
| DOCS-01 | Phase 10 | Pending |

**Coverage:**
- v1.0.1 requirements: 11 total
- Mapped to phases: 11
- Unmapped: 0

---
*Requirements defined: 2026-03-20*
