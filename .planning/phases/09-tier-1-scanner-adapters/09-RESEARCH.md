# Phase 9: Tier-1 Scanner Adapters - Research

**Researched:** 2026-03-21
**Domain:** Security scanner adapter implementation (gosec, Bandit, Brakeman, cargo-audit)
**Confidence:** HIGH

## Summary

Phase 9 implements four new scanner adapters following the established ScannerAdapter pattern from Phase 8's plugin registry. The codebase already has a well-defined adapter contract (base.py), a reference implementation (semgrep.py), and a config-driven registry. Each new adapter is a straightforward subclass: construct CLI command, parse JSON stdout, map fields to FindingSchema, register in config.yml.

The Phase 7 research report provides detailed per-tool analysis including CLI flags, JSON output schemas, and severity mappings. All decisions about severity mapping, output parsing strategy, and edge cases (cargo-audit lockfile generation, Bandit+Semgrep overlap) are locked in CONTEXT.md. The primary technical risk is cargo-audit's CVSS vector string requiring score computation (the `cvss` field is a vector like `CVSS:3.1/AV:N/AC:L/...`, not a numeric score).

**Primary recommendation:** Implement each adapter as a standalone module following the semgrep.py pattern exactly. Use the `cvss` pip package for cargo-audit CVSS score extraction. Add config.yml entries and tests per the established phase_02 test pattern.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Severity mapping: gosec direct (HIGH/MEDIUM/LOW), Bandit confidence x severity matrix, Brakeman confidence-weighted downgrade, cargo-audit CVSS-based ranges
- Parse each tool's native JSON output directly (not SARIF) -- consistent with semgrep.py pattern
- SARIF helper deferred to v1.0.2 (SARIF-01 requirement)
- Same pattern as existing adapters -- no shared helper abstractions for this phase
- For single-line tools (gosec, cargo-audit): set line_end = line_start
- cargo-audit: run `cargo generate-lockfile` if no Cargo.lock found
- cargo-audit: file_path = "Cargo.lock", line_start/line_end = None, rule_id = advisory ID
- cargo-audit: only report vulnerabilities (exclude unmaintained/yanked warnings)
- Bandit + Semgrep: no deduplication, show findings independently
- Both Bandit and Semgrep auto-enabled for Python projects via languages: ["python"]

### Claude's Discretion
- Exact CLI command construction per tool (flags, excludes, target path handling)
- Error handling for non-zero exit codes per tool
- Test fixture structure and mock data
- Whether to include snippet extraction (tool-dependent)
- Config.yml default values for timeout and extra_args per scanner

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SCAN-01 | gosec adapter scans Go source code and produces FindingSchema-compatible results | gosec JSON output has `Issues` array with `severity`, `confidence`, `rule_id`, `details`, `file`, `code`, `line` fields. Direct severity mapping. |
| SCAN-02 | Bandit adapter scans Python source code and produces FindingSchema-compatible results | Bandit JSON output has `results` array with `issue_severity`, `issue_confidence`, `test_id`, `test_name`, `filename`, `code`, `line_number`, `line_range`, `issue_text` fields. Confidence x severity matrix mapping. |
| SCAN-03 | Brakeman adapter scans Ruby/Rails applications and produces FindingSchema-compatible results | Brakeman JSON output has `warnings` array with `warning_type`, `warning_code`, `confidence`, `file`, `line`, `code`, `message`, `link`, `check_name`, `fingerprint` fields. Confidence-weighted severity. |
| SCAN-04 | cargo-audit adapter scans Rust dependencies via Cargo.lock and produces FindingSchema-compatible results | cargo-audit JSON has `vulnerabilities.list` array with nested `advisory` (id, title, description, cvss vector, date) and `package` (name, version) objects. CVSS vector parsing needed for severity mapping. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| scanner.adapters.base.ScannerAdapter | existing | Abstract base class | Established contract in codebase |
| scanner.schemas.finding.FindingSchema | existing | Normalized finding output | Pydantic model, all adapters use it |
| scanner.schemas.severity.Severity | existing | Severity enum (CRITICAL..INFO) | IntEnum for comparisons |
| scanner.core.fingerprint.compute_fingerprint | existing | SHA-256 dedup fingerprint | Deterministic from file_path + rule_id + snippet |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| cvss | 3.2+ | CVSS vector string to base score | cargo-audit adapter only -- parse CVSS:3.1 vectors |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| cvss pip package | Manual CVSS 3.x parser | Manual parser is error-prone for 8 metric combinations; library is 50KB, well-tested |
| cvss pip package | Map advisory categories instead of CVSS scores | Loses granularity; CONTEXT.md explicitly requires CVSS-based ranges |

