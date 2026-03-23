# Admin Guide

## Configuration

### Config Sources (Priority Order)

1. **Constructor arguments** -- programmatic overrides
2. **Environment variables** -- `SCANNER_*` prefix
3. **Dotenv file** -- `.env` file
4. **File secrets** -- Docker/K8s secrets
5. **YAML config file** -- `config.yml` (lowest priority)

### Configuration File

Copy the example and customize:

```bash
cp config.yml.example config.yml
```

## Scanner Configuration

Each of the twelve scanner tools can be independently configured with enable/disable, timeout, extra arguments, and language detection. Scanners with `enabled: "auto"` are activated automatically when matching project files are detected.

```yaml
scanners:
  semgrep:
    adapter_class: "scanner.adapters.semgrep.SemgrepAdapter"
    enabled: true
    timeout: 180
    extra_args: ["--exclude", ".venv", "--exclude", "node_modules"]
    languages: ["python", "php", "javascript", "typescript", "go", "java", "kotlin", "ruby", "csharp", "rust"]
  cppcheck:
    adapter_class: "scanner.adapters.cppcheck.CppcheckAdapter"
    enabled: true
    timeout: 120
    extra_args: ["-i.venv", "-inode_modules"]
    languages: ["cpp"]
  gitleaks:
    adapter_class: "scanner.adapters.gitleaks.GitleaksAdapter"
    enabled: true
    timeout: 120
    extra_args: []
    languages: []
  trivy:
    adapter_class: "scanner.adapters.trivy.TrivyAdapter"
    enabled: true
    timeout: 120
    extra_args: []
    languages: ["docker", "terraform", "yaml"]
  checkov:
    adapter_class: "scanner.adapters.checkov.CheckovAdapter"
    enabled: true
    timeout: 120
    extra_args: ["--skip-path", ".venv", "--skip-path", "node_modules"]
    languages: ["docker", "terraform", "yaml", "ci"]
  psalm:
    adapter_class: "scanner.adapters.psalm.PsalmAdapter"
    enabled: "auto"
    timeout: 300
    extra_args: []
    languages: ["php"]
  enlightn:
    adapter_class: "scanner.adapters.enlightn.EnlightnAdapter"
    enabled: "auto"
    timeout: 120
    extra_args: []
    languages: ["laravel"]
  php_security_checker:
    adapter_class: "scanner.adapters.php_security_checker.PhpSecurityCheckerAdapter"
    enabled: "auto"
    timeout: 30
    extra_args: []
    languages: ["php"]
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

- **adapter_class** -- fully qualified Python class implementing the scanner adapter (see Plugin Registry below)
- **enabled** -- set to `true` (always on), `false` (always off), or `"auto"` (enabled when matching files detected)
- **timeout** -- maximum seconds before the tool is killed
- **extra_args** -- additional CLI arguments passed to the tool
- **languages** -- file types that trigger auto-detection; scanners with an empty list (e.g., Gitleaks) run on all projects

## Plugin Registry

The scanner uses a config-driven plugin registry to load scanner adapters dynamically from `config.yml`. This architecture allows adding new scanners without modifying application code.

### How Scanners Are Registered

Each scanner entry in `config.yml` includes an `adapter_class` field that specifies the fully qualified Python class path implementing the `ScannerAdapter` interface. On startup, the `ScannerRegistry` reads all entries from the `scanners` section and dynamically imports each adapter class.

The `adapter_class` field follows the format:

```
scanner.adapters.<module_name>.<ClassName>
```

For example: `scanner.adapters.gosec.GosecAdapter`

### Language Auto-Detection

Scanners with a `languages` field are automatically enabled when the scanned repository contains matching files. The orchestrator detects file extensions in the target repository and activates scanners whose `languages` list overlaps with the detected languages. Scanners with an empty `languages` list (like Gitleaks) always run regardless of project type.

### Adding a New Scanner

To add a new scanner to the platform:

1. **Create an adapter class** implementing the `ScannerAdapter` interface:

```python
# src/scanner/adapters/my_scanner.py
from scanner.adapters.base import ScannerAdapter
from scanner.schemas.finding import FindingSchema

