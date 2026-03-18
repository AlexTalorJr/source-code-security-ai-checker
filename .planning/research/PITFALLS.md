# Pitfalls Research

**Domain:** Automated security scanning pipeline (multi-tool orchestration with AI analysis)
**Researched:** 2026-03-18
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: Alert Fatigue From Untuned Scanners

**What goes wrong:**
Running five scanners (Semgrep, cppcheck, Gitleaks, Trivy, Checkov) with default rulesets produces hundreds or thousands of findings on first scan. Developers immediately lose trust in the tool, start ignoring reports, and the scanner becomes shelfware. The 10-minute CI constraint becomes impossible to meet because AI analysis chokes on the volume, and reports become 50+ page documents nobody reads.

**Why it happens:**
Default rulesets are designed for maximum coverage, not precision. Semgrep community rules, Trivy CVE databases, and Checkov policies all flag low-confidence findings by default. Teams assume "more findings = better security" and skip the tuning phase entirely.

**How to avoid:**
- Start with a minimal, curated ruleset per tool. For Semgrep, use `--severity ERROR` initially and expand later.
- For Trivy, filter to HIGH and CRITICAL CVEs only. Ignore unfixable CVEs (`--ignore-unfixed`).
- For Checkov, start with CKV_DOCKER and CKV_K8S checks only -- skip low-priority CIS benchmarks.
- For Gitleaks, use a custom `.gitleaks.toml` with allowlists for known test fixtures and example configs.
- Build a `suppressions.yml` mechanism from day one -- a file where teams can mark false positives with justification.
- Track false positive rate as a metric. Target under 20% false positive rate before enabling quality gate blocking.

**Warning signs:**
- First scan produces more than 100 findings on a mature codebase
- Developers ask "how do I suppress everything?" within the first week
- Quality gate blocks builds on findings that are clearly not vulnerabilities
- AI analysis section of reports contains generic advice rather than specific guidance

**Phase to address:**
Phase 1 (Core Scanner Orchestration) -- ruleset tuning must happen during initial tool integration, not after. The suppression/allowlist mechanism is a core feature, not an afterthought.

---

### Pitfall 2: AI Hallucinated Vulnerabilities and Fix Suggestions

**What goes wrong:**
Claude generates findings that do not exist in the actual code, fabricates CVE numbers, invents function names, or suggests "fixes" that introduce new vulnerabilities. Research shows 29-45% of AI-generated code suggestions contain security vulnerabilities, and LLMs repeat planted errors in up to 83% of cases. In a security scanner context, a hallucinated critical finding could block a legitimate release, and a hallucinated "safe" assessment could let a real vulnerability through.

**Why it happens:**
LLMs are prediction engines, not code analyzers. When fed aggregated scanner output, Claude will pattern-match against training data and generate plausible-sounding but potentially fabricated analysis. The model has no way to verify its claims against the actual codebase state. Large context windows increase hallucination risk as the model loses track of specific details.

**How to avoid:**
- Never let AI analysis be the sole source of any finding. AI should only annotate, correlate, and explain findings already detected by deterministic tools (Semgrep, Trivy, etc.).
- Structure the AI prompt to be grounding-focused: provide the exact code snippet, the exact tool finding, and ask for explanation/fix -- not for "find more vulnerabilities."
- Implement output validation: if Claude references a CVE, verify it exists. If it references a function name, verify it exists in the scanned code.
- Include a confidence disclaimer in reports: "AI-generated analysis -- verify before acting."
- Set `temperature=0` for deterministic output. Use structured output (JSON mode) to constrain response format.
- Cap the context sent to Claude: send individual findings with surrounding code, not the entire codebase.

**Warning signs:**
- AI section of reports mentions functions or files that don't exist in the scanned repository
- AI suggests fixes that contradict the tool's finding (e.g., tool says "SQL injection" but AI says "this is safe")
- AI generates CVE identifiers that return no results in NVD
- AI analysis section is longer than the tool findings section

