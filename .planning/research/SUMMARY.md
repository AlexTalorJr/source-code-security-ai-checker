# Project Research Summary

**Project:** aipix-security-scanner
**Domain:** Automated security scanning pipeline for VSaaS platform (self-hosted, CI-integrated)
**Researched:** 2026-03-18
**Confidence:** HIGH

## Executive Summary

The aipix-security-scanner is a containerized, multi-tool security scanning pipeline that orchestrates five open-source scanners (Semgrep, cppcheck, Gitleaks, Trivy, Checkov) in parallel, enriches findings with Claude AI analysis, and produces actionable reports with quality gate enforcement. This is a well-understood domain -- LinkedIn, AWS, and others have published architectures for multi-scanner orchestration pipelines. The key innovation here is the AI enrichment layer for business-logic analysis specific to the aipix VSaaS platform, and the single-docker-compose portability requirement for partner distribution. All recommended stack components are mature, well-documented, and HIGH confidence.

The recommended approach is a four-layer pipeline architecture: parallel tool execution, finding normalization with deduplication, AI-powered semantic analysis, and report generation with quality gate. Python 3.12 with FastAPI provides the async orchestration backbone. SARIF serves as tool output format but NOT as the internal data model -- a purpose-built Finding dataclass is simpler and supports AI enrichment fields that SARIF lacks. The entire system runs in a single Docker container with SQLite for persistence, matching the portability constraint.

The top risks are: (1) alert fatigue from untuned default rulesets drowning developers in false positives -- mitigate by starting with minimal, high-severity rulesets and building suppression from day one; (2) AI hallucination of non-existent vulnerabilities or fabricated fixes -- mitigate by grounding AI prompts strictly to tool-detected findings with code context, never asking it to "find more"; (3) CI timeout brittleness when any tool hangs or the Claude API is down -- mitigate with per-tool timeouts, graceful degradation (skip AI if unavailable), and pre-baked Trivy vulnerability databases. The deduplication data model must be designed in Phase 1 because retrofitting it later has HIGH recovery cost.

## Key Findings

### Recommended Stack

The stack is entirely Python-based with external scanner binaries containerized in a single Docker image (~1.5-2GB). All technology choices are HIGH confidence with broad community adoption. See `.planning/research/STACK.md` for full details.

**Core technologies:**
- **Python 3.12 + FastAPI + Uvicorn**: Async-native API server and scan orchestrator. FastAPI provides auto-generated OpenAPI docs, SSE for live progress, and Pydantic validation.
- **Semgrep CE + cppcheck**: SAST coverage for PHP, C#, and C++. Semgrep handles most languages; cppcheck fills the C++ gap with proper buffer overflow and memory leak detection for the Mediaserver component.
- **Gitleaks + Trivy + Checkov**: Secrets detection, container/CVE scanning, and IaC scanning respectively. All produce SARIF output. Together they cover the full vulnerability surface.
- **Claude claude-sonnet-4-6 via anthropic SDK**: AI-powered semantic analysis at ~$3/1M input tokens. Targets $5/scan budget with 100-200K input tokens.
- **SQLite + SQLAlchemy 2.0 + aiosqlite**: Zero-config persistence for scan history. WAL mode for concurrent reads. Alembic for schema migrations.
- **Jinja2 + WeasyPrint**: HTML report templates with PDF conversion. No headless browser needed. WeasyPrint 68.1+ required (security fix).
- **httpx**: Async HTTP client for Slack webhooks and Bitbucket API calls.

**Critical version notes:** WeasyPrint must be >= 68.1 (security fix). Semgrep >= 1.156.0 (multicore performance). Pin scanner binaries to exact versions in Dockerfile for reproducible builds.

### Expected Features

See `.planning/research/FEATURES.md` for full feature landscape and dependency graph.

**Must have (table stakes):**
- Multi-tool SAST scanning with parallel execution (Semgrep, cppcheck, Gitleaks, Trivy, Checkov)
- Unified severity classification (Critical/High/Medium/Low/Info) across all tools
- Quality gate with configurable severity thresholds (pass/fail for CI)
- HTML interactive report with code context, severity filtering, collapsible sections
- PDF formal report for management and compliance
- Finding deduplication within and across tools
- Scan history and trending in SQLite
- Jenkins CI integration and REST API for triggering scans
- Configurable Slack/email notifications

**Should have (differentiators):**
- AI-powered semantic analysis for business logic flaws (RTSP auth, tenant isolation, webhook validation)
- AI-generated fix suggestions with actual code diffs
- Platform-specific custom Semgrep rules (the "moat" -- encodes institutional aipix security knowledge)
- Cross-tool finding correlation via AI (compound risk identification)
- Release-to-release delta comparison (new/fixed/persisting findings)
- False positive suppression with memory across scans
- Dual-mode scan input (local path for Jenkins, repo URL for API)

