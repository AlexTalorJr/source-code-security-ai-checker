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

Each of the five scanner tools can be independently enabled, given a timeout, and passed extra arguments:

```yaml
scanners:
  semgrep:
    enabled: true
    timeout: 180
    extra_args: []
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

- **enabled** -- set to `false` to skip a tool entirely
- **timeout** -- maximum seconds before the tool is killed
- **extra_args** -- additional CLI arguments passed to the tool

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