**Phase to address:**
Phase 2 (AI Analysis Layer) -- the prompt engineering, output validation, and grounding strategy must be designed before any AI features ship. This is the hardest part of the project to get right.

---

### Pitfall 3: Finding Deduplication Failure Across Tools

**What goes wrong:**
The same vulnerability gets reported by multiple tools with different descriptions, severities, and identifiers. A hardcoded AWS key shows up as a Gitleaks finding, a Semgrep finding, and a Trivy secret. A Kubernetes misconfiguration appears in both Checkov and Trivy. Reports show 150 "findings" when there are really 60 unique issues. Research shows a 30-50% inflation in finding counts is common when deduplication is absent. This destroys the quality gate's credibility and makes severity-based blocking unreliable.

**Why it happens:**
Each scanner uses its own taxonomy, severity scale, and finding format. There is no universal vulnerability identifier that spans SAST, secrets detection, and IaC scanning. Teams build the tools first and plan to "add deduplication later" -- but by then the data model doesn't support correlation.

**How to avoid:**
- Design a unified finding data model from day one with: file path, line range, finding category (enum), normalized severity (Critical/High/Medium/Low/Info), tool source, and a dedup key.
- The dedup key should be: `hash(file_path + line_range + category)` -- not based on tool-specific identifiers.
- Define tool priority for overlapping domains: Gitleaks is authoritative for secrets (Semgrep secrets findings are supplementary), Checkov is authoritative for IaC (Trivy IaC findings are supplementary).
- Implement dedup as a pipeline stage between Layer 1 (tool execution) and Layer 2 (AI analysis). AI should only see deduplicated findings.
- Store both raw tool output and deduplicated findings in SQLite -- raw for audit trail, deduped for reports and quality gate.

**Warning signs:**
- Report finding count is more than 2x what any individual tool reports
- Same file:line appears multiple times in a report with different descriptions
- Quality gate triggers on "5 Critical findings" but manual review shows 2 unique issues
- AI analysis repeats itself because it received duplicate findings

**Phase to address:**
Phase 1 (Core Scanner Orchestration) -- the unified finding model and dedup logic must be part of the orchestrator from the start. Retrofitting dedup onto an existing pipeline requires rewriting the data layer.

---

### Pitfall 4: CI Pipeline Timeout and Build-Blocking Brittleness

**What goes wrong:**
The scanner exceeds the 10-minute CI budget, causing Jenkins builds to timeout or take unacceptably long. Alternatively, a scanner crashes or hangs (Semgrep OOM on large C++ files, Trivy DB download fails, Claude API is down), and the quality gate cannot produce a result -- either silently passing unsafe code or blocking all deployments.

**Why it happens:**
Five parallel scanners plus AI analysis plus report generation is a lot of work. Semgrep on large C++ files can consume 4+ GB RAM. Trivy needs to download vulnerability databases on first run (or when cache expires). Claude API has rate limits and occasional outages. Any single failure in the chain breaks the pipeline. Teams test with small repos and are surprised when scanning the actual aipix codebase takes 15 minutes.

**How to avoid:**
- Set per-tool timeouts: Semgrep 3min, cppcheck 3min, Gitleaks 2min, Trivy 2min, Checkov 1min. Kill and report partial results on timeout.
- Cache Trivy vulnerability databases in the Docker image (rebuild weekly). Never download at scan time in CI.
- Implement graceful degradation: if Claude API is unreachable, skip AI analysis and generate report without it. Mark report as "partial -- AI analysis unavailable."
- If any tool fails, the quality gate should use only the tools that succeeded -- not block indefinitely and not silently pass.
- Pre-warm scanner caches in the Docker image build, not at scan time.
- For Semgrep on C++, limit `--max-memory` to 70% of available container memory and reduce parallelism with `-j 2`.
- Profile scanning time on the actual aipix codebase early -- do not wait until CI integration phase.

