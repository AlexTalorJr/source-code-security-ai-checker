# Phase 4: Reports and Quality Gate - Research

**Researched:** 2026-03-19
**Domain:** Report generation (HTML/PDF), quality gate configuration, scan history delta comparison
**Confidence:** HIGH

## Summary

Phase 4 adds three major capabilities: (1) interactive HTML reports with severity grouping, filtering, and AI fix suggestions, (2) formal PDF reports for management with charts, and (3) delta comparison showing new/fixed/persisting findings between scans. The existing codebase already has all the data models (`ScanResultSchema`, `FindingSchema`, `CompoundRiskSchema`), SQLite persistence with fingerprint-indexed findings, and a basic quality gate (hardcoded Critical+High check). This phase enhances the gate to be configurable and adds report generation as a new layer after `run_scan()`.

The tech stack is well-established: Jinja2 for HTML templating (already a transitive dependency via FastAPI), WeasyPrint for HTML-to-PDF conversion, and matplotlib with the Agg backend for server-side chart generation. WeasyPrint requires system library additions to the Docker image (`libpango-1.0-0`, `libpangoft2-1.0-0`, `libharfbuzz-subset0`). All report generation is synchronous (CPU-bound rendering), so it runs after the async scan pipeline completes.

**Primary recommendation:** Build a `src/scanner/reports/` module with separate HTML and PDF generators, both consuming `ScanResultSchema` + findings + compound risks. Use Jinja2 templates with inlined CSS/JS for the self-contained HTML report. Use WeasyPrint to render a separate PDF-specific HTML template to PDF. Add a `GateConfig` to `ScannerSettings` for configurable thresholds. Implement delta comparison as a database query module that compares fingerprints between the current and most recent previous scan of the same branch.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- HTML report layout: Severity-first grouping (Critical > High > Medium > Low > Info), each finding shows component/tool tags, AI fix suggestions as side-by-side diff (before/after code blocks with syntax highlighting, GitHub PR diff style), single self-contained HTML file with all CSS/JS inlined, left sidebar with checkbox filters for severity/tool/component with instant update and count badges
- PDF report structure: Management audience, non-technical language, executive summary first, pie chart for severity + bar chart for findings per tool, findings as summary table only (severity/file/rule/one-line description), 3-5 pages concise, English only (bilingual is v2 ADV-02)
- Quality gate configurability: `gate.fail_on: [critical, high]` severity list, `gate.include_compound_risks: true/false` toggle (default true), gate decision (PASSED/FAILED) prominently at top of both reports showing which thresholds triggered failure
- Delta comparison: Compare to most recent previous scan of same branch (automatic), matching by existing SHA-256 fingerprint, HTML report gets dedicated delta section at top with colored badges, CLI gets one-line delta summary after severity table
- Gate PASSED/FAILED should be the first thing visible in both report types
- Delta section at top of HTML mirrors security team triage workflow

