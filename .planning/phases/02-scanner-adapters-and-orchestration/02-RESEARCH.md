# Phase 2: Scanner Adapters and Orchestration - Research

**Researched:** 2026-03-18
**Domain:** Python asyncio subprocess orchestration, security tool JSON/XML output parsing, CLI design
**Confidence:** HIGH

## Summary

Phase 2 requires building five scanner adapters (Semgrep, cppcheck, Gitleaks, Trivy, Checkov) behind a common interface, an orchestrator that runs them in parallel with per-tool timeouts and graceful degradation, a deduplication layer using the existing `compute_fingerprint()`, and a CLI entry point. The codebase already provides `FindingSchema`, `ScanResultSchema`, `compute_fingerprint()`, `ScannerSettings`, async SQLite persistence, and ORM models -- the adapters need to produce `list[FindingSchema]` from each tool's native output.

All five tools support structured output (JSON or XML) that can be parsed deterministically. The main technical challenges are: (1) correct severity mapping from each tool's native levels to the unified `Severity` enum, (2) robust subprocess management with timeouts using `asyncio.create_subprocess_exec`, and (3) git clone handling with SSH/HTTPS auth and shallow vs. full clone differentiation for Gitleaks.

**Primary recommendation:** Use `asyncio.create_subprocess_exec` + `asyncio.gather` with `return_exceptions=True` for parallel execution, Typer for the CLI (same author as FastAPI, native async support), and a base `ScannerAdapter` ABC that each tool implements with `run()` and `parse_output()` methods.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- CLI command: `python -m scanner scan --path /code` or `--repo-url URL --branch NAME`
- Stdout summary table (tool, findings count, status) + full results persisted to SQLite
- `--json` flag for machine-readable JSON output (for scripting/CI)
- Early quality gate: exit code 1 when Critical/High findings found, exit 0 otherwise
- Auth: support both SSH key mount (primary) and HTTPS token via `SCANNER_GIT_TOKEN` env var (fallback)
- Clone strategy: shallow clone (depth=1) for code scanners; full clone for Gitleaks (needs git history)
- Branch only (no tag/commit support)
- Auto-delete temp clone directory after scan completes
- Scan status = "completed" with warnings list when tools fail/timeout (graceful degradation per SCAN-06)
- Prominent WARNING banner in CLI output showing which tools failed and why
- Quality gate evaluates available findings only -- tool failure does not auto-fail the gate
- Per-tool configurable timeouts in config.yml
- Each tool individually enable/disable in config.yml (all enabled by default)
- Extra args field per tool in config.yml
- Severity mapping: hardcoded sensible defaults per adapter (not configurable in v1)
- Semgrep uses built-in rulesets only (p/security-audit, p/secrets)

### Claude's Discretion
- Scanner adapter interface design (base class, output parsing approach)
- Parallel execution strategy (asyncio.gather, subprocess management)
- Finding deduplication algorithm details (fingerprint matching, merge strategy)
- Config.yml structure for scanner sections
- Temp directory naming and location for git clones
- Exact CLI argument parsing library (click, typer, argparse)

### Deferred Ideas (OUT OF SCOPE)
- Web interface for config management (enable/disable tools, edit args, timeouts via dashboard) -- Phase 5 scope
- Custom Semgrep rules for aipix platform (RTSP auth, VMS API, webhooks) -- v2 scope (RULES-01 to RULES-04)
- Tag/commit hash support for git ref (currently branch-only) -- add if needed later
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SCAN-01 | Scanner runs Semgrep, cppcheck, Gitleaks, Trivy, and Checkov in parallel on target codebase | Asyncio subprocess pattern with `asyncio.gather(return_exceptions=True)`, per-tool adapter classes, orchestrator module |
| SCAN-03 | Findings deduplicated across tools using stable fingerprints (file + rule + snippet hash) | Existing `compute_fingerprint()` -- adapters normalize file_path/rule_id/snippet, orchestrator groups by fingerprint and merges |
| SCAN-04 | Scanner accepts local filesystem path as scan target | CLI `--path` arg, validated as existing directory, passed directly to tool subprocesses |
| SCAN-05 | Scanner accepts git repository URL + branch as scan target and clones automatically | Git clone module with SSH/HTTPS support, shallow clone (depth=1) default, full clone for Gitleaks, tempdir cleanup |
| SCAN-06 | Each scanner tool has configurable timeout with graceful degradation on failure | Per-tool timeout in config.yml, `asyncio.wait_for()` wrapping, `process.kill()` on timeout, warning capture |
| SCAN-07 | Total scan time under 10 minutes for a typical aipix release branch | Parallel execution via `asyncio.gather`, shallow clones, per-tool timeout caps (default 180s each) |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| typer | 0.24.1 | CLI framework | Built on Click by FastAPI author, native async support, type-hint driven -- natural fit with existing FastAPI codebase |
| rich | 14.3.3 | CLI output formatting (tables, warnings) | De facto standard for Python CLI output, Typer uses it internally for help rendering |
| pyyaml | 6.0.3 | Already a dependency via pydantic-settings[yaml] | Config parsing for scanner sections |