**Warning signs:**
- Scans take more than 5 minutes on the development test repo
- Docker container memory usage exceeds 4GB during scanning
- Trivy spends 30+ seconds downloading databases at scan start
- CI builds randomly fail with OOM or timeout errors

**Phase to address:**
Phase 1 (Core Scanner Orchestration) for tool timeouts and caching. Phase 3 (CI Integration) for Jenkins-specific timeout handling and graceful degradation.

---

### Pitfall 5: WeasyPrint Memory Explosion on Large Reports

**What goes wrong:**
HTML/PDF report generation for a scan with 100+ findings causes WeasyPrint to consume 2-4 GB of memory and take several minutes, potentially crashing the container. Multiple concurrent report generation requests (two scans finishing simultaneously) can OOM the host. This is well-documented: WeasyPrint issues #671, #1104, #2130 all describe memory spikes on large documents, with reports of 2.5 GB spikes for relatively small PDFs.

**Why it happens:**
WeasyPrint loads the entire document into memory for CSS layout calculation. Large HTML tables (finding lists), syntax-highlighted code blocks, and embedded images all compound the problem. There is no streaming/incremental rendering. Multi-byte characters (Russian documentation) increase memory usage further.

**How to avoid:**
- Cap findings per report: if more than 200 findings, paginate into multiple PDFs or show top 50 with "full report available via dashboard."
- Avoid large CSS frameworks in report templates. Use minimal, purpose-built CSS.
- Run `gc.collect()` after each PDF generation.
- Generate PDF in a separate subprocess with memory limits (`resource.setrlimit` or Docker memory limits on the generation worker).
- Consider generating HTML as the primary report format and PDF only on explicit request (lazy generation).
- For the bilingual requirement: generate reports in one language at a time, never both simultaneously.
- Test report generation with 500+ findings early to validate memory behavior.

**Warning signs:**
- Report generation takes more than 30 seconds for a 50-finding scan
- Container memory usage spikes during report generation
- PDF generation crashes silently and no report file is created
- Russian-language reports take significantly longer than English ones

**Phase to address:**
Phase 2 or Phase 3 (Report Generation) -- test with realistic finding volumes immediately when building the report generator. Do not wait until integration testing.

---

### Pitfall 6: Claude API Cost Overrun

**What goes wrong:**
A single scan sends the entire aggregated output of five tools to Claude, consuming 50K-100K+ input tokens per scan. At $3/M input tokens for Sonnet, a single scan could cost $0.15-$0.50. Running 20 release scans per day during active development burns through $100+/month, far exceeding the $5/scan budget. Worse, retries on rate limits or timeouts double costs silently.

**Why it happens:**
Developers send raw tool output (including INFO-level findings, stack traces, and verbose metadata) to the AI without filtering. No token budget enforcement exists. Retry logic sends the same large payload multiple times.

**How to avoid:**
- Pre-filter findings before sending to Claude: only send HIGH and CRITICAL findings to AI. Medium/Low findings get template-based analysis only.
- Strip tool metadata, keep only: file path, line number, code snippet (10 lines context), finding description, severity.
- Implement a token budget per scan (e.g., 30K input tokens max). If findings exceed the budget, batch into multiple smaller requests or truncate to highest-severity findings.
- Track cost per scan in SQLite. Alert if any scan exceeds $2.
- Use prompt caching where possible -- custom Semgrep rule descriptions and platform context are static and can be cached across scans.
- Never retry a failed Claude API call with the same payload without exponential backoff and a retry limit of 2.

**Warning signs:**
- Claude API call takes more than 60 seconds (likely large payload)
- Monthly API bill exceeds $50 with normal scan frequency
- Token usage per scan varies wildly (10K to 200K) across different branches
- Retry logic triggers more than once per scan on average

