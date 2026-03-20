# Phase 7: Security Scanner Ecosystem Research - Context

**Gathered:** 2026-03-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Produce a comprehensive research report on available open-source security scanning tools, their optimal configurations, and recommendations for expanding the scanner. Covers SAST per language, SCA tools, DAST feasibility, secrets scanning, plugin architecture patterns, and orchestration improvements. The output is a research document that informs future implementation phases — no code changes in this phase.

</domain>

<decisions>
## Implementation Decisions

### Research scope & depth
- **Gaps + re-evaluate existing**: Research tools for languages with no dedicated scanner (Go, Rust, Java, C#, Ruby, JS/TS SAST) AND re-evaluate whether current tools (Semgrep, Cppcheck, Psalm, Gitleaks, Trivy, Checkov) are still optimal
- **Full SCA comparison**: Research SCA alternatives (Grype, Dependency-Check, etc.) even though Trivy handles SCA today — to have a complete picture of the landscape
- **DAST feasibility assessment**: Survey major open-source DAST tools (ZAP, Nuclei, Nikto), assess integration feasibility with the existing adapter pattern, recommend whether to pursue
- **Secrets scanning quick check**: Briefly compare Gitleaks vs TruffleHog — confirm Gitleaks is still best or note if TruffleHog has pulled ahead

### Report structure & output
- **Organized by language**: Main sections per language (Python, PHP, Go, Rust, Java, C#, Ruby, JS/TS, C/C++), each listing tools with pros/cons/recommendation. Cross-cutting sections for SCA, DAST, secrets
- **Per-language comparison tables**: Each language section ends with a comparison matrix. Plus a final summary matrix ranking all recommended tools
- **Single document**: One comprehensive research report in the phase directory (07-RESEARCH.md). Easy to reference and review as a whole
- **Config snippets included**: Each recommended tool includes a sample config.yml entry (enabled, timeout, extra_args) showing how it would look in the scanner

### Evaluation criteria
- **Primary criterion: integration ease**: CLI interface, JSON/SARIF output support, Docker availability, how easy to wrap in a ScannerAdapter (run command, parse output, normalize to FindingSchema)
- **False positive reduction: tool-level config**: Document which rulesets to enable/disable per tool, severity tuning, exclude patterns. Practical configuration guidance
- **T-shirt size effort estimates**: S/M/L per tool based on output parsing complexity, Docker install size, config needs
- **Docker image size impact**: Note approximate footprint per tool (e.g., "adds ~50MB" or "requires JVM ~200MB")

### Plugin architecture vision
- **Research patterns, recommend approach**: Survey plugin/adapter patterns (stevedore, entry points, config-driven dispatch) and recommend an approach. Don't implement, just propose
- **Include non-JSON tools with effort notes**: Research all relevant tools regardless of output format, but flag parsing effort for non-JSON/non-SARIF tools
- **SARIF evaluation**: Assess which tools support SARIF and whether adopting it as a normalized intermediate format would simplify adding new scanners
- **Orchestration improvements in scope**: Research parallel execution patterns and incremental scanning strategies (changed-files-only scanning) alongside plugin architecture

### Claude's Discretion
- Exact organization of sub-sections within each language
- How to structure the comparison matrices (which columns, scoring scale)
- How deep to go into each individual tool's configuration options
- Formatting and level of detail in config.yml snippets
- How to present the SARIF evaluation findings

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Current scanner architecture
- `src/scanner/adapters/base.py` — ScannerAdapter abstract base class defining the adapter contract (run, get_version, _version_command)
- `src/scanner/adapters/__init__.py` — ALL_ADAPTERS registry listing current 8 adapters
- `src/scanner/core/orchestrator.py` — Scan orchestration logic, adapter dispatch, deduplication
- `src/scanner/core/language_detect.py` — Language detection with _EXT_TO_LANG mapping (determines which scanners activate)
- `src/scanner/config.py` — ScannerSettings, ScannersConfig defining per-scanner config structure

### Existing adapters (re-evaluate these)
- `src/scanner/adapters/semgrep.py` — Multi-language SAST (uses 'auto' config)
- `src/scanner/adapters/cppcheck.py` — C/C++ SAST
- `src/scanner/adapters/psalm.py` — PHP SAST
- `src/scanner/adapters/enlightn.py` — PHP/Laravel security
- `src/scanner/adapters/php_security_checker.py` — PHP dependency checker
- `src/scanner/adapters/checkov.py` — Infrastructure as code scanning
- `config.yml` — Current scanner configuration (semgrep, cppcheck, gitleaks, trivy, checkov enabled)

### Project context
- `.planning/REQUIREMENTS.md` — SCAN-01 through SCAN-07 requirements for this phase
- `.planning/ROADMAP.md` — Phase 7 goal and 6 success criteria
- `.planning/codebase/ARCHITECTURE.md` — Full architecture overview with layer descriptions

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ScannerAdapter` base class: Well-defined contract (tool_name, run, get_version, _version_command, _execute) — new scanners follow this pattern
- `FindingSchema`: Pydantic data contract all adapters normalize to — research should evaluate how well new tools' output maps to this schema
- `language_detect.py`: Maps file extensions to language tags — determines which scanners activate per project
- `config.yml` scanners section: Per-scanner config with enabled/timeout/extra_args — research should propose entries in this format

### Established Patterns
- Adapter pattern: Each scanner is a Python class extending ScannerAdapter, wrapping a CLI tool
- Async subprocess execution via `_execute()` with timeout handling
- JSON output parsing as the primary normalization path (Semgrep, Trivy, Checkov all output JSON)
- Config-driven enablement: Each scanner has enabled/timeout/extra_args in config.yml
- ALL_ADAPTERS list in `__init__.py` serves as the scanner registry

### Integration Points
- `orchestrator.py` dispatches to adapters based on detected languages and enabled scanners
- `ScanQueue` processes scans serially — orchestration research should consider parallel execution
- Docker image installs scanner CLI tools in Dockerfile — new tools need Docker install steps
- `language_detect.py` maps extensions to languages — new language-specific scanners need corresponding mappings

</code_context>

<specifics>
## Specific Ideas

- Config snippets should match existing config.yml format (scanners.{name}.enabled/timeout/extra_args)
- Effort estimates should account for Docker image size impact (some tools bring JVM or large runtimes)
- SARIF evaluation should consider whether a SARIF intermediate layer would reduce per-adapter parsing work
- Orchestration research should cover both parallel scanner execution and incremental (changed-files-only) scanning

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 07-security-scanner-ecosystem-research*
*Context gathered: 2026-03-20*