**Installation:**
```bash
pip install cvss
```

**Note:** The `cvss` package (by RedHat) supports CVSS v2, v3.0, v3.1, and v4.0 vectors. Usage: `CVSS3(vector_string).scores()` returns `(base_score, temporal_score, environmental_score)`.

## Architecture Patterns

### Recommended Project Structure
```
src/scanner/adapters/
    base.py              # Existing abstract base
    semgrep.py           # Reference implementation (existing)
    gosec.py             # NEW: Go SAST
    bandit.py            # NEW: Python SAST
    brakeman.py          # NEW: Ruby/Rails SAST
    cargo_audit.py       # NEW: Rust SCA
    registry.py          # Existing plugin registry
config.yml               # Add 4 new scanner entries
tests/phase_09/
    __init__.py
    conftest.py          # Fixtures for all 4 adapters
    fixtures/
        gosec_output.json
        bandit_output.json
        brakeman_output.json
        cargo_audit_output.json
    test_adapter_gosec.py
    test_adapter_bandit.py
    test_adapter_brakeman.py
    test_adapter_cargo_audit.py
```

### Pattern 1: Adapter Implementation (follow semgrep.py exactly)
**What:** Each adapter subclasses ScannerAdapter, implements `tool_name`, `run()`, `_version_command()`
**When to use:** Every new scanner adapter
**Example:**
```python
# Source: src/scanner/adapters/semgrep.py (reference)
class NewAdapter(ScannerAdapter):
    @property
    def tool_name(self) -> str:
        return "tool_name"

    def _version_command(self) -> list[str]:
        return ["tool", "--version"]

    async def run(self, target_path, timeout, extra_args=None):
        cmd = ["tool", "--json", target_path]
        if extra_args:
            cmd.extend(extra_args)
        stdout, stderr, returncode = await self._execute(cmd, timeout)
        # Handle exit codes per tool
        data = json.loads(stdout)
        # Parse and map to FindingSchema list
        return findings
```

### Pattern 2: Severity Mapping (tool-specific dict/function)
**What:** Each adapter defines its own severity mapping strategy
**When to use:** Always -- each tool has different severity semantics

**gosec (direct mapping):**
```python
GOSEC_SEVERITY_MAP = {
    "HIGH": Severity.HIGH,
    "MEDIUM": Severity.MEDIUM,
    "LOW": Severity.LOW,
}
```

**Bandit (confidence x severity matrix):**
```python
def _bandit_severity(issue_severity: str, issue_confidence: str) -> Severity:
    key = (issue_severity.upper(), issue_confidence.upper())
    matrix = {
        ("HIGH", "HIGH"): Severity.CRITICAL,
        ("HIGH", "MEDIUM"): Severity.HIGH,
        ("HIGH", "LOW"): Severity.MEDIUM,
        ("MEDIUM", "HIGH"): Severity.MEDIUM,
        ("MEDIUM", "MEDIUM"): Severity.MEDIUM,
        ("MEDIUM", "LOW"): Severity.LOW,
        ("LOW", "HIGH"): Severity.LOW,
        ("LOW", "MEDIUM"): Severity.LOW,
        ("LOW", "LOW"): Severity.INFO,
    }
    return matrix.get(key, Severity.INFO)
```

**Brakeman (confidence-weighted downgrade):**
```python
BRAKEMAN_BASE_SEVERITY = {
    "High": Severity.HIGH,
    "Medium": Severity.MEDIUM,
    "Weak": Severity.LOW,
}
# Weak confidence findings get downgraded one level
def _brakeman_severity(confidence: str) -> Severity:
    base = BRAKEMAN_BASE_SEVERITY.get(confidence, Severity.MEDIUM)
    if confidence == "Weak" and base.value > Severity.INFO.value:
        return Severity(base.value - 1)
    return base
```
Note: Brakeman uses `confidence` as a proxy for severity. The CONTEXT.md decision says "Weak confidence get downgraded one severity level" -- meaning warnings with Weak confidence have their severity reduced.

