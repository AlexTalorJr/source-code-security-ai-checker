# User Guide

## What is Security AI Scanner?

A security scanning tool that analyzes source code for vulnerabilities using twelve parallel security scanning tools, enriches findings with AI analysis via Claude, and produces actionable reports with fix suggestions. Scanners are automatically enabled based on detected project languages.

## Supported Scanners

### Semgrep (Multi-language SAST)

**Language:** Python, PHP, JavaScript, TypeScript, Go, Java, Kotlin, Ruby, C#, Rust
**Type:** SAST
**What it detects:** Injection flaws, authentication issues, insecure patterns, and language-specific vulnerabilities across multiple languages using semantic pattern matching.
**Example finding:**
> `python.lang.security.audit.exec-detected`: Use of exec() detected at `app.py:42`

**Enabled:** Automatically when Python, PHP, JS/TS, Go, Java, Kotlin, Ruby, C#, or Rust files are detected

### cppcheck (C/C++)

**Language:** C/C++
**Type:** SAST
**What it detects:** Memory safety issues, buffer overflows, null pointer dereferences, undefined behavior, and resource leaks.
**Example finding:**
> `arrayIndexOutOfBounds`: Array index out of bounds at `buffer.cpp:15`

**Enabled:** Automatically when C/C++ files are detected

### Gitleaks (Secrets)

**Language:** All languages
**Type:** Secrets detection
**What it detects:** Hardcoded secrets, API keys, tokens, passwords, and credentials in source code and git history.
**Example finding:**
> `generic-api-key`: Generic API Key detected at `config.py:8`

**Enabled:** Always enabled for all projects

### Trivy (Infrastructure)

**Language:** Docker, Terraform, YAML/Kubernetes
**Type:** SCA / Infrastructure
**What it detects:** CVEs in container images, IaC misconfigurations, and Kubernetes security issues.
**Example finding:**
> `CVE-2023-44487`: HTTP/2 rapid reset attack in `Dockerfile:1`

**Enabled:** Automatically when Dockerfiles, Terraform, or Kubernetes YAML files are detected

### Checkov (Infrastructure)

**Language:** Docker, Terraform, YAML, CI configs
**Type:** Infrastructure
**What it detects:** Infrastructure-as-code security best practices, cloud misconfigurations, and CI pipeline security.
**Example finding:**
> `CKV_DOCKER_2`: Ensure that HEALTHCHECK instructions have been added to container images at `Dockerfile:1`

**Enabled:** Automatically when Docker, Terraform, YAML, or CI configuration files are detected

### Psalm (PHP)

**Language:** PHP
**Type:** SAST (taint analysis)
**What it detects:** SQL injection, XSS, and other taint-related vulnerabilities via data flow tracking in PHP code.
**Example finding:**
> `TaintedSql`: Detected tainted SQL in `UserController.php:34`

**Enabled:** Automatically when PHP files are detected

### Enlightn (Laravel)

**Language:** Laravel (PHP)
**Type:** SAST
**What it detects:** CSRF vulnerabilities, mass assignment, debug mode exposure, exposed .env files, and 120+ Laravel-specific security checks.
**Example finding:**
> `MassAssignmentAnalyzer`: Potential mass assignment vulnerability in `User.php:12`

**Enabled:** Automatically when a Laravel project is detected

### PHP Security Checker (PHP SCA)

**Language:** PHP (Composer)
**Type:** SCA
**What it detects:** Known CVEs in Composer dependencies by checking against the SensioLabs security advisories database.
**Example finding:**
> `CVE-2023-46734`: Twig code injection via sandbox bypass in `composer.lock`

**Enabled:** Automatically when PHP Composer files are detected

### gosec (Go SAST)

**Language:** Go
**Type:** SAST
**What it detects:** Hardcoded credentials, SQL injection, insecure cryptography, unsafe file permissions, and Go-specific security issues.
**Example finding:**
> `G101`: Potential hardcoded credentials at `config.go:22`

**Enabled:** Automatically when Go files are detected

### Bandit (Python SAST)

**Language:** Python
**Type:** SAST
**What it detects:** Hardcoded passwords, SQL injection, eval usage, weak cryptography, and Python-specific security patterns.
**Example finding:**
> `B105`: Possible hardcoded password at `settings.py:15`

**Enabled:** Automatically when Python files are detected

### Brakeman (Ruby/Rails SAST)

**Language:** Ruby / Rails
**Type:** SAST
**What it detects:** SQL injection, XSS, mass assignment, command injection, and Rails-specific vulnerabilities.
**Example finding:**
> `SQL Injection`: Possible SQL injection near line 15 in `app/models/user.rb`

**Enabled:** Automatically when Ruby files are detected

### cargo-audit (Rust SCA)

**Language:** Rust
**Type:** SCA
**What it detects:** Known vulnerable dependencies via the RustSec advisory database by auditing Cargo.lock files.
**Example finding:**
> `RUSTSEC-2019-0009`: Heap overflow in smallvec in `Cargo.lock`

**Enabled:** Automatically when Rust files are detected

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