class MyScannerAdapter(ScannerAdapter):
    async def run(self, target_path: str, timeout: int, extra_args: list[str] | None = None) -> list[FindingSchema]:
        # Execute scanner binary and parse output
        ...
        return findings
```

2. **Add an entry to `config.yml`** in the `scanners` section:

```yaml
scanners:
  my_scanner:
    adapter_class: "scanner.adapters.my_scanner.MyScannerAdapter"
    enabled: "auto"
    timeout: 120
    extra_args: []
    languages: ["python"]
```

3. **Install the scanner binary** in the Dockerfile if it is an external tool.

No other code changes are required. The registry discovers and loads the new adapter automatically from the configuration.

### Listing Registered Scanners

The `/api/scanners` endpoint returns all registered scanners with their configuration:

```bash
curl -H "Authorization: Bearer nvsec_your_token" http://localhost:8000/api/scanners
```

Response includes each scanner's name, enabled status, configured languages, and adapter class.

## AI Configuration

```yaml
ai:
  max_cost_per_scan: 5.0
  model: "claude-sonnet-4-6"
  max_findings_per_batch: 50
  max_tokens_per_response: 4096
```

| Setting | Description | Default |
|---------|-------------|---------|
| `max_cost_per_scan` | Maximum USD spend on AI analysis per scan | `5.0` |
| `model` | Claude model identifier | `claude-sonnet-4-6` |
| `max_findings_per_batch` | Max findings sent to Claude in one request | `50` |
| `max_tokens_per_response` | Max response tokens from Claude | `4096` |

## Quality Gate Configuration

```yaml
gate:
  fail_on:
    - critical
    - high
  include_compound_risks: true
```

- **fail_on** -- list of severity levels that cause the gate to fail
- **include_compound_risks** -- when `true`, compound risks with matching severity also fail the gate

## Notification Configuration

### Slack

```yaml
notifications:
  slack:
    enabled: false
```

Set the webhook URL at the top level:

```yaml
slack_webhook_url: "https://hooks.slack.com/services/T.../B.../xxx"
```

Or via environment variable: `SCANNER_SLACK_WEBHOOK_URL`

### Email

```yaml
notifications:
  email:
    enabled: false
    recipients: ["security@example.com"]
    smtp_port: 587
    smtp_user: ""
    smtp_password: ""  # Use env var instead
    use_tls: true
```

Set the SMTP host at the top level:

```yaml
email_smtp_host: "smtp.example.com"
```

Or via environment variable: `SCANNER_EMAIL_SMTP_HOST`

SMTP password should use the nested env var: `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PASSWORD`

### Dashboard URL

```yaml
dashboard_url: ""  # e.g., http://scanner:8000/dashboard
```

Used in notification messages to link back to scan results. If empty, auto-derived from host and port.

## Environment Variables

All settings can be overridden with the `SCANNER_` prefix:

| Variable | Description | Default |
|----------|-------------|---------|
| `SCANNER_HOST` | Listen address | `0.0.0.0` |
| `SCANNER_PORT` | Listen port | `8000` |
| `SCANNER_DB_PATH` | SQLite database file path | `/data/scanner.db` |
| `SCANNER_API_KEY` | API authentication key | `""` (empty) |
| `SCANNER_CLAUDE_API_KEY` | Anthropic API key for AI analysis | `""` (empty) |
| `SCANNER_SLACK_WEBHOOK_URL` | Slack webhook URL | `""` |
| `SCANNER_EMAIL_SMTP_HOST` | SMTP server hostname | `""` |
| `SCANNER_LOG_LEVEL` | Log level (debug/info/warning/error) | `info` |
| `SCANNER_SCAN_TIMEOUT` | Global scan timeout in seconds | `600` |
| `SCANNER_CONFIG_PATH` | Path to YAML config file | `config.yml` |

### Nested Environment Variables

For nested config sections, use double underscores:

| Variable | Maps To |
|----------|---------|
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PASSWORD` | `notifications.email.smtp_password` |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PORT` | `notifications.email.smtp_port` |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_USER` | `notifications.email.smtp_user` |
| `SCANNER_NOTIFICATIONS__SLACK__ENABLED` | `notifications.slack.enabled` |