**cargo-audit (CVSS-based ranges):**
```python
def _cvss_to_severity(cvss_vector: str | None) -> Severity:
    if not cvss_vector:
        return Severity.MEDIUM  # safe default per CONTEXT.md
    from cvss import CVSS3
    try:
        score = CVSS3(cvss_vector).scores()[0]  # base score
    except Exception:
        return Severity.MEDIUM
    if score >= 9.0:
        return Severity.CRITICAL
    elif score >= 7.0:
        return Severity.HIGH
    elif score >= 4.0:
        return Severity.MEDIUM
    elif score > 0:
        return Severity.LOW
    return Severity.MEDIUM
```

### Pattern 3: Exit Code Handling (per-tool)
**What:** Some security tools use exit code 1 to mean "findings found" (not error)
**When to use:** Each adapter's run() method

| Tool | Exit 0 | Exit 1 | Exit 2+ |
|------|--------|--------|---------|
| gosec | No findings | Findings found (not error) | Error |
| Bandit | No findings | Findings found (not error) | Error |
| Brakeman (with --no-exit-on-warn) | Always (findings in JSON) | N/A | Error |
| cargo-audit | No vulnerabilities | Vulnerabilities found (not error) | Error |

### Pattern 4: Test Fixture Pattern (follow phase_02)
**What:** JSON fixture files + conftest.py fixtures + AsyncMock on _execute
**When to use:** All adapter tests
```python
# conftest.py
@pytest.fixture
def gosec_output(fixtures_dir):
    return json.loads((fixtures_dir / "gosec_output.json").read_text())

# test_adapter_gosec.py
async def test_parse_gosec_findings(adapter, gosec_output):
    adapter._execute = AsyncMock(
        return_value=(json.dumps(gosec_output), "", 0)
    )
    findings = await adapter.run("/tmp/target", timeout=60)
    assert len(findings) == N
    assert all(f.tool == "gosec" for f in findings)
```

### Anti-Patterns to Avoid
- **Shared base parsing logic:** CONTEXT.md explicitly says no shared helper abstractions. Each adapter parses independently.
- **SARIF parsing:** Deferred to v1.0.2 (SARIF-01). Parse native JSON only.
- **Cross-tool deduplication:** Deferred to v1.0.3 (DEDUP-01). Bandit and Semgrep findings are independent.
- **Importing adapter classes directly:** Use config.yml adapter_class paths; registry does dynamic loading.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CVSS vector to base score | Manual CVSS 3.x calculator | `cvss` pip package (RedHat) | CVSS calculation has 8 metrics with complex interactions; library handles all edge cases |
| Finding fingerprint | Custom hash function | `compute_fingerprint()` from scanner.core | Already exists, normalizes inputs, SHA-256 |
| Subprocess with timeout | Manual asyncio.create_subprocess_exec | `self._execute()` from ScannerAdapter base | Already handles timeout, encoding, process cleanup |
| Path normalization | String manipulation | `self._normalize_path()` from ScannerAdapter base | Already handles leading ./, absolute paths, target prefix stripping |

**Key insight:** The ScannerAdapter base class provides `_execute()`, `_normalize_path()`, and the async subprocess pattern. Each adapter only needs to construct the CLI command, handle exit codes, and parse tool-specific JSON output.

## Common Pitfalls

### Pitfall 1: gosec line field is a string, not int
**What goes wrong:** `json.loads()` returns `"line": "32"` (string), not `"line": 32` (int)
**Why it happens:** gosec serializes line numbers as strings in JSON output
**How to avoid:** `int(issue.get("line", "0")) or None`
**Warning signs:** TypeError when constructing FindingSchema with line_start

### Pitfall 2: Brakeman requires Rails app detection
**What goes wrong:** Brakeman exits with error on non-Rails Ruby projects
**Why it happens:** Brakeman specifically looks for `config/environment.rb` or Rails markers
**How to avoid:** Let Brakeman fail gracefully -- if returncode indicates "not a Rails app", return empty findings list instead of raising ScannerExecutionError
**Warning signs:** stderr contains "Please supply the path to a Rails application"

### Pitfall 3: cargo-audit CVSS field can be null
**What goes wrong:** Some advisories lack CVSS vectors (older advisories, withdrawn ones)
**Why it happens:** Not all RustSec advisories have CVSS scores assigned
**How to avoid:** Default to Severity.MEDIUM when cvss is null (per CONTEXT.md decision)
**Warning signs:** NoneType errors in CVSS parsing