### Claude's Discretion
- HTML template framework choice (Jinja2 assumed from PROJECT.md tech stack)
- PDF generation library (WeasyPrint assumed from PROJECT.md tech stack)
- Chart generation library (matplotlib, plotly, or SVG generation)
- CSS styling, color scheme, typography for HTML report
- Exact sidebar filter implementation (vanilla JS vs lightweight library)
- PDF page layout, margins, fonts
- Delta section visual design

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| RPT-01 | HTML interactive report with findings grouped by severity, filterable by component/tool | Jinja2 template with inlined vanilla JS for checkbox filters; severity-grouped sections |
| RPT-02 | HTML report shows code context with line numbers and AI fix suggestions | FindingSchema has snippet, line_start/end, ai_fix_suggestion; render as syntax-highlighted diff blocks |
| RPT-03 | PDF formal report with executive summary, severity breakdown, and finding details | WeasyPrint renders PDF-specific Jinja2 template; matplotlib generates pie/bar charts as base64 PNG |
| RPT-04 | Reports include scan metadata (date, branch, commit, duration, tool versions) | ScanResultSchema already has all metadata fields; template renders them in header |
| GATE-01 | Scanner returns non-zero exit code when Critical or High findings exist | CLI already exits with code 1 on gate failure; enhance with configurable thresholds |
| GATE-02 | Severity thresholds configurable in config.yml | New GateConfig pydantic model in ScannerSettings with fail_on severity list |
| GATE-03 | Quality gate decision included in scan output and reports | gate_passed already in ScanResultSchema; add fail_reasons list for report display |
| HIST-01 | All scan results stored in SQLite database with full finding details | Already implemented -- ScanResult + Finding ORM models with full persistence in orchestrator |
| HIST-02 | Delta comparison between current and previous scan (new/fixed/persisting findings) | Query previous scan by branch, compare fingerprint sets, compute new/fixed/persisting |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Jinja2 | 3.1.6 | HTML/PDF template rendering | Already a transitive dep via FastAPI; industry standard for Python templating |
| WeasyPrint | 68.1 | HTML-to-PDF conversion | Best Python library for CSS-based PDF generation; renders from HTML so templates reusable |
| matplotlib | 3.10.8 | Server-side chart generation (pie/bar) | Industry standard for Python charts; Agg backend works headless in Docker |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Rich (existing) | - | CLI delta summary output | Already installed; use for colored CLI delta line |
| Typer (existing) | - | CLI report path options | Already installed; add --output-dir, --format options |
| SQLAlchemy (existing) | 2.0+ | Delta comparison queries | Already installed; query previous scan by branch |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| matplotlib | Inline SVG generation | SVG avoids a large dependency but matplotlib is more maintainable for chart complexity changes |
| WeasyPrint | fpdf2 or reportlab | fpdf2/reportlab generate PDFs directly but cannot render from HTML templates -- separate layout code needed |
| Vanilla JS filters | Alpine.js (~17KB) | Alpine.js adds reactivity but violates single-file simplicity; vanilla JS sufficient for checkbox filters |

**Recommendation for discretion areas:**
- **Template framework:** Jinja2 -- confirmed, already a project dependency
- **PDF library:** WeasyPrint -- confirmed, HTML-to-PDF approach lets us reuse Jinja2 skills
- **Chart library:** matplotlib with Agg backend -- lightweight enough for two charts, well-documented headless usage, generates PNG that embeds as base64 in both HTML and PDF
- **Sidebar filters:** Vanilla JS -- no external dependencies, keeps the HTML file self-contained, checkbox filtering is simple DOM manipulation
- **CSS styling:** Modern CSS with CSS custom properties for theming; dark header with white content area; monospace for code blocks

**Installation:**
```bash
pip install jinja2>=3.1.6 weasyprint>=68.0 matplotlib>=3.10.0
```