**Defer (v2+):**
- Bilingual reports (Russian/English) -- add i18n template structure early, translate later
- SARIF output format for external integrations
- Compliance framework mapping (PCI-DSS, SOC2) -- tag with CWE IDs now, map later
- DAST, IDE integration, user management, Jira integration, auto-remediation PRs

### Architecture Approach

The architecture follows a pipeline orchestrator pattern with four sequential layers. Layer 1 runs all five scanner tools in parallel via `asyncio.create_subprocess_exec` with per-tool timeouts. Layer 2 normalizes and deduplicates findings into a unified internal format, then optionally enriches with Claude AI analysis. Layer 3 generates HTML and PDF reports. Layer 4 evaluates the quality gate and fires notifications. The API uses an async job pattern -- POST returns a scan ID immediately, clients poll for status. See `.planning/research/ARCHITECTURE.md` for full component diagrams and data flow.

**Major components:**
1. **FastAPI Server** -- REST API, dashboard, scan lifecycle management
2. **Scan Orchestrator** -- Coordinates parallel tool execution with timeouts and graceful failure
3. **Scanner Adapters (x5)** -- Uniform interface wrapping each tool (adapter pattern); independently testable, trivial to add/remove tools
4. **Finding Normalizer** -- Parses tool-native output into unified Finding dataclass, deduplicates cross-tool
5. **AI Analysis Layer** -- Claude API integration with prompt batching by file, token budgeting, output validation
6. **Report Generator** -- Jinja2 HTML + WeasyPrint PDF from enriched findings
7. **Quality Gate** -- Configurable severity thresholds, produces pass/fail + exit code for Jenkins
8. **Config Manager** -- Three-tier: hardcoded defaults, config.yml overrides, env vars for secrets

### Critical Pitfalls

See `.planning/research/PITFALLS.md` for full analysis with warning signs and recovery strategies.

1. **Alert fatigue from untuned scanners** -- Five tools with default rulesets produce hundreds of findings. Start with minimal, high-severity rulesets. Build suppression mechanism from day one. Target under 20% false positive rate before enabling quality gate blocking. Must address in Phase 1.
2. **AI hallucinated vulnerabilities** -- Claude may fabricate CVEs, function names, or fixes. Never let AI be the sole source of any finding. Ground prompts to tool-detected findings only. Validate AI output references against actual code. Set temperature=0 and use structured output. Must address in Phase 2.
3. **Finding deduplication failure** -- Same vulnerability reported by multiple tools inflates counts 30-50%. Design unified Finding model with deterministic dedup keys from day one. Define tool priority for overlapping domains. HIGH recovery cost if retrofitted. Must address in Phase 1.
4. **CI timeout and brittleness** -- Scanner OOM (Semgrep on large C++), Trivy DB downloads, Claude API outages. Set per-tool timeouts, cache Trivy DB in Docker image, implement graceful degradation (skip failed tools, skip AI if unavailable). Must address in Phase 1 and Phase 3.
5. **WeasyPrint memory explosion** -- 2-4GB memory for 100+ finding reports. Cap findings per PDF, generate in subprocess with memory limits, make PDF lazy (generate on request, not automatically). Must address in Phase 2/3.
6. **Claude API cost overrun** -- Pre-filter to HIGH/CRITICAL only for AI. Implement token budget per scan (30K input max). Track cost in SQLite. Must address in Phase 2.

## Implications for Roadmap

Based on combined research, the build order is driven by a clear dependency chain: config/models must exist before adapters, adapters before normalization, normalization before AI, and all findings must exist before reports and quality gate. The architecture and features research both converge on the same phasing.

### Phase 1: Foundation and Core Infrastructure
**Rationale:** Everything depends on the config system, data models, database, and basic API skeleton. The unified Finding dataclass with dedup key must be designed here -- it is the spine of the entire system. Retrofitting dedup later has HIGH recovery cost per pitfalls research.
**Delivers:** Project skeleton, config loading (3-tier), Finding/ScanResult data models, SQLite with WAL mode and Alembic migrations, FastAPI app with health endpoint, Docker setup with python:3.12-slim base.
**Addresses:** Severity classification, configurable quality gate thresholds (data model only).
**Avoids:** Deduplication failure (designing model upfront), SQLite concurrency issues (WAL mode from day one), hardcoded config (config.yml from day one).

