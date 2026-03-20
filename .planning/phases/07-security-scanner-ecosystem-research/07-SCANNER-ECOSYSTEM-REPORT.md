# Security Scanner Ecosystem Research Report

**Date:** 2026-03-20
**Phase:** 07 -- Security Scanner Ecosystem Research
**Scope:** Open-source SAST, SCA, DAST, secrets scanning tools
**Existing adapters:** Semgrep, Cppcheck, Gitleaks, Trivy, Checkov, Psalm, Enlightn, PHP Security Checker

---

## Table of Contents

1. [Per-Language SAST Sections](#per-language-sast-sections)
   - [Python](#python)
   - [PHP](#php)
   - [JavaScript/TypeScript](#javascripttypescript)
   - [Go](#go)
   - [Rust](#rust)
   - [Java](#java)
   - [C#](#c)
   - [C/C++](#cc)
   - [Ruby](#ruby)
2. [SCA (Software Composition Analysis) Tools](#sca-software-composition-analysis-tools)
3. [DAST (Dynamic Application Security Testing) Feasibility](#dast-dynamic-application-security-testing-feasibility)
4. [Secrets Scanning Comparison](#secrets-scanning-comparison)

---

## Per-Language SAST Sections

Each language section evaluates current coverage, recommends additions where gaps exist, and provides research cards following the established template. Config snippets match the existing `config.yml` format (`scanners.{name}.enabled/timeout/extra_args`).

---

## Python

**Current coverage:** Semgrep (multi-language SAST)
**Recommendation:** Add Bandit as complementary Python-specific SAST

### Semgrep (Re-evaluation)

- **Purpose:** Multi-language SAST via pattern matching
- **Language(s):** Python, PHP, JS/TS, Go, Java, Ruby, C#, Rust (10 languages)
- **License:** LGPL-2.1 (Semgrep CE); proprietary for Semgrep Code (commercial)
- **Output formats:** JSON, SARIF, text, emacs, vim
- **CLI usage:** `semgrep scan --json --config auto /path/to/code`
- **Docker install:** `pip install semgrep`, ~150MB total footprint
- **SARIF support:** Yes (`--sarif` flag)
- **Integration effort:** Already integrated (adapter exists)
- **Status:** Active development. Remains the best multi-language SAST for this project.

**Opengrep Fork Situation (January 2025):**
- Semgrep Inc. moved cross-function taint analysis behind the commercial license
- Opengrep launched as an LGPL-2.1 community fork restoring those features
- Opengrep is fully backward compatible: same CLI, same rule format, same JSON/SARIF output
- **Recommendation:** Monitor but do not switch yet. Semgrep CE works well for this project's needs. Cross-function taint analysis (now commercial-only) would improve detection of data-flow vulnerabilities, but the current rule set provides adequate coverage. If cross-function taint becomes critical, Opengrep is a drop-in replacement.

**Current config:**
```yaml
scanners:
  semgrep:
    enabled: true
    timeout: 180
    extra_args: ["--exclude", ".venv", "--exclude", "node_modules"]
```

- **Pros:** Broadest language coverage, active rule community, well-integrated already
- **Cons:** Cross-function taint analysis now commercial-only, Opengrep fork creates ecosystem uncertainty

### Bandit (Recommended Addition)

- **Purpose:** Python-specific SAST with 47 security checks
- **Language(s):** Python
- **License:** Apache-2.0
- **Output formats:** JSON, SARIF, HTML, CSV, XML, text
- **CLI usage:** `bandit -r /path/to/code -f json`
- **Docker install:** `pip install bandit`, ~5MB; official multi-arch Docker image available
- **SARIF support:** Yes (`-f sarif` flag)
- **Integration effort:** S -- JSON output maps cleanly to FindingSchema, pip install, small footprint
- **Config snippet:**
```yaml
scanners:
  bandit:
    enabled: "auto"
    timeout: 120
    extra_args: ["-ll", "--exclude", ".venv"]
```
- **FindingSchema mapping:**
  - fingerprint: computed from `file_path + test_id + code`
  - rule_id: from `test_id` field (e.g., B101, B102)
  - severity: from `issue_severity` (LOW/MEDIUM/HIGH maps directly to FindingSchema severity)
  - line_start: from `line_number`
  - line_end: from `line_range[-1]` if available
  - snippet: from `code` field
  - file_path: from `filename`, normalized via `_normalize_path()`
  - title: from `test_name` (e.g., "assert_used", "exec_used")
  - description: from `issue_text`
- **False positive reduction:**
  - Use `-ll` flag to report only medium+ severity (skips LOW)
  - Exclude test directories: `--exclude .venv,tests`
  - Use `.bandit` config file for project-specific rule skips
  - Baseline support: `bandit -b baseline.json` for incremental scanning (compare against previous run)
- **Detection:** 47 Python-specific checks covering:
  - Dangerous function calls (exec, eval, subprocess)
  - Hardcoded passwords and secrets
  - Weak cryptography (MD5, SHA1, DES)
  - SQL injection (string concatenation in queries)
  - XML vulnerabilities (XXE)
  - Assert statements in production code
  - 88% recall rate on OWASP benchmarks
- **Pros:**
  - Deep Python-specific checks that Semgrep may miss
  - Complements Semgrep rather than replacing it
  - JSON/SARIF output for easy integration
  - Tiny footprint (5MB pip install)
  - Baseline support for incremental scanning
  - Active OpenStack-maintained project
- **Cons:**
  - Python-only (no multi-language value)
  - Some overlap with Semgrep Python rules
  - Higher false positive rate on LOW severity findings (mitigated by `-ll` flag)

**SCANNER_LANGUAGES entry:**
```python
"bandit": {"python"},
```

### Comparison Matrix

| Feature | Semgrep | Bandit |
|---------|---------|--------|
| **Coverage** | Broad (10 languages, pattern-based) | Deep (Python-only, 47 checks) |
| **Output Format** | JSON, SARIF | JSON, SARIF |
| **SARIF** | Yes | Yes |
| **Docker Size** | ~150MB | ~5MB |
| **Integration Effort** | Already integrated | S |
| **Detection Style** | Pattern matching, cross-file | AST analysis, Python-specific |
| **False Positive Rate** | Low-medium | Medium (tunable with -ll) |
| **Recommendation** | Keep as primary multi-language SAST | **Add as Python complement** |

**Verdict:** Use both. Semgrep provides broad coverage across languages. Bandit adds deeper Python-specific checks (dangerous function calls, weak crypto, XML vulnerabilities) that Semgrep's generic patterns may not catch. Overlap exists but the complementary coverage justifies the small footprint.

---

## PHP

**Current coverage:** Psalm (type-aware SAST), Enlightn (Laravel security), PHP Security Checker (dependency scanning)
**Recommendation:** Keep existing tools. PHP is well-covered.

### Psalm (Re-evaluation)

- **Purpose:** PHP static analysis with type inference and security taint analysis
- **Language(s):** PHP
- **License:** MIT
- **Output formats:** JSON, XML, text, SARIF (via plugin)
- **CLI usage:** `psalm --output-format=json /path/to/code`
- **Docker install:** `composer require --dev vimeo/psalm`, ~20MB
- **SARIF support:** Via community plugin
- **Integration effort:** Already integrated (adapter exists)
- **Status:** Active development. Remains the best open-source PHP SAST tool.
- **Key strengths:** Type-aware analysis, taint analysis for security vulnerabilities (SQLi, XSS), deep PHP understanding
- **Pros:** Type-aware analysis catches issues other tools miss, active development, strong community
- **Cons:** Requires `psalm.xml` config for best results, slower on large codebases

### Enlightn (Re-evaluation)

- **Purpose:** Laravel-specific security and performance auditing
- **Language(s):** Laravel (PHP framework)
- **License:** LGPL-3.0
- **Output formats:** JSON (via adapter parsing)
- **CLI usage:** `php artisan enlightn --json`
- **Docker install:** `composer require enlightn/enlightn`, framework-integrated
- **Integration effort:** Already integrated (adapter exists)
- **Status:** Active. Complementary to Psalm -- covers Laravel-specific security patterns.
- **Key strengths:** Laravel-specific checks (route security, CSRF, mass assignment, file upload validation)
- **Pros:** Zero-config for Laravel projects, catches framework-specific issues Psalm misses
- **Cons:** Laravel-only, not applicable to non-Laravel PHP projects

### PHP Security Checker (Re-evaluation)

- **Purpose:** PHP dependency vulnerability checking via SensioLabs security advisories
- **Language(s):** PHP
- **License:** MIT
- **Output formats:** JSON, YAML, text
- **CLI usage:** `local-php-security-checker --format=json --path=/path/to/composer.lock`
- **Docker install:** Single binary ~5MB
- **Integration effort:** Already integrated (adapter exists)
- **Status:** Active. Provides PHP-specific SCA that complements Trivy's broader dependency scanning.
- **Pros:** Fast, lightweight, PHP-specific advisory database
- **Cons:** PHP-only SCA (Trivy also covers PHP deps but with less PHP-specific depth)

### Comparison Matrix

| Feature | Psalm | Enlightn | PHP Security Checker |
|---------|-------|----------|---------------------|
| **Purpose** | SAST (type-aware) | Laravel security audit | SCA (PHP deps) |
| **Coverage** | All PHP code | Laravel-specific | composer.lock deps |
| **Output Format** | JSON, XML | JSON | JSON |
| **SARIF** | Via plugin | No | No |
| **Docker Size** | ~20MB | Framework-integrated | ~5MB |
| **Integration Effort** | Already integrated | Already integrated | Already integrated |
| **Recommendation** | **Keep** | **Keep** (for Laravel) | **Keep** |

**Verdict:** All three tools serve different purposes and complement each other well. No changes needed for PHP coverage.

---

## JavaScript/TypeScript

**Current coverage:** Semgrep (multi-language SAST)
**Recommendation:** Do NOT add eslint-plugin-security. Semgrep coverage is sufficient.

### Semgrep JS/TS Coverage (Re-evaluation)

Semgrep provides broad JavaScript and TypeScript SAST coverage through its rule registry:
- OWASP Top 10 patterns (XSS, injection, SSRF)
- Node.js security patterns (child_process, eval, prototype pollution)
- Framework-specific rules (Express, React)
- Dependency confusion patterns
- Covers both `.js/.jsx` and `.ts/.tsx` files

Semgrep's JS/TS coverage is comprehensive enough that a dedicated JS/TS security scanner is not needed.

### eslint-plugin-security (Evaluated -- Not Recommended)

- **Purpose:** ESLint plugin adding 14 security-focused lint rules for Node.js
- **Language(s):** JavaScript, TypeScript (via ESLint)
- **License:** Apache-2.0
- **Output formats:** ESLint JSON format (not standard JSON or SARIF)
- **CLI usage:** `eslint --format json --plugin security /path/to/code`
- **Docker install:** `npm install eslint eslint-plugin-security`, requires Node.js runtime (~100MB+)
- **SARIF support:** No (requires separate ESLint SARIF formatter adapter, adding complexity)
- **Integration effort:** M -- needs Node.js runtime in Docker image, ESLint config setup, custom output parsing
- **Config snippet:** N/A (not recommended)
- **Detection:** Only 14 security rules:
  - `detect-eval-with-expression`
  - `detect-child-process`
  - `detect-non-literal-regexp`
  - `detect-non-literal-fs-filename`
  - `detect-object-injection`
  - `detect-possible-timing-attacks`
  - And 8 others
- **FindingSchema mapping:** Would require custom ESLint JSON parsing -- rule_id from `ruleId`, severity from ESLint `severity` (1=warn, 2=error), line from `line`, snippet from `source`
- **Pros:**
  - Runs within ESLint (if project already uses ESLint)
  - Some Node.js-specific checks
- **Cons:**
  - Only 14 rules -- very limited coverage
  - Requires Node.js runtime (~100MB+ Docker image increase)
  - No SARIF support without additional tooling
  - Custom ESLint JSON output requires dedicated parser
  - Semgrep already covers all 14 patterns and more
  - Would add significant Docker image bloat for minimal value

**Why Not Recommended:** Semgrep already covers JS/TS security patterns more thoroughly with 100+ rules compared to eslint-plugin-security's 14. Adding Node.js runtime (~100MB) to the Docker image for 14 overlapping rules does not justify the cost. Projects using ESLint can adopt this plugin independently, but it should not be bundled in the scanner.

### Comparison Matrix

| Feature | Semgrep | eslint-plugin-security |
|---------|---------|----------------------|
| **Coverage** | 100+ JS/TS security rules | 14 rules |
| **Output Format** | JSON, SARIF | ESLint JSON (custom) |
| **SARIF** | Yes | No |
| **Docker Size** | Already installed | +100MB (Node.js runtime) |
| **Integration Effort** | Already integrated | M |
| **Runtime Dependency** | None (standalone binary) | Node.js required |
| **Recommendation** | **Keep as sole JS/TS SAST** | **Not Recommended** |

**Verdict:** Semgrep provides superior JS/TS coverage without additional runtime dependencies. eslint-plugin-security is not recommended for integration.

---

## Go

**Current coverage:** Semgrep (multi-language SAST)
**Recommendation:** Add gosec for dedicated Go SAST

### gosec (Recommended Addition)

- **Purpose:** Go source code security analyzer with 70+ checks
- **Language(s):** Go
- **License:** Apache-2.0
- **Output formats:** JSON, SARIF, CSV, JUnit-XML, text
- **CLI usage:** `gosec -fmt=json ./...`
- **Docker install:** Single Go binary, ~15MB
- **SARIF support:** Yes (`-fmt=sarif`)
- **Integration effort:** S -- clean JSON output, small binary, straightforward CLI
- **Config snippet:**
```yaml
scanners:
  gosec:
    enabled: "auto"
    timeout: 120
    extra_args: ["-exclude=G101"]
```
- **FindingSchema mapping:**
  - fingerprint: computed from `file + rule_id + code`
  - rule_id: from `rule_id` field (e.g., G101, G201, G401)
  - severity: from `severity` field (LOW/MEDIUM/HIGH maps directly)
  - line_start: from `line` field
  - line_end: from `line` field (gosec reports single line)
  - file_path: from `file` field, normalized via `_normalize_path()`
  - snippet: from `code` field
  - title: from `details` field (short description)
  - description: from `details` field
- **False positive reduction:**
  - Exclude G101 (hardcoded credentials) if project uses test constants -- this is the noisiest rule
  - Use `-exclude-generated` to skip generated code (protobuf, wire, etc.)
  - Use `-severity=medium` to skip LOW findings
  - Use `-confidence=medium` to skip low-confidence detections
  - Per-line suppression via `// #nosec G101` comments
- **Detection:** 70+ security checks covering:
  - G101: Hardcoded credentials
  - G201-G203: SQL injection (string concatenation, format strings)
  - G301-G307: File permissions and path traversal
  - G401-G407: Weak cryptography (DES, RC4, MD5)
  - G501-G505: Blocklisted imports (crypto/md5, net/http/cgi)
  - G601: Implicit memory aliasing in loops
  - And more
- **Pros:**
  - Deep Go-specific security analysis
  - Single binary, tiny footprint (15MB)
  - JSON and SARIF output for easy integration
  - Active development with regular rule updates
  - Understands Go idioms (goroutines, channels, defer)
- **Cons:**
  - Go-only (no multi-language value)
  - G101 (hardcoded credentials) can be noisy in test code
  - Some overlap with Semgrep Go rules

**SCANNER_LANGUAGES entry:**
```python
"gosec": {"go"},
```

### Comparison Matrix

| Feature | Semgrep | gosec |
|---------|---------|-------|
| **Coverage** | Broad Go patterns | 70+ Go-specific security checks |
| **Output Format** | JSON, SARIF | JSON, SARIF |
| **SARIF** | Yes | Yes |
| **Docker Size** | Already installed | +15MB |
| **Integration Effort** | Already integrated | S |
| **Detection Depth** | Pattern-based, shallower | Deep Go-specific (crypto, SQL, file perms) |
| **Recommendation** | Keep for broad patterns | **Add for deep Go analysis** |

**Verdict:** Use both. Semgrep provides broad pattern coverage, while gosec adds deeper Go-specific security checks covering SQL injection, cryptographic misuse, file permission errors, and more. The 15MB footprint and clean JSON/SARIF output make integration straightforward.

---

## Rust

**Current coverage:** Semgrep (multi-language SAST)
**Recommendation:** Add cargo-audit for Rust SCA (dependency vulnerability scanning)

### cargo-audit (Recommended Addition)

- **Purpose:** Audit Rust crate dependencies for known security vulnerabilities using the RustSec advisory database
- **Language(s):** Rust
- **License:** Apache-2.0 / MIT (dual-licensed)
- **Output formats:** JSON, text
- **CLI usage:** `cargo-audit audit --json`
- **Docker install:** `cargo install cargo-audit` or pre-built binary, ~10MB
- **SARIF support:** No (JSON only -- would need a JSON-to-SARIF adapter or custom parsing)
- **Integration effort:** S -- simple JSON output, dependency-only scanning, small binary
- **Config snippet:**
```yaml
scanners:
  cargo_audit:
    enabled: "auto"
    timeout: 60
    extra_args: []
```
- **FindingSchema mapping:**
  - fingerprint: computed from `advisory.id + affected_crate + version`
  - rule_id: from advisory `id` field (e.g., RUSTSEC-2021-0001)
  - severity: from advisory `cvss` score mapped to severity: CVSS 0.0-3.9 = LOW, 4.0-6.9 = MEDIUM, 7.0-8.9 = HIGH, 9.0-10.0 = CRITICAL
  - line_start: N/A (dependency-level, not source-level)
  - file_path: "Cargo.lock" (all findings reference the lockfile)
  - snippet: affected crate name + version (e.g., "openssl 0.10.35")
  - title: from advisory `title` field
  - description: from advisory `description` field
- **False positive reduction:**
  - Use `--ignore RUSTSEC-xxxx-xxxx` for known false positives or accepted risks
  - Use `cargo-audit audit --json --stale` to flag outdated advisories
  - Maintain `audit.toml` config for project-specific ignores with expiry dates
- **Detection:** RustSec advisory database covering:
  - Known CVEs in published crates
  - Yanked crate versions
  - Unmaintained crate warnings
- **Note:** This is SCA only (dependency vulnerabilities), not SAST. Semgrep handles Rust SAST patterns. cargo-audit requires a `Cargo.lock` file to be present in the target directory.
- **Pros:**
  - Official RustSec advisory database integration
  - Simple JSON output
  - Small binary footprint (10MB)
  - Fast execution (reads lockfile only)
  - Active maintenance by RustSec project
- **Cons:**
  - SCA only -- does not analyze source code
  - No SARIF support (JSON only)
  - Requires Cargo.lock file (not all Rust projects have one committed)
  - Does not detect unsafe code patterns (Semgrep covers this)

**SCANNER_LANGUAGES entry:**
```python
"cargo_audit": {"rust"},
```

### Comparison Matrix

| Feature | Semgrep (SAST) | cargo-audit (SCA) |
|---------|----------------|-------------------|
| **Purpose** | Source code pattern matching | Dependency vulnerability scanning |
| **Coverage** | Rust code patterns | Crate dependency CVEs |
| **Output Format** | JSON, SARIF | JSON |
| **SARIF** | Yes | No |
| **Docker Size** | Already installed | +10MB |
| **Integration Effort** | Already integrated | S |
| **Overlap** | None | None |
| **Recommendation** | Keep for Rust SAST | **Add for Rust SCA** |

**Verdict:** Semgrep and cargo-audit are complementary, not overlapping. Semgrep analyzes Rust source code patterns (unsafe blocks, common mistakes). cargo-audit scans Cargo.lock for known dependency vulnerabilities. Both should be used for complete Rust security coverage.

---

## Java

**Current coverage:** Semgrep (multi-language SAST)
**Recommendation:** Evaluate SpotBugs + FindSecBugs but note major integration challenges

### SpotBugs + FindSecBugs (Evaluated -- High Effort)

- **Purpose:** Java bytecode analysis for bugs (SpotBugs) and security vulnerabilities (FindSecBugs plugin)
- **Language(s):** Java
- **License:** LGPL-2.1 (SpotBugs), LGPL-3.0 (FindSecBugs)
- **Output formats:** XML, SARIF, HTML
- **CLI usage:** `java -jar spotbugs.jar -sarif -pluginList findsecbugs-plugin.jar target/classes`
- **Docker install:** Requires JVM (~200MB+ image size increase)
- **SARIF support:** Yes (since SpotBugs 4.5.0, native `-sarif` flag)
- **Integration effort:** L -- requires Java compilation step, JVM dependency, bytecode analysis
- **Config snippet:**
```yaml
scanners:
  spotbugs:
    enabled: "auto"
    timeout: 300
    extra_args: ["-effort:max", "-threshold:medium"]
```
- **FindingSchema mapping (via SARIF):**
  - fingerprint: computed from `file_path + ruleId + region`
  - rule_id: from SARIF `ruleId` (e.g., SQL_INJECTION, COMMAND_INJECTION)
  - severity: from SARIF `level` (error=HIGH, warning=MEDIUM, note=LOW)
  - line_start: from SARIF `region.startLine`
  - line_end: from SARIF `region.endLine`
  - file_path: from SARIF `artifactLocation.uri`
  - snippet: from SARIF `region.snippet.text`
  - title: from SARIF `message.text`
  - description: from rule `shortDescription.text`
- **False positive reduction:**
  - Use `-threshold:medium` to skip low-confidence detections
  - Use `-effort:max` for best detection accuracy (slower but fewer false positives)
  - Use filter files to exclude known false positives: `-excludeFilter filter.xml`
  - FindSecBugs allows category-level suppression via `@SuppressFBWarnings`
- **Detection:** 400+ bug patterns (SpotBugs) + 144 security vulnerability types (FindSecBugs) covering:
  - SQL injection, Command injection, LDAP injection
  - XSS (reflected, stored, DOM-based)
  - XXE, SSRF, Path traversal
  - Weak cryptography, insecure random
  - Deserialization vulnerabilities
  - Spring/Struts/JSP-specific checks

**CRITICAL CONCERN: Requires compiled .class files.** The scanner currently operates on source directories. SpotBugs performs bytecode analysis, meaning it requires:
1. A Java build step (Maven/Gradle compilation) before scanning
2. Access to compiled `.class` files in `target/classes` or `build/classes`
3. JVM runtime in the Docker image (+200MB minimum)

This is fundamentally different from all other adapters, which operate on source code directly. Integration would require either:
- **Option A:** A pre-scan build step in the adapter (running `mvn compile` or `gradle build` before SpotBugs)
- **Option B:** A new adapter base class (`CompiledCodeAdapter`) that handles build-then-scan
- **Option C:** Defer SpotBugs integration and rely on Semgrep for Java SAST

- **Pros:**
  - Deepest Java security analysis available (144 FindSecBugs vulnerability types)
  - Bytecode analysis catches issues source-level tools miss (reflection, serialization)
  - SARIF support since 4.5.0
  - Well-established, widely adopted tool
- **Cons:**
  - Requires compiled bytecode (major integration challenge)
  - JVM dependency adds 200MB+ to Docker image
  - Slower execution (compilation + analysis)
  - Build environment must match project (correct JDK version, dependencies)
  - Significantly more complex adapter implementation than other tools

**SCANNER_LANGUAGES entry (if implemented):**
```python
"spotbugs": {"java"},
```

### Comparison Matrix

| Feature | Semgrep | SpotBugs + FindSecBugs |
|---------|---------|----------------------|
| **Analysis Type** | Source code pattern matching | Bytecode analysis |
| **Coverage** | Broad Java patterns | 144 security vulnerability types |
| **Requires Compilation** | No | **Yes (major concern)** |
| **Output Format** | JSON, SARIF | XML, SARIF |
| **SARIF** | Yes | Yes |
| **Docker Size** | Already installed | **+200MB (JVM)** |
| **Integration Effort** | Already integrated | **L** |
| **Detection Depth** | Pattern-based, shallower | Deep bytecode analysis |
| **Recommendation** | Keep for source-level Java SAST | Consider for deep analysis if compilation can be solved |

**Verdict:** SpotBugs + FindSecBugs provides the deepest Java security analysis available, but the compilation requirement is a major integration challenge. Semgrep provides adequate Java SAST coverage at the source level. SpotBugs should be considered a Tier 3 addition -- high value but high effort. If pursued, it likely needs a separate adapter pattern that handles build-then-scan workflows.

---

## C\#

**Current coverage:** Semgrep (multi-language SAST)
**Recommendation:** Consider security-code-scan as a complement, medium effort

### security-code-scan (Evaluated -- Medium Effort)

- **Purpose:** .NET security static analysis using Roslyn compiler platform
- **Language(s):** C#, VB.NET
- **License:** LGPL-3.0
- **Output formats:** SARIF (native)
- **CLI usage:** `security-scan /path/to/solution.sln --export=report.sarif`
- **Docker install:** Requires .NET SDK (~200MB)
- **SARIF support:** Yes (native -- SARIF is the primary output format)
- **Integration effort:** M -- SARIF output simplifies parsing, but .NET SDK is heavy
- **Config snippet:**
```yaml
scanners:
  security_code_scan:
    enabled: "auto"
    timeout: 180
    extra_args: []
```
- **FindingSchema mapping (via SARIF -- direct parsing):**
  - fingerprint: computed from `file_path + ruleId + startLine`
  - rule_id: from SARIF `ruleId` (e.g., SCS0001, SCS0002)
  - severity: from SARIF `level` (error=HIGH, warning=MEDIUM, note=LOW)
  - line_start: from SARIF `region.startLine`
  - line_end: from SARIF `region.endLine`
  - file_path: from SARIF `artifactLocation.uri`
  - snippet: from SARIF `region.snippet.text`
  - title: from SARIF `message.text`
  - description: from rule `shortDescription.text`
- **False positive reduction:**
  - Configure via `SecurityCodeScan.config.yml` in project
  - Suppress specific rules via `#pragma warning disable SCSxxxx`
  - Use audit mode (`--config-audit`) vs default mode for different strictness levels
- **Detection:** Security vulnerabilities in C#/VB.NET:
  - SCS0001: Command injection
  - SCS0002: SQL injection
  - SCS0003: XPath injection
  - SCS0005: Weak random number generator
  - SCS0007: XML eXternal Entity injection (XXE)
  - SCS0012: LDAP injection
  - SCS0016: CSRF missing
  - SCS0019: Output caching
  - SCS0024: Open Redirect
  - And more
- **Note:** Requires `.sln` or `.csproj` files for Roslyn-based analysis. Will not work on standalone `.cs` files without a project structure.
- **Pros:**
  - SARIF-native output (simplest parsing of any evaluated tool)
  - Roslyn-based deep analysis (understands C# type system, data flow)
  - Covers OWASP Top 10 for .NET
  - Standalone CLI available (no Visual Studio needed)
- **Cons:**
  - .NET SDK dependency adds ~200MB to Docker image
  - Requires .sln/.csproj project files
  - Limited to C#/VB.NET
  - Less active development than other tools in this report

**SCANNER_LANGUAGES entry (if implemented):**
```python
"security_code_scan": {"csharp"},
```

### Comparison Matrix

| Feature | Semgrep | security-code-scan |
|---------|---------|-------------------|
| **Analysis Type** | Source code pattern matching | Roslyn-based type-aware analysis |
| **Coverage** | Broad C# patterns | Deep C#/VB.NET security analysis |
| **Requires Project Files** | No | **Yes (.sln/.csproj)** |
| **Output Format** | JSON, SARIF | SARIF (native) |
| **SARIF** | Yes | Yes |
| **Docker Size** | Already installed | **+200MB (.NET SDK)** |
| **Integration Effort** | Already integrated | M |
| **Detection Depth** | Pattern-based | Type-aware, data-flow |
| **Recommendation** | Keep for source-level C# SAST | Consider for .NET-heavy projects |

**Verdict:** security-code-scan provides deeper C# analysis than Semgrep through Roslyn-based type-aware scanning. However, the .NET SDK dependency is heavy (~200MB). Recommended as a Tier 2 addition for projects with significant C# codebases. The SARIF-native output makes adapter implementation relatively clean despite the medium effort rating.

---

## C/C++

**Current coverage:** Cppcheck (dedicated C/C++ SAST) + Semgrep (pattern matching)
**Recommendation:** Keep existing tools. C/C++ is well-covered.

### Cppcheck (Re-evaluation)

- **Purpose:** C/C++ static analysis for bugs, undefined behavior, and security issues
- **Language(s):** C, C++
- **License:** GPL-3.0
- **Output formats:** XML, text
- **CLI usage:** `cppcheck --xml --enable=all /path/to/code`
- **Docker install:** `apt-get install cppcheck`, ~10MB
- **SARIF support:** No (XML output only -- current adapter already handles XML parsing)
- **Integration effort:** Already integrated (adapter exists)
- **Status:** Active development. Remains the best open-source C/C++ SAST tool.
- **Key strengths:**
  - Memory leak detection
  - Buffer overflow detection
  - Null pointer dereference
  - Undefined behavior analysis
  - Use-after-free detection
  - Integer overflow checks

**Current config:**
```yaml
scanners:
  cppcheck:
    enabled: true
    timeout: 120
    extra_args: ["-i.venv", "-inode_modules"]
```

- **Pros:** Deep C/C++ understanding, memory safety analysis, active development, lightweight
- **Cons:** XML-only output (no JSON/SARIF), C/C++ only

### Semgrep C/C++ Coverage

Semgrep also covers C/C++ patterns through its rule registry. However, Semgrep provides pattern-based analysis while Cppcheck provides deeper C-specific analysis (memory leaks, buffer overflows, undefined behavior). Both are complementary.

### Comparison Matrix

| Feature | Cppcheck | Semgrep |
|---------|----------|---------|
| **Coverage** | Deep C/C++ specific | Broad pattern matching |
| **Analysis Type** | Flow analysis, memory model | Pattern matching |
| **Memory Safety** | Yes (leaks, overflows, use-after-free) | Limited |
| **Output Format** | XML | JSON, SARIF |
| **SARIF** | No | Yes |
| **Docker Size** | ~10MB | Already installed |
| **Integration Effort** | Already integrated | Already integrated |
| **Recommendation** | **Keep as primary C/C++ SAST** | Keep for broad patterns |

**Verdict:** No changes needed. Cppcheck provides the deepest C/C++ analysis available in open source, and the existing adapter handles its XML output well. Semgrep adds complementary pattern coverage. No alternative tool justifies replacing or supplementing this combination.

---

## Ruby

**Current coverage:** Semgrep (multi-language SAST)
**Recommendation:** Add Brakeman for Rails-specific SAST

### Brakeman (Recommended Addition)

- **Purpose:** Ruby on Rails static security scanner with 33 vulnerability types
- **Language(s):** Ruby (Rails framework specifically)
- **License:** Brakeman Public Use License (free for any use)
- **Output formats:** JSON, SARIF, HTML, CSV, text, markdown
- **CLI usage:** `brakeman --format json --no-exit-on-warn /path/to/rails/app`
- **Docker install:** `gem install brakeman`, ~5MB (Ruby runtime needed)
- **SARIF support:** Yes (`-f sarif`)
- **Integration effort:** S -- clean JSON output, zero-config for Rails apps, small footprint
- **Config snippet:**
```yaml
scanners:
  brakeman:
    enabled: "auto"
    timeout: 120
    extra_args: ["--no-exit-on-warn"]
```
- **FindingSchema mapping:**
  - fingerprint: computed from `file + warning_type + line`
  - rule_id: from `warning_type` (e.g., "SQL Injection", "Cross-Site Scripting", "Command Injection")
  - severity: from `confidence` field (High=HIGH, Medium=MEDIUM, Weak=LOW)
  - line_start: from `line` field
  - line_end: from `line` field (Brakeman reports single line)
  - file_path: from `file` field, normalized via `_normalize_path()`
  - snippet: from `code` field
  - title: from `warning_type` field
  - description: from `message` field
- **False positive reduction:**
  - Use `brakeman.ignore` file for project-specific false positive management (`brakeman -I`)
  - Use `--skip-checks` for known noisy check types
  - Use `--confidence-level 2` to report only high-confidence findings
  - Use `--safe` to skip checks that may produce false positives
- **Detection:** 33 vulnerability types covering Rails 2.3.x through 8.x:
  - SQL injection (ActiveRecord, raw SQL)
  - Cross-site scripting (reflected, stored)
  - Command injection (system, exec, backticks)
  - Mass assignment
  - File access (path traversal, file disclosure)
  - CSRF token verification
  - Session management issues
  - Redirect vulnerabilities (open redirect)
  - Deserialization (YAML, Marshal)
  - Header injection
  - And more
- **Note:** Rails-specific only. For non-Rails Ruby projects, Semgrep is the only available option. Brakeman detects Rails applications automatically by looking for `config/environment.rb` or similar markers.
- **Pros:**
  - Zero-config for Rails applications (auto-detects app structure)
  - Deep Rails-specific analysis (understands ActiveRecord, views, routes)
  - JSON/SARIF output for easy integration
  - Small footprint (5MB gem install)
  - Active development, supports latest Rails versions
  - False positive management via ignore file
- **Cons:**
  - Rails-only (no value for non-Rails Ruby)
  - Requires Ruby runtime in Docker image
  - Confidence-based severity (not standard LOW/MEDIUM/HIGH -- needs mapping)

**SCANNER_LANGUAGES entry:**
```python
"brakeman": {"ruby"},  # Activates on Ruby detection; auto-detects Rails
```

### Comparison Matrix

| Feature | Semgrep | Brakeman |
|---------|---------|----------|
| **Coverage** | General Ruby patterns | 33 Rails-specific vulnerability types |
| **Framework Awareness** | Pattern-based (no framework knowledge) | Deep Rails understanding |
| **Output Format** | JSON, SARIF | JSON, SARIF |
| **SARIF** | Yes | Yes |
| **Docker Size** | Already installed | +5MB (+ Ruby runtime) |
| **Integration Effort** | Already integrated | S |
| **Zero-Config** | Requires rules | Yes (auto-detects Rails) |
| **Recommendation** | Keep for general Ruby patterns | **Add for Rails projects** |

**Verdict:** Use both for Rails projects. Semgrep provides general Ruby pattern matching. Brakeman adds deep Rails-specific analysis (33 vulnerability types) with zero configuration. For non-Rails Ruby projects, Semgrep remains the only option. The 5MB footprint and clean JSON/SARIF output make Brakeman a high-value, low-effort addition.

---

## SCA (Software Composition Analysis) Tools

Software Composition Analysis tools scan project dependencies for known vulnerabilities (CVEs). The scanner currently uses Trivy for SCA alongside IaC scanning. This section evaluates whether additional SCA tools add value.

### Trivy (Re-evaluation -- Current SCA Tool)

- **Purpose:** Comprehensive security scanner covering dependencies, containers, IaC, and filesystems
- **Language(s):** Universal (supports package managers for Python/pip, Node/npm, Go/mod, Rust/cargo, Java/Maven/Gradle, Ruby/gems, PHP/composer, C#/NuGet, and more)
- **License:** Apache-2.0
- **Output formats:** JSON, SARIF, table, CycloneDX, SPDX
- **CLI usage:** `trivy fs --format json /path/to/project`
- **Docker install:** Single binary, ~50MB
- **SARIF support:** Yes (`--format sarif`)
- **Integration effort:** Already integrated (adapter exists)
- **Current version:** 0.69.3 (installed in Dockerfile)
- **Status:** Active development by Aqua Security. Broadest scope of any SCA tool evaluated.

**Current config:**
```yaml
scanners:
  trivy:
    enabled: true
    timeout: 120
    extra_args: []
```

**Key strengths:**
- Single tool covers dependencies + containers + IaC + filesystem secrets
- Supports the widest range of package managers and lockfile formats
- Active CVE database updates
- CycloneDX and SPDX SBOM generation
- Already integrated and working well

**Limitations:**
- Risk scoring is binary (vulnerability exists or not) -- lacks EPSS/KEV risk prioritization
- Broad scope means it is a generalist, not a specialist in any single ecosystem
- Can produce high finding counts without risk-based prioritization

- **Pros:** Broadest scope, single binary, already integrated, active development
- **Cons:** Less precise risk scoring than specialized SCA tools, no EPSS/KEV support

### Grype (Evaluated -- Consider as Complement)

- **Purpose:** Vulnerability scanner for container images and filesystems with advanced risk scoring
- **Language(s):** Universal (supports same package managers as Trivy)
- **License:** Apache-2.0
- **Output formats:** JSON, SARIF, table, CycloneDX
- **CLI usage:** `grype dir:/path/to/project -o json`
- **Docker install:** Single binary, ~30MB
- **SARIF support:** Yes (`-o sarif`)
- **Integration effort:** S -- clean CLI, familiar pattern to existing Trivy adapter
- **Config snippet:**
```yaml
scanners:
  grype:
    enabled: "auto"
    timeout: 120
    extra_args: []
```
- **FindingSchema mapping:**
  - fingerprint: computed from `vulnerability.id + artifact.name + artifact.version`
  - rule_id: from vulnerability `id` field (e.g., CVE-2023-12345)
  - severity: from `severity` field (Critical/High/Medium/Low/Negligible mapped to CRITICAL/HIGH/MEDIUM/LOW/LOW)
  - line_start: N/A (dependency-level finding)
  - file_path: from artifact `name` (package name) or lockfile path
  - snippet: from `matchDetails` (affected version range, fix version if available)
  - title: from vulnerability `id` + artifact `name`
  - description: from vulnerability `description`
- **False positive reduction:**
  - Use `--only-fixed` to report only vulnerabilities with available fixes (actionable findings only)
  - Use `--fail-on critical` for gate decisions
  - Configure `.grype.yaml` for project-specific ignores
- **Detection:** CVE matching with advanced risk scoring:
  - CVSS scoring (standard vulnerability severity)
  - EPSS scoring (Exploit Prediction Scoring System -- probability of exploitation)
  - KEV integration (CISA Known Exploited Vulnerabilities catalog)
  - Combined risk scoring helps prioritize which vulnerabilities to fix first
- **Pros:**
  - Superior risk prioritization (CVSS + EPSS + KEV)
  - Single binary, small footprint (30MB)
  - Clean JSON/SARIF output
  - `--only-fixed` flag reduces noise to actionable findings
  - Maintained by Anchore (SBOM/security company)
- **Cons:**
  - Narrower scope than Trivy (dependencies only, no IaC/container scanning)
  - Overlaps with Trivy's dependency scanning
  - Adding a second SCA tool increases finding deduplication complexity

**SCANNER_LANGUAGES entry:**
```python
"grype": set(),  # Universal -- scans lockfiles regardless of language
```

### OWASP Dependency-Check (Evaluated -- Not Recommended)

- **Purpose:** SCA tool using CPE (Common Platform Enumeration) matching for dependency vulnerabilities
- **Language(s):** Primarily Java/Maven, also supports .NET, Node.js, Python, Ruby
- **License:** Apache-2.0
- **Output formats:** XML, HTML, CSV, JSON, SARIF (experimental)
- **CLI usage:** `dependency-check --scan /path --format XML --out report.xml`
- **Docker install:** Requires JVM (~200MB+), large NVD database download (~1GB)
- **SARIF support:** Experimental (not production-ready)
- **Integration effort:** L -- JVM dependency, XML output, slow NVD database updates, high false positives
- **Detection:** CPE-based matching against NVD (National Vulnerability Database)

**Why Not Recommended:**
- Higher false positive rate than Trivy/Grype due to CPE matching ambiguity
- Slower execution (NVD database download and update required)
- XML-only reliable output (SARIF is experimental)
- JVM dependency adds 200MB+ to Docker image
- NVD database requires ~1GB disk space
- Trivy already covers Java/Maven dependencies adequately
- Deepest Java/Maven coverage, but the marginal benefit over Trivy does not justify the cost

### SCA Comparison Matrix

| Feature | Trivy (current) | Grype | OWASP Dep-Check |
|---------|----------------|-------|-----------------|
| **Scope** | Deps + IaC + containers | Dependencies only | Dependencies only |
| **Risk Scoring** | CVSS only | CVSS + EPSS + KEV | CVSS only |
| **Output Formats** | JSON, SARIF, CycloneDX | JSON, SARIF, CycloneDX | XML, HTML (SARIF experimental) |
| **SARIF** | Yes | Yes | Experimental |
| **Docker Size** | ~50MB (already installed) | +30MB | +200MB (JVM) + 1GB (NVD) |
| **Integration Effort** | Already integrated | S | L |
| **False Positive Rate** | Low-medium | Low (with --only-fixed) | **High** (CPE matching) |
| **Recommendation** | **Keep as primary SCA** | Consider as complement for risk prioritization | **Not Recommended** |

**Verdict:** Keep Trivy as the primary SCA tool (broadest scope, already integrated). Consider adding Grype as a complement specifically for its EPSS + KEV risk scoring, which helps teams prioritize which vulnerabilities to fix first. Skip OWASP Dependency-Check (high false positives, JVM dependency, XML output, Trivy covers its use case).

---

## DAST (Dynamic Application Security Testing) Feasibility

**Important note:** DAST tools require a running application to scan. This is fundamentally different from SAST/SCA tools, which analyze source code and dependency files statically. The current `ScannerAdapter` pattern (receives a directory path, runs CLI tool, parses output) does not directly support DAST workflows. DAST integration would likely require:

- A separate `DastAdapter` base class that accepts a target URL instead of a directory path
- Application startup/teardown management
- Authentication configuration for scanning protected endpoints
- Network access from the scanner container to the target application

This section assesses feasibility, not integration design.

### Nuclei (Recommended DAST Candidate)

- **Purpose:** Template-based vulnerability scanner for known CVEs, misconfigurations, and exposed services
- **Language(s):** N/A (scans running applications via HTTP)
- **License:** MIT
- **Output formats:** JSON (JSONL), SARIF, markdown
- **CLI usage:** `nuclei -u https://target -jsonl -o results.json`
- **Docker install:** Single binary, ~30MB
- **SARIF support:** Yes
- **Integration effort:** M -- CLI-friendly and lightweight, but requires a running target application (different paradigm from SAST)
- **Config snippet:**
```yaml
scanners:
  nuclei:
    enabled: false
    timeout: 300
    extra_args: ["-severity", "medium,high,critical"]
```

**Note:** `enabled: false` by default because DAST requires a target URL, which the current scanner does not provide. Enabling Nuclei would require additional configuration (target URL, authentication) beyond the standard `ScannerAdapter` pattern.

- **FindingSchema mapping:**
  - fingerprint: computed from `template-id + matched-at`
  - rule_id: from `template-id` (e.g., CVE-2021-44228, exposed-panels/phpmyadmin)
  - severity: from `info.severity` (critical/high/medium/low/info mapped directly)
  - line_start: N/A (HTTP-based findings)
  - file_path: from `matched-at` (target URL)
  - snippet: from `curl-command` or `extracted-results`
  - title: from `info.name`
  - description: from `info.description`
- **False positive reduction:**
  - Use `-severity medium,high,critical` to skip info/low findings
  - Use `-tags cve,owasp` to run only CVE and OWASP templates
  - Exclude noisy templates via `-exclude-templates`
  - Use `-rate-limit` to avoid overwhelming targets
- **Detection:** 11,000+ community templates covering:
  - Known CVEs (Log4Shell, Spring4Shell, etc.)
  - Exposed admin panels (phpMyAdmin, Grafana, Jenkins)
  - Default credentials
  - Misconfigurations (CORS, security headers, SSL)
  - Information disclosure (server version, debug pages)
  - API vulnerabilities
- **Pros:**
  - Template-based -- targeted scanning, not brute-force
  - Fast execution (minutes, not hours)
  - Single binary, small footprint (30MB)
  - Huge community template library (11,000+)
  - SARIF support for standardized output
  - CLI-friendly (similar pattern to SAST tools)
- **Cons:**
  - Requires a running application target
  - Template-based means it finds known issues, not unknown ones
  - Does not crawl application (requires URL list or target specification)
  - Different paradigm from current ScannerAdapter pattern

### ZAP (Evaluated -- Defer)

- **Purpose:** Comprehensive web application security scanner with proxy, spider, and active/passive scanning
- **Language(s):** N/A (scans running web applications)
- **License:** Apache-2.0
- **Output formats:** JSON, XML, HTML, SARIF (via community plugins)
- **CLI usage:** `zap-cli quick-scan --self-contained https://target`
- **Docker install:** Requires JVM + full ZAP install (~500MB+)
- **SARIF support:** Via community plugins (not native)
- **Integration effort:** L -- requires running app, massive Docker footprint, complex configuration for authentication, proxy setup, scan policies
- **Detection:** Comprehensive web application security:
  - XSS (reflected, stored, DOM-based)
  - SQL injection (all variants)
  - CSRF, SSRF
  - Directory traversal
  - Session management flaws
  - Authentication bypass
  - Application crawling and discovery
- **Pros:**
  - Most comprehensive open-source DAST tool
  - Active scanning discovers unknown vulnerabilities (not just templates)
  - Application crawling (spider) discovers endpoints automatically
  - OWASP flagship project, widely adopted
  - Proxy mode for development-time testing
- **Cons:**
  - Massive Docker footprint (~500MB+)
  - JVM dependency
  - Slow execution (hours for full scan)
  - Complex configuration for production use
  - Requires authentication setup for protected applications
  - SARIF support via plugins only (not native)
  - Hardest to integrate of all evaluated tools

### Nikto (Evaluated -- Not Recommended)

- **Purpose:** Web server scanner for server-level misconfigurations
- **Language(s):** N/A (scans web servers)
- **License:** GPL-2.0
- **Output formats:** CSV, HTML, text, XML
- **CLI usage:** `nikto -h https://target -Format csv -output report.csv`
- **Docker install:** Perl runtime + Nikto scripts, ~50MB
- **SARIF support:** No
- **Integration effort:** S (simple CLI) but limited value

**Why Not Recommended:**
- Server-level only (HTTP headers, server version, default files) -- does not test application logic
- Limited detection compared to Nuclei (which covers server issues plus CVEs, panels, and more)
- No JSON or SARIF output (CSV/XML only)
- Nuclei's template library covers Nikto's server-level checks and far more

### DAST Comparison Matrix

| Feature | Nuclei | ZAP | Nikto |
|---------|--------|-----|-------|
| **Type** | Template-based scanner | Full proxy + active scanner | Server scanner |
| **Best For** | Known CVEs, misconfigs, exposed panels | Comprehensive web app testing | Web server misconfiguration |
| **Docker Size** | ~30MB | ~500MB+ | ~50MB |
| **SARIF** | Yes | Via plugins | No |
| **Integration Effort** | M | L | S (but limited value) |
| **Scan Speed** | Minutes | Hours | Minutes |
| **Detection Depth** | Known issues (template-based) | Unknown + known (active scanning) | Server-level only |
| **Requires Running App** | Yes | Yes | Yes |
| **Recommendation** | **Recommended if DAST pursued** | Defer (high effort) | **Not Recommended** |

**Integration Feasibility Summary:**

If DAST is pursued in a future phase, **Nuclei is the recommended starting point**:
- CLI-friendly interface similar to SAST tools
- Lightweight single binary (30MB vs ZAP's 500MB)
- SARIF output for standardized parsing
- Template-based approach allows targeted scanning
- Fast execution (minutes vs ZAP's hours)

ZAP is the most thorough DAST tool but should be deferred due to its massive footprint, complex configuration, and JVM dependency. It may be worth pursuing later for projects requiring comprehensive active scanning.

Both DAST tools require a running application target URL, which the current scanner architecture does not support. Integration would require extending the configuration to accept target URLs and potentially creating a `DastAdapter` base class separate from `ScannerAdapter`.

---

## Secrets Scanning Comparison

**Current coverage:** Gitleaks (universal secrets scanner)
**Recommendation:** Keep Gitleaks as primary. TruffleHog is a valid complement for deep audits but not a replacement.

### Gitleaks (Re-evaluation -- Current Tool)

- **Purpose:** Detect hardcoded secrets, passwords, and API keys in source code and git history
- **Language(s):** Universal (scans all file types)
- **License:** MIT
- **Output formats:** JSON, CSV, SARIF
- **CLI usage:** `gitleaks detect --source /path --report-format json --report-path results.json`
- **Docker install:** Single binary, ~15MB
- **SARIF support:** No (JSON and CSV only; custom JSON format, not SARIF)
- **Integration effort:** Already integrated (adapter exists)
- **Current version:** 8.30.0 (installed in Dockerfile)
- **Status:** Active development. Fast, reliable, well-integrated.

**Current config:**
```yaml
scanners:
  gitleaks:
    enabled: true
    timeout: 120
    extra_args: []
```

**Detection method:** Regex-based pattern matching against 150+ built-in rules covering:
- AWS keys, Google Cloud credentials, Azure tokens
- GitHub/GitLab/Bitbucket tokens
- Stripe, Twilio, SendGrid API keys
- Database connection strings
- Private keys (RSA, SSH, PGP)
- Generic passwords and secrets patterns

**Key characteristics:**
- Fast: regex-only scanning, no network calls
- Deterministic: same input always produces same output
- Offline: does not verify if detected secrets are active
- Higher false positive rate due to pattern matching without verification

### TruffleHog (Comparison)

- **Purpose:** Detect and verify secrets in source code, git history, and external sources
- **Language(s):** Universal
- **License:** AGPL-3.0
- **Output formats:** JSON, text
- **CLI usage:** `trufflehog filesystem /path --json`
- **Docker install:** Single binary, ~50MB
- **SARIF support:** No (custom JSON format)
- **Integration effort:** S -- clean CLI, JSON output, but adds network dependency for verification
- **Detection method:** Pattern matching + **active credential verification**
  - Detects a potential secret via regex/entropy
  - Attempts to verify if the credential is live (e.g., makes API call with detected key)
  - Marks findings as verified or unverified
- **Scope:** Beyond git repos, supports scanning:
  - S3 buckets
  - Docker images
  - Slack history
  - Jira
  - And more external sources

### Secrets Scanner Comparison Matrix

| Feature | Gitleaks (current) | TruffleHog |
|---------|-------------------|------------|
| **Speed** | Fast (regex-only, no network) | Slower (verifies credentials) |
| **Detection Method** | Pattern matching | Pattern matching + active verification |
| **Verification** | No (offline) | Yes (attempts to use detected credentials) |
| **Scope** | Git repos, directories | Git + S3 + Docker + Slack + more |
| **False Positives** | Higher (no verification) | Lower (verified findings are confirmed) |
| **Network Required** | No | Yes (for verification) |
| **Docker Size** | ~15MB | ~50MB |
| **SARIF** | No | No |
| **License** | MIT | AGPL-3.0 |
| **Integration Effort** | Already integrated | S |
| **Recommendation** | **Keep as primary** | Consider for deep audits |

**Verdict:** Keep Gitleaks as the primary secrets scanner. Its speed, simplicity, and offline operation make it ideal for CI/CD integration where fast feedback is critical. TruffleHog's credential verification is valuable -- it can confirm whether a detected secret is actually live and exploitable -- but it adds network dependency and slower execution. TruffleHog is best used as an optional complement for periodic deep security audits rather than on every scan.

**Note on AGPL-3.0:** TruffleHog's AGPL license may have implications for some deployment models. Gitleaks' MIT license is more permissive.