**Phase to address:**
Phase 2 (AI Analysis Layer) -- token budgeting and cost tracking must be built into the AI integration from the start, not bolted on after the first invoice shock.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Hardcoded scanner configs instead of config.yml | Faster initial dev | Every ruleset change requires code change; teams receiving the tool cannot customize | Never -- config.yml from day one |
| Storing raw JSON tool output in SQLite TEXT columns | No schema design needed | Cannot query findings by severity, file, or tool; deduplication becomes string parsing | First prototype only, refactor before Phase 2 |
| Single-threaded scanner execution | Simpler orchestration | Scans take 12-15 min instead of 4-5 min, breaks CI time constraint | Never -- parallel execution is a core requirement |
| Skipping Gitleaks `--no-git` for path-mode scans | Avoids git history scanning complexity | Misses secrets committed in history and later "deleted" | Acceptable for MVP if documented as limitation |
| Inline CSS in report templates | No build step for CSS | Report template changes are painful; theming is impossible | Acceptable for Phase 1 if external CSS is planned |
| No scan cancellation mechanism | Simpler API design | Zombie scans consume resources; no way to abort a stuck scan | Must add by CI integration phase |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Jenkins Pipeline | Treating scanner as a shell script (`sh './scan.sh'`) with no error handling | Use Jenkins `httpRequest` to call FastAPI, parse JSON response for pass/fail, handle timeouts with `timeout()` step |
| Claude API | Sending findings as unstructured text dump | Use structured prompts with JSON input and request JSON output. Include explicit instructions: "Only analyze the findings provided. Do not invent additional findings." |
| Bitbucket/Git clone | Cloning full repo history for every scan | Use `--depth 1` for code scanning. Only Gitleaks needs history -- and even then, limit to `--log-opts="--since=6months"` for performance |
| Trivy DB updates | Downloading vulnerability DB at scan time | Bake DB into Docker image on weekly rebuild. Use `--skip-db-update` at scan time. Provide manual refresh endpoint for zero-day response |
| SQLite in Docker | Storing DB inside the container filesystem | Mount SQLite file as a Docker volume. Without this, scan history is lost on container restart/upgrade |
| Slack/Email notifications | Sending notification for every scan regardless of result | Only notify on: quality gate failure, first clean scan after failure, scanner errors. Otherwise it becomes noise |
| Semgrep custom rules | Writing rules without `fix:` patterns | Always include `fix:` in custom Semgrep rules for aipix patterns -- this feeds directly into AI-enhanced fix suggestions |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Gitleaks scanning full git history | Scan takes 10+ minutes on repos with 5K+ commits | Use `--log-opts="--since=2024-01-01"` or scan only diff between branches | Repos with 2+ years of history |
| Semgrep on C++ with all rules | OOM kill at 4GB+ memory, scan hangs | Use `--max-memory 2048 -j 2` and C++-specific ruleset only | C++ files over 5K lines (Mediaserver) |
| WeasyPrint concurrent PDF generation | Container OOM, 2.5GB memory spike per render | Queue PDF generation, process one at a time, use subprocess isolation | More than 1 concurrent report generation |
| Trivy scanning all layers of large Docker images | 5+ minute scan per image | Use `--scanners vuln` (skip misconfig for images), scan only final layer with `--image-src` | Images with 20+ layers or 2GB+ size |
| SQLite under concurrent FastAPI requests | "database is locked" errors, 500 responses | Enable WAL mode, use IMMEDIATE transactions for writes, keep transactions short | More than 5 concurrent write operations |
| Loading entire scan result JSON into memory for report | Memory spike proportional to finding count | Stream findings from SQLite with pagination, render report sections incrementally | Scans with 500+ findings |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Storing API keys in config.yml committed to repo | Scanner's own credentials leaked -- ironic for a security tool | Environment variables only, `.env` in `.gitignore`, validate no secrets in config at startup |
| Claude API key in Docker image layer | Anyone with image access gets API key, billed token usage | Pass via `docker-compose.yml` environment section referencing host env vars, never in Dockerfile |
| No auth on FastAPI dashboard | Anyone on the network can view vulnerability reports and trigger scans | API key auth middleware on all endpoints, not just scan triggers |
| Scan results accessible without authentication | Vulnerability details exposed to unauthorized users | Authenticate report download endpoints, not just the dashboard UI |
| Running scanners as root in Docker | Container escape gives root on host | Use non-root user in Dockerfile, scanner tools work fine as non-root |
| Git clone with credentials in URL | Credentials visible in process list and logs | Use SSH keys or credential helpers, mask URLs in log output |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Report shows all findings with equal visual weight | Critical findings buried among 80 Info-level notes | Visual severity hierarchy: Critical = red banner, High = orange, Medium = yellow card, Low/Info = collapsed by default |
| No finding diff between scans | Developers cannot tell what is new vs. pre-existing | Implement "new in this scan" vs "existing" tagging. Show delta prominently |
| Quality gate message says only "FAILED" | Developer has no idea what to fix without opening the full report | Quality gate response includes: count by severity, top 3 findings with file:line, direct link to full report |
| Dashboard requires manual refresh | Users do not know when a scan completes | Use SSE or WebSocket for scan progress. At minimum, auto-refresh every 30 seconds during active scan |
| Fix suggestions are generic | "Sanitize user input" is not actionable | AI fix suggestions must include the exact code change as a diff, referencing the actual variable names and file |
| Reports only in English | Russian-speaking teams cannot use formal PDF reports for compliance | Bilingual support must cover report content (finding descriptions, fix suggestions), not just UI labels |