**Docker system dependencies (add to Dockerfile):**
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz-subset0 \
    && rm -rf /var/lib/apt/lists/*
```

## Architecture Patterns

### Recommended Project Structure
```
src/scanner/
├── reports/
│   ├── __init__.py           # Public API: generate_html_report, generate_pdf_report
│   ├── html_report.py        # HTML report generator
│   ├── pdf_report.py         # PDF report generator (uses WeasyPrint)
│   ├── charts.py             # matplotlib chart generation (pie + bar as base64 PNG)
│   ├── delta.py              # Delta comparison logic (new/fixed/persisting)
│   └── templates/
│       ├── report.html.j2    # Interactive HTML report template
│       └── report_pdf.html.j2 # PDF-specific HTML template (rendered by WeasyPrint)
├── core/
│   └── orchestrator.py       # Modified: pass findings to report generators
├── config.py                 # Modified: add GateConfig model
└── cli/
    └── main.py               # Modified: add report output options, delta CLI summary
```

### Pattern 1: Report Generator Interface
**What:** Each report generator takes the same data bundle and produces output
**When to use:** Both HTML and PDF generators consume identical data
**Example:**
```python
from dataclasses import dataclass
from scanner.schemas.finding import FindingSchema
from scanner.schemas.scan import ScanResultSchema
from scanner.schemas.compound_risk import CompoundRiskSchema

@dataclass
class ReportData:
    """Bundle of all data needed for report generation."""
    scan_result: ScanResultSchema
    findings: list[FindingSchema]
    compound_risks: list[CompoundRiskSchema]
    delta: DeltaResult | None  # None if no previous scan exists
    gate_config: GateConfig
    fail_reasons: list[str]  # Which thresholds triggered failure

def generate_html_report(data: ReportData, output_path: str) -> str:
    """Generate self-contained HTML report. Returns the file path."""
    ...

def generate_pdf_report(data: ReportData, output_path: str) -> str:
    """Generate PDF report via WeasyPrint. Returns the file path."""
    ...
```

### Pattern 2: Delta Comparison via Fingerprint Sets
**What:** Compare current scan fingerprints against previous scan of same branch
**When to use:** Every scan that has a previous scan on the same branch
**Example:**
```python
from dataclasses import dataclass

@dataclass
class DeltaResult:
    """Result of comparing current scan to previous scan."""
    new_fingerprints: set[str]      # In current, not in previous
    fixed_fingerprints: set[str]    # In previous, not in current
    persisting_fingerprints: set[str]  # In both
    previous_scan_id: int | None

async def compute_delta(
    current_findings: list[FindingSchema],
    branch: str,
    current_scan_id: int,
    db_path: str,
) -> DeltaResult:
    """Query previous scan by branch, compare fingerprint sets."""
    current_fps = {f.fingerprint for f in current_findings}
    # Query: SELECT fingerprint FROM findings WHERE scan_id = (
    #   SELECT id FROM scans WHERE branch = ? AND id != ?
    #   ORDER BY created_at DESC LIMIT 1
    # )
    previous_fps = await _get_previous_fingerprints(branch, current_scan_id, db_path)
    return DeltaResult(
        new_fingerprints=current_fps - previous_fps,
        fixed_fingerprints=previous_fps - current_fps,
        persisting_fingerprints=current_fps & previous_fps,
        previous_scan_id=...,
    )
```

### Pattern 3: Configurable Quality Gate
**What:** Gate configuration as a Pydantic model in settings
**When to use:** Replaces the hardcoded Critical+High check in orchestrator
**Example:**
```python
from scanner.schemas.severity import Severity

class GateConfig(BaseModel):
    """Quality gate configuration."""
    fail_on: list[str] = ["critical", "high"]  # Severity names
    include_compound_risks: bool = True

    def evaluate(
        self,
        severity_counts: dict[Severity, int],
        compound_risks: list[CompoundRiskSchema],
    ) -> tuple[bool, list[str]]:
        """Returns (passed, fail_reasons)."""
        reasons = []
        for sev_name in self.fail_on:
            sev = Severity[sev_name.upper()]
            count = severity_counts.get(sev, 0)
            if count > 0:
                reasons.append(f"{count} {sev.name} finding(s)")
        if self.include_compound_risks:
            for cr in compound_risks:
                sev = Severity(cr.severity)
                if sev.name.lower() in self.fail_on:
                    reasons.append(f"Compound risk: {cr.title} ({sev.name})")
        return (len(reasons) == 0, reasons)
```

### Pattern 4: Chart Generation as Base64 PNG
**What:** Generate charts in memory, encode as base64 for embedding
**When to use:** Both HTML and PDF reports need inline charts
**Example:**
```python
import base64
import io
import matplotlib
matplotlib.use("Agg")  # MUST be before pyplot import
import matplotlib.pyplot as plt

def generate_severity_pie_chart(counts: dict[str, int]) -> str:
    """Generate severity pie chart, return as base64 PNG data URI."""
    fig, ax = plt.subplots(figsize=(4, 4))
    labels = [k for k, v in counts.items() if v > 0]
    values = [v for v in counts.values() if v > 0]
    colors = {"Critical": "#dc3545", "High": "#fd7e14", "Medium": "#ffc107", "Low": "#28a745", "Info": "#6c757d"}
    ax.pie(values, labels=labels, colors=[colors.get(l, "#999") for l in labels], autopct="%1.0f%%")
    ax.set_title("Severity Distribution")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return f"data:image/png;base64,{base64.b64encode(buf.read()).decode()}"
```

### Anti-Patterns to Avoid
- **Generating PDF from the interactive HTML:** The interactive HTML has JS filters, sidebars, etc. that make poor PDF output. Use a separate simpler template for PDF.
- **Storing report files in SQLite:** Reports are output artifacts, not data. Write to filesystem, store path in scan result if needed.
- **Synchronous DB queries in report generation:** Delta computation uses async SQLAlchemy -- keep it async and compute before passing to synchronous report renderers.
- **plt.show() in headless environment:** Never call `plt.show()` -- always use `fig.savefig()` with the Agg backend.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTML-to-PDF rendering | Custom PDF layout code | WeasyPrint | CSS-based PDF from HTML is dramatically simpler than imperative PDF construction |
| Chart generation | SVG path string building | matplotlib + Agg | Chart libraries handle axes, labels, legends, proportions correctly |
| HTML template rendering | f-string concatenation | Jinja2 | Autoescaping prevents XSS, template inheritance, loop/filter support |
| Syntax highlighting in HTML | Custom regex colorizer | CSS class-based highlighting | Simple `<pre><code>` with CSS classes; or Pygments if needed later |
| Fingerprint set comparison | Manual loop iteration | Python set operations | `current - previous`, `previous - current`, `current & previous` |

**Key insight:** Report generation is presentation-layer work. Use mature rendering libraries and keep the logic in data preparation, not in output formatting.

## Common Pitfalls

### Pitfall 1: WeasyPrint System Dependencies in Docker
**What goes wrong:** `pip install weasyprint` succeeds but rendering fails at runtime with missing shared library errors (libpango, libharfbuzz)
**Why it happens:** WeasyPrint's Python wheel installs fine, but it dynamically links to system C libraries at render time
**How to avoid:** Add `libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0` to the Dockerfile's apt-get install step. Test PDF generation in Docker specifically, not just locally.
**Warning signs:** `OSError: cannot load library` or `ImportError` mentioning gobject/pango at runtime

### Pitfall 2: matplotlib Backend Not Set Before pyplot Import
**What goes wrong:** `matplotlib.use('Agg')` has no effect or raises error
**Why it happens:** pyplot was imported before `matplotlib.use('Agg')` -- the backend is locked at first pyplot import
**How to avoid:** Set `matplotlib.use("Agg")` at the top of charts.py, before any `import matplotlib.pyplot as plt`
**Warning signs:** Warnings about Tcl/Tk, DISPLAY variable, or GUI backend errors in Docker logs

### Pitfall 3: Memory Leak from Unclosed matplotlib Figures
**What goes wrong:** Memory usage grows with each scan
**Why it happens:** matplotlib figures persist in memory until explicitly closed
**How to avoid:** Always call `plt.close(fig)` after `savefig()`. Use `try/finally` pattern.
**Warning signs:** Growing memory usage across multiple scans in long-running process

### Pitfall 4: Delta Comparison on First Scan
**What goes wrong:** Delta section crashes or shows confusing data when there is no previous scan
**Why it happens:** No previous scan exists for this branch (first scan ever)
**How to avoid:** `DeltaResult` should be `None` when no previous scan exists. Templates must handle `{% if delta %}` gracefully. All findings are implicitly "new" on first scan.
**Warning signs:** SQL query returns empty results, NoneType errors

### Pitfall 5: Large HTML Report File Size
**What goes wrong:** Reports become multi-MB with hundreds of findings and inlined code snippets
**Why it happens:** Inlining all CSS/JS plus rendering hundreds of code blocks with syntax highlighting
**How to avoid:** Keep CSS/JS minimal (~10KB). Truncate very long snippets (limit to ~20 lines). Pagination or virtual scrolling only if needed in v2.
**Warning signs:** HTML file exceeds 5MB, browser sluggish on open

### Pitfall 6: Jinja2 Autoescaping Off
**What goes wrong:** Code snippets from scanned files contain HTML-like content that breaks report layout
**Why it happens:** Jinja2 does not autoescape by default when you create `Environment()` manually
**How to avoid:** Always use `Environment(autoescape=select_autoescape(["html"]))` or `autoescape=True`
**Warning signs:** Broken HTML in report when scanning files containing `<script>`, `<div>`, etc.

### Pitfall 7: Gate Config Overriding Existing Behavior
**What goes wrong:** Changing gate logic breaks existing tests that expect hardcoded Critical+High behavior
**Why it happens:** Orchestrator currently hardcodes gate logic at lines 205-210
**How to avoid:** Default `GateConfig(fail_on=["critical", "high"], include_compound_risks=True)` produces identical behavior to current hardcoded logic. Existing tests pass without changes.
**Warning signs:** Existing phase 02/03 tests fail after config change

## Code Examples

### Self-Contained HTML Template Structure
```html
{# report.html.j2 #}
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Security Scan Report - {{ scan.branch or scan.target_path }}</title>
    <style>
        /* All CSS inlined for portability */
        :root {
            --critical: #dc3545;
            --high: #fd7e14;
            --medium: #ffc107;
            --low: #28a745;
            --info: #6c757d;
        }
        /* ... layout, sidebar, finding cards, diff blocks ... */
    </style>
