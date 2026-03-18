# Feature Landscape

**Domain:** Automated security scanning pipeline for VSaaS platform (self-hosted, CI-integrated)
**Researched:** 2026-03-18

## Table Stakes

Features users expect. Missing = product feels incomplete or untrustworthy.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Multi-tool SAST scanning | Every serious scanner aggregates multiple engines. SonarQube, Checkmarx, and Snyk all cover SAST as baseline. Single-tool scanners are toys. | Medium | Semgrep + cppcheck covers PHP/C#/C++. Already planned. |
| Secrets detection | GitHub Advanced Security ships push protection and secret scanning as a standalone product ($19/mo/committer). It is the minimum bar. Gitleaks is the standard OSS choice. | Low | Gitleaks already planned. Must scan git history, not just current files. |
| Container and dependency CVE scanning | Snyk's core value prop is SCA/container scanning. Trivy is the OSS standard. Not having this means missing an entire vulnerability class. | Low | Trivy already planned. Covers Docker images + K8s manifests. |
| IaC scanning | Checkov/tfsec are expected for any pipeline touching Kubernetes or Docker Compose. Wiz, Bridgecrew (now Palo Alto) established this as table stakes. | Low | Checkov already planned for Helm charts and docker-compose. |
| Quality gate (pass/fail on severity) | SonarQube popularized quality gates. Every CI security tool now supports fail-on-severity. Without this, the scanner is advisory-only and gets ignored. | Low | Block on Critical/High. Must be configurable (threshold per severity level). |
| CI/CD pipeline integration | Must run as a stage in existing CI. Jenkins, GitLab CI, GitHub Actions -- the tool must fit into the build, not replace it. | Low | Jenkins integration planned. Provide shell script / stage template. |
| Severity classification | Findings must map to severity levels (Critical/High/Medium/Low/Info). Users expect CVSS or equivalent scoring. Without it, prioritization is impossible. | Low | Normalize severities across all tools to a unified scale. |
| HTML/web report with findings detail | Every tool from SonarQube to Checkmarx provides a web view of findings with code context, file paths, and severity. PDF-only is not enough for developers. | Medium | Interactive HTML report with code snippets, line numbers, collapsible sections. Already planned. |
| PDF formal report | Management and compliance teams expect downloadable PDF summaries. DefectDojo, Checkmarx, and Veracode all provide this. | Medium | WeasyPrint for PDF generation. Already planned. |
| Scan history and trending | DefectDojo's core value is tracking findings over time. Users need to see "are we getting better or worse?" | Medium | SQLite-backed scan history. Show finding counts over time per release. |
| Configurable notifications | Slack/email alerts on scan completion or findings above threshold. Every CI tool supports this. | Low | Already planned. Make channels configurable per severity level. |
| API for triggering scans | REST API to kick off scans programmatically. Every enterprise scanner provides this. Without it, the tool is Jenkins-only. | Low | FastAPI already planned. POST /scan with repo URL or local path. |
| Parallel tool execution | Running SAST tools sequentially wastes CI time. SonarQube and commercial scanners run analyses in parallel. Users expect scans under 10 minutes. | Medium | Layer 1 parallel execution already in architecture. Critical for the 10-min constraint. |
| Finding deduplication (same tool, across runs) | The same vulnerability found in consecutive scans must be recognized as the same issue. DefectDojo's deduplication algorithm is the gold standard. Without this, every scan looks like a new disaster. | Medium | Hash findings by file + line + rule ID + snippet. Track across scan runs. |

## Differentiators