## "Looks Done But Isn't" Checklist

- [ ] **Scanner Orchestration:** Often missing individual tool timeout handling -- verify each scanner has a kill timer and partial-result fallback
- [ ] **Quality Gate:** Often missing "scanner failure" vs "no findings" distinction -- verify that a crashed scanner does not silently pass the gate
- [ ] **Report Generation:** Often missing handling for zero findings -- verify report renders correctly when scan is clean (not an error page)
- [ ] **AI Analysis:** Often missing token counting before API call -- verify budget enforcement prevents surprise costs
- [ ] **Git Integration:** Often missing support for branches with special characters (slashes, spaces) -- verify with `feature/AIPIX-123/fix-auth`
- [ ] **Docker Compose:** Often missing health check dependencies -- verify scanner container waits for DB/API to be ready, not just "started"
- [ ] **Notifications:** Often missing rate limiting -- verify a flapping quality gate does not send 50 Slack messages in an hour
- [ ] **Suppression System:** Often missing audit trail -- verify who suppressed what finding and when is recorded
- [ ] **PDF Reports:** Often missing Unicode/Cyrillic rendering -- verify Russian text renders correctly in WeasyPrint PDF output
- [ ] **Dual-mode Input:** Often missing cleanup of cloned repos -- verify temp directories are removed after scan, especially on failure paths

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Alert fatigue / untuned scanners | LOW | Add suppressions file, reduce ruleset severity, re-run scans. No data model change needed if suppression was designed in |
| AI hallucinated findings | LOW | Add validation layer, adjust prompts, re-generate reports. Historical reports may need disclaimer addendum |
| No deduplication | HIGH | Requires data model redesign, re-processing of historical scan data, updating all report templates and quality gate logic |
| CI timeout/brittleness | MEDIUM | Add per-tool timeouts and graceful degradation. May require re-architecting scanner execution from sequential to parallel |
| WeasyPrint OOM | MEDIUM | Add pagination/caps to reports, isolate PDF generation in subprocess. May need to switch to alternative (Playwright PDF) if fundamental |
| Claude API cost overrun | LOW | Add token budget, filter findings before AI. Immediate -- just update the AI analysis layer configuration |
| SQLite locking under concurrency | MEDIUM | Enable WAL mode (one-line change), but if schema was not designed for it, may need transaction refactoring |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Alert fatigue | Phase 1: Scanner Orchestration | First scan on aipix codebase produces fewer than 100 findings with tuned rulesets |
| AI hallucination | Phase 2: AI Analysis | 100% of AI-referenced file paths and function names verified to exist in scanned code |
| Finding deduplication | Phase 1: Scanner Orchestration | Unified finding model with dedup key exists; duplicate count across tools is under 10% |
| CI timeout | Phase 1 + Phase 3: CI Integration | Full scan completes in under 8 minutes on aipix codebase (2 min buffer for variance) |
| WeasyPrint memory | Phase 2: Report Generation | PDF generation for 200-finding scan uses under 1GB RAM, measured in staging |
| API cost overrun | Phase 2: AI Analysis | Token usage per scan logged in SQLite; no scan exceeds 50K input tokens without explicit override |
| SQLite concurrency | Phase 1: Core Infrastructure | WAL mode enabled; 10 concurrent API requests do not produce "database is locked" errors |
| Quality gate brittleness | Phase 3: CI Integration | Scanner failure produces "degraded" gate result, not silent pass or indefinite block |
| Notification noise | Phase 3: Notifications | Only gate-failure and recovery events trigger notifications; rate limited to 1 per scan |
| Docker portability | Phase 1: Containerization | `docker-compose up` on clean machine reaches healthy state in under 2 minutes with no internet access (pre-baked DBs) |