</head>
<body>
    <header>
        <div class="gate-badge gate-{{ 'passed' if scan.gate_passed else 'failed' }}">
            {{ 'PASSED' if scan.gate_passed else 'FAILED' }}
        </div>
        {% if fail_reasons %}
        <ul class="fail-reasons">
            {% for reason in fail_reasons %}
            <li>{{ reason }}</li>
            {% endfor %}
        </ul>
        {% endif %}
    </header>

    {% if delta %}
    <section class="delta-summary">
        <span class="badge new">{{ delta.new | length }} new</span>
        <span class="badge fixed">{{ delta.fixed | length }} fixed</span>
        <span class="badge persisting">{{ delta.persisting | length }} persisting</span>
    </section>
    {% endif %}

    <aside class="sidebar">
        <!-- Checkbox filters with counts -->
    </aside>

    <main>
        {% for severity_name, severity_findings in findings_by_severity.items() %}
        <section class="severity-group" data-severity="{{ severity_name }}">
            <h2>{{ severity_name }} ({{ severity_findings | length }})</h2>
            {% for finding in severity_findings %}
            <div class="finding-card" data-tool="{{ finding.tool }}" data-component="{{ finding.file_path.split('/')[0] }}">
                <!-- Finding details, code context, AI fix -->
            </div>
            {% endfor %}
        </section>
        {% endfor %}
    </main>

    <script>
        // Vanilla JS: checkbox filter logic
        document.querySelectorAll('.filter-checkbox').forEach(cb => {
            cb.addEventListener('change', () => { /* filter findings */ });
        });
    </script>