### External Tools (in Docker image)
| Tool | Purpose | Output Format | Install Method |
|------|---------|---------------|----------------|
| semgrep | SAST for PHP, C#, C++ | JSON (`--json`) | pip install semgrep |
| cppcheck | C++ static analysis | XML v2 (`--xml`) | apt-get install cppcheck |
| gitleaks | Secrets detection in code + git history | JSON (`--report-format json`) | Binary from GitHub releases |
| trivy | CVE scanning, Docker/K8s/IaC | JSON (`--format json`) | apt-get or install script |
| checkov | IaC scanning (Helm, docker-compose) | JSON (`--output json`) | pip install checkov |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Typer | Click | Click lacks native async; more boilerplate for type hints. Typer wraps Click anyway |
| Typer | argparse | Stdlib but no rich output, no type hint integration, more verbose |
| asyncio subprocess | concurrent.futures | asyncio integrates better with existing async SQLAlchemy; no thread overhead |

**Installation (pyproject.toml additions):**
```bash
pip install typer[all] rich
```

**Dockerfile additions:**
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    git cppcheck curl \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir semgrep checkov
# Trivy: official install script
RUN curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
# Gitleaks: binary from GitHub releases
RUN curl -sSfL https://github.com/gitleaks/gitleaks/releases/latest/download/gitleaks_8.24.0_linux_amd64.tar.gz | tar xz -C /usr/local/bin gitleaks
```

## Architecture Patterns

### Recommended Project Structure
```
src/scanner/
├── adapters/            # Scanner tool adapters
│   ├── __init__.py
│   ├── base.py          # ScannerAdapter ABC
│   ├── semgrep.py       # Semgrep adapter
│   ├── cppcheck.py      # cppcheck adapter
│   ├── gitleaks.py      # Gitleaks adapter
│   ├── trivy.py         # Trivy adapter
│   └── checkov.py       # Checkov adapter
├── core/
│   ├── fingerprint.py   # (existing)
│   ├── orchestrator.py  # Parallel execution + dedup
│   └── git.py           # Git clone/cleanup
├── cli/
│   ├── __init__.py
│   └── main.py          # Typer app with scan command
├── schemas/             # (existing)
├── models/              # (existing)
├── config.py            # (extend with scanner sections)
└── main.py              # (existing FastAPI)
```

### Pattern 1: Scanner Adapter ABC
**What:** Abstract base class that all tool adapters implement
**When to use:** Every scanner adapter
**Example:**
```python
import abc
from scanner.schemas.finding import FindingSchema

class ScannerAdapter(abc.ABC):
    """Base class for all scanner tool adapters."""

    tool_name: str  # e.g., "semgrep"

    @abc.abstractmethod
    async def run(self, target_path: str, extra_args: list[str] | None = None) -> list[FindingSchema]:
        """Run the scanner on target_path and return normalized findings."""
        ...

    async def get_version(self) -> str:
        """Return the tool's version string."""
        proc = await asyncio.create_subprocess_exec(
            *self._version_command(),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        return stdout.decode().strip()

    @abc.abstractmethod
    def _version_command(self) -> list[str]:
        ...
```

### Pattern 2: Subprocess Execution with Timeout
**What:** Run external tool as async subprocess with configurable timeout
**When to use:** Every adapter's `run()` method
**Example:**
```python
async def _execute(self, cmd: list[str], timeout: int) -> tuple[str, str, int]:
    """Execute command with timeout, return (stdout, stderr, returncode)."""
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=timeout
        )
        return stdout.decode(), stderr.decode(), proc.returncode
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise ScannerTimeoutError(
            f"{self.tool_name} timed out after {timeout}s"
        )
