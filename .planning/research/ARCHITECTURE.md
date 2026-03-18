# Architecture Patterns

**Domain:** Automated security scanning pipeline for VSaaS platform
**Researched:** 2026-03-18

## Recommended Architecture

The scanner follows a **pipeline orchestrator pattern** with four sequential layers, where Layer 1 runs tools in parallel for speed, and subsequent layers depend on prior layer output. This matches how LinkedIn, AWS, and other large-scale SAST pipelines structure multi-tool scanning: parallel execution of independent analyzers, normalized result aggregation, then post-processing.

```
                         +-------------------+
                         |   Entry Points    |
                         | (API / Jenkins)   |
                         +--------+----------+
                                  |
                                  v
                         +-------------------+
                         |  Scan Orchestrator |
                         |  (async Python)    |
                         +--------+----------+
                                  |
                    +-------------+-------------+
                    |             |             |
                    v             v             v
              +---------+  +---------+  +-----------+
              | Semgrep |  |Gitleaks |  |  Trivy    |
              |+cppcheck|  |         |  | +Checkov  |
              +---------+  +---------+  +-----------+
                    |             |             |
                    v             v             v
                  +---------------------------+
                  |   Finding Normalizer      |
                  |   (unified internal fmt)  |
                  +------------+--------------+
                               |
                               v
                  +---------------------------+
                  |   AI Analysis Layer       |
                  |   (Claude API)            |
                  +------------+--------------+
                               |
                               v
                  +---------------------------+
                  |   Report Generator        |
                  |   (HTML / PDF)            |
                  +------------+--------------+
                               |
                               v
                  +---------------------------+
                  |   Quality Gate            |
                  |   (pass/fail decision)    |
                  +------------+--------------+
                               |
                     +---------+---------+
                     |                   |
                     v                   v
               +-----------+     +-----------+
               |Notifications|   | Exit Code |
               |(Slack/Email)|   | (Jenkins) |
               +-----------+     +-----------+
```

### Component Boundaries

| Component | Responsibility | Communicates With | Input | Output |
|-----------|---------------|-------------------|-------|--------|
| **FastAPI Server** | REST API, dashboard, scan lifecycle management | Scan Orchestrator, SQLite, Report Store | HTTP requests (trigger scan, fetch reports) | JSON responses, HTML dashboard |
| **Scan Orchestrator** | Coordinates tool execution, manages parallelism, timeouts | All scanner adapters, Finding Normalizer | Scan request (repo path or URL, config) | Raw tool outputs |
| **Scanner Adapters** (x5) | Wraps each tool (Semgrep, cppcheck, Gitleaks, Trivy, Checkov) with uniform interface | CLI tools via subprocess, Finding Normalizer | Source code path, tool-specific config | Tool-native output (JSON/SARIF) |
| **Finding Normalizer** | Parses tool-native output into unified internal format, deduplicates | Scanner Adapters, AI Analysis Layer | Raw tool outputs in various formats | Normalized finding list |
| **AI Analysis Layer** | Semantic analysis of findings, business logic review, fix suggestions | Claude API, Finding Normalizer | Normalized findings + source code context | Enriched findings with AI assessment |
| **Report Generator** | Renders HTML interactive and PDF formal reports | Jinja2 templates, WeasyPrint | Enriched findings | HTML/PDF files |
| **Quality Gate** | Evaluates severity thresholds, produces pass/fail decision | Report Generator output, config | Finding severity counts | Pass/fail + exit code |
| **Notification Service** | Sends Slack/email alerts on findings | Quality Gate, config | Scan summary + severity counts | Slack messages, emails |
| **SQLite Store** | Persists scan history, finding counts, report references | FastAPI Server, Scan Orchestrator | Scan metadata, finding summaries | Query results for dashboard/API |
| **Config Manager** | Loads config.yml, env vars, merges defaults | All components | YAML file + env vars | Typed config object |

### Data Flow

**1. Scan Trigger (two paths converge to one)**

- **Jenkins path:** Jenkins pipeline stage calls `POST /api/v1/scans` with local repo path + API key header. FastAPI validates, creates scan record in SQLite, dispatches to Scan Orchestrator.
- **API path:** External caller hits same endpoint with repo URL. Orchestrator clones repo to temp dir first, then proceeds identically.