Features that set the product apart. Not expected in every scanner, but high-value.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| AI-powered semantic analysis | No OSS scanner does this. Claude API reviewing aggregated findings for business logic flaws (RTSP auth bypass, tenant isolation, webhook validation) is genuinely novel. Checkmarx has "KICS AI" but it's marketing fluff. | High | Layer 2 in the architecture. Must be cost-controlled ($5/scan target). Send summarized findings + code context, not raw output. |
| AI-generated fix suggestions | Snyk provides "fix PRs" for dependency upgrades. AI fix suggestions for SAST findings with actual code diffs are a step beyond what OSS tools offer. | High | Generate as part of AI analysis. Show before/after code in reports. Key value for developers who don't know how to fix security issues. |
| Platform-specific custom rules | Generic Semgrep rules miss domain-specific issues. Custom rules for RTSP stream auth, VMS multi-tenant authorization, webhook signature verification, and MinIO access patterns catch what generic scanners cannot. | High | Write custom .yaml Semgrep rules. This is the moat -- rules encode institutional security knowledge specific to aipix. |
| Cross-tool finding correlation | When Semgrep finds an auth bypass AND Gitleaks finds a hardcoded API key in the same component, that is worse than either alone. Correlating findings across tools is something only DefectDojo does well, and even then it's manual. | High | AI layer can do this -- feed findings from all tools, ask Claude to identify compound risks. |
| Release-to-release comparison (delta report) | Show what's new, what's fixed, and what persists between releases. Checkmarx supports incremental scans and delta views. Most OSS pipelines don't. | Medium | Compare current scan against previous scan for same project. Requires stable finding fingerprints. |
| Dual-mode scan input (path + URL) | Jenkins passes local paths; API users pass repo URLs. Supporting both makes the tool usable standalone and in CI. Most scanners support only one mode. | Low | Already planned. Clone repo if URL provided, use local path otherwise. |
| Bilingual reports (Russian/English) | Specific to the aipix ecosystem serving Russian telecom operators. No generic scanner handles this. | Medium | Jinja2 templates with i18n. Report language as a scan parameter. |
| Single docker-compose portability | Enterprise scanners require complex deployments. "Transfer to partner, run docker-compose up" is a genuine advantage for the aipix partner ecosystem. | Low | Already a constraint. Keep all state in mounted volumes. |
| False positive suppression with memory | Mark a finding as false positive once, and it stays suppressed in future scans. DefectDojo does this well. Most OSS pipelines re-report everything every time. | Medium | Store suppression decisions in SQLite keyed by finding fingerprint. Carry forward across scans. |
| SARIF output format | SARIF is the OASIS standard for static analysis interchange. GitHub Code Security, Azure DevOps, and many tools consume SARIF. Producing SARIF output makes the scanner composable with other platforms. | Low | Semgrep and Trivy already produce SARIF. Aggregate into unified SARIF for the full scan. |

## Anti-Features

