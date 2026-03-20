# Phase 7: Security Scanner Ecosystem Research - Research

**Researched:** 2026-03-20
**Domain:** Security scanning tools ecosystem (SAST, SCA, DAST, Secrets, Plugin Architecture)
**Confidence:** HIGH

## Summary

This phase produces a comprehensive research report -- no code changes. The existing scanner has 8 adapters (Semgrep, Cppcheck, Gitleaks, Trivy, Checkov, Psalm, Enlightn, PHP Security Checker) following a well-defined `ScannerAdapter` pattern with async subprocess execution, JSON parsing, and normalization to `FindingSchema`. The research must cover tools for languages currently uncovered (Go, Rust, Java, C#, Ruby, JS/TS dedicated SAST), re-evaluate existing tools, assess SCA alternatives to Trivy, survey DAST tools, compare secrets scanners, and propose plugin architecture improvements.

The codebase already runs adapters in parallel via `asyncio.gather`, uses config-driven enablement (`enabled: true/false/"auto"`, `timeout`, `extra_args`), and auto-detects languages via file extensions. New tool research must evaluate how easily each tool maps to this existing pattern: CLI invocation, JSON/SARIF output parsing, Docker installability, and severity mapping to the existing `FindingSchema`.

**Primary recommendation:** Organize the research report by language with cross-cutting sections for SCA, DAST, secrets, SARIF evaluation, and plugin architecture. Each tool entry needs: CLI usage, output format, Docker install method, approximate image size impact, config.yml snippet, and T-shirt effort estimate.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Research scope**: Gaps + re-evaluate existing tools. Research tools for uncovered languages (Go, Rust, Java, C#, Ruby, JS/TS SAST) AND re-evaluate current tools (Semgrep, Cppcheck, Psalm, Gitleaks, Trivy, Checkov)
- **Full SCA comparison**: Research SCA alternatives (Grype, Dependency-Check, etc.) even though Trivy handles SCA today
- **DAST feasibility assessment**: Survey ZAP, Nuclei, Nikto with integration feasibility
- **Secrets scanning quick check**: Compare Gitleaks vs TruffleHog, confirm which is best
- **Report organized by language**: Main sections per language, cross-cutting sections for SCA, DAST, secrets
- **Per-language comparison tables**: Each language section ends with a comparison matrix, plus a final summary matrix
- **Single document**: One comprehensive research report (07-RESEARCH.md)
- **Config snippets included**: Each recommended tool includes a sample config.yml entry
- **Primary criterion: integration ease**: CLI interface, JSON/SARIF output, Docker availability, ScannerAdapter wrapping
- **False positive reduction: tool-level config**: Document rulesets, severity tuning, exclude patterns
- **T-shirt size effort estimates**: S/M/L per tool
- **Docker image size impact**: Note approximate footprint per tool
- **Research plugin patterns, recommend approach**: Survey stevedore, entry points, config-driven dispatch
- **Include non-JSON tools with effort notes**: Flag parsing effort for non-JSON/non-SARIF tools
- **SARIF evaluation**: Assess which tools support SARIF and whether to adopt it as normalized intermediate format
- **Orchestration improvements in scope**: Parallel execution patterns and incremental scanning strategies

### Claude's Discretion
- Exact organization of sub-sections within each language
- How to structure comparison matrices (columns, scoring scale)
- Depth of individual tool configuration options
- Formatting and detail level of config.yml snippets
- How to present SARIF evaluation findings

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SCAN-01 | Research available SAST tools per language (Python, PHP, JS/TS, Go, Rust, Java, C#, C/C++, Ruby) | Per-language tool research with pros/cons, CLI interface, output format, Docker install |
| SCAN-02 | Research SCA tools for dependency vulnerability detection | Full SCA comparison: Trivy vs Grype vs OWASP Dependency-Check |
| SCAN-03 | Research DAST tools applicable to web applications and APIs | ZAP, Nuclei, Nikto feasibility assessment with integration analysis |
| SCAN-04 | Evaluate scanner configuration best practices -- rulesets, severity tuning, false positive reduction | Per-tool config guidance, ruleset recommendations, exclude patterns |
| SCAN-05 | Research scanner plugin/adapter patterns -- how to add new scanners without code changes | Stevedore, entry_points, config-driven dispatch analysis and recommendation |
| SCAN-06 | Document integration requirements per tool (installation, CLI, output format, licensing) | Per-tool integration card: install method, CLI args, output format, license, Docker size |
| SCAN-07 | Produce actionable recommendations with priority ranking | Final priority matrix with T-shirt effort estimates and recommended implementation order |
</phase_requirements>

## Standard Stack

This phase produces a research document, not code. The "stack" here refers to the existing codebase patterns that the research must account for.

### Existing Architecture (research must evaluate compatibility)
| Component | Current | Purpose | Research Implication |
|-----------|---------|---------|---------------------|
| ScannerAdapter | `src/scanner/adapters/base.py` | Abstract base class with `run()`, `get_version()`, `_execute()` | New tools must map to this contract |
| FindingSchema | `src/scanner/schemas/finding.py` | Pydantic model: fingerprint, tool, rule_id, file_path, line_start/end, snippet, severity, title, description | New tools' output must normalize to these fields |
| ScannersConfig | `src/scanner/config.py` | Per-tool `ScannerToolConfig(enabled, timeout, extra_args)` | Config snippets must match this structure |
| language_detect | `src/scanner/core/language_detect.py` | `_EXT_TO_LANG` mapping + `SCANNER_LANGUAGES` dispatch | New language-specific scanners need entries here |
| orchestrator | `src/scanner/core/orchestrator.py` | `asyncio.gather` parallel execution, dedup, AI enrichment | Orchestration research accounts for this pattern |

### Currently Installed Tools (re-evaluate these)
| Tool | Version (Dockerfile) | Purpose | Languages |
|------|---------------------|---------|-----------|
| Semgrep | pip latest | Multi-language SAST | Python, PHP, JS/TS, Go, Java, Ruby, C#, Rust |
| Cppcheck | apt latest | C/C++ SAST | C/C++ |
| Gitleaks | 8.30.0 | Secrets scanning | All (universal) |
| Trivy | 0.69.3 | SCA + IaC scanning | Docker, Terraform, YAML |
| Checkov | pip latest | IaC scanning | Docker, Terraform, YAML, CI |
| Psalm | composer latest | PHP SAST | PHP |
| Enlightn | via adapter | PHP/Laravel security | Laravel |
| PHP Security Checker | 2.1.3 | PHP dependency checker | PHP |

## Architecture Patterns

### Research Report Structure
The report itself (the deliverable) should follow this organization:

```
07-RESEARCH.md (this file IS the deliverable)
  Per-Language Sections:
    Python, PHP, JavaScript/TypeScript, Go, Rust,
    Java, C#, C/C++, Ruby
  Cross-Cutting Sections:
    SCA Tools Comparison
    DAST Feasibility Assessment
    Secrets Scanning Comparison
    SARIF Evaluation
    Plugin Architecture Patterns
    Orchestration Improvements
    Final Priority Matrix
```

### Per-Tool Research Card Pattern
Each tool evaluated should include:

```
### Tool Name
- **Purpose:** What it scans for
- **Language(s):** Target languages
- **License:** OSS license
- **Output formats:** JSON, SARIF, XML, text, etc.
- **CLI usage:** `command --flags target`
- **Docker install:** apt/pip/binary download, approximate image size impact
- **SARIF support:** Yes/No (critical for normalized parsing)
- **Integration effort:** S/M/L with justification
- **Config snippet:**
  ```yaml
  scanners:
    tool_name:
      enabled: "auto"
      timeout: 120
      extra_args: []
  ```
- **FindingSchema mapping:**
  - fingerprint: computed from file_path + rule_id + snippet
  - rule_id: maps to X field in output
  - severity: maps via {TOOL}_SEVERITY_MAP
  - line_start/end: available? Y/N
  - snippet: available? Y/N
- **False positive reduction:** Which rulesets to enable/disable, severity tuning
- **Pros:** [list]
- **Cons:** [list]
```

### Adapter Implementation Pattern (existing, for reference)
New adapters follow this exact pattern from the existing codebase:

```python
class NewToolAdapter(ScannerAdapter):
    @property
    def tool_name(self) -> str:
        return "tool_name"

    def _version_command(self) -> list[str]:
        return ["tool", "--version"]

    async def run(self, target_path, timeout, extra_args=None):
        cmd = ["tool", "--json", "--flags", target_path]
        if extra_args:
            cmd.extend(extra_args)
        stdout, stderr, rc = await self._execute(cmd, timeout)
        data = json.loads(stdout)
        # Parse and normalize to FindingSchema
        return findings
```

### Anti-Patterns to Avoid
- **Researching commercial/paid tools:** Out of scope per REQUIREMENTS.md
- **Performance benchmarking:** Focus on capability and integration ease, not speed comparisons
- **Custom scanner development:** Research existing tools, do not propose building new ones
- **Ignoring Docker size impact:** JVM-based tools (SpotBugs) add significant footprint; always note this

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Go SAST | Custom Go AST analyzer | gosec | 70+ checks, JSON/SARIF output, active maintenance |
| Rust SCA | Custom crate vulnerability checker | cargo-audit | Official RustSec advisory database integration |
| Java SAST | Custom bytecode analyzer | SpotBugs + FindSecBugs | 400+ bug patterns + 144 security vulnerability types |
| Ruby SAST | Custom Ruby AST parser | Brakeman | 33 vulnerability types, zero-config Rails scanning |
| Python SAST beyond Semgrep | Custom Python checker | Bandit | 47 Python-specific checks, JSON/SARIF output |
| SARIF parsing | Custom SARIF parser | sarif-tools (pip) or direct JSON parsing | SARIF is just JSON with a known schema |
| Plugin discovery | Custom plugin loader | stevedore or importlib entry_points | Battle-tested patterns for Python plugin systems |

## Common Pitfalls

### Pitfall 1: JVM Dependency Bloat
**What goes wrong:** Adding SpotBugs/FindSecBugs requires JVM in Docker image, adding 200+ MB
**Why it happens:** Java bytecode analysis requires compilation and JVM runtime
**How to avoid:** Document image size impact clearly; consider whether Semgrep's Java coverage is sufficient before adding SpotBugs
**Warning signs:** Docker image size doubling; longer build times

### Pitfall 2: Non-JSON Output Parsing Complexity
**What goes wrong:** Tools with only XML/text output require complex parsing that breaks between versions
**Why it happens:** Not all security tools prioritize machine-readable output
**How to avoid:** Prefer tools with JSON or SARIF output; document parsing effort as part of T-shirt sizing
**Warning signs:** Regex-based parsing, format-specific libraries needed

### Pitfall 3: Semgrep Licensing Confusion
**What goes wrong:** Semgrep changed licensing in January 2025; some features moved behind commercial license
**Why it happens:** Semgrep Inc. moved cross-function taint analysis to commercial tier; Opengrep fork emerged
**How to avoid:** Document which features are in CE vs commercial; evaluate whether Opengrep fork is needed
**Warning signs:** Missing taint analysis features, rule license restrictions

### Pitfall 4: False Positive Overload
**What goes wrong:** Adding too many scanners without tuning creates alert fatigue
**Why it happens:** Default rulesets are often overly broad
**How to avoid:** Document per-tool recommended rulesets and severity tuning; research should include specific config recommendations for reducing noise
**Warning signs:** Hundreds of INFO/LOW findings drowning out real issues

### Pitfall 5: DAST Scope Creep
**What goes wrong:** DAST tools require a running application, fundamentally different from SAST/SCA
**Why it happens:** DAST needs network access, target URLs, authentication configuration
**How to avoid:** Research should clearly separate DAST feasibility from SAST/SCA integration
**Warning signs:** Trying to fit DAST into the same adapter pattern as SAST

### Pitfall 6: Tool Overlap Without Deduplication
**What goes wrong:** Multiple tools report the same vulnerability, inflating finding counts
**Why it happens:** Semgrep covers many languages; adding language-specific tools creates overlap
**How to avoid:** Document which rules overlap between Semgrep and language-specific tools; existing deduplication uses fingerprints but same-issue-different-rule creates duplicates
**Warning signs:** Same vulnerability with different rule_ids from different tools

## Code Examples

### Existing Adapter Pattern (Semgrep - reference for researchers)
The Semgrep adapter demonstrates the canonical pattern. Key aspects:
- CLI invocation with `--json` flag
- Exit code handling (1 = findings found, not error; >= 2 = real error)
- JSON parsing with severity mapping dict
- Path normalization via `_normalize_path()`
- Fingerprint computation via `compute_fingerprint(file_path, rule_id, snippet)`

### Existing Config Pattern (config.yml)
```yaml
scanners:
  semgrep:
    enabled: true
    timeout: 180
    extra_args: ["--exclude", ".venv", "--exclude", "node_modules"]
  cppcheck:
    enabled: true
    timeout: 120
    extra_args: ["-i.venv", "-inode_modules"]
```

### Existing Language Detection Pattern
```python
SCANNER_LANGUAGES = {
    "semgrep": {"python", "php", "javascript", "typescript", "go", "java",
                "kotlin", "ruby", "csharp", "rust"},
    "cppcheck": {"cpp"},
    "gitleaks": set(),       # Universal
    "trivy": {"docker", "terraform", "yaml"},
    "checkov": {"docker", "terraform", "yaml", "ci"},
    "psalm": {"php"},
    "enlightn": {"laravel"},
    "php_security_checker": {"php"},
}
```
New scanners will need entries added here.

## State of the Art

### SAST Landscape (2025-2026)

| Language | No Dedicated Scanner Today | Recommended Tool | Output Format | SARIF? | Effort |
|----------|---------------------------|------------------|---------------|--------|--------|
| Go | Semgrep only | **gosec** | JSON, SARIF | Yes | S |
| Rust | Semgrep only | **cargo-audit** (SCA) + Semgrep (SAST) | JSON | No (JSON only) | S |
| Java | Semgrep only | **SpotBugs + FindSecBugs** | XML, SARIF | Yes | L |
| C# | Semgrep only | **security-code-scan** | SARIF | Yes | M |
| Ruby | Semgrep only | **Brakeman** | JSON, SARIF | Yes | S |
| JS/TS | Semgrep only | **eslint-plugin-security** (via ESLint) | JSON | No | M |
| Python | Semgrep only | **Bandit** (complementary) | JSON, SARIF | Yes | S |
| PHP | Psalm + Enlightn | Keep existing | -- | -- | -- |
| C/C++ | Cppcheck | Keep existing | -- | -- | -- |

### Semgrep/Opengrep Fork Situation
- January 2025: Semgrep Inc. moved cross-function taint analysis behind commercial license
- Opengrep launched as LGPL-2.1 community fork restoring those features
- Opengrep is fully backward compatible with Semgrep rule format, JSON output, and SARIF output
- **Research should evaluate**: Whether to recommend staying on Semgrep CE or switching to Opengrep

### SCA Landscape
| Tool | Strengths | Weaknesses | SARIF? | Recommendation |
|------|-----------|------------|--------|----------------|
| **Trivy** (current) | Broadest scope (deps + IaC + containers), single binary | Less precise risk scoring | Yes | Keep as primary |
| **Grype** | Best risk scoring (CVSS + EPSS + KEV), pure SCA focus | Narrower scope than Trivy | Yes | Consider as complement for risk prioritization |
| **OWASP Dep-Check** | Deepest Java/Maven coverage, CPE matching | Higher false positives, slower | No (XML) | Skip -- Trivy covers this |

### DAST Landscape
| Tool | Type | Best For | Integration Feasibility |
|------|------|----------|------------------------|
| **ZAP** | Full proxy + scanner | Comprehensive web app testing | L -- requires running app, proxy setup |
| **Nuclei** | Template-based scanner | Known CVE/misconfig detection | M -- CLI-friendly, template-based |
| **Nikto** | Server scanner | Web server misconfiguration | S -- but limited value (server-level only) |

### Secrets Scanning Comparison
| Feature | Gitleaks (current) | TruffleHog |
|---------|-------------------|------------|
| Speed | Faster (regex-only, no network) | Slower (verifies credentials) |
| Detection | Pattern matching | Pattern matching + active verification |
| Scope | Git repos, directories | Git + S3 + Docker + Slack + more |
| False positives | Higher (no verification) | Lower (active verification) |
| Docker size | ~15MB binary | ~50MB binary |
| **Recommendation** | **Keep as primary** (speed + simplicity) | Consider as CI/CD complement for depth |

### SARIF Adoption Assessment
| Tool | SARIF Support | Notes |
|------|--------------|-------|
| Semgrep/Opengrep | Yes | Native `--sarif` flag |
| gosec | Yes | `-fmt=sarif` flag |
| Bandit | Yes | `-f sarif` flag |
| Brakeman | Yes | `-f sarif` flag |
| SpotBugs | Yes | `-sarif` flag (since 4.5.0) |
| security-code-scan | Yes | `--export=report.sarif` |
| Trivy | Yes | `--format sarif` |
| Grype | Yes | `-o sarif` |
| cargo-audit | No | JSON only |
| Cppcheck | No | XML only |
| eslint-plugin-security | No | ESLint JSON format (custom) |
| Gitleaks | No | Custom JSON |
| Checkov | No | Custom JSON |

**SARIF evaluation conclusion:** 8 of 13 tools support SARIF. Adopting SARIF as an intermediate format could reduce adapter parsing code for SARIF-capable tools. However, 5 tools still need custom parsing. **Recommendation**: Introduce an optional SARIF parsing path alongside existing JSON parsing. New SARIF-capable tools can use a shared `parse_sarif()` helper to reduce per-adapter boilerplate. Non-SARIF tools keep custom parsers.

### Plugin Architecture Patterns

| Approach | Mechanism | Pros | Cons | Fit for Scanner |
|----------|-----------|------|------|----------------|
| **stevedore** | setuptools entry_points | Battle-tested, namespace isolation, lazy loading | Extra dependency, overkill for <20 plugins | Overkill |
| **importlib entry_points** | Python stdlib (3.9+) | No extra deps, standard pattern | Less helper infrastructure than stevedore | Good |
| **Config-driven registry** | YAML config lists adapter classes | Simplest, matches existing config.yml pattern | No dynamic discovery | **Best fit** |
| **Directory scanning** | Auto-discover adapters in a folder | Zero config for new adapters | Implicit, harder to control ordering | Acceptable |

**Recommendation:** Config-driven registry pattern. The project already uses `config.yml` for scanner enablement. Extend `ScannersConfig` to accept a dynamic list of scanner entries mapping `tool_name` to adapter class path. New scanners: add a Python file in `adapters/`, add entry in `config.yml`. No stevedore dependency needed -- the project has <20 scanners.

### Orchestration Improvements

**Parallel execution:** Already implemented via `asyncio.gather` in `orchestrator.py`. Current pattern is good.

**Incremental scanning (changed-files-only):**
- Pass a file list to scanners instead of entire directory
- Tools that support file-list input: Semgrep (`--include`), Bandit (`-f` with file list), gosec (path args), Brakeman (`--only-files`)
- Tools that require full project context: SpotBugs (needs compiled bytecode), Trivy (needs lockfiles), Checkov (needs full IaC context)
- **Recommendation:** Implement opt-in incremental mode for tools that support file-list input; fall back to full scan for tools that need project context

## Per-Tool Research Detail

### gosec (Go SAST)
- **Output:** JSON, SARIF, CSV, JUnit-XML, text
- **CLI:** `gosec -fmt=json -out=results.json ./...`
- **Docker install:** Single Go binary, ~15MB
- **SARIF:** Yes (`-fmt=sarif`)
- **Effort:** S -- JSON output, clean CLI, small binary
- **Detection:** 70+ security checks covering SQL injection, file traversal, hardcoded creds, crypto misuse
- **Config snippet:**
  ```yaml
  scanners:
    gosec:
      enabled: "auto"
      timeout: 120
      extra_args: ["-exclude=G101"]
  ```

### cargo-audit (Rust SCA)
- **Output:** JSON
- **CLI:** `cargo-audit audit --json`
- **Docker install:** `cargo install cargo-audit` or pre-built binary, ~10MB
- **SARIF:** No
- **Effort:** S -- simple JSON output, dependency-only scanning
- **Detection:** RustSec advisory database for known vulnerabilities in crate dependencies
- **Note:** Requires Cargo.lock file to be present

### SpotBugs + FindSecBugs (Java SAST)
- **Output:** XML, SARIF, HTML
- **CLI:** `java -jar spotbugs.jar -sarif -pluginList findsecbugs-plugin.jar target/classes`
- **Docker install:** Requires JVM (~200MB+ image size increase)
- **SARIF:** Yes (since SpotBugs 4.5.0)
- **Effort:** L -- requires Java compilation step, JVM dependency, bytecode analysis
- **Detection:** 400+ bug patterns + 144 security vulnerability types from FindSecBugs
- **Concern:** Requires compiled .class files, not just source code. Scanner currently works on source directories.

### security-code-scan (C# SAST)
- **Output:** SARIF
- **CLI:** `security-scan /path/to/solution.sln --export=report.sarif`
- **Docker install:** Requires .NET SDK (~200MB)
- **SARIF:** Yes (native)
- **Effort:** M -- SARIF output simplifies parsing, but .NET SDK is heavy
- **Detection:** SQLi, XSS, CSRF, XXE, Open Redirect in C#/VB.NET
- **Note:** Requires .sln/.csproj files, Roslyn-based analysis

### Brakeman (Ruby SAST)
- **Output:** JSON, SARIF, HTML, CSV, text, markdown
- **CLI:** `brakeman --format json --no-exit-on-warn /path/to/rails/app`
- **Docker install:** `gem install brakeman`, ~5MB (Ruby runtime needed)
- **SARIF:** Yes (`-f sarif`)
- **Effort:** S -- clean JSON output, zero-config for Rails apps
- **Detection:** 33 vulnerability types covering OWASP Top 10 for Rails 2.3.x through 8.x
- **Note:** Rails-specific; for non-Rails Ruby, Semgrep is the only option

### Bandit (Python SAST)
- **Output:** JSON, SARIF, HTML, CSV, XML, text
- **CLI:** `bandit -r /path/to/code -f json`
- **Docker install:** `pip install bandit`, ~5MB; official multi-arch Docker image available
- **SARIF:** Yes (`-f sarif`)
- **Effort:** S -- JSON/SARIF output, pip install, small footprint
- **Detection:** 47 Python-specific security checks, 88% recall rate
- **Note:** Overlaps with Semgrep's Python rules; use as complement for deeper Python-specific checks
- **Baseline support:** Can compare against baseline file for incremental scanning

### eslint-plugin-security (JS/TS SAST)
- **Output:** ESLint JSON format (not standard SARIF)
- **CLI:** `eslint --format json --plugin security /path/to/code`
- **Docker install:** `npm install eslint eslint-plugin-security`, Node.js runtime needed (~100MB+)
- **SARIF:** No (requires ESLint SARIF formatter adapter)
- **Effort:** M -- needs Node.js runtime, ESLint config setup, custom JSON parsing
- **Detection:** 14 security rules for Node.js (eval injection, child_process, regex DoS, etc.)
- **Note:** Limited coverage compared to Semgrep's JS/TS rules; may not justify the Node.js dependency

### Grype (SCA alternative)
- **Output:** JSON, SARIF, table, CycloneDX
- **CLI:** `grype dir:/path/to/project -o json`
- **Docker install:** Single binary ~30MB
- **SARIF:** Yes (`-o sarif`)
- **Effort:** S -- clean CLI, familiar pattern to Trivy adapter
- **Detection:** CVE matching with CVSS + EPSS + KEV risk scoring
- **Note:** Complementary to Trivy; better risk prioritization but narrower scope

### Nuclei (DAST)
- **Output:** JSON, SARIF, markdown
- **CLI:** `nuclei -u https://target -jsonl -o results.json`
- **Docker install:** Single binary ~30MB
- **SARIF:** Yes
- **Effort:** M -- different paradigm (needs running app + URL), but CLI-friendly
- **Detection:** 11,000+ community templates for CVEs, misconfigs, exposed panels
- **Note:** Template-based approach means targeted scanning; fast (minutes not hours)

### ZAP (DAST)
- **Output:** JSON, XML, HTML, SARIF (via plugins)
- **CLI:** `zap-cli quick-scan --self-contained https://target`
- **Docker install:** Requires JVM + full ZAP install (~500MB+)
- **SARIF:** Via community plugins
- **Effort:** L -- heavy footprint, requires running app, complex configuration
- **Detection:** Comprehensive web app security (XSS, SQLi, CSRF, etc.)
- **Note:** Most thorough DAST but hardest to integrate in current architecture

## Priority Ranking (SCAN-07)

### Tier 1: High Value, Low Effort (implement first)
| Priority | Tool | Language | Effort | Justification |
|----------|------|----------|--------|---------------|
| 1 | gosec | Go | S | Clean JSON/SARIF, small binary, fills major gap |
| 2 | Brakeman | Ruby | S | Clean JSON/SARIF, zero-config Rails, fills gap |
| 3 | Bandit | Python | S | Complements Semgrep, JSON/SARIF, pip install |
| 4 | cargo-audit | Rust | S | Simple JSON, fills Rust SCA gap |

### Tier 2: Medium Value, Medium Effort
| Priority | Tool | Language | Effort | Justification |
|----------|------|----------|--------|---------------|
| 5 | Grype | SCA (all) | S | Better risk scoring than Trivy, easy CLI |
| 6 | security-code-scan | C# | M | SARIF native, but .NET SDK dependency |
| 7 | Nuclei | DAST | M | Template-based, CLI-friendly, but requires running app |

### Tier 3: High Value but High Effort
| Priority | Tool | Language | Effort | Justification |
|----------|------|----------|--------|---------------|
| 8 | SpotBugs + FindSecBugs | Java | L | Deep Java coverage, but JVM + compilation required |
| 9 | ZAP | DAST | L | Most comprehensive DAST, but massive footprint |

### Not Recommended
| Tool | Reason |
|------|--------|
| eslint-plugin-security | Only 14 rules, Semgrep already covers JS/TS more thoroughly; not worth Node.js dependency |
| OWASP Dependency-Check | Higher false positives than Trivy/Grype, slower, XML-only output |
| Nikto | Server-level only, limited value compared to Nuclei |
| TruffleHog (replace Gitleaks) | Gitleaks is faster and simpler; TruffleHog's verification is nice but adds complexity. Keep Gitleaks. |

### Opengrep Evaluation
- **Recommendation:** Monitor but don't switch yet. Semgrep CE still works well for this project's needs. If cross-function taint analysis becomes important, evaluate Opengrep as a drop-in replacement (same CLI, same rules, same output format).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (existing) |
| Config file | `pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `pytest tests/ -x --timeout=30` |
| Full suite command | `pytest tests/ --timeout=60` |

### Phase Requirements to Test Map
This phase produces a research document, not code. Validation is review-based.

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SCAN-01 | Per-language SAST tool coverage documented | manual-only | Review 07-RESEARCH.md language sections | N/A |
| SCAN-02 | SCA tools compared | manual-only | Review SCA comparison section | N/A |
| SCAN-03 | DAST tools assessed | manual-only | Review DAST feasibility section | N/A |
| SCAN-04 | Config best practices documented | manual-only | Review per-tool config guidance | N/A |
| SCAN-05 | Plugin architecture researched | manual-only | Review plugin architecture section | N/A |
| SCAN-06 | Integration requirements documented | manual-only | Review per-tool research cards | N/A |
| SCAN-07 | Priority ranking produced | manual-only | Review priority matrix | N/A |

### Sampling Rate
- **Per task commit:** Manual review of section completeness
- **Per wave merge:** Full document review against success criteria
- **Phase gate:** All 6 success criteria met before `/gsd:verify-work`

### Wave 0 Gaps
None -- this is a research-only phase with no test infrastructure needed.

## Open Questions

1. **Opengrep stability and long-term viability**
   - What we know: Fork launched January 2025 with consortium backing; backward compatible
   - What's unclear: Long-term maintenance commitment, pace of updates vs Semgrep CE
   - Recommendation: Document in research report; monitor but don't recommend switching yet

2. **SpotBugs compilation requirement**
   - What we know: SpotBugs requires compiled Java bytecode (.class files), not source
   - What's unclear: How to handle this in a source-code-scanning tool (scanner receives source dirs)
   - Recommendation: Document as a major integration challenge; may need a build step before scanning

3. **DAST integration model**
   - What we know: DAST requires a running application, fundamentally different from SAST/SCA
   - What's unclear: Whether to extend ScannerAdapter or create a separate DastAdapter base class
   - Recommendation: Research should propose but leave implementation to a future phase

4. **Incremental scanning trade-offs**
   - What we know: Some tools support file-list input; others need full project context
   - What's unclear: Whether partial scans miss cross-file vulnerabilities
   - Recommendation: Document which tools support incremental safely and which don't

## Sources

### Primary (HIGH confidence)
- Existing codebase: `src/scanner/adapters/`, `src/scanner/core/`, `src/scanner/config.py` -- full adapter pattern analysis
- [gosec GitHub](https://github.com/securego/gosec) -- Go security scanner with 70+ checks, JSON/SARIF output
- [Brakeman](https://brakemanscanner.org/) -- Ruby on Rails scanner, JSON/SARIF output, 33 vuln types
- [Bandit PyPI](https://pypi.org/project/bandit/) -- Python SAST, JSON/SARIF, multi-arch Docker images
- [SpotBugs](https://spotbugs.github.io/) -- Java SAST, SARIF support since 4.5.0
- [FindSecBugs](https://find-sec-bugs.github.io/) -- SpotBugs security plugin, 144 vulnerability types
- [security-code-scan](https://security-code-scan.github.io/) -- C#/VB.NET SAST, standalone CLI, SARIF output
- [Grype GitHub](https://github.com/anchore/grype) -- SCA scanner, CVSS+EPSS+KEV scoring
- [SARIF OASIS Standard](https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html) -- SARIF v2.1.0 specification

### Secondary (MEDIUM confidence)
- [Wiz SAST Tools Overview](https://www.wiz.io/academy/application-security/top-open-source-sast-tools) -- Multi-tool comparison
- [AppSec Santa DAST Comparison](https://appsecsanta.com/dast-tools/free-dast-tools) -- ZAP vs Nuclei vs Nikto
- [AppSec Santa SCA Comparison](https://appsecsanta.com/sca-tools/open-source-sca-tools) -- Grype vs Trivy vs Dep-Check
- [Opengrep vs Semgrep Comparison](https://appsecsanta.com/sast-tools/opengrep-vs-semgrep) -- Fork analysis
- [Gitleaks vs TruffleHog](https://appsecsanta.com/sast-tools/gitleaks-vs-trufflehog) -- Secrets scanner comparison
- [stevedore docs](https://docs.openstack.org/stevedore/latest/) -- Python plugin architecture patterns

### Tertiary (LOW confidence)
- Docker image size estimates are approximate based on experience and general package sizes; exact sizes should be verified during implementation

## Metadata

**Confidence breakdown:**
- Standard stack (existing tools): HIGH -- verified from codebase directly
- New tool recommendations: HIGH -- verified from official GitHub repos and documentation
- SARIF support claims: HIGH -- verified from multiple official sources
- Docker size estimates: LOW -- approximate, need verification
- Plugin architecture: MEDIUM -- based on known patterns but project-specific fit needs validation
- DAST integration: MEDIUM -- feasibility assessed but integration model unproven

**Research date:** 2026-03-20
**Valid until:** 2026-04-20 (30 days -- security tool ecosystem is moderately stable)