### Pitfall 4: cargo-audit warnings vs vulnerabilities
**What goes wrong:** Adapter reports unmaintained/yanked crate warnings as security findings
**Why it happens:** cargo-audit JSON has both `vulnerabilities` and `warnings` sections
**How to avoid:** Only iterate `vulnerabilities.list`, ignore `warnings` entirely (per CONTEXT.md decision)
**Warning signs:** Findings with "unmaintained" or "yanked" in description

### Pitfall 5: Bandit exit code semantics
**What goes wrong:** Adapter raises ScannerExecutionError when Bandit finds issues
**Why it happens:** Bandit uses exit code 1 for "issues found" (like semgrep)
**How to avoid:** Only treat returncode >= 2 as error (match semgrep pattern)
**Warning signs:** ScannerExecutionError on projects with known Python security issues

### Pitfall 6: Empty JSON output on no findings
**What goes wrong:** json.loads fails or KeyError on empty results
**Why it happens:** Some tools output minimal JSON when no findings exist
**How to avoid:** Default to empty arrays: `data.get("Issues", [])`, `data.get("results", [])`, etc.
**Warning signs:** KeyError or json.JSONDecodeError on clean codebases

### Pitfall 7: cargo-audit generate-lockfile requires cargo
**What goes wrong:** `cargo generate-lockfile` fails if cargo is not installed or Cargo.toml is invalid
**Why it happens:** Rust toolchain may not be present even though Cargo.toml exists
**How to avoid:** Wrap lockfile generation in try/except, return empty findings if cargo is unavailable
**Warning signs:** FileNotFoundError for cargo binary

## Code Examples

### gosec JSON Output Structure
```json
{
  "Issues": [
    {
      "severity": "HIGH",
      "confidence": "LOW",
      "cwe": {"ID": "798", "URL": "https://cwe.mitre.org/..."},
      "rule_id": "G101",
      "details": "Potential hardcoded credentials",
      "file": "/tmp/target/main.go",
      "code": "var password = \"secret\"",
      "line": "32",
      "column": "6"
    }
  ],
  "Stats": {"files": 20, "lines": 1500, "nosec": 2, "found": 5}
}
```

### Bandit JSON Output Structure
```json
{
  "results": [
    {
      "code": "exec(user_input)\n",
      "filename": "/tmp/target/app.py",
      "issue_confidence": "HIGH",
      "issue_severity": "HIGH",
      "issue_cwe": {"id": 78, "link": "https://cwe.mitre.org/..."},
      "issue_text": "Use of exec detected.",
      "line_number": 10,
      "line_range": [10],
      "more_info": "https://bandit.readthedocs.io/...",
      "test_id": "B102",
      "test_name": "exec_used"
    }
  ],
  "errors": [],
  "generated_at": "2026-03-21T12:00:00Z",
  "metrics": {}
}
```

### Brakeman JSON Output Structure
```json
{
  "warnings": [
    {
      "warning_type": "SQL Injection",
      "warning_code": 0,
      "fingerprint": "abc123...",
      "check_name": "SQL",
      "message": "Possible SQL injection",
      "file": "app/controllers/users_controller.rb",
      "line": 15,
      "link": "https://brakemanscanner.org/...",
      "code": "User.where(\"name = '#{params[:name]}'\")",
      "confidence": "High"
    }
  ],
  "errors": [],
  "ignored_warnings": [],
  "scan_info": {}
}
```

### cargo-audit JSON Output Structure
```json
{
  "database": {"advisory-count": 650, "last-commit": "...", "last-updated": "..."},
  "lockfile": {"dependency-count": 125},
  "vulnerabilities": {
    "found": true,
    "count": 2,
    "list": [
      {
        "advisory": {
          "id": "RUSTSEC-2023-0001",
          "package": "openssl",
          "title": "Buffer overflow in openssl crate",
          "description": "A buffer overflow vulnerability...",
          "date": "2023-01-15",
          "aliases": ["CVE-2023-12345"],
          "cvss": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
          "url": "https://rustsec.org/advisories/RUSTSEC-2023-0001"
        },
        "versions": {
          "patched": [">=0.10.40"],
          "unaffected": ["<0.9.0"]
        },
        "package": {
          "name": "openssl",
          "version": "0.10.35",
          "source": "registry+https://github.com/rust-lang/crates.io-index"
        }
      }
    ]
  },
  "warnings": {
    "unsound": [],
    "yanked": []
  }
}
```