```

### Pattern 3: Orchestrator with Parallel Execution
**What:** Run all enabled adapters via `asyncio.gather` with `return_exceptions=True`
**When to use:** Main scan orchestration
**Example:**
```python
async def run_all_scanners(
    target_path: str,
    adapters: list[ScannerAdapter],
    timeouts: dict[str, int],
) -> tuple[list[FindingSchema], list[str]]:
    """Run adapters in parallel, return (all_findings, warnings)."""
    tasks = [
        asyncio.wait_for(
            adapter.run(target_path),
            timeout=timeouts.get(adapter.tool_name, 180),
        )
        for adapter in adapters
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_findings: list[FindingSchema] = []
    warnings: list[str] = []
    for adapter, result in zip(adapters, results):
        if isinstance(result, Exception):
            warnings.append(f"{adapter.tool_name}: {result}")
        else:
            all_findings.extend(result)

    return all_findings, warnings
```

### Pattern 4: Finding Deduplication
**What:** Group findings by fingerprint, merge tool attributions
**When to use:** After collecting all adapter results
**Example:**
```python
def deduplicate_findings(findings: list[FindingSchema]) -> list[FindingSchema]:
    """Collapse duplicate findings across tools, keep highest severity."""
    seen: dict[str, FindingSchema] = {}
    for finding in findings:
        if finding.fingerprint in seen:
            existing = seen[finding.fingerprint]
            # Keep the one with higher severity; merge tool info in description
            if finding.severity > existing.severity:
                seen[finding.fingerprint] = finding
        else:
            seen[finding.fingerprint] = finding
    return list(seen.values())
```

### Anti-Patterns to Avoid
- **Blocking subprocess.run in async code:** Never use `subprocess.run()` -- always use `asyncio.create_subprocess_exec()`. Blocking calls will serialize parallel execution.
- **Parsing stdout text with regex:** All five tools have structured output (JSON/XML). Always use `json.loads()` or `xml.etree.ElementTree` instead of regex parsing.
- **Global exception handler swallowing tool errors:** Each adapter failure must be captured individually and reported as a warning, not silently swallowed or escalated to scan failure.
- **Hardcoding tool paths:** Use `shutil.which()` to find tool binaries, allowing the Docker image and local dev to work without path changes.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CLI argument parsing | Custom arg parser | Typer with Click underneath | Handles validation, help generation, error messages |
| CLI output tables | String formatting | `rich.table.Table` | Handles column alignment, colors, Unicode borders |
| XML parsing for cppcheck | Regex on XML | `xml.etree.ElementTree` (stdlib) | Handles encoding, entities, namespaces correctly |
| Temp directory management | Manual mkdir/cleanup | `tempfile.TemporaryDirectory` context manager | Auto-cleanup even on exceptions |
| Git clone operations | Raw subprocess git calls | Structured git module with auth injection | SSH/HTTPS auth, shallow/full clone logic, error handling |
| Process timeout | Manual timer threads | `asyncio.wait_for()` | Native cancellation, proper cleanup |

**Key insight:** Every security tool already produces structured output in a well-defined format. The adapter's job is parsing and normalizing, not re-implementing analysis.

## Common Pitfalls

### Pitfall 1: Semgrep exit codes
**What goes wrong:** Semgrep returns exit code 1 when findings are found (not just on error)
**Why it happens:** By design -- exit code 0 means no findings, 1 means findings exist, other codes mean actual errors
**How to avoid:** Check returncode explicitly: 0 = clean, 1 = findings present (parse them), other = real error
**Warning signs:** All Semgrep scans appear to "fail" even when findings are present

### Pitfall 2: Gitleaks requires full git history
**What goes wrong:** Gitleaks finds no secrets when run on shallow clone
**Why it happens:** Gitleaks scans git commit history for secrets; shallow clone (depth=1) has only one commit
**How to avoid:** Use `--no-git` flag for filesystem-only scan, or full clone when scanning git history. Per CONTEXT.md decision: full clone for Gitleaks specifically.
**Warning signs:** Zero Gitleaks findings on repos known to have committed secrets

### Pitfall 3: cppcheck on non-C++ repos
**What goes wrong:** cppcheck errors or hangs scanning repos with no C/C++ files
**Why it happens:** cppcheck tries to find .c/.cpp files and may produce misleading results or take excessive time
**How to avoid:** Pre-check for C/C++ files before invoking cppcheck; if none found, skip with info message
**Warning signs:** cppcheck timeout on PHP-only repos

### Pitfall 4: Checkov requires Bridgecrew API key for severity
**What goes wrong:** Checkov outputs show no severity field without API key
**Why it happens:** Severity metadata comes from Bridgecrew platform; without API key, checks have no severity
**How to avoid:** Map Checkov check_id prefixes to severity levels (CKV_DOCKER, CKV_K8S, etc. -> hardcoded mapping), or treat all Checkov findings as MEDIUM by default
**Warning signs:** All Checkov findings have null/missing severity

### Pitfall 5: Trivy vulnerability DB download on first run
**What goes wrong:** First Trivy scan takes 5+ minutes downloading vulnerability database
**Why it happens:** Trivy needs its vuln DB; in Docker container, it downloads fresh each time unless cached
**How to avoid:** Pre-download DB in Dockerfile with `trivy --download-db-only`, or mount a volume for the DB cache at `/root/.cache/trivy`
**Warning signs:** First scan is extremely slow; subsequent scans are fast

### Pitfall 6: asyncio.gather cancellation semantics
**What goes wrong:** When one task fails, other tasks continue running indefinitely
**Why it happens:** `return_exceptions=True` means gather never cancels siblings -- it waits for all
**How to avoid:** This is actually the desired behavior for our use case (graceful degradation). But ensure individual tasks have their own timeouts via `asyncio.wait_for()`.
**Warning signs:** Scan hangs waiting for a single stuck tool

### Pitfall 7: File paths differ between tools
**What goes wrong:** Same file reported as `./src/main.cpp`, `src/main.cpp`, `/tmp/scan123/src/main.cpp`
**Why it happens:** Each tool has its own path normalization
**How to avoid:** Strip the scan target prefix from all file paths in adapters, normalize to relative paths without leading `./`
**Warning signs:** Deduplication fails because fingerprints differ due to path format

## Code Examples

### Semgrep Adapter -- Parse JSON Output
```python
# Semgrep JSON output structure (top-level):
# { "results": [...], "errors": [...], "version": "..." }
# Each result:
# { "check_id": "...", "path": "...", "start": {"line": N, "col": N},
#   "end": {"line": N, "col": N}, "extra": {"message": "...",
#   "severity": "ERROR|WARNING|INFO", "metadata": {...}, "lines": "..."} }

SEMGREP_SEVERITY_MAP = {
    "ERROR": Severity.HIGH,
    "WARNING": Severity.MEDIUM,
    "INFO": Severity.INFO,
}

def parse_semgrep_result(result: dict, target_prefix: str) -> FindingSchema:
    rel_path = result["path"].removeprefix(target_prefix).lstrip("/")
    extra = result.get("extra", {})
    snippet = extra.get("lines", "")
    severity = SEMGREP_SEVERITY_MAP.get(extra.get("severity", "WARNING"), Severity.MEDIUM)

    return FindingSchema(
        fingerprint=compute_fingerprint(rel_path, result["check_id"], snippet),
        tool="semgrep",
        rule_id=result["check_id"],
        file_path=rel_path,
        line_start=result["start"]["line"],
        line_end=result["end"]["line"],
        snippet=snippet,
        severity=severity,
        title=extra.get("message", result["check_id"]),
        description=extra.get("message", ""),
    )
```

### cppcheck Adapter -- Parse XML Output
```python
# cppcheck XML v2 structure:
# <results version="2"><cppcheck version="..."/>
#   <errors><error id="..." severity="error|warning|style|performance|portability"
#     msg="..." verbose="..." cwe="...">
#     <location file="..." line="..." column="..."/>
#   </error></errors></results>

import xml.etree.ElementTree as ET

CPPCHECK_SEVERITY_MAP = {
    "error": Severity.HIGH,
    "warning": Severity.MEDIUM,
    "style": Severity.LOW,
    "performance": Severity.LOW,
    "portability": Severity.LOW,
    "information": Severity.INFO,
}

def parse_cppcheck_xml(xml_str: str, target_prefix: str) -> list[FindingSchema]:
    root = ET.fromstring(xml_str)
    findings = []
    for error in root.iter("error"):
        locations = error.findall("location")
        if not locations:
            continue
        loc = locations[0]
        file_path = loc.get("file", "").removeprefix(target_prefix).lstrip("/")
        severity = CPPCHECK_SEVERITY_MAP.get(error.get("severity", "warning"), Severity.MEDIUM)
        snippet = error.get("verbose", error.get("msg", ""))

        findings.append(FindingSchema(
            fingerprint=compute_fingerprint(file_path, error.get("id", ""), snippet),
            tool="cppcheck",
            rule_id=error.get("id", "unknown"),
            file_path=file_path,
            line_start=int(loc.get("line", 0)) or None,
            snippet=snippet,
            severity=severity,
            title=error.get("msg", ""),
            description=error.get("verbose", ""),
        ))
    return findings
```

### Gitleaks Adapter -- Parse JSON Output
```python
# Gitleaks JSON output: array of objects
# [{ "RuleID": "...", "Description": "...", "StartLine": N, "EndLine": N,
#    "File": "...", "Match": "...", "Secret": "...", "Fingerprint": "...",
#    "Commit": "...", "Author": "...", "Tags": [] }]

def parse_gitleaks_results(results: list[dict], target_prefix: str) -> list[FindingSchema]:
    findings = []
    for r in results:
        file_path = r.get("File", "").removeprefix(target_prefix).lstrip("/")
        # All secrets are HIGH severity by default
        snippet = r.get("Match", "")
        findings.append(FindingSchema(
            fingerprint=compute_fingerprint(file_path, r.get("RuleID", ""), snippet),
            tool="gitleaks",
            rule_id=r.get("RuleID", "unknown"),
            file_path=file_path,
            line_start=r.get("StartLine"),
            line_end=r.get("EndLine"),
            snippet=snippet,  # Note: mask actual secrets before storing
            severity=Severity.HIGH,
            title=r.get("Description", "Secret detected"),
            description=f"Secret found by rule {r.get('RuleID', '')} in commit {r.get('Commit', 'N/A')[:8]}",
        ))
    return findings
```

### Trivy Adapter -- Parse JSON Output
```python
# Trivy JSON: { "SchemaVersion": 2, "Results": [
#   { "Target": "...", "Vulnerabilities": [
#     { "VulnerabilityID": "...", "PkgName": "...", "Severity": "CRITICAL|HIGH|...",
#       "Title": "...", "InstalledVersion": "...", "FixedVersion": "..." }
#   ], "Misconfigurations": [
#     { "ID": "...", "Title": "...", "Severity": "...", "Message": "...",
#       "Resolution": "..." }
#   ] } ] }

TRIVY_SEVERITY_MAP = {
    "CRITICAL": Severity.CRITICAL,
    "HIGH": Severity.HIGH,
    "MEDIUM": Severity.MEDIUM,
    "LOW": Severity.LOW,
    "UNKNOWN": Severity.INFO,
}
```

### Checkov Adapter -- Parse JSON Output
```python
# Checkov JSON: { "check_type": "...", "results": {
#   "passed_checks": [...], "failed_checks": [
#     { "check_id": "CKV_DOCKER_2", "check_name": "...",
#       "check_result": {"result": "FAILED"},
#       "file_path": "...", "file_line_range": [1, 16],
#       "resource": "...", "guideline": "..." }
#   ], "skipped_checks": [] },
#   "summary": { "passed": N, "failed": N } }

# Default severity by check_id prefix (no Bridgecrew API key needed)
CHECKOV_SEVERITY_MAP = {
    "CKV_DOCKER": Severity.MEDIUM,
    "CKV_K8S": Severity.MEDIUM,
    "CKV2_K8S": Severity.HIGH,  # CKV2 checks are generally more severe
    "CKV_HELM": Severity.MEDIUM,
}
```

### Config.yml Scanner Sections
```yaml
# config.yml scanner sections structure
scanners:
  semgrep:
    enabled: true
    timeout: 180
    extra_args: []
    rulesets:
      - "p/security-audit"
      - "p/secrets"
  cppcheck:
    enabled: true
    timeout: 120
    extra_args: []
  gitleaks:
    enabled: true
    timeout: 120
    extra_args: []
  trivy:
    enabled: true
    timeout: 120
    extra_args: []
  checkov:
    enabled: true
    timeout: 120
    extra_args: []
```

### Git Clone Module
```python
import tempfile
import asyncio
import os

async def clone_repo(
    repo_url: str,
    branch: str,
    shallow: bool = True,
    git_token: str | None = None,
) -> str:
    """Clone a git repo to a temp directory, return path."""
    tmpdir = tempfile.mkdtemp(prefix="scanner-clone-")

    # Inject HTTPS token if provided
    env = os.environ.copy()
    if git_token and repo_url.startswith("https://"):
        # GIT_ASKPASS approach avoids leaking token in process args
        askpass_script = os.path.join(tmpdir, ".git-askpass")
        with open(askpass_script, "w") as f:
            f.write(f"#!/bin/sh\necho {git_token}\n")
        os.chmod(askpass_script, 0o700)
        env["GIT_ASKPASS"] = askpass_script

    cmd = ["git", "clone", "--branch", branch, "--single-branch"]
    if shallow:
        cmd.extend(["--depth", "1"])
    cmd.extend([repo_url, tmpdir])

    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, env=env
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise GitCloneError(f"git clone failed: {stderr.decode()}")

    return tmpdir
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| subprocess.run for tools | asyncio.create_subprocess_exec | Python 3.4+ (mature) | True parallel execution without threads |
| Click for CLI | Typer (wraps Click) | 2020+ | Type hints as CLI params, native async, less boilerplate |
| Trivy v1 format | Trivy JSON SchemaVersion 2 | Trivy 0.19+ | Unified Results array with Vulnerabilities + Misconfigurations |
| cppcheck --template | cppcheck --xml (v2 default) | cppcheck 1.x+ | Structured XML, CWE IDs included |
| Gitleaks v7 format | Gitleaks v8 JSON format | Gitleaks 8.0 | New field names (RuleID, Description, etc.) |

**Deprecated/outdated:**
- Semgrep `--config r/...` syntax: replaced with `--config p/...` for registry rulesets
- Trivy `--format table` for parsing: always use `--format json` for programmatic access
- cppcheck XML version 1: only version 2 is supported now

## Open Questions

1. **Gitleaks full clone + filesystem-only mode**
   - What we know: CONTEXT.md says full clone for Gitleaks. Gitleaks supports `--no-git` for filesystem-only scanning.
   - What's unclear: Should we do a full clone once and run all tools on it, or do two clones (shallow for code scanners, full for Gitleaks)?
   - Recommendation: Single full clone used by all tools. The time difference between shallow and full clone is typically small (30-60s) for typical repos, and avoids clone duplication. If performance is a concern, can optimize later.

2. **Checkov severity without API key**
   - What we know: Checkov does not provide severity in output without a Bridgecrew API key
   - What's unclear: Exact mapping of check_id prefixes to appropriate severity levels
   - Recommendation: Default all Checkov findings to MEDIUM severity; CKV2_* prefix checks to HIGH. This is a conservative approach; can refine mapping over time based on which checks fire.

3. **Semgrep in Docker -- pip install size**
   - What we know: Semgrep pip package is large (~500MB installed)
   - What's unclear: Whether this significantly impacts Docker image size
   - Recommendation: Accept the size trade-off; Semgrep is a core tool. Consider multi-stage build if image size becomes a concern.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio (already installed) |
| Config file | `pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `pytest tests/phase_02/ -x -q` |
| Full suite command | `pytest tests/ -x -q` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SCAN-01 | Five scanners run in parallel producing findings | integration | `pytest tests/phase_02/test_orchestrator.py -x` | No -- Wave 0 |
| SCAN-03 | Findings deduplicated by fingerprint across tools | unit | `pytest tests/phase_02/test_dedup.py -x` | No -- Wave 0 |
| SCAN-04 | Scanner accepts local filesystem path | unit | `pytest tests/phase_02/test_cli.py::test_scan_local_path -x` | No -- Wave 0 |
| SCAN-05 | Scanner accepts git URL + branch, clones automatically | unit | `pytest tests/phase_02/test_git.py -x` | No -- Wave 0 |
| SCAN-06 | Per-tool timeout with graceful degradation | unit | `pytest tests/phase_02/test_orchestrator.py::test_timeout_graceful -x` | No -- Wave 0 |
| SCAN-07 | Total scan time under 10 minutes | manual-only | Manual timing test against aipix repo | N/A |

### Testing Strategy for Adapters
Each adapter should be tested with **mock subprocess output** (fixture JSON/XML files), not actual tool execution. This ensures:
- Tests run without installing all five security tools
- Tests are deterministic and fast
- Each adapter's parse logic is verified independently

**Fixture approach:**
```
tests/phase_02/
├── conftest.py              # Shared fixtures
├── fixtures/                # Sample tool outputs
│   ├── semgrep_output.json
│   ├── cppcheck_output.xml
│   ├── gitleaks_output.json
│   ├── trivy_output.json
│   └── checkov_output.json
├── test_adapter_semgrep.py
├── test_adapter_cppcheck.py
├── test_adapter_gitleaks.py
├── test_adapter_trivy.py
├── test_adapter_checkov.py
├── test_orchestrator.py     # Parallel exec, dedup, graceful degradation
├── test_dedup.py            # Deduplication logic
├── test_git.py              # Git clone module
└── test_cli.py              # CLI commands
```

### Sampling Rate
- **Per task commit:** `pytest tests/phase_02/ -x -q`
- **Per wave merge:** `pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/phase_02/__init__.py` -- package init
- [ ] `tests/phase_02/conftest.py` -- shared fixtures (mock subprocess, temp dirs)
- [ ] `tests/phase_02/fixtures/` -- sample tool output files for each adapter
- [ ] All test files listed above

## Sources

### Primary (HIGH confidence)
- Python 3.12 asyncio subprocess docs: https://docs.python.org/3.12/library/asyncio-subprocess.html
- Semgrep JSON schema: https://github.com/semgrep/semgrep-interfaces/blob/main/semgrep_output_v1.jsonschema
- Gitleaks JSON output format: https://github.com/gitleaks/gitleaks/blob/master/testdata/expected/report/json_simple.json
- Trivy reporting docs: https://trivy.dev/docs/latest/configuration/reporting/
- Checkov scan results: https://www.checkov.io/2.Basics/Reviewing%20Scan%20Results.html
- cppcheck manual: https://cppcheck.sourceforge.io/manual.pdf
- Typer docs: https://typer.tiangolo.com/features/

### Secondary (MEDIUM confidence)
- Typer version 0.24.1 verified via `pip index versions typer`
- Rich version 14.3.3 verified via `pip index versions rich`
- Semgrep severity values (ERROR/WARNING/INFO) from WebSearch cross-referenced with CLI docs
- Gitleaks JSON fields verified via GitHub testdata fixtures

### Tertiary (LOW confidence)
- Semgrep pip install size (~500MB) -- anecdotal from community reports, needs verification
- Gitleaks v8 binary download URL -- exact version/filename may need updating at implementation time

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all tools well-documented, versions verified against PyPI/apt
- Architecture: HIGH -- asyncio subprocess pattern is well-established, adapter pattern is standard
- Pitfalls: HIGH -- most pitfalls documented in official tool docs or widely reported
- Tool output formats: HIGH -- verified against official docs and test fixtures

**Research date:** 2026-03-18
**Valid until:** 2026-04-18 (stable domain, tools evolve slowly)
