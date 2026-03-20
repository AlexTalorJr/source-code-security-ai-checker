# User Guide

## What is aipix-security-scanner?

A security scanning tool that analyzes source code for vulnerabilities using five parallel static analysis tools, enriches findings with AI analysis via Claude, and produces actionable reports with fix suggestions.

## Running a Scan

### Via API

```bash
curl -X POST http://localhost:8000/api/scans \
  -H "X-API-Key: $SCANNER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/your-org/repo.git", "branch": "main"}'
```

The API returns a scan ID immediately (202 Accepted). The scan runs asynchronously in the background queue.

### Via CLI

```bash
scanner scan --repo-url https://github.com/your-org/repo.git --branch main
```

The CLI executes the scan directly and prints results to stdout. Use `--format html` or `--format pdf` to generate report files.

### Via Dashboard

Navigate to `http://localhost:8000/dashboard`, fill in the repository URL and branch, then submit. The dashboard shows scan progress and results inline.

## Understanding Severity Levels

| Level | Meaning | Action |
|-------|---------|--------|
| **CRITICAL** | Immediate exploitation risk (e.g., SQL injection, RCE) | Fix immediately; blocks deployment |
| **HIGH** | Serious vulnerability (e.g., auth bypass, hardcoded secrets) | Fix before release |
| **MEDIUM** | Moderate risk (e.g., weak crypto, missing headers) | Fix in current sprint |
| **LOW** | Minor issue (e.g., verbose error messages) | Fix when convenient |
| **INFO** | Informational finding (e.g., deprecated API usage) | Review, no action needed |

## Reports

### HTML Reports

Interactive HTML reports include:

- **Summary section** -- total findings, severity breakdown, quality gate result
- **Filterable findings table** -- filter by severity, tool, file path
- **Code context** -- source code snippets with highlighted vulnerable lines
- **AI fix suggestions** -- Claude-generated fix code with explanations
- **Compound risks** -- cross-tool correlation findings identified by AI
- **Charts** -- severity distribution pie chart and findings-by-tool bar chart

Access HTML reports via `GET /api/scans/{id}/report/html` or from the dashboard.

### PDF Reports

PDF reports provide a formal document suitable for management review:

- **Executive summary** -- scan metadata, severity counts, gate result
- **Charts** -- embedded PNG charts (severity distribution, tool breakdown)
- **Detailed findings** -- grouped by severity with code snippets
- **Compound risks section** -- AI-identified cross-component vulnerabilities

Access PDF reports via `GET /api/scans/{id}/report/pdf`.

## Quality Gate

The quality gate evaluates scan results against configured severity thresholds. By default, any CRITICAL or HIGH finding causes the gate to fail.

- **pass** -- no findings at or above the configured severity threshold
- **fail** -- one or more findings at or above threshold, or compound risks with Critical/High severity when `include_compound_risks` is enabled

Quality gate results are available via `GET /api/scans/{id}/gate` and shown in reports and dashboard.

## AI Analysis

Each finding batch is sent to Claude for contextual analysis:

- **Contextual review** -- understanding what the code does and whether the finding is a true positive
- **Fix suggestions** -- concrete code changes to remediate the vulnerability
- **Compound risks** -- identification of attack chains spanning multiple findings (e.g., auth bypass + IDOR = account takeover)

AI analysis cost per scan is tracked and capped by `ai.max_cost_per_scan` in config.

## Delta Comparison

When a repository has been scanned before, the scanner automatically computes a delta:

- **New findings** -- vulnerabilities not present in the previous scan
- **Fixed findings** -- vulnerabilities from the previous scan no longer present
- **Persisting findings** -- vulnerabilities present in both scans

Delta is computed by matching fingerprints between the current and most recent previous scan of the same repository and branch. The first scan returns no delta (no previous baseline).

## Managing False Positives

### Via Dashboard

From the findings view, click the suppress button on any finding. Provide a reason for the suppression.

### Via API

```bash
curl -X POST http://localhost:8000/api/suppressions \
  -H "X-API-Key: $SCANNER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"fingerprint": "<finding-fingerprint>", "reason": "False positive: test fixture"}'
```

Suppressed findings are excluded from quality gate evaluation and flagged in reports.