### Config.yml Entries (to add)
```yaml
scanners:
  # ... existing entries ...
  gosec:
    adapter_class: "scanner.adapters.gosec.GosecAdapter"
    enabled: "auto"
    timeout: 120
    extra_args: []
    languages: ["go"]
  bandit:
    adapter_class: "scanner.adapters.bandit.BanditAdapter"
    enabled: "auto"
    timeout: 120
    extra_args: []
    languages: ["python"]
  brakeman:
    adapter_class: "scanner.adapters.brakeman.BrakemanAdapter"
    enabled: "auto"
    timeout: 120
    extra_args: []
    languages: ["ruby"]
  cargo_audit:
    adapter_class: "scanner.adapters.cargo_audit.CargoAuditAdapter"
    enabled: "auto"
    timeout: 60
    extra_args: []
    languages: ["rust"]
```

### CLI Commands Per Tool

**gosec:**
```bash
gosec -fmt=json -stdout ./...
# Target path: pass directory as last arg, gosec scans ./... within it
# Alternative: gosec -fmt=json -stdout /path/to/project/...
```

**Bandit:**
```bash
bandit -r /path/to/project -f json --exit-zero
# -r = recursive, -f json = JSON output
# --exit-zero prevents non-zero exit on findings (alternative to handling exit 1)
# Or handle exit 1 like semgrep
```

**Brakeman:**
```bash
brakeman --format json --no-exit-on-warn --quiet /path/to/rails/app
# --no-exit-on-warn: exit 0 even with warnings
# --quiet: suppress progress output
# --no-pager: don't pipe through pager
```

**cargo-audit:**
```bash
cargo-audit audit --json
# Must be run from directory containing Cargo.lock
# Or: cargo-audit audit --json --file /path/to/Cargo.lock
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hard-coded adapter list | Config-driven plugin registry | Phase 8 (2026-03-20) | New adapters only need config.yml entry + module |
| SCANNER_LANGUAGES dict | Per-scanner `languages` in config | Phase 8 (2026-03-20) | Language detection is config-driven |
| ALL_ADAPTERS import | `load_adapter_class()` dynamic import | Phase 8 (2026-03-20) | No __init__.py changes needed |

**Deprecated/outdated:**
- `ALL_ADAPTERS` list in `__init__.py`: Removed in Phase 8, replaced by registry
- `SCANNER_LANGUAGES` dict: Removed in Phase 8, replaced by per-scanner `languages` config

## Open Questions

1. **gosec target path handling**
   - What we know: gosec accepts `./...` pattern for recursive scanning
   - What's unclear: Whether we should `cd` to target_path and run `gosec ./...` or pass `target_path/...` as argument
   - Recommendation: Use `gosec -fmt=json -stdout {target_path}/...` -- simpler, no directory change needed. The `_execute` method doesn't support cwd parameter, but we can construct the path. If this fails, we can prepend `cd target_path &&` or adjust the command.

2. **Brakeman on non-Rails Ruby projects**
   - What we know: Brakeman only works on Rails applications, auto-detects Rails structure
   - What's unclear: How to gracefully handle non-Rails Ruby projects (return empty? log warning?)
   - Recommendation: Run Brakeman, catch error exit code or "not a Rails app" stderr, return empty list with debug log. The registry enables brakeman for all `ruby` language detection -- non-Rails projects will just get 0 findings.

3. **cvss package as new dependency**
   - What we know: cargo-audit provides CVSS vector strings, not numeric scores
   - What's unclear: Whether adding a new pip dependency is acceptable vs. inline calculation
   - Recommendation: Add `cvss` package -- it's small (50KB), well-maintained (RedHat), and CVSS score calculation is genuinely complex. Alternative: if dependency is rejected, parse the vector with a simple mapping function for the most common vectors.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `python -m pytest tests/phase_09/ -x -q` |
| Full suite command | `python -m pytest tests/ -x -q` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SCAN-01 | gosec adapter parses JSON, maps severity, normalizes paths, handles exit codes | unit | `python -m pytest tests/phase_09/test_adapter_gosec.py -x` | Wave 0 |
| SCAN-02 | Bandit adapter parses JSON, applies confidence x severity matrix, handles exit codes | unit | `python -m pytest tests/phase_09/test_adapter_bandit.py -x` | Wave 0 |
| SCAN-03 | Brakeman adapter parses JSON, applies confidence-weighted severity, handles non-Rails | unit | `python -m pytest tests/phase_09/test_adapter_brakeman.py -x` | Wave 0 |
| SCAN-04 | cargo-audit adapter parses JSON, CVSS scoring, lockfile generation, filters warnings | unit | `python -m pytest tests/phase_09/test_adapter_cargo_audit.py -x` | Wave 0 |
| ALL | Config.yml entries load correctly via registry | unit | `python -m pytest tests/phase_09/test_config_registration.py -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/phase_09/ -x -q`
- **Per wave merge:** `python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before /gsd:verify-work