## Sources

- [Semgrep: Boosting Security Scan Performance for Monorepos](https://semgrep.dev/blog/2025/boosting-security-scan-performance-for-monorepos-with-multicore-parallel-processing/)
- [Semgrep: Scanning Monorepos in Parts](https://semgrep.dev/docs/kb/semgrep-ci/scan-monorepo-in-parts)
- [Semgrep: Reduce False Positives](https://semgrep.dev/docs/kb/semgrep-code/reduce-false-positives)
- [WeasyPrint Memory Issues #2130](https://github.com/Kozea/WeasyPrint/issues/2130)
- [WeasyPrint Memory with Large Tables #1104](https://github.com/Kozea/WeasyPrint/issues/1104)
- [WeasyPrint Memory for Long Documents #671](https://github.com/Kozea/WeasyPrint/issues/671)
- [Strobes: Why Deduplication Is the Most Underrated Security Control](https://strobes.co/blog/vulnerability-deduplication-security/)
- [NorthStar: Vulnerability Deduplication](https://www.northstar.io/blog/vulnerability-deduplication/)
- [DefectDojo: Deduplication Tuning](https://docs.defectdojo.com/en/working_with_findings/finding_deduplication/tune_deduplication/)
- [SQLite Concurrent Writes and "database is locked"](https://tenthousandmeters.com/blog/sqlite-concurrent-writes-and-database-is-locked-errors/)
- [SQLite WAL Mode Documentation](https://www.sqlite.org/wal.html)
- [LLM Hallucinations in AI Code Review](https://diffray.ai/blog/llm-hallucinations-code-review/)
- [Hallucinations in AI-Driven Cybersecurity Systems](https://www.sciencedirect.com/science/article/abs/pii/S0045790625002502)
- [Claude API Rate Limits](https://platform.claude.com/docs/en/api/rate-limits)
- [Claude API Pricing](https://platform.claude.com/docs/en/about-claude/pricing)
- [Harness: Security Testing Orchestration](https://www.harness.io/products/application-security-testing/security-testing-orchestration)
- [BoostSecurity: 2025 State of Pipeline Security](https://boostsecurity.io/blog/defensive-research-weaponized-the-2025-state-of-pipeline-security)

---
*Pitfalls research for: aipix-security-scanner -- automated security scanning pipeline*
*Researched: 2026-03-18*