**2. Parallel Tool Execution (Layer 1)**

The Scan Orchestrator launches all five tools concurrently using `asyncio.create_subprocess_exec`. Each scanner adapter:
1. Constructs CLI arguments for its tool
2. Runs tool as subprocess with timeout (configurable, ~2 min per tool)
3. Captures stdout/stderr
4. Parses tool-native output (JSON preferred, SARIF where available)
5. Returns structured results or error status

Scanner adapters are independent -- if one tool fails/times out, others continue. The orchestrator collects all results and marks failed tools in metadata.

**3. Finding Normalization**

All tool outputs are parsed into a **unified finding format**:

```python
@dataclass
class Finding:
    id: str                    # deterministic hash for dedup
    tool: str                  # "semgrep", "gitleaks", "trivy", etc.
    severity: Severity         # CRITICAL, HIGH, MEDIUM, LOW, INFO
    category: str              # "sast", "secrets", "iac", "cve", "cpp"
    title: str                 # human-readable finding title
    description: str           # what the issue is
    file_path: str | None      # affected file
    line_start: int | None     # line number
    line_end: int | None
    code_snippet: str | None   # relevant code context
    rule_id: str               # tool-specific rule identifier
    cwe: str | None            # CWE ID if available
    confidence: str            # tool's confidence level
    metadata: dict             # tool-specific extras
```

Deduplication happens here -- if Semgrep and cppcheck both flag the same line with overlapping rules, the normalizer keeps the higher-confidence finding and links the other as corroborating evidence.

**4. AI Analysis (Layer 2)**

The AI layer receives normalized findings in batches (to control API costs). It does NOT re-scan all source code -- it analyzes the findings already identified by tools:

- **Triage:** Confirms or dismisses findings as false positives based on code context
- **Business logic review:** Checks findings against aipix-specific concerns (RTSP auth, multi-tenant isolation, webhook validation)
- **Fix suggestions:** Generates concrete code patches for confirmed findings
- **Severity adjustment:** May upgrade/downgrade severity based on semantic understanding

Cost control: Batch findings by file, send code context windows (not entire files), cap token usage per scan. Target under $5/scan means roughly 100K-200K input tokens at Sonnet pricing.

**5. Report Generation (Layer 3)**

Two report types from the same enriched finding data:

- **HTML interactive:** Jinja2 template with collapsible sections, code highlighting, filter/sort by severity/tool/file, diff-style fix suggestions. Served via FastAPI static files or downloadable.
- **PDF formal:** WeasyPrint renders a print-optimized version with executive summary, severity distribution chart, finding details. For management and telecom operator compliance.

**6. Quality Gate (Layer 4)**

Reads configured thresholds from config.yml:

```yaml
quality_gate:
  fail_on:
    critical: 0    # any critical = fail
    high: 0        # any high = fail
  warn_on:
    medium: 5      # warn if > 5 medium
```

Produces: pass/fail boolean, exit code (0 or 1 for Jenkins), summary message. This is the final step -- the exit code propagates back through FastAPI response and/or Jenkins pipeline return code.

**7. Notifications**

Fire-and-forget after quality gate decision. Both Slack and email are optional (configured in config.yml). Include: scan summary, severity counts, pass/fail status, link to HTML report.

## Patterns to Follow

### Pattern 1: Scanner Adapter Interface

Every scanner tool gets wrapped in an adapter class with a uniform interface. This is critical for maintainability -- adding a new tool means writing one adapter, not touching orchestrator logic.

**What:** Abstract base class that all scanner adapters implement.
**When:** For every external security tool integration.
**Why:** Isolates tool-specific parsing, CLI invocation, and error handling. Makes it trivial to add/remove/replace tools.

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class ScannerResult:
    tool: str
    success: bool
    findings: list[Finding]
    execution_time_seconds: float
    error_message: str | None = None
    raw_output: str | None = None