### Wave 0 Gaps
- [ ] `tests/phase_09/__init__.py` -- package init
- [ ] `tests/phase_09/conftest.py` -- shared fixtures (fixtures_dir, adapter instances, JSON fixture loaders)
- [ ] `tests/phase_09/fixtures/gosec_output.json` -- gosec sample output with 2-3 findings
- [ ] `tests/phase_09/fixtures/bandit_output.json` -- bandit sample with varying severity/confidence
- [ ] `tests/phase_09/fixtures/brakeman_output.json` -- brakeman sample with High/Medium/Weak confidence
- [ ] `tests/phase_09/fixtures/cargo_audit_output.json` -- cargo-audit sample with CVSS vectors and null CVSS
- [ ] `tests/phase_09/test_adapter_gosec.py` -- covers SCAN-01
- [ ] `tests/phase_09/test_adapter_bandit.py` -- covers SCAN-02
- [ ] `tests/phase_09/test_adapter_brakeman.py` -- covers SCAN-03
- [ ] `tests/phase_09/test_adapter_cargo_audit.py` -- covers SCAN-04
- [ ] `tests/phase_09/test_config_registration.py` -- covers config.yml integration

### Tests Per Adapter (minimum)
Each adapter test file should cover:
1. **Parse findings:** Mock `_execute`, verify correct count and tool name
2. **Severity mapping:** Verify tool-specific severity logic (direct/matrix/confidence-weighted/CVSS)
3. **Path normalization:** Verify target prefix stripped from file paths
4. **Exit code 1 handling:** Verify findings returned (not error raised)
5. **Exit code 2+ handling:** Verify ScannerExecutionError raised
6. **Fingerprint populated:** Verify 64-char hex SHA-256
7. **Empty results:** Verify empty list returned for clean output
8. **Tool-specific edge cases:** gosec string line numbers, Brakeman non-Rails, cargo-audit null CVSS, cargo-audit warning filtering

## Sources

### Primary (HIGH confidence)
- `src/scanner/adapters/semgrep.py` -- reference adapter implementation pattern
- `src/scanner/adapters/base.py` -- ScannerAdapter contract
- `src/scanner/schemas/finding.py` -- FindingSchema fields
- `src/scanner/adapters/registry.py` -- plugin registry loading
- `tests/phase_02/test_adapter_semgrep.py` -- test pattern reference
- `.planning/milestones/v2.0-phases/07-security-scanner-ecosystem-research/07-SCANNER-ECOSYSTEM-REPORT.md` -- per-tool research
- [Bandit JSON formatter docs](https://bandit.readthedocs.io/en/latest/formatters/json.html) -- confirmed field names
- [Brakeman JSON format (GitHub issue #1467)](https://github.com/presidentbeef/brakeman/issues/1467) -- confirmed warning fields
- [DefectDojo gosec sample](https://github.com/DefectDojo/sample-scan-files/blob/master/gosec/gosec_v2.0.0.json) -- confirmed JSON structure
- [ICTU quality-time cargo-audit JSON](https://github.com/ICTU/quality-time/issues/6347) -- confirmed full JSON schema

### Secondary (MEDIUM confidence)
- [gosec GitHub](https://github.com/securego/gosec) -- CLI flags and output formats
- [cvss PyPI](https://pypi.org/project/cvss/) -- CVSS vector parsing library

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- existing codebase patterns are well-established and documented
- Architecture: HIGH -- direct extension of existing adapter pattern, no new architecture needed
- Pitfalls: HIGH -- verified against actual JSON output schemas and tool documentation
- Tool JSON schemas: HIGH -- verified against multiple sources (official docs, sample files, GitHub issues)

**Research date:** 2026-03-21
**Valid until:** 2026-04-21 (stable -- tools have mature JSON APIs)