Features to explicitly NOT build. These add complexity without matching the project's constraints.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| DAST (dynamic testing) | Out of scope for v1 per PROJECT.md. DAST requires running application, network access, and vastly different architecture. ZAP/Burp integration would double complexity. | Focus on SAST + SCA + IaC + secrets. DAST is a separate tool/project. |
| SaaS-hosted scanner | Violates the self-hosted constraint. The entire value prop is portability and no external dependencies. | Keep everything in Docker containers. No phone-home, no cloud dependency. |
| Real-time code monitoring / IDE integration | File watchers, LSP servers, and IDE plugins are a separate product category. The scanner is batch-oriented (scan-on-demand and CI-triggered). | Provide clear CLI invocation so developers can run locally if they want, but don't build IDE plugins. |
| User management / RBAC | SQLite + API key auth is appropriate for an internal tool. Building user accounts, roles, and permissions is enterprise scanner territory (SonarQube has this) and adds massive complexity. | Single API key in environment variable. If multi-user needed later, put a reverse proxy with SSO in front. |
| Vulnerability database / CVE tracking | Trivy already pulls CVE databases. Building and maintaining your own CVE database is a full-time job (see NVD, OSV). | Rely on Trivy's vulnerability DB updates. Don't reinvent this. |
| Jira / issue tracker integration | DefectDojo's bi-directional Jira sync is complex and brittle. For v1, creating Jira tickets manually from report links is sufficient. | Export findings as structured data (JSON/SARIF). Let users integrate downstream. |
| Compliance framework mapping (PCI-DSS, SOC2) | Mapping findings to compliance controls requires deep domain expertise and ongoing maintenance. DefectDojo and Checkmarx charge enterprise prices for this. | Tag findings with CWE IDs where available. Compliance mapping is a v2+ concern. |
| Auto-remediation / auto-fix PRs | Snyk's auto-fix PRs work for dependency upgrades (bump version). Auto-fixing code vulnerabilities is unreliable and dangerous. AI suggestions in reports are safer. | Provide fix suggestions in reports. Never auto-commit changes. |
| Windows host support | Linux containers only per PROJECT.md. Docker Desktop on Windows is not targeted. | Document that Windows users should use WSL2. |
| Mobile app scanning (Flutter/Dart) | Deferred per PROJECT.md. Flutter analysis tooling is immature for security. | Focus on server-side (PHP, C++, C#, K8s). Revisit when Semgrep Dart support matures. |
| PostgreSQL/MySQL support | SQLite is the right choice for portability. External DB adds deployment complexity that contradicts the single-compose goal. | SQLite with WAL mode for concurrent reads. Backup is just copying a file. |

## Feature Dependencies

```
Severity Classification --> Quality Gate (gate needs severity levels)
Severity Classification --> Notifications (alert thresholds need severity)
Multi-tool SAST Scanning --> Finding Deduplication (dedup needs normalized findings)
Multi-tool SAST Scanning --> AI Semantic Analysis (AI reviews aggregated findings)
Finding Deduplication --> Release-to-Release Comparison (delta needs stable fingerprints)
Finding Deduplication --> False Positive Suppression (suppression needs stable fingerprints)
Scan History --> Release-to-Release Comparison (delta needs historical data)
AI Semantic Analysis --> AI Fix Suggestions (fixes come from the same AI pass)
AI Semantic Analysis --> Cross-tool Finding Correlation (correlation is an AI task)
HTML/Web Report --> PDF Report (PDF is rendered from same data, different template)
API for Triggering Scans --> Dual-mode Scan Input (API accepts URL; Jenkins passes path)
Parallel Tool Execution --> CI Time Constraint (parallelism is how you hit 10 min)
```

## MVP Recommendation

**Prioritize (Phase 1 -- working pipeline):**

1. **Multi-tool SAST scanning** with unified output -- Semgrep, cppcheck, Gitleaks, Trivy, Checkov running in parallel
2. **Severity classification** -- normalize all tool outputs to Critical/High/Medium/Low/Info
3. **Quality gate** -- pass/fail based on configurable severity thresholds
4. **HTML interactive report** -- findings with code context, severity, tool source
5. **Jenkins integration** -- run as a pipeline stage, local path input
6. **Finding deduplication** within a single scan (cross-tool, same file+line+type)

**Prioritize (Phase 2 -- AI and reporting):**

7. **AI semantic analysis** -- Claude reviews findings for business logic issues
8. **AI fix suggestions** -- code-level remediation guidance in reports
9. **Platform-specific custom Semgrep rules** -- RTSP, VMS, webhook patterns
10. **PDF formal report** -- management-ready output
11. **Scan history** in SQLite -- track scans over time

**Prioritize (Phase 3 -- operational maturity):**

12. **Release-to-release delta comparison** -- what changed since last scan
13. **False positive suppression** -- mark and remember across scans
14. **Notifications** -- Slack and email on findings
15. **REST API** for standalone scans (URL input mode)
16. **Cross-tool finding correlation** via AI

**Defer:**

- **Bilingual reports**: Low priority until partner transfer is imminent. Add i18n template support early but translate later.
- **SARIF output**: Nice to have. Most value if integrating with GitHub/Azure later.
- **Compliance mapping**: v2+ territory. Tag with CWE IDs now, map to frameworks later.

**Rationale:** The dependency chain drives ordering. You cannot build AI analysis without normalized multi-tool output. You cannot build delta reports without scan history and deduplication. You cannot suppress false positives without stable finding fingerprints. Phase 1 builds the foundation that everything else depends on.

## Sources

- [Snyk vs SonarQube 2026 Comparison](https://konvu.com/compare/snyk-vs-sonarqube)
- [SonarQube vs Checkmarx Comparison](https://www.aikido.dev/blog/sonarqube-vs-checkmarx)
- [Checkmarx vs Snyk vs SonarQube Comparison](https://sourceforge.net/software/compare/Checkmarx-vs-Snyk-vs-SonarQube/)
- [DefectDojo Platform Overview](https://defectdojo.com/platform)
- [DefectDojo Auto-Triage and Deduplication](https://defectdojo.com/blog/auto-triage-and-deduplicate-security-findings-to-reduce-alert-fatigue)
- [GitHub Advanced Security Restructuring](https://github.blog/changelog/2025-03-04-introducing-github-secret-protection-and-github-code-security/)
- [GitHub Security Features Docs](https://docs.github.com/en/code-security/getting-started/github-security-features)
- [SARIF Standard Overview - Sonar](https://www.sonarsource.com/resources/library/sarif/)
- [Semgrep CI Integration](https://semgrep.dev/docs/semgrep-ci/overview/)
- [Semgrep Policy Management API](https://semgrep.dev/blog/2025/automating-security-workflows-with-the-semgrep-policy-management-api/)
- [Checkmarx Incremental Scanning](https://docs.checkmarx.com/en/34965-68557-scanning-projects.html)
- [CI/CD Security Scanning Best Practices - Wiz](https://www.wiz.io/academy/application-security/ci-cd-security-scanning)
- [DevSecOps CI/CD Security Gate](https://infosecwriteups.com/devsecops-phase-3-build-stage-ci-cd-security-gate-with-sast-sca-a61d988d32d7)
- [False Positives in Vulnerability Scanning - Anchore](https://anchore.com/blog/false-positives-and-false-negatives-in-vulnerability-scanning/)