class ScannerAdapter(ABC):
    @abstractmethod
    async def scan(self, target_path: str, config: ScannerConfig) -> ScannerResult:
        """Run the scanner and return normalized results."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the tool binary is installed and accessible."""
        ...

    @abstractmethod
    def parse_output(self, raw_output: str) -> list[Finding]:
        """Parse tool-native output into unified findings."""
        ...
```

**Confidence:** HIGH -- this is a standard adapter pattern, well-established in multi-tool orchestration systems.

### Pattern 2: Async Subprocess Orchestration

**What:** Use `asyncio.create_subprocess_exec` to run scanner tools in parallel, with per-tool timeouts and graceful failure handling.
**When:** Layer 1 parallel execution.
**Why:** FastAPI is async-native. Running 5 tools sequentially would take 10-20 minutes; parallel brings it to 2-4 minutes (bounded by slowest tool).

```python
import asyncio

async def run_all_scanners(target_path: str, config: Config) -> list[ScannerResult]:
    scanners = [
        SemgrepAdapter(), CppcheckAdapter(), GitleaksAdapter(),
        TrivyAdapter(), CheckovAdapter()
    ]
    tasks = [
        asyncio.wait_for(
            scanner.scan(target_path, config),
            timeout=config.scanner_timeout_seconds
        )
        for scanner in scanners
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    # Convert exceptions to failed ScannerResult objects
    return [handle_result(r, s) for r, s in zip(results, scanners)]
```

**Confidence:** HIGH -- `asyncio.create_subprocess_exec` works correctly on Linux (the target platform). FastAPI's async model supports this natively.

### Pattern 3: Configuration Layering

**What:** Three-tier config: defaults (hardcoded) -> config.yml (project) -> env vars (runtime/secrets).
**When:** All components need configuration.
**Why:** Portable defaults mean `docker-compose up` works immediately. YAML overrides for project customization. Env vars for secrets (API keys, notification webhooks) that never go in files.

```python
@dataclass
class Config:
    # Defaults
    scanner_timeout_seconds: int = 120
    ai_enabled: bool = True
    ai_max_tokens_per_scan: int = 150000
    quality_gate_fail_on_critical: int = 0
    quality_gate_fail_on_high: int = 0
    # From env only
    claude_api_key: str = ""  # CLAUDE_API_KEY env var
    api_auth_key: str = ""    # SCANNER_API_KEY env var
```

**Confidence:** HIGH -- standard pattern for containerized applications.

### Pattern 4: Deterministic Finding IDs

**What:** Hash finding attributes (tool + rule_id + file_path + line_start) to create stable IDs.
**When:** Normalization step.
**Why:** Enables deduplication across tools, cross-scan comparison ("3 new findings since last release"), and suppression lists (known false positives).

**Confidence:** HIGH -- standard approach in vulnerability management platforms like DefectDojo.

### Pattern 5: AI Prompt Batching by File

**What:** Group findings by file, send file content + its findings as one prompt. Cap at ~4K tokens of code context per file.
**When:** AI analysis layer.
**Why:** Reduces API calls (cost), provides semantic context (AI sees the full function, not just a line), and keeps within token budgets.

**Confidence:** MEDIUM -- the batching strategy is sound, but optimal batch size requires tuning during implementation.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Monolithic Scanner Script

**What:** One giant Python script that runs all tools sequentially, parses all outputs inline, generates reports, and makes gate decisions.
**Why bad:** Untestable, fragile (one tool failure kills entire scan), impossible to add/remove tools without risk. Any change risks regression across the entire pipeline.
**Instead:** Use the adapter pattern with clear component boundaries. Each adapter is independently testable. Orchestrator only coordinates.

### Anti-Pattern 2: SARIF as Internal Format

**What:** Using SARIF as the internal data interchange format between all components.
**Why bad:** SARIF is verbose, complex (the spec is 200+ pages), and designed for interchange between organizations/tools -- not as an internal data model. Parsing SARIF from 5 different tools (each implementing a subset differently) adds unnecessary complexity. SARIF also lacks fields needed for this project (AI enrichment, aipix-specific metadata).
**Instead:** Define a simple internal `Finding` dataclass. Write SARIF exporters if needed for external integrations later, but keep the internal model lean and purpose-built.

### Anti-Pattern 3: Full Source Code to AI

**What:** Sending entire repository contents to Claude API for analysis.
**Why bad:** Exceeds cost target ($5/scan) by 10-50x. Token limits become a problem. AI analysis works better on focused context than entire codebases.
**Instead:** Send only the code context around findings identified by Layer 1 tools. The static analyzers do the broad sweep; AI does targeted deep analysis.

### Anti-Pattern 4: Hard-Coding Severity Thresholds

**What:** Embedding quality gate thresholds directly in code.
**Why bad:** Different teams/partners will have different risk tolerance. Changing thresholds requires code changes and redeployment.
**Instead:** config.yml with sensible defaults. Partners can override without touching code.

### Anti-Pattern 5: Synchronous API for Long Scans

**What:** Having the `/api/v1/scans` endpoint block until the scan completes (2-10 minutes).
**Why bad:** HTTP timeouts, Jenkins stage timeouts, poor UX. Connection drops lose all progress.
**Instead:** Async job pattern: POST returns scan ID immediately, client polls `GET /api/v1/scans/{id}` for status. Dashboard shows live progress. Jenkins wrapper script polls until complete.

## Component Interaction Detail

### Internal Module Structure

```
src/
  scanner/
    __init__.py
    config.py              # Config loading and validation
    models.py              # Finding, ScanResult, Severity dataclasses
    orchestrator.py        # Scan lifecycle, parallel tool execution
    adapters/
      __init__.py
      base.py              # ScannerAdapter ABC
      semgrep.py
      cppcheck.py
      gitleaks.py
      trivy.py
      checkov.py
    normalizer.py          # Tool output -> unified Finding
    ai_analyzer.py         # Claude API integration, prompt construction
    report/
      __init__.py
      html_generator.py    # Jinja2 HTML report
      pdf_generator.py     # WeasyPrint PDF report
      templates/           # Jinja2 templates
    quality_gate.py        # Threshold evaluation, pass/fail
    notifications/
      __init__.py
      slack.py
      email.py
    db.py                  # SQLite operations
  api/
    __init__.py
    app.py                 # FastAPI app factory
    routes/
      scans.py             # Scan CRUD endpoints
      reports.py           # Report download endpoints
      health.py            # Health check
      dashboard.py         # Dashboard HTML serving
    auth.py                # API key middleware
    dependencies.py        # FastAPI dependency injection
  cli.py                   # CLI entry point for direct invocation
  main.py                  # Uvicorn entry point
```

### Key Interfaces Between Components

**API -> Orchestrator:**
```python
# api/routes/scans.py calls orchestrator
scan_id = await orchestrator.start_scan(
    target=ScanTarget(path="/repo/path", mode="local"),
    config=scan_config,
)
# Returns immediately, scan runs in background task
```

**Orchestrator -> Adapters:**
```python
# orchestrator.py runs adapters in parallel
results: list[ScannerResult] = await run_all_scanners(target_path, config)
```

**Orchestrator -> Normalizer -> AI:**
```python
# Sequential: normalize, then AI analysis
findings = normalizer.normalize(results)
if config.ai_enabled:
    findings = await ai_analyzer.enrich(findings, source_files)
```

**Orchestrator -> Report -> Gate -> Notify:**
```python
# Sequential: generate reports, evaluate gate, notify
html_path = report.generate_html(findings, scan_metadata)
pdf_path = report.generate_pdf(findings, scan_metadata)
gate_result = quality_gate.evaluate(findings, config.quality_gate)
await notifications.send(gate_result, scan_metadata)
return ScanResult(gate_result=gate_result, report_paths=[html_path, pdf_path])
```

## Scalability Considerations

| Concern | At 1 scan/day | At 10 scans/day | At 50+ scans/day |
|---------|---------------|-----------------|-------------------|
| **SQLite contention** | No issue | No issue (WAL mode) | May need read replicas or move to PostgreSQL (out of scope for v1) |
| **Disk usage (reports)** | Trivial (~5MB/scan) | ~50MB/day, monthly cleanup | Retention policy, S3 archival |
| **Claude API costs** | ~$5/day | ~$50/day | Caching layer for identical findings, reduce AI scope |
| **Concurrent scans** | N/A | Queue with max 2-3 concurrent | Job queue (but out of scope -- v1 targets sequential or low-concurrency) |
| **Container resources** | 2GB RAM, 2 CPU | 4GB RAM, 4 CPU | Horizontal scaling (out of scope for v1) |

For v1, the target is 1-5 scans/day for release branches. SQLite and single-container Docker are perfectly adequate. Do not over-engineer for scale that is not needed.

## Suggested Build Order (Dependencies)

Build order is driven by component dependencies -- you cannot build downstream components without upstream ones existing.

```
Phase 1: Foundation
  config.py -> models.py -> db.py -> basic FastAPI app with health endpoint
  (Everything depends on config and models; DB needed for scan tracking)

Phase 2: Scanner Core
  base.py adapter interface -> individual adapters (can be built in parallel)
  -> normalizer.py -> orchestrator.py
  (This is the core value: tools run, findings produced)

Phase 3: AI Enrichment
  ai_analyzer.py (depends on normalized findings from Phase 2)
  (Can be toggled off, so Phase 2 is independently useful)

Phase 4: Reports + Quality Gate
  html_generator.py -> pdf_generator.py -> quality_gate.py
  (Depends on enriched findings from Phase 2/3)

Phase 5: Integration Layer
  Full API routes -> Jenkins integration -> notifications
  Dashboard (depends on DB, reports, scan history)
  (Everything upstream must work first)

Phase 6: Polish + Portability
  Custom Semgrep rules, Docker packaging, docs, migration scripts
  (Refinement after core pipeline works end-to-end)
```

**Critical path:** Config/Models -> Scanner Adapters -> Normalizer -> Orchestrator -> Reports -> Quality Gate. Every other component hangs off this spine.

**Parallelizable work within phases:**
- All 5 scanner adapters can be built independently (Phase 2)
- HTML and PDF report generators are independent (Phase 4)
- Slack and email notification handlers are independent (Phase 5)
- English and Russian docs are independent (Phase 6)

## Sources

- [LinkedIn SAST Pipeline Architecture (InfoQ, Feb 2026)](https://www.infoq.com/news/2026/02/linkedin-redesigns-sast-pipeline/) -- parallel multi-scanner orchestration, SARIF normalization, scale patterns
- [AWS DevSecOps CI/CD Pipeline](https://aws.amazon.com/blogs/devops/building-end-to-end-aws-devsecops-ci-cd-pipeline-with-open-source-sca-sast-and-dast-tools/) -- parallel SCA/SAST execution, Security Hub aggregation
- [SARIF Standard (OASIS)](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html) -- interchange format specification (used as reference, not as internal format)
- [Sonar Guide to SARIF](https://www.sonarsource.com/resources/library/sarif/) -- normalization and aggregation patterns
- [ARMO: Security Gates in CI/CD](https://www.armosec.io/blog/securing-ci-cd-pipelines-security-gates/) -- quality gate severity threshold patterns
- [Wiz: DevSecOps Pipeline Best Practices](https://www.wiz.io/academy/application-security/devsecops-pipeline-best-practices) -- progressive security, scanner integration
- [GitLab Pipeline with Gitleaks, Semgrep, Trivy, Checkov (Medium)](https://manabpokhrel7.medium.com/building-a-secure-gitlab-ci-cd-pipeline-with-sast-tools-gitleaks-hadolint-checkov-semgrep-8bd5501ec841) -- multi-tool pipeline staging pattern
- [AI Code Review Architecture (ProjectDiscovery)](https://projectdiscovery.io/blog/ai-code-review-vs-neo) -- LLM combined with static analysis tools raises detection to 94%
- [FastAPI Async Patterns](https://fastapi.tiangolo.com/async/) -- async subprocess handling in FastAPI context
- [DefectDojo Integration with SAST Tools (Medium)](https://medium.com/@alirezamokhtari82/integrating-sast-tools-with-defectdojo-in-a-kubernetes-based-ci-cd-pipeline-fa7e1ca79213) -- centralized findings aggregation pattern