## Secrets Management

Never store secrets in `config.yml` or commit them to git.

```bash
# Set secrets via environment:
export SCANNER_API_KEY="your-secure-key"
export SCANNER_CLAUDE_API_KEY="sk-ant-..."

# Or in docker-compose via .env file:
echo "SCANNER_API_KEY=your-secure-key" >> .env
echo "SCANNER_CLAUDE_API_KEY=sk-ant-..." >> .env
```

## Database Management

### Location

- Docker: `/data/scanner.db` (persistent volume `scanner_data`)
- Local: configurable via `SCANNER_DB_PATH`

### WAL Mode

SQLite runs in WAL (Write-Ahead Logging) mode for concurrent read performance. This is set automatically on every connection via SQLAlchemy event listeners.

### Backup

```bash
# WAL mode allows hot backup (no need to stop scanner)
docker cp naveksoft-security-scanner-1:/data/scanner.db ./backup/
```

## Threshold Tuning

### Quality Gate

Adjust which severities fail the gate:

```yaml
gate:
  fail_on:
    - critical        # Only block on critical (relaxed)
```

Or include medium:

```yaml
gate:
  fail_on:
    - critical
    - high
    - medium           # Stricter policy
```

### Scanner Tool Management

Disable tools not relevant to your codebase:

```yaml
scanners:
  cppcheck:
    enabled: false     # No C/C++ code
  checkov:
    enabled: false     # No IaC files
```

## Performance Tuning

### Timeouts

- `scan_timeout` (global): maximum total scan duration (default: 600s)
- Per-scanner `timeout`: maximum per-tool execution time (default: 120-180s)

If scans are timing out, increase the per-tool timeout for the slow scanner rather than the global timeout.

### AI Batch Size

For large scans with many findings, adjust:

```yaml
ai:
  max_findings_per_batch: 25   # Smaller batches for faster responses
  max_tokens_per_response: 8192  # More room for detailed analysis
```

### Monitoring

```bash
# Health check
curl http://localhost:8000/api/health

# Container status
docker compose ps

# Logs
docker compose logs scanner --tail 50
```

Docker Compose performs automatic health checks every 30 seconds.

## User Management (RBAC)

Security AI Scanner uses role-based access control (RBAC) to manage user permissions. Three roles are available:

### Roles

| Action | Admin | Viewer | Scanner |
|--------|-------|--------|---------|
| Trigger scan | Yes | No | Yes (API only) |
| View results | Yes | Yes | Yes (API only) |
| Manage users | Yes | No | No |
| Configure scanners | Yes | No | No |
| Manage profiles | Yes | No | No |

- **Admin** -- full access to all features including user management, scanner configuration, and profile management
- **Viewer** -- read-only access to scan results and reports via dashboard
- **Scanner** -- API-only role for triggering scans and viewing results programmatically

### Creating Users

Users can be created in two ways:

1. **Via Dashboard** -- navigate to `/dashboard/users` (admin only) and fill in the user creation form
2. **Via environment variables** -- set `SCANNER_ADMIN_USER` and `SCANNER_ADMIN_PASSWORD` to bootstrap an admin account on first startup

Password requirements: minimum 8 characters.

### Deactivating Users

Admins can deactivate users from the dashboard or via the API (`DELETE /api/users/{id}`). Deactivated users cannot log in or use API tokens. Existing tokens for deactivated users are automatically invalidated.

## API Tokens

API tokens provide programmatic access to the scanner API using Bearer authentication.

### Generating Tokens

Navigate to `/dashboard/tokens` to manage your tokens. Click "Create Token" and provide a name for the token.

### Token Format

All tokens use the `nvsec_` prefix:

```
nvsec_a1b2c3d4e5f6...
```

### Usage

Include the token in the `Authorization` header:

```bash
curl -H "Authorization: Bearer nvsec_your_token_here" http://localhost:8000/api/scans
```

### Expiry Options

When creating a token, select an expiry period:

- 30 days
- 90 days
- 365 days
- Never (no expiration)

### Token Limits

Each user can have up to 10 active tokens (soft limit).

### Revoking Tokens