### Phase 2: Scanner Adapters and Orchestration
**Rationale:** The scanner adapters and parallel orchestration are the core value of the product. All five adapters can be built independently and in parallel. This phase also includes the normalizer and deduplication logic, which must exist before AI or reports.
**Delivers:** Five scanner adapters (Semgrep, cppcheck, Gitleaks, Trivy, Checkov), async parallel orchestration with per-tool timeouts, finding normalization and cross-tool deduplication, suppression mechanism.
**Addresses:** Multi-tool SAST scanning, parallel tool execution, finding deduplication, dual-mode scan input (local path + URL).
**Avoids:** Alert fatigue (tuned rulesets with severity filtering), CI timeout (per-tool timeouts and graceful degradation), monolithic scanner script (adapter pattern).

### Phase 3: AI Analysis Layer
**Rationale:** AI enrichment depends on normalized, deduplicated findings from Phase 2. This is the hardest phase to get right due to hallucination risk and cost control. Prompt engineering, output validation, and token budgeting must be designed together.
**Delivers:** Claude API integration, prompt construction with file-grouped batching, output validation (verify referenced files/functions exist), token budget enforcement, cost tracking in SQLite, graceful degradation when API unavailable.
**Addresses:** AI semantic analysis, AI fix suggestions, cross-tool finding correlation, platform-specific business logic review (RTSP, multi-tenant, webhooks).
**Avoids:** AI hallucination (grounded prompts, output validation, temperature=0), cost overrun (token budgeting, pre-filtering to HIGH/CRITICAL), full-source-to-AI anti-pattern.

### Phase 4: Reports and Quality Gate
**Rationale:** Reports consume enriched findings from Phase 3. Quality gate evaluates severity counts from normalized findings. These are the user-facing outputs that determine whether the scanner is trusted. WeasyPrint memory issues must be addressed here with finding caps and subprocess isolation.
**Delivers:** Jinja2 HTML interactive report, WeasyPrint PDF formal report, quality gate with configurable thresholds, pass/fail exit code for Jenkins.
**Addresses:** HTML/web report, PDF formal report, quality gate, severity-based filtering/sorting in reports.
**Avoids:** WeasyPrint memory explosion (cap findings, subprocess isolation), hard-coded thresholds (config.yml), zero-finding edge case in reports.

### Phase 5: CI Integration and Notifications
**Rationale:** Full Jenkins integration requires the complete pipeline (scan, report, gate) to be working. Notifications fire after quality gate decisions. This phase also includes the dashboard for scan history and the full REST API.
**Delivers:** Jenkins pipeline stage template, scan status polling API, dashboard with scan history and trending, Slack/email notifications with rate limiting, SSE for live scan progress.
**Addresses:** Jenkins CI integration, scan history/trending, configurable notifications, API for standalone scans.
**Avoids:** Synchronous API for long scans (async job pattern), notification noise (rate limiting, gate-change-only alerts), quality gate brittleness (degraded mode for scanner failures).

### Phase 6: Custom Rules and Polish
**Rationale:** Platform-specific Semgrep rules require understanding the aipix codebase patterns discovered during earlier scanning. Docker packaging and portability testing happen after the pipeline is feature-complete. Release-to-release comparison and false positive suppression build on the stable finding fingerprints established in Phase 2.
**Delivers:** Custom Semgrep rules for aipix patterns (RTSP auth, tenant isolation, webhook validation, MinIO access), release-to-release delta reports, false positive suppression with audit trail, Docker production packaging, documentation.
**Addresses:** Platform-specific custom rules, release-to-release comparison, false positive suppression, single docker-compose portability.
**Avoids:** Docker portability issues (pre-baked Trivy DB, non-root user, volume mounts for SQLite), scan cleanup failures (temp directory cleanup on all code paths).

### Phase Ordering Rationale

