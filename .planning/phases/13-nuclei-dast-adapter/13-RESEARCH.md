# Phase 13: Nuclei DAST Adapter - Research

**Researched:** 2026-03-23
**Domain:** Dynamic Application Security Testing (DAST) via Nuclei CLI integration
**Confidence:** HIGH

## Summary

Phase 13 integrates Nuclei (ProjectDiscovery's template-based vulnerability scanner) as a DAST adapter following the exact same ScannerAdapter pattern used by all existing SAST tools (semgrep, gosec, trivy, etc.). The codebase already has 12 adapter implementations providing a well-established contract: subclass `ScannerAdapter`, parse JSON/JSONL output, map to `FindingSchema`, register in `config.yml`.

The key differences from SAST adapters are: (1) target is a URL not a filesystem path, requiring a `target_url` field on `ScanRequest` and routing logic in the orchestrator, (2) Nuclei outputs JSONL (one JSON object per line) via the `-jsonl` flag rather than a single JSON blob, and (3) the `file_path` field stores the matched-at URL instead of a source file path. Everything else -- severity mapping, fingerprinting, deduplication, reporting, quality gate -- reuses existing infrastructure with zero changes.

**Primary recommendation:** Follow the gosec adapter as the reference implementation pattern. Nuclei adapter is a straightforward extension with the main complexity being the orchestrator routing logic (DAST vs SAST based on `target_url` presence) and the `ScanRequest` validator update.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Store matched-at URL in `FindingSchema.file_path` -- no new schema fields needed
- Use Nuclei's built-in severity (info/low/medium/high/critical) mapped directly to the `Severity` enum
- Template ID maps to `rule_id`
- Snippet contains Nuclei's extracted/matched content from the response
- Fingerprint computed from URL + template ID + matched content (same `compute_fingerprint` pattern)
- Add optional `target_url` field to existing `ScanRequest` -- single endpoint, no separate DAST API
- If `target_url` is provided, only Nuclei runs (DAST-only scan) -- SAST scanners skipped
- If `target_url` is absent, SAST as usual -- Nuclei adapter skipped
- Template selection via `extra_args` in `config.yml` (e.g. `-tags cve,exposure`) -- follows existing adapter pattern
- Nuclei registered in plugin registry like all other adapters (`adapter_class` in config.yml)
- DAST findings appear alongside SAST findings in the same report, tagged with "nuclei" tool badge
- Grouped by severity as usual -- no separate DAST section
- Quality gate applies equally to DAST findings
- Download pre-built Nuclei binary from GitHub releases, pinned to specific version
- Use Docker `TARGETARCH` build arg for multi-arch (linux_amd64 vs linux_arm64)
- Run `nuclei -update-templates` during Docker build -- templates baked into image
- No runtime network dependency for templates

### Claude's Discretion
- Nuclei JSON output parsing details and edge cases
- Exact version to pin for initial release
- Template update frequency in Docker rebuilds
- Error handling for Nuclei-specific failure modes (e.g. target unreachable)
- Whether to pass `target_url` validation (URL format check) in the adapter or API layer

### Deferred Ideas (OUT OF SCOPE)
- DAST target management (save/edit target URLs) -- DAST-05 in v1.0.3+
- DAST-specific report section with URL-based grouping -- DAST-06 in v1.0.3+
- Scheduled DAST scans -- DAST-07 in v1.0.3+
- Template category selection per scan via API parameter -- could revisit in scan profiles (Phase 15)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DAST-01 | Nuclei adapter scans target URLs using templates and produces FindingSchema-compatible results | Nuclei JSONL output structure documented; field mapping (template-id->rule_id, matched-at->file_path, info.severity->Severity enum) verified; adapter pattern from gosec provides exact template |
| DAST-02 | Scan API accepts optional target_url field for DAST scans | ScanRequest model_validator needs updating to allow target_url as third option; orchestrator routing logic needed to dispatch DAST vs SAST |
| DAST-03 | Nuclei binary installed in Docker image with multi-arch support | Nuclei v3.7.1 releases confirmed with zip files for linux_amd64 and linux_arm64; Dockerfile pattern established by gitleaks/trivy/gosec installations |
| DAST-04 | Nuclei findings appear in HTML/PDF reports alongside SAST findings | Reports already use tool-based filtering with `all_tools` variable; findings with tool="nuclei" will appear automatically with tool badge; no report template changes needed |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Nuclei | v3.7.1 | Template-based DAST scanner CLI | Latest stable release (March 2025); actively maintained by ProjectDiscovery; 30MB binary vs 500MB+ ZAP |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Nuclei Templates | Built-in (baked at build time) | Vulnerability detection templates | Always -- `nuclei -update-templates` during Docker build |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Nuclei | ZAP (OWASP) | 500MB+ image size, complex setup, Java dependency -- Nuclei is 30MB Go binary |
| Pinned binary | pip/apt install | No official pip package; apt version lags behind; direct binary gives version control |

**Installation (Docker):**
```dockerfile
ARG TARGETARCH
RUN ARCH=$(echo ${TARGETARCH} | sed 's/amd64/amd64/;s/arm64/arm64/') && \
    curl -sSL "https://github.com/projectdiscovery/nuclei/releases/download/v3.7.1/nuclei_3.7.1_linux_${ARCH}.zip" \
    -o /tmp/nuclei.zip && \
    unzip -o /tmp/nuclei.zip -d /usr/local/bin nuclei && \
    chmod +x /usr/local/bin/nuclei && \
    rm /tmp/nuclei.zip && \
    nuclei -update-templates
```

**Version verification:** Nuclei v3.7.1 confirmed as latest via GitHub API on 2026-03-23. Release assets are zip format (not tar.gz like other tools in this project).

## Architecture Patterns

### Recommended Project Structure
```
src/scanner/adapters/
    nuclei.py            # NucleiAdapter (ScannerAdapter subclass)
src/scanner/api/
    schemas.py           # ScanRequest updated with target_url field
src/scanner/core/
    orchestrator.py      # run_scan() updated with DAST routing
config.yml.example       # nuclei entry added to scanners section
Dockerfile               # Nuclei binary installation added
tests/phase_13/
    __init__.py
    conftest.py          # Fixtures with sample JSONL output
    fixtures/
        nuclei_output.jsonl
    test_nuclei_adapter.py
    test_dast_routing.py
    test_scan_request.py
```

### Pattern 1: Nuclei Adapter (follows gosec pattern exactly)
**What:** Subclass `ScannerAdapter`, parse JSONL output, map to `FindingSchema`
**When to use:** This is the only pattern for adding scanner tools
**Example:**
```python
# Source: existing gosec.py adapter pattern + Nuclei JSONL output
import json
from scanner.adapters.base import ScannerAdapter
from scanner.core.exceptions import ScannerExecutionError
from scanner.core.fingerprint import compute_fingerprint
from scanner.schemas.finding import FindingSchema
from scanner.schemas.severity import Severity

NUCLEI_SEVERITY_MAP: dict[str, Severity] = {
    "critical": Severity.CRITICAL,
    "high": Severity.HIGH,
    "medium": Severity.MEDIUM,
    "low": Severity.LOW,
    "info": Severity.INFO,
}

class NucleiAdapter(ScannerAdapter):
    @property
    def tool_name(self) -> str:
        return "nuclei"

    def _version_command(self) -> list[str]:
        return ["nuclei", "-version"]

    async def run(self, target_path: str, timeout: int,
                  extra_args: list[str] | None = None) -> list[FindingSchema]:
        # target_path is the URL for DAST scans
        cmd = ["nuclei", "-u", target_path, "-jsonl", "-silent",
               "-omit-raw", "-omit-template"]
        if extra_args:
            cmd.extend(extra_args)

        stdout, stderr, returncode = await self._execute(cmd, timeout)

        # Nuclei exit code 0 for success (with or without findings)
        if returncode != 0:
            raise ScannerExecutionError(
                self.tool_name, stderr or "unknown error", returncode
            )

        findings: list[FindingSchema] = []
        for line in stdout.strip().splitlines():
            if not line.strip():
                continue
            event = json.loads(line)
            # ... parse event into FindingSchema
        return findings
```

### Pattern 2: DAST Routing in Orchestrator
**What:** Conditional adapter selection based on `target_url` presence
**When to use:** In `run_scan()` to dispatch DAST vs SAST
**Example:**
```python
# In orchestrator.py run_scan():
# If target_url provided, only run nuclei adapter against URL
# If target_url absent, run SAST adapters as usual (nuclei skipped)
if target_url:
    # DAST mode: only nuclei
    registry = ScannerRegistry(settings.scanners)
    nuclei_config = registry.get_scanner_config("nuclei")
    if nuclei_config and nuclei_config.adapter_class:
        adapter = nuclei_config.adapter_class()
        # Pass target_url as target_path (adapter uses -u flag)
        results = await _run_adapter(adapter, target_url, ...)
else:
    # SAST mode: language-based detection, existing flow
    ...
```

### Pattern 3: ScanRequest Validator Update
**What:** Add optional `target_url` field, update validation logic
**When to use:** API schema modification
**Example:**
```python
class ScanRequest(BaseModel):
    path: str | None = None
    repo_url: str | None = None
    branch: str | None = None
    target_url: str | None = None  # NEW: DAST target URL
    skip_ai: bool = False

    @model_validator(mode="after")
    def validate_target(self) -> "ScanRequest":
        if self.target_url:
            # DAST mode -- path and repo_url must be absent
            if self.path or self.repo_url:
                raise ValueError(
                    'target_url cannot be combined with "path" or "repo_url".'
                )
            return self
        # Existing SAST validation
        if self.path and self.repo_url:
            raise ValueError('Provide either "path" or "repo_url", not both.')
        if not self.path and not self.repo_url:
            raise ValueError(
                'Provide "path", "repo_url", or "target_url".'
            )
        return self
```

### Anti-Patterns to Avoid
- **Creating a separate DAST API endpoint:** The decision is to use the existing scan endpoint with `target_url` field -- do NOT create `/api/dast/scans`
- **Adding new FindingSchema fields for DAST:** Use `file_path` for the matched URL, `rule_id` for template-id -- no schema changes
- **Running Nuclei alongside SAST tools:** When `target_url` is provided, ONLY Nuclei runs; when absent, Nuclei is skipped
- **Downloading templates at runtime:** Templates are baked into Docker image at build time via `nuclei -update-templates`

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSONL parsing | Custom streaming parser | `stdout.splitlines()` + `json.loads()` per line | Nuclei outputs one JSON object per line; simple line splitting is sufficient |
| Severity mapping | Custom severity logic | Direct enum map from Nuclei's severity strings | Nuclei uses exact same severity names (info/low/medium/high/critical) |
| Fingerprint computation | New hash function | `compute_fingerprint(matched_at_url, template_id, snippet)` | Existing function handles all normalization |
| URL validation | Custom regex | `urllib.parse.urlparse` or Pydantic `HttpUrl` | Standard library handles edge cases |
| Multi-arch Docker | Runtime arch detection | Docker `TARGETARCH` build arg | Standard Docker BuildKit feature, already used conceptually by other tools |

**Key insight:** The entire adapter infrastructure exists. This phase is 90% following established patterns and 10% orchestrator routing logic.

## Common Pitfalls

### Pitfall 1: Nuclei JSONL vs JSON Output
**What goes wrong:** Using `-json` flag produces a different format than `-jsonl`; some versions output to stderr
**Why it happens:** Nuclei has multiple output modes; `-jsonl` writes to stdout, `-j` is an alias
**How to avoid:** Use `-jsonl` flag explicitly. Add `-silent` to suppress banner/progress output to stdout. Use `-omit-raw` and `-omit-template` to reduce output size.
**Warning signs:** Parsing errors, empty stdout, banner text mixed with JSON

### Pitfall 2: Nuclei Exit Codes
**What goes wrong:** Assuming exit code 1 means "findings found" (like gosec)
**Why it happens:** Different tools have different exit code conventions
**How to avoid:** Nuclei returns exit code 0 for successful execution regardless of findings count. Non-zero exit codes indicate actual errors. Do NOT treat exit code 1 as "findings found with success" -- treat any non-zero as error.
**Warning signs:** `ScannerExecutionError` raised when findings exist

### Pitfall 3: ScanRequest Validator Breakage
**What goes wrong:** Adding `target_url` breaks the existing SAST validation that requires either `path` or `repo_url`
**Why it happens:** Current validator uses strict either/or logic
**How to avoid:** Update validator to handle three-way logic: target_url (DAST), path (local SAST), or repo_url (remote SAST) -- mutually exclusive
**Warning signs:** 422 validation errors on DAST requests

### Pitfall 4: Orchestrator target_path Reuse
**What goes wrong:** Passing URL as `target_path` parameter to `run_scan()` triggers git clone or language detection on a URL string
**Why it happens:** `run_scan()` currently assumes `target_path` is a filesystem path
**How to avoid:** Add a new `target_url` parameter to `run_scan()` with separate DAST flow that bypasses language detection, git clone, and SAST adapter selection
**Warning signs:** FileNotFoundError on URL string, git clone failure

### Pitfall 5: Nuclei Template Update Network Dependency
**What goes wrong:** Container fails to start or scan fails because templates need updating
**Why it happens:** Templates not baked into image, runtime `nuclei -update-templates` fails without network
**How to avoid:** Run `nuclei -update-templates` during Docker build. Templates are stored in `~/.local/nuclei-templates/` (or `/home/scanner/.local/nuclei-templates/` for the scanner user). Ensure the build runs as the correct user or copies templates to the right location.
**Warning signs:** "no templates found" error at runtime

### Pitfall 6: Docker Build Runs as Root but App Runs as scanner User
**What goes wrong:** Templates downloaded during build as root are not accessible by the scanner user
**Why it happens:** `nuclei -update-templates` stores in `$HOME/.local/nuclei-templates/`; root's home vs scanner's home differ
**How to avoid:** Either run template update as scanner user, or explicitly set `NUCLEI_TEMPLATES` env var, or copy templates to a shared location. Consider running `nuclei -update-templates` before `USER scanner` and then copying the template dir.
**Warning signs:** "no templates loaded" at runtime despite build succeeding

### Pitfall 7: Zip vs Tar.gz Format
**What goes wrong:** Using `tar xz` to extract Nuclei binary (like other tools in the Dockerfile)
**Why it happens:** Copy-pasting from gitleaks/trivy/gosec patterns which use tar.gz; Nuclei uses zip
**How to avoid:** Use `unzip` instead of `tar`. Add `unzip` to apt-get install if not present.
**Warning signs:** `tar: Error is not recoverable: exiting now`

## Code Examples

### Nuclei JSONL Output Structure (Single Finding)
```json
{
  "template-id": "nginx-version",
  "info": {
    "name": "nginx version detect",
    "author": ["philippedelteil"],
    "tags": ["tech", "nginx"],
    "description": "Some nginx servers have the version on the response header.",
    "reference": null,
    "severity": "info"
  },
  "type": "http",
  "host": "http://example.com",
  "matched-at": "http://example.com/",
  "extracted-results": ["nginx/1.19.0"],
  "ip": "93.184.216.34",
  "timestamp": "2024-05-03T15:24:45.78543+05:30",
  "curl-command": "curl -X 'GET' ...",
  "matcher-status": true,
  "matched-line": null
}
```

### Field Mapping to FindingSchema
```python
# Source: CONTEXT.md locked decisions + Nuclei output structure
def _parse_event(self, event: dict) -> FindingSchema:
    template_id = event.get("template-id", "unknown")
    info = event.get("info", {})
    matched_at = event.get("matched-at", event.get("host", ""))
    severity_str = info.get("severity", "info").lower()
    severity = NUCLEI_SEVERITY_MAP.get(severity_str, Severity.INFO)

    # Snippet: extracted results or matched line
    extracted = event.get("extracted-results") or []
    matched_line = event.get("matched-line")
    snippet = "\n".join(extracted) if extracted else (matched_line or "")

    fingerprint = compute_fingerprint(matched_at, template_id, snippet)

    return FindingSchema(
        fingerprint=fingerprint,
        tool=self.tool_name,
        rule_id=template_id,
        file_path=matched_at,  # URL stored in file_path per decision
        line_start=None,       # No line numbers for DAST
        line_end=None,
        snippet=snippet or None,
        severity=severity,
        title=info.get("name", template_id),
        description=info.get("description"),
    )
```

### Config.yml Entry
```yaml
scanners:
  # ... existing SAST scanners ...
  nuclei:
    enabled: true  # Always enabled (not "auto" -- no language detection for DAST)
    timeout: 300   # DAST scans can be slower than SAST
    extra_args: []  # e.g. ["-tags", "cve,exposure", "-severity", "medium,high,critical"]
    adapter_class: "scanner.adapters.nuclei.NucleiAdapter"
    languages: []  # Not language-dependent
```

### Dockerfile Nuclei Installation
```dockerfile
# Install nuclei (DAST scanner) -- NOTE: uses zip not tar.gz
# Requires: unzip package in apt-get install
ARG TARGETARCH
RUN curl -sSL "https://github.com/projectdiscovery/nuclei/releases/download/v3.7.1/nuclei_3.7.1_linux_${TARGETARCH}.zip" \
    -o /tmp/nuclei.zip && \
    unzip -o /tmp/nuclei.zip -d /usr/local/bin nuclei && \
    chmod +x /usr/local/bin/nuclei && \
    rm /tmp/nuclei.zip

# Update templates before switching to non-root user
RUN nuclei -update-templates
```

### ScanQueue Worker Update
```python
# scan_queue.py needs to pass target_url to run_scan
# Read from ScanResult model (needs target_url column or reuse target_path)
target_url = db_scan.target_url  # new field, or None for SAST

scan_result, findings, compound_risks = await run_scan(
    app.state.settings,
    target_path=target_path if not target_url else None,
    repo_url=repo_url if not target_url else None,
    branch=branch if not target_url else None,
    target_url=target_url,  # new parameter
    persist=False,
    progress_callback=_progress_cb,
    skip_ai=skip_ai,
)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Nuclei v2.x | Nuclei v3.x (currently v3.7.1) | 2023 | v3 has improved output format, better template engine, Go module path changed |
| Separate JSON flag (`-json`) | JSONL flag (`-jsonl`) | v2.5+ | JSONL is the standard output format; one event per line |
| ZAP for DAST | Nuclei | Project decision | 30MB vs 500MB+; CLI-native; template-driven |

**Deprecated/outdated:**
- Nuclei v2.x: no longer maintained; v3.x is current
- `-json` flag: still works but `-jsonl` is preferred for parsing

## Open Questions

1. **ScanResult Model: target_url Storage**
   - What we know: `ScanResult` has `target_path` (String 500). For DAST, we need to store the target URL.
   - What's unclear: Should we add a dedicated `target_url` column or reuse `target_path` for URLs?
   - Recommendation: Add a `target_url` column to `ScanResult` for clarity. The `target_path` field has SAST semantics (filesystem path). A new column avoids ambiguity and makes querying DAST vs SAST scans straightforward. Requires an Alembic migration.

2. **Nuclei Version Output Format**
   - What we know: `nuclei -version` prints version info
   - What's unclear: Exact output format for parsing (may include extra text like "ProjectDiscovery Nuclei v3.7.1")
   - Recommendation: Use `_version_command` returning `["nuclei", "-version"]` and strip/parse the output. Non-critical -- worst case shows "unknown".

3. **URL Validation Layer**
   - What we know: `target_url` needs basic URL format validation
   - What's unclear: Whether to validate in API schema (Pydantic) or adapter
   - Recommendation: Validate in API layer using Pydantic `HttpUrl` type or a custom validator on `ScanRequest`. This fails fast with a 422 before any scanning begins. The adapter should not need to validate URL format.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `python -m pytest tests/phase_13/ -x -q` |
| Full suite command | `python -m pytest tests/ -x -q` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DAST-01 | NucleiAdapter parses JSONL output into FindingSchema list with correct field mapping | unit | `python -m pytest tests/phase_13/test_nuclei_adapter.py -x` | Wave 0 |
| DAST-01 | Severity mapping (info/low/medium/high/critical) maps correctly to Severity enum | unit | `python -m pytest tests/phase_13/test_nuclei_adapter.py::test_severity_mapping -x` | Wave 0 |
| DAST-01 | Fingerprint computed from matched-at URL + template-id + snippet | unit | `python -m pytest tests/phase_13/test_nuclei_adapter.py::test_fingerprint -x` | Wave 0 |
| DAST-01 | Nuclei execution error raises ScannerExecutionError | unit | `python -m pytest tests/phase_13/test_nuclei_adapter.py::test_execution_error -x` | Wave 0 |
| DAST-02 | ScanRequest accepts target_url and rejects invalid combinations | unit | `python -m pytest tests/phase_13/test_scan_request.py -x` | Wave 0 |
| DAST-02 | Orchestrator routes to Nuclei adapter when target_url provided | unit | `python -m pytest tests/phase_13/test_dast_routing.py -x` | Wave 0 |
| DAST-02 | Orchestrator skips Nuclei and runs SAST when target_url absent | unit | `python -m pytest tests/phase_13/test_dast_routing.py::test_sast_mode -x` | Wave 0 |
| DAST-03 | Nuclei binary installation in Dockerfile (manual Docker build verification) | manual-only | N/A -- requires Docker build | N/A |
| DAST-04 | Nuclei findings with tool="nuclei" render in HTML report template | manual-only | N/A -- visual verification | N/A |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/phase_13/ -x -q`
- **Per wave merge:** `python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/phase_13/__init__.py` -- package init
- [ ] `tests/phase_13/conftest.py` -- shared fixtures (sample JSONL output, mock subprocess)
- [ ] `tests/phase_13/fixtures/nuclei_output.jsonl` -- sample Nuclei JSONL output
- [ ] `tests/phase_13/test_nuclei_adapter.py` -- covers DAST-01
- [ ] `tests/phase_13/test_scan_request.py` -- covers DAST-02 (API schema validation)
- [ ] `tests/phase_13/test_dast_routing.py` -- covers DAST-02 (orchestrator routing)

## Sources

### Primary (HIGH confidence)
- Existing codebase: `src/scanner/adapters/gosec.py` -- reference adapter implementation
- Existing codebase: `src/scanner/adapters/base.py` -- ScannerAdapter contract
- Existing codebase: `src/scanner/adapters/registry.py` -- plugin registration
- Existing codebase: `src/scanner/core/orchestrator.py` -- run_scan() dispatch logic
- Existing codebase: `src/scanner/api/schemas.py` -- ScanRequest model
- GitHub API: `https://api.github.com/repos/projectdiscovery/nuclei/releases/latest` -- v3.7.1 confirmed with linux_amd64.zip and linux_arm64.zip assets

### Secondary (MEDIUM confidence)
- [ProjectDiscovery Nuclei Running Docs](https://docs.projectdiscovery.io/opensource/nuclei/running) -- CLI flags (-jsonl, -u, -tags, -severity, -silent, -omit-raw)
- [Nuclei GitHub Issue #5086](https://github.com/projectdiscovery/nuclei/issues/5086) -- Exit code behavior (0 = success, non-zero = error)
- [Bugcrowd Nuclei Guide](https://www.bugcrowd.com/blog/the-ultimate-beginners-guide-to-nuclei/) -- JSONL output structure example
- [Nuclei GitHub Repository](https://github.com/projectdiscovery/nuclei) -- General reference

### Tertiary (LOW confidence)
- Nuclei JSONL field completeness: based on web examples; actual v3.7.1 output may have additional or renamed fields. Recommend capturing real output in test fixtures during implementation.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- Nuclei v3.7.1 verified via GitHub API, single binary, well-documented CLI
- Architecture: HIGH -- follows exact same adapter pattern as 12 existing adapters in the codebase
- Pitfalls: HIGH -- identified from codebase analysis (exit codes, zip format, Docker user context, validator logic)
- JSONL output format: MEDIUM -- based on web examples, needs validation with actual binary output

**Research date:** 2026-03-23
**Valid until:** 2026-04-23 (stable -- Nuclei releases monthly but adapter pattern is version-independent)