</body>
</html>
```

### Vanilla JS Sidebar Filter Logic
```javascript
// Inlined in report.html.j2
(function() {
    const findings = document.querySelectorAll('.finding-card');
    const filterGroups = {
        severity: new Set(),
        tool: new Set(),
        component: new Set()
    };

    // Initialize: all checked
    document.querySelectorAll('.filter-checkbox').forEach(cb => {
        filterGroups[cb.dataset.group].add(cb.value);
        cb.addEventListener('change', function() {
            if (this.checked) filterGroups[this.dataset.group].add(this.value);
            else filterGroups[this.dataset.group].delete(this.value);
            applyFilters();
        });
    });

    function applyFilters() {
        findings.forEach(card => {
            const show = filterGroups.severity.has(card.dataset.severity)
                && filterGroups.tool.has(card.dataset.tool)
                && filterGroups.component.has(card.dataset.component);
            card.style.display = show ? '' : 'none';
        });
        updateCounts();
    }

    function updateCounts() {
        // Update badge counts based on visible findings
    }
})();
```

### WeasyPrint PDF Generation
```python
# Source: WeasyPrint official docs
from weasyprint import HTML

def generate_pdf_report(data: ReportData, output_path: str) -> str:
    """Render PDF from a dedicated PDF template via WeasyPrint."""
    env = Environment(
        loader=PackageLoader("scanner.reports", "templates"),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("report_pdf.html.j2")

    # Pre-generate charts as base64 data URIs
    pie_chart = generate_severity_pie_chart(data.scan_result)
    bar_chart = generate_tool_bar_chart(data.findings)

    html_content = template.render(
        scan=data.scan_result,
        findings=data.findings,
        compound_risks=data.compound_risks,
        delta=data.delta,
        pie_chart=pie_chart,
        bar_chart=bar_chart,
        gate_config=data.gate_config,
        fail_reasons=data.fail_reasons,
    )

    HTML(string=html_content).write_pdf(output_path)
    return output_path
```

### Delta Query
```python
from sqlalchemy import select, desc
from scanner.models.scan import ScanResult
from scanner.models.finding import Finding

async def get_previous_scan_fingerprints(
    branch: str,
    current_scan_id: int,
    session,
) -> set[str]:
    """Get fingerprints from the most recent previous scan of the same branch."""
    # Find previous scan
    prev_scan_stmt = (
        select(ScanResult.id)
        .where(ScanResult.branch == branch)
        .where(ScanResult.id != current_scan_id)
        .where(ScanResult.status == "completed")
        .order_by(desc(ScanResult.created_at))
        .limit(1)
    )
    prev_result = await session.execute(prev_scan_stmt)
    prev_scan_id = prev_result.scalar_one_or_none()

    if prev_scan_id is None:
        return set()  # First scan on this branch

    # Get all fingerprints from previous scan
    fp_stmt = (
        select(Finding.fingerprint)
        .where(Finding.scan_id == prev_scan_id)
    )
    fp_result = await session.execute(fp_stmt)
    return {row[0] for row in fp_result.fetchall()}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| ReportLab/fpdf for PDF | WeasyPrint (HTML-to-PDF) | WeasyPrint 50+ (2020+) | Templates reusable between HTML and PDF; CSS-based layout |
| Jinja2 2.x without autoescape | Jinja2 3.x with select_autoescape | Jinja2 3.0 (2021) | Security by default for HTML output |
| matplotlib pyplot global state | matplotlib OO interface (fig, ax) | Best practice since 3.0+ | Avoids global state issues in multi-threaded/concurrent usage |

**Deprecated/outdated:**
- Jinja2 < 3.1.6: CVE-2024-22195 (XSS via xmlattr filter), CVE-2025-27516 (sandbox escape via attr filter). Must use 3.1.6+.
- WeasyPrint < 60: Older versions had more system dependencies and less reliable CSS support.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `python -m pytest tests/phase_04/ -x -q` |
| Full suite command | `python -m pytest tests/ -x -q` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| RPT-01 | HTML report generated with severity grouping and filter elements | unit | `python -m pytest tests/phase_04/test_html_report.py -x` | Wave 0 |
| RPT-02 | HTML report contains code context and AI fix suggestion blocks | unit | `python -m pytest tests/phase_04/test_html_report.py::test_code_context -x` | Wave 0 |
| RPT-03 | PDF report generated with charts and executive summary | unit | `python -m pytest tests/phase_04/test_pdf_report.py -x` | Wave 0 |
| RPT-04 | Reports include metadata (date, branch, commit, duration, tool versions) | unit | `python -m pytest tests/phase_04/test_html_report.py::test_metadata -x` | Wave 0 |
| GATE-01 | Non-zero exit when findings exceed threshold | unit | `python -m pytest tests/phase_04/test_gate.py::test_exit_code -x` | Wave 0 |
| GATE-02 | Severity thresholds configurable | unit | `python -m pytest tests/phase_04/test_gate.py::test_configurable_thresholds -x` | Wave 0 |
| GATE-03 | Gate decision in output and reports | unit | `python -m pytest tests/phase_04/test_gate.py::test_gate_in_report -x` | Wave 0 |
| HIST-01 | Scan results stored in SQLite | unit | `python -m pytest tests/phase_04/test_delta.py::test_persistence -x` | Wave 0 (already covered by phase_02 tests) |
| HIST-02 | Delta comparison new/fixed/persisting | unit | `python -m pytest tests/phase_04/test_delta.py -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/phase_04/ -x -q`
- **Per wave merge:** `python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/phase_04/__init__.py` -- package init
- [ ] `tests/phase_04/conftest.py` -- shared fixtures (sample ScanResultSchema, FindingSchema list, CompoundRiskSchema list)
- [ ] `tests/phase_04/test_html_report.py` -- covers RPT-01, RPT-02, RPT-04
- [ ] `tests/phase_04/test_pdf_report.py` -- covers RPT-03
- [ ] `tests/phase_04/test_gate.py` -- covers GATE-01, GATE-02, GATE-03
- [ ] `tests/phase_04/test_delta.py` -- covers HIST-01, HIST-02
- [ ] `tests/phase_04/test_charts.py` -- covers chart generation for RPT-03

## Open Questions

1. **Findings data for reports -- how to retrieve from DB?**
   - What we know: `run_scan()` returns `ScanResultSchema` but not the full findings list (only counts). The findings are persisted to DB during `run_scan()`.
   - What's unclear: Should we modify `run_scan()` to also return findings/compound_risks, or query them back from DB after persistence?
   - Recommendation: Have `run_scan()` return a richer result that includes findings and compound_risks alongside the summary. This avoids a redundant DB round-trip. Alternatively, pass the enriched_findings list alongside ScanResultSchema back to CLI for report generation.

2. **Report output directory convention**
   - What we know: CLI needs to write HTML/PDF files somewhere
   - What's unclear: Should there be a default output directory (e.g., `./reports/`) or require explicit `--output-dir`?
   - Recommendation: Default to `./reports/` with `--output-dir` override. File naming: `scan-{scan_id}-{branch}-{date}.html` and `.pdf`.

3. **commit_hash population**
   - What we know: `ScanResultSchema.commit_hash` exists but `run_scan()` does not currently populate it (it's None)
   - What's unclear: How to get commit hash for local path scans vs repo URL scans
   - Recommendation: For repo URL scans, read HEAD after clone. For local path scans, try `git rev-parse HEAD` in target_path, fall back to None.

## Sources

### Primary (HIGH confidence)
- WeasyPrint 68.1 official docs: https://doc.courtbouillon.org/weasyprint/stable/first_steps.html -- system dependencies for Debian/Ubuntu
- matplotlib 3.10.8 official docs: https://matplotlib.org/stable/users/explain/figure/backends.html -- Agg backend usage
- Existing codebase: `src/scanner/schemas/`, `src/scanner/models/`, `src/scanner/core/orchestrator.py`, `src/scanner/cli/main.py`

### Secondary (MEDIUM confidence)
- PyPI version checks: Jinja2 3.1.6, WeasyPrint 68.1, matplotlib 3.10.8 -- verified via `pip index versions`
- Docker WeasyPrint patterns: Multiple community Dockerfiles confirm `libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0` as minimal set

### Tertiary (LOW confidence)
- None -- all findings verified against official docs or existing code

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- Jinja2/WeasyPrint/matplotlib are the established Python stack for this; confirmed in PROJECT.md tech decisions
- Architecture: HIGH -- Patterns derived from existing codebase (schemas, ORM models, config pattern)
- Pitfalls: HIGH -- WeasyPrint Docker issues are well-documented; matplotlib Agg backend is standard knowledge
- Delta comparison: HIGH -- Simple set operations on existing fingerprint infrastructure

**Research date:** 2026-03-19
**Valid until:** 2026-04-19 (stable libraries, unlikely to change)