Tokens can be revoked from the dashboard (`/dashboard/tokens`) or via the API (`DELETE /api/tokens/{id}`). Revoked tokens are immediately invalidated.

## Scanner Configuration UI

The web-based scanner configuration interface allows admins to manage scanner settings, edit the raw YAML config, and manage scan profiles -- all from the dashboard.

### Accessing the Configuration UI

Navigate to `/dashboard/scanners` (admin only). The page has three tabs:

### Scanners Tab

Displays all registered scanners as cards with:

- **Enable/Disable toggle** -- switch between ON, AUTO, and OFF states
- **Timeout** -- maximum execution time in seconds (30-900)
- **Extra arguments** -- additional CLI flags passed to the scanner tool

Changes are saved individually per scanner and take effect on the next scan.

### YAML Editor Tab

A CodeMirror-powered editor for direct `config.yml` editing with:

- YAML syntax highlighting
- Full config validation before save
- Raw text preservation (formatting and comments are kept)

### Profiles Tab

Manage scan profiles (see Scan Profiles section below).

## Scan Profiles

Scan profiles are named scanner presets stored in `config.yml`. Each profile defines which scanners to run and optionally overrides per-scanner settings like timeout.

### Overview

A profile is an explicit allowlist -- only the scanners listed in the profile run when that profile is selected. Scanners not listed in the profile are disabled for that scan.

### Creating Profiles

Navigate to `/dashboard/scanners` and select the Profiles tab. Click "New Profile" and provide:

- **Name** -- letters, numbers, hyphens, and underscores only (e.g., `quick_scan`, `full-audit`)
- **Description** -- optional human-readable description
- **Scanners** -- select which scanners to include, with optional timeout overrides per scanner

### Example config.yml Profiles

```yaml
profiles:
  quick_scan:
    description: "Fast scan with essential tools only"
    scanners:
      semgrep: {}
      gitleaks: {}
  full_audit:
    description: "Comprehensive scan with all available tools"
    scanners:
      semgrep: {}
      gitleaks: {}
      trivy: {}
      checkov: {}
      cppcheck: {}
      bandit: {}
      gosec: {}
      brakeman: {}
      cargo_audit: {}
      psalm: {}
      enlightn: {}
      php_security_checker: {}
  dast_only:
    description: "DAST scan using Nuclei only"
    scanners:
      nuclei:
        timeout: 300
```

### Editing and Deleting Profiles

From the Profiles tab, click a profile card to expand the edit form. Modify settings and click Save, or click Delete to remove the profile.

### Limits

- Maximum 10 profiles (soft limit)
- Profile names must contain only letters, numbers, hyphens, and underscores
- YAML reserved words (`true`, `false`, `null`, `yes`, `no`, `on`, `off`) cannot be used as profile names

## DAST Scanning

Dynamic Application Security Testing (DAST) scans running web applications for vulnerabilities by sending HTTP requests and analyzing responses.

### Overview

DAST scanning is powered by Nuclei, a fast and configurable vulnerability scanner. Unlike SAST tools that analyze source code, DAST tests the application as a black-box by probing live endpoints.

### Configuring Nuclei

Ensure the Nuclei scanner is enabled in `config.yml`:

```yaml
scanners:
  nuclei:
    adapter_class: "scanner.adapters.nuclei.NucleiAdapter"
    enabled: true
    timeout: 300
    extra_args: []
    languages: []
```

### Triggering a DAST Scan

DAST scans require a `target_url` parameter instead of `path` or `repo_url`:

**Via API:**

```bash
curl -X POST http://localhost:8000/api/scans \
  -H "Authorization: Bearer nvsec_your_token" \
  -H "Content-Type: application/json" \
  -d '{"target_url": "https://example.com"}'
```

**Via Dashboard:** Enter the target URL in the URL field on the scan trigger form.

### DAST vs SAST

The `target_url` parameter is exclusive with `path` and `repo_url`. You cannot combine DAST and SAST targets in a single scan request.

### DAST Findings

DAST findings appear in reports alongside SAST findings. Each DAST finding includes:

- Severity level (critical, high, medium, low, info)
- Nuclei template ID identifying the vulnerability type
- The target URL where the vulnerability was found