- **Dependency chain drives order:** Config/Models (P1) -> Adapters/Orchestrator (P2) -> AI (P3) -> Reports/Gate (P4) -> Integration (P5) -> Polish (P6). Each phase produces artifacts consumed by the next.
- **Feature grouping matches architecture layers:** Phase 2 = Layer 1 (tool execution), Phase 3 = Layer 2 (AI), Phase 4 = Layer 3 (reports) + Layer 4 (gate). This alignment reduces cross-cutting concerns.
- **Risk front-loading:** The two highest-recovery-cost pitfalls (deduplication failure, CI timeout) are addressed in Phases 1-2. The hardest technical challenge (AI hallucination control) is isolated in Phase 3 where it can be iterated without affecting the working scanner pipeline.
- **Incremental value:** After Phase 2, the scanner is independently useful (tools run, findings produced, no AI). After Phase 4, it is production-ready for CI. Phases 5-6 add operational maturity.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3 (AI Analysis):** Prompt engineering for security analysis is not well-documented. Optimal batch sizes, token budgets, and hallucination detection strategies need experimentation. The 29-45% vulnerability rate in AI-generated suggestions is concerning and requires validation testing.
- **Phase 4 (Reports):** WeasyPrint memory behavior needs profiling with realistic finding volumes (200+ findings). May need fallback plan to Playwright PDF if WeasyPrint proves unworkable for large reports.
- **Phase 6 (Custom Rules):** Writing effective Semgrep rules for aipix-specific patterns (RTSP, VMS multi-tenant) requires deep understanding of the codebase. Rules need to be developed alongside actual scanning of the aipix repos.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Foundation):** Standard FastAPI + SQLAlchemy + Pydantic setup. Well-documented patterns.
- **Phase 2 (Scanner Adapters):** Adapter pattern is textbook. asyncio subprocess execution is well-documented. Each tool's CLI and output format has official docs.
- **Phase 5 (CI Integration):** Jenkins pipeline stages, REST API polling, Slack webhooks are all well-established patterns.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All technologies are mature, well-documented, and widely adopted. Version recommendations verified against official release pages. No experimental or bleeding-edge choices. |
| Features | HIGH | Feature landscape validated against 6+ commercial and open-source competitors (SonarQube, Checkmarx, Snyk, DefectDojo, GitHub Advanced Security, Wiz). Clear consensus on table stakes. |
| Architecture | HIGH | Pipeline orchestrator pattern validated by LinkedIn SAST pipeline (InfoQ 2026), AWS DevSecOps reference, and multiple open-source implementations. Component boundaries are clean. |
| Pitfalls | HIGH | All critical pitfalls backed by specific GitHub issues, documented incidents, or research papers. WeasyPrint memory issues confirmed across three separate GitHub issues. AI hallucination rates from published research. |

**Overall confidence:** HIGH

### Gaps to Address

- **Optimal AI prompt structure for security analysis:** No established best practice exists. Requires experimentation during Phase 3 implementation. Start with the grounded-prompt pattern (tool finding + code context + specific question) and iterate.
- **Actual aipix codebase scan profile:** Scan time, finding volume, memory usage, and tool behavior on the real codebase are unknown. Must profile early in Phase 2 -- do not wait until CI integration. The 10-minute constraint may require additional tuning.
- **WeasyPrint viability for large reports:** Memory behavior at 200+ findings is a known risk. Validate during Phase 4 with synthetic test data. Have Playwright PDF as a documented fallback if WeasyPrint proves unusable.
- **Betterleaks vs Gitleaks decision:** Betterleaks (March 2026, same creator as Gitleaks) has 98.6% vs 70.4% recall, but is brand new. Revisit in 6 months. Build Gitleaks adapter with clean interface so swapping is trivial.
- **Bilingual report scope:** Research identified the need but not the specific translation requirements. Defer implementation but design Jinja2 templates with i18n placeholders from the start.

## Sources

### Primary (HIGH confidence)
- [Semgrep CE releases and docs](https://semgrep.dev/) -- SAST capabilities, custom rules, multicore performance
- [Trivy releases and docs](https://github.com/aquasecurity/trivy) -- container/CVE scanning, SARIF output
- [FastAPI official docs](https://fastapi.tiangolo.com/) -- async patterns, SSE, test client
- [SQLite WAL mode docs](https://www.sqlite.org/wal.html) -- concurrency handling
- [LinkedIn SAST Pipeline (InfoQ Feb 2026)](https://www.infoq.com/news/2026/02/linkedin-redesigns-sast-pipeline/) -- multi-scanner orchestration architecture
- [AWS DevSecOps CI/CD Pipeline](https://aws.amazon.com/blogs/devops/building-end-to-end-aws-devsecops-ci-cd-pipeline-with-open-source-sca-sast-and-dast-tools/) -- parallel execution patterns

### Secondary (MEDIUM confidence)
- [WeasyPrint GitHub issues #671, #1104, #2130](https://github.com/Kozea/WeasyPrint/issues/) -- memory behavior documentation
- [DefectDojo deduplication docs](https://docs.defectdojo.com/en/working_with_findings/finding_deduplication/) -- dedup algorithm reference
- [LLM hallucinations in code review (DiffRay)](https://diffray.ai/blog/llm-hallucinations-code-review/) -- hallucination rates and mitigation
- [AI code review architecture (ProjectDiscovery)](https://projectdiscovery.io/blog/ai-code-review-vs-neo) -- LLM + static analysis detection rates

### Tertiary (LOW confidence)
- **Betterleaks viability:** Single announcement blog post, no production track record. Revisit Q3 2026.
- **Optimal AI token budget:** $5/scan target is based on Sonnet pricing estimates, not measured data. Validate during Phase 3.

---
*Research completed: 2026-03-18*
*Ready for roadmap: yes*
