# Phase 5: API, Dashboard, CI, and Notifications - Research

**Researched:** 2026-03-19
**Domain:** REST API, server-rendered dashboard, CI integration, notifications (Slack/email), false positive management
**Confidence:** HIGH

## Summary

Phase 5 transforms the scanner from a CLI tool into a fully operational service. The codebase already has a solid FastAPI app factory with lifespan-managed async SQLAlchemy sessions, Pydantic schemas for all data contracts, and Jinja2+matplotlib for server-side rendering. The core `run_scan()` orchestrator returns `(ScanResultSchema, findings, compound_risks)` which the API layer will invoke as a background task. The `Finding` model already has a `false_positive` column (integer, default 0), and `ScannerSettings` already defines `api_key`, `slack_webhook_url`, and `email_smtp_host` fields.

The phase covers five distinct subsystems: (1) scan lifecycle API with background task execution, (2) server-rendered Jinja2 dashboard with matplotlib charts, (3) Jenkinsfile.security drop-in stage, (4) Slack + email notifications, and (5) false positive suppression by fingerprint. All subsystems integrate through the existing orchestrator, config, and database layers.

**Primary recommendation:** Build the API auth dependency and scan background task first (they unblock everything), then layer dashboard, notifications, and FP management on top. Use `asyncio.Queue` for the single-scan-at-a-time constraint with a background worker loop managed by the app lifespan.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- Server-rendered Jinja2 templates for dashboard -- reuses existing Jinja2 stack from HTML reports, no JS framework, no build step
- Three dashboard pages: scan history list, scan detail (findings/delta/gate), trends (severity over time, branch comparison)
- Dashboard authentication via API key in session cookie -- simple login page, same SCANNER_API_KEY for API and dashboard
- Charts rendered server-side with matplotlib (same approach as PDF reports) -- no JS charting library
- Background task model: POST /api/scans returns 202 with scan ID immediately, client polls GET /api/scans/{id}
- Scan status progression: queued -> running -> completed -> failed
- One scan at a time -- if a scan is running, new requests get queued status and wait
- Core API endpoints: POST /api/scans, GET /api/scans, GET /api/scans/{id}, GET /api/scans/{id}/report, GET /api/scans/{id}/findings
- Authentication: X-API-Key header on all /api/* endpoints except /api/health
- FastAPI dependency injection for auth check
- Notifications fire on every scan completion (both pass and fail)
- Slack: Rich Block Kit message with gate status emoji, severity table, branch, delta summary, dashboard link
- Email: Styled HTML with gate status banner, severity table, delta summary, dashboard link
- Email recipients in config.yml: `notifications.email.recipients: [list]`
- SMTP credentials via env vars (SCANNER_EMAIL_SMTP_HOST, SCANNER_EMAIL_SMTP_PORT, etc.)
- Both notification channels independently enable/disable via config.yml toggles
- Suppression by fingerprint globally -- marking FP suppresses across ALL future scans
- Reversible via API: PUT /api/findings/{fingerprint}/suppress, DELETE /api/findings/{fingerprint}/suppress
- Dashboard shows suppressed findings in separate tab with unsuppress button
- Suppressed findings excluded from quality gate entirely
- Optional comment/reason when marking FP
- Jenkinsfile.security stage ready to drop into existing pipelines
- Jenkins passes workspace path via API, quality gate result determines stage pass/fail
- X-API-Key via Jenkins credentials/environment variable

### Claude's Discretion
- Jinja2 template styling, CSS, dashboard layout details
- Background task implementation (asyncio.Task or simple queue)
- Slack Block Kit exact block structure
- Email HTML template design
- Suppression table schema details
- Pagination strategy for findings endpoint
- Jenkins pipeline syntax details

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| API-01 | FastAPI REST API to trigger scans (POST /api/scans with path or repo URL) | Background task pattern with asyncio.Queue; scan router module; request schema with path/repo_url/branch |
| API-02 | API returns scan status and results (GET /api/scans/{id}) | Query ScanResult ORM model; return status field (queued/running/completed/failed); include findings summary when completed |
| API-03 | API authenticated via API key in header | FastAPI Depends() with X-API-Key header extraction; compare against settings.api_key; raise 401 |
| API-05 | Live web dashboard showing scan history, finding trends, release comparison | Jinja2 templates with PackageLoader; matplotlib charts as base64 data URIs; SQLAlchemy queries for history/trends |
| API-06 | Dashboard accessible via browser with API key authentication | Session cookie auth; login page sets cookie; middleware checks cookie on /dashboard/* routes |
| CI-01 | Jenkinsfile.security stage ready to drop into existing pipelines | Declarative pipeline syntax; curl-based API calls; polling loop for scan completion |
| CI-02 | Jenkins stage passes local workspace path to scanner | POST /api/scans body with "path" field pointing to Jenkins WORKSPACE |
| CI-03 | Quality gate result determines Jenkins stage pass/fail | Poll GET /api/scans/{id} until completed; check gate_passed field; exit 1 on failure |
| NOTF-01 | Slack webhook notification on scan completion with severity summary | HTTP POST to slack_webhook_url with Block Kit JSON payload |
| NOTF-02 | Email notification on scan completion with severity summary | Python smtplib/email.mime for SMTP; Jinja2 HTML email template |
| NOTF-03 | Both notification channels independently configurable | Config toggles: notifications.slack.enabled, notifications.email.enabled in config.yml |
| HIST-03 | User can mark findings as false positive, suppressed across future scans | Suppression table keyed by fingerprint; check during gate evaluation; filter in API responses |
| HIST-04 | Scan history queryable via API (list scans, get scan details, get finding trends) | GET /api/scans with pagination; GET /api/scans/{id}; trends query grouping by date/branch |

</phase_requirements>

## Standard Stack

### Core (already installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.135.1 | REST API framework | Already in use; dependency injection for auth |
| Jinja2 | 3.1.6 | Dashboard templates + email templates | Already used for HTML/PDF reports |
| SQLAlchemy | 2.0.48 | Async ORM for scan/finding queries | Already in use with aiosqlite |
| aiosqlite | 0.22.1 | Async SQLite driver | Already in use |
| matplotlib | 3.10.8 | Server-side chart generation | Already used for report charts |
| Pydantic | 2.12.5 | Request/response schemas | Already used throughout |
| httpx | 0.28.1 | Test client + Slack webhook HTTP calls | Already in dev deps; use for Slack POST |

### Supporting (no new dependencies needed)
| Library | Purpose | When to Use |
|---------|---------|-------------|
| `smtplib` (stdlib) | SMTP email sending | Email notifications |
| `email.mime` (stdlib) | HTML email construction | Building multipart email messages |
| `asyncio.Queue` (stdlib) | Scan queue management | One-at-a-time scan execution |
| `hashlib` (stdlib) | Cookie token hashing | Dashboard session validation |
| `secrets` (stdlib) | Secure token comparison | API key timing-safe compare |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| asyncio.Queue | Celery/Redis | Massive overkill for single-scanner; adds Redis dependency |
| smtplib | aiosmtplib | Async but adds dependency; smtplib in thread pool is fine |
| matplotlib charts | Chart.js | Would require JS; violates locked decision of server-rendered only |
| Session cookies | JWT tokens | Adds complexity; cookie with API key hash is simpler for single-user |

**Installation:** No new packages needed. All dependencies already satisfied.

## Architecture Patterns

### Recommended Project Structure
```
src/scanner/
├── api/
│   ├── router.py          # Existing - add new sub-routers
│   ├── health.py          # Existing - excluded from auth
│   ├── auth.py            # NEW: API key dependency + dashboard session auth
│   ├── scans.py           # NEW: POST/GET /api/scans endpoints
│   ├── findings.py        # NEW: GET /api/scans/{id}/findings + suppress endpoints
│   └── schemas.py         # NEW: API-specific request/response schemas
├── dashboard/
│   ├── __init__.py
│   ├── router.py          # NEW: Dashboard routes (/dashboard/*)
│   ├── auth.py            # NEW: Login page, cookie management
│   └── templates/         # NEW: Jinja2 dashboard templates
│       ├── base.html.j2
│       ├── login.html.j2
│       ├── history.html.j2
│       ├── detail.html.j2
│       └── trends.html.j2
├── notifications/
│   ├── __init__.py
│   ├── service.py         # NEW: Notification dispatcher
│   ├── slack.py           # NEW: Slack Block Kit sender
│   └── email.py           # NEW: SMTP email sender
├── core/
│   ├── orchestrator.py    # Existing - run_scan() called by background worker
│   ├── scan_queue.py      # NEW: Async scan queue + background worker
│   └── suppression.py     # NEW: Fingerprint suppression logic
├── models/
│   ├── suppression.py     # NEW: Suppression ORM model
│   └── ...existing...
└── ...existing...
```

### Pattern 1: API Key Auth Dependency
**What:** FastAPI `Depends()` that extracts X-API-Key header and validates
**When to use:** All /api/* endpoints except /api/health

```python
from fastapi import Depends, Header, HTTPException, Request
import secrets

async def require_api_key(
    request: Request,
    x_api_key: str = Header(..., alias="X-API-Key"),
) -> str:
    """Validate API key from header. Returns the key on success."""
    expected = request.app.state.settings.api_key
    if not expected:
        raise HTTPException(status_code=500, detail="API key not configured")
    if not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key
```

### Pattern 2: Background Scan Queue
**What:** asyncio.Queue with a single worker loop started in lifespan
**When to use:** POST /api/scans creates a DB record, enqueues scan ID; worker dequeues and runs

```python
import asyncio
from scanner.core.orchestrator import run_scan

class ScanQueue:
    def __init__(self):
        self._queue: asyncio.Queue[int] = asyncio.Queue()
        self._current_scan_id: int | None = None

    async def enqueue(self, scan_id: int):
        await self._queue.put(scan_id)

    async def worker(self, app):
        """Long-running worker; started in lifespan, cancelled on shutdown."""
        while True:
            scan_id = await self._queue.get()
            self._current_scan_id = scan_id
            try:
                # Update status to "running"
                # Call run_scan()
                # Update status to "completed" with results
                # Fire notifications
                pass
            except Exception:
                # Update status to "failed"
                pass
            finally:
                self._current_scan_id = None
                self._queue.task_done()
```

### Pattern 3: Dashboard Session Auth
**What:** Login page that sets a session cookie; middleware checks cookie on dashboard routes
**When to use:** All /dashboard/* routes

```python
from fastapi import Cookie, HTTPException, Request
from fastapi.responses import RedirectResponse
import hashlib

def make_session_token(api_key: str) -> str:
    """Hash the API key to create a session cookie value."""
    return hashlib.sha256(api_key.encode()).hexdigest()

async def require_dashboard_auth(request: Request):
    """Check session cookie for dashboard access."""
    token = request.cookies.get("scanner_session")
    expected = make_session_token(request.app.state.settings.api_key)
    if not token or not secrets.compare_digest(token, expected):
        return RedirectResponse(url="/dashboard/login", status_code=302)
```

### Pattern 4: Notification Dispatcher
**What:** Service that calls Slack and email senders based on config toggles
**When to use:** After scan completion in the background worker

```python
async def notify_scan_complete(scan_result, findings, delta, settings):
    """Send notifications on configured channels."""
    if settings.notifications.slack.enabled and settings.slack_webhook_url:
        await send_slack_notification(scan_result, findings, delta, settings)
    if settings.notifications.email.enabled and settings.email_smtp_host:
        await send_email_notification(scan_result, findings, delta, settings)
```

### Anti-Patterns to Avoid
- **Running scan synchronously in request handler:** Scans take minutes; always use background task with 202 response
- **Storing suppression state only in Finding.false_positive column:** This marks individual finding rows but new scans create new rows. Use a separate suppression table keyed by fingerprint
- **Using FastAPI BackgroundTasks for long scans:** BackgroundTasks runs after response but blocks the next request on single-worker; use a dedicated asyncio worker loop
- **Hardcoding Slack message as raw JSON string:** Use a builder/dict approach for Block Kit; raw strings are fragile
- **Making dashboard templates depend on report templates:** Keep dashboard templates separate; they serve different purposes (interactive browsing vs. static report)

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Timing-safe string comparison | Custom `==` on API keys | `secrets.compare_digest()` | Prevents timing attacks on API key validation |
| SMTP connection management | Raw socket handling | `smtplib.SMTP` / `smtplib.SMTP_SSL` | Handles TLS, AUTH, EHLO correctly |
| HTML email MIME construction | Manual header formatting | `email.mime.multipart` + `email.mime.text` | Handles encoding, boundaries, Content-Type |
| Chart generation | HTML5 canvas or SVG by hand | `matplotlib` (already in use) | Consistent with existing report charts |
| Scan queue | Thread pools or subprocess | `asyncio.Queue` with worker coroutine | Native to existing async architecture |
| URL-safe cookie tokens | Custom encoding | `hashlib.sha256` hex digest | Standard, predictable, no special chars |

**Key insight:** This phase adds no new pip dependencies. Python stdlib covers SMTP, email MIME, asyncio queuing, and cookie tokens. The existing stack (FastAPI, Jinja2, SQLAlchemy, matplotlib, httpx) covers everything else.

## Common Pitfalls

### Pitfall 1: Scan Queue Not Surviving App Restart
**What goes wrong:** Scans in "queued" or "running" status when server restarts are stuck forever
**Why it happens:** asyncio.Queue is in-memory; state is lost on restart
**How to avoid:** On startup, query for scans with status "queued" or "running" and re-enqueue them. Mark "running" scans as "queued" first (they didn't complete)
**Warning signs:** Scans stuck in "running" status in the dashboard after a restart

### Pitfall 2: Orchestrator Creates Its Own Engine
**What goes wrong:** `run_scan()` in orchestrator.py creates its own engine via `create_engine(settings.db_path)` and `create_session_factory()`. The background worker also needs a session. Two engines on the same SQLite file can cause locking issues.
**Why it happens:** The orchestrator was designed for CLI where it owns the entire lifecycle
**How to avoid:** Either (a) pass the app's session factory into the scan worker so it reuses the lifespan-managed engine, or (b) accept that the orchestrator manages its own engine lifecycle (it calls `engine.dispose()` at the end), which works with WAL mode. Option (b) is simpler and already proven in CLI context.
**Warning signs:** "database is locked" errors during concurrent dashboard queries while scan runs

### Pitfall 3: Suppression Table vs Finding.false_positive Column
**What goes wrong:** The `Finding` model already has `false_positive = Column(Integer, default=0)` but this is per-finding-row, per-scan. Marking one finding row doesn't suppress the same fingerprint in future scans.
**Why it happens:** The column was a Phase 5 placeholder
**How to avoid:** Create a separate `suppressions` table keyed by fingerprint (unique). During gate evaluation and API responses, LEFT JOIN or pre-query suppressed fingerprints and filter them out. The existing `false_positive` column on Finding can be updated retroactively for historical findings but the authoritative source is the suppressions table.
**Warning signs:** Suppressed finding reappears as gate-failing in next scan

### Pitfall 4: Blocking SMTP in Async Context
**What goes wrong:** `smtplib.SMTP.send_message()` is synchronous and blocks the event loop
**Why it happens:** Python stdlib SMTP is not async
**How to avoid:** Run SMTP calls in a thread pool via `asyncio.to_thread(send_email_sync, ...)` or `loop.run_in_executor(None, ...)`. Since notifications fire after scan completion (already in background worker), a brief block is acceptable, but thread pool is cleaner.
**Warning signs:** Dashboard queries hang during email sending

### Pitfall 5: Dashboard Static Assets
**What goes wrong:** CSS/JS files not served; templates render unstyled
**Why it happens:** FastAPI needs explicit StaticFiles mount for serving CSS
**How to avoid:** Use inline CSS in templates (single-file approach like existing HTML reports) OR mount a small static directory. Inline is simpler and consistent with existing report approach.
**Warning signs:** Broken layout, missing styles in browser

### Pitfall 6: Jenkinsfile Assuming Scanner Runs on Same Host
**What goes wrong:** Jenkins agent passes `${WORKSPACE}` path but scanner runs in Docker container where that path doesn't exist
**Why it happens:** Path mismatch between host and container
**How to avoid:** Document that the scanner container must mount the Jenkins workspace volume, or that scanner runs on the same host. The Jenkinsfile should pass the container-relative path.
**Warning signs:** "Path not found" errors from scanner API

## Code Examples

### API Auth Dependency (FastAPI pattern)
```python
# src/scanner/api/auth.py
import secrets
from fastapi import Depends, Header, HTTPException, Request

async def require_api_key(
    request: Request,
    x_api_key: str = Header(..., alias="X-API-Key"),
) -> str:
    expected = request.app.state.settings.api_key
    if not expected:
        raise HTTPException(503, "API key not configured on server")
    if not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(401, "Invalid API key")
    return x_api_key
```

### Scan Trigger Endpoint
```python
# src/scanner/api/scans.py
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

class ScanRequest(BaseModel):
    path: str | None = None
    repo_url: str | None = None
    branch: str | None = None

class ScanResponse(BaseModel):
    id: int
    status: str

router = APIRouter(prefix="/scans", tags=["scans"])

@router.post("", status_code=202, response_model=ScanResponse)
async def trigger_scan(
    body: ScanRequest,
    request: Request,
    api_key: str = Depends(require_api_key),
):
    # Create DB record with status="queued"
    # Enqueue scan_id into scan_queue
    # Return 202 with scan ID
    pass
```

### Suppression Model
```python
# src/scanner/models/suppression.py
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text
from scanner.models.base import Base

class Suppression(Base):
    __tablename__ = "suppressions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fingerprint = Column(String(64), nullable=False, unique=True, index=True)
    reason = Column(Text, nullable=True)
    suppressed_by = Column(String(100), default="api")  # audit trail
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Slack Block Kit Message
```python
# src/scanner/notifications/slack.py
import httpx

async def send_slack_notification(scan_result, delta, dashboard_url, webhook_url):
    gate_emoji = ":white_check_mark:" if scan_result.gate_passed else ":x:"
    gate_text = "PASSED" if scan_result.gate_passed else "FAILED"

    delta_text = ""
    if delta:
        delta_text = f"+{len(delta.new_fingerprints)} new, -{len(delta.fixed_fingerprints)} fixed"

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"{gate_emoji} Security Scan {gate_text}"}
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Branch:* {scan_result.branch or 'local'}"},
                {"type": "mrkdwn", "text": f"*Duration:* {scan_result.duration_seconds:.0f}s"},
                {"type": "mrkdwn", "text": f"*Critical:* {scan_result.critical_count}"},
                {"type": "mrkdwn", "text": f"*High:* {scan_result.high_count}"},
                {"type": "mrkdwn", "text": f"*Medium:* {scan_result.medium_count}"},
                {"type": "mrkdwn", "text": f"*Low:* {scan_result.low_count}"},
            ]
        },
    ]
    if delta_text:
        blocks.append({
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": f"Delta: {delta_text}"}]
        })
    blocks.append({
        "type": "actions",
        "elements": [{"type": "button", "text": {"type": "plain_text", "text": "View Details"}, "url": dashboard_url}]
    })

    async with httpx.AsyncClient() as client:
        await client.post(webhook_url, json={"blocks": blocks})
```

### Email Notification (sync, run in thread)
```python
# src/scanner/notifications/email.py
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_email_sync(
    smtp_host: str, smtp_port: int, smtp_user: str, smtp_password: str,
    recipients: list[str], subject: str, html_body: str,
    use_tls: bool = True,
):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        if use_tls:
            server.starttls()
        if smtp_user and smtp_password:
            server.login(smtp_user, smtp_password)
        server.send_message(msg)
```

### Jenkinsfile.security
```groovy
// Jenkinsfile.security
pipeline {
    agent any
    environment {
        SCANNER_URL = credentials('scanner-url')       // e.g., http://scanner:8000
        SCANNER_API_KEY = credentials('scanner-api-key')
    }
    stages {
        stage('Security Scan') {
            steps {
                script {
                    // Trigger scan
                    def triggerResp = httpRequest(
                        url: "${SCANNER_URL}/api/scans",
                        httpMode: 'POST',
                        contentType: 'APPLICATION_JSON',
                        requestBody: """{"path": "${WORKSPACE}"}""",
                        customHeaders: [[name: 'X-API-Key', value: "${SCANNER_API_KEY}"]],
                        validResponseCodes: '202'
                    )
                    def scanId = readJSON(text: triggerResp.content).id

                    // Poll for completion
                    def status = 'queued'
                    while (status == 'queued' || status == 'running') {
                        sleep(time: 10, unit: 'SECONDS')
                        def pollResp = httpRequest(
                            url: "${SCANNER_URL}/api/scans/${scanId}",
                            customHeaders: [[name: 'X-API-Key', value: "${SCANNER_API_KEY}"]],
                            validResponseCodes: '200'
                        )
                        def result = readJSON(text: pollResp.content)
                        status = result.status
                        if (status == 'completed') {
                            if (!result.gate_passed) {
                                error("Security gate FAILED: ${result.total_findings} findings")
                            }
                        } else if (status == 'failed') {
                            error("Security scan failed")
                        }
                    }
                }
            }
        }
    }
}
```

### Notification Config Extension
```python
# Addition to ScannerSettings in config.py
class NotificationSlackConfig(BaseModel):
    enabled: bool = False

class NotificationEmailConfig(BaseModel):
    enabled: bool = False
    recipients: list[str] = []
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    use_tls: bool = True

class NotificationsConfig(BaseModel):
    slack: NotificationSlackConfig = NotificationSlackConfig()
    email: NotificationEmailConfig = NotificationEmailConfig()

# Add to ScannerSettings:
# notifications: NotificationsConfig = NotificationsConfig()
```

### Pagination Pattern
```python
# Offset-based pagination for findings
from pydantic import BaseModel

class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
    pages: int

@router.get("/{scan_id}/findings")
async def get_findings(
    scan_id: int,
    page: int = 1,
    page_size: int = 50,
    # ... auth dependency
):
    offset = (page - 1) * page_size
    # SELECT ... LIMIT page_size OFFSET offset
    # SELECT COUNT(*) for total
    pass
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| FastAPI BackgroundTasks for long jobs | asyncio.Queue + worker loop | Best practice for >30s tasks | BackgroundTasks blocks between requests in Uvicorn single-worker |
| Per-finding false_positive flag | Separate suppression table by fingerprint | Standard pattern for cross-scan suppression | Fingerprint-based lookup scales across scans |
| JS charting (Chart.js) | matplotlib server-side | Project decision | No JS build step, consistent with PDF reports |
| SPA dashboard (React/Vue) | Server-rendered Jinja2 | Project decision | Zero JS complexity, works offline, fast for internal tool |

## Open Questions

1. **Orchestrator engine management in API context**
   - What we know: `run_scan()` creates its own engine and disposes it. The app has a lifespan-managed engine.
   - What's unclear: Whether to refactor `run_scan()` to accept an external session factory or let it manage its own engine
   - Recommendation: Let it keep its own engine (proven pattern, WAL mode handles concurrent reads). The background worker just calls `run_scan(settings)` as-is. This avoids touching working code.

2. **Dashboard base URL for notification links**
   - What we know: Slack/email notifications should link to dashboard scan detail page
   - What's unclear: How to determine the external URL (scanner may be behind reverse proxy)
   - Recommendation: Add `dashboard_url` config field (e.g., `http://scanner:8000/dashboard`). Default to `http://{settings.host}:{settings.port}/dashboard`.

3. **Table creation for new suppression model**
   - What we know: Phase 1 uses `Base.metadata.create_all` in lifespan. Alembic is installed but not configured.
   - What's unclear: Whether to continue with create_all or introduce Alembic migrations
   - Recommendation: Continue with `create_all` for now -- it's idempotent and handles new tables. Migration from Phase 1 approach to Alembic can happen in Phase 6.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x + pytest-asyncio (auto mode) |
| Config file | `pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `python -m pytest tests/phase_05/ -x -q` |
| Full suite command | `python -m pytest tests/ -x -q` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| API-01 | POST /api/scans triggers scan, returns 202 with ID | integration | `python -m pytest tests/phase_05/test_scan_api.py::test_trigger_scan -x` | Wave 0 |
| API-02 | GET /api/scans/{id} returns status and results | integration | `python -m pytest tests/phase_05/test_scan_api.py::test_get_scan_status -x` | Wave 0 |
| API-03 | All /api/* endpoints require X-API-Key (except health) | integration | `python -m pytest tests/phase_05/test_auth.py -x` | Wave 0 |
| API-05 | Dashboard shows scan history, trends, comparison | integration | `python -m pytest tests/phase_05/test_dashboard.py -x` | Wave 0 |
| API-06 | Dashboard requires API key authentication via cookie | integration | `python -m pytest tests/phase_05/test_dashboard_auth.py -x` | Wave 0 |
| CI-01 | Jenkinsfile.security is valid pipeline syntax | manual-only | N/A (requires Jenkins) | Wave 0 (file only) |
| CI-02 | Jenkins passes workspace path to scanner | unit | `python -m pytest tests/phase_05/test_scan_api.py::test_trigger_with_path -x` | Wave 0 |
| CI-03 | Gate result in API response for Jenkins consumption | unit | `python -m pytest tests/phase_05/test_scan_api.py::test_gate_result_in_response -x` | Wave 0 |
| NOTF-01 | Slack notification fires on scan completion | unit | `python -m pytest tests/phase_05/test_notifications.py::test_slack -x` | Wave 0 |
| NOTF-02 | Email notification fires on scan completion | unit | `python -m pytest tests/phase_05/test_notifications.py::test_email -x` | Wave 0 |
| NOTF-03 | Notification channels independently configurable | unit | `python -m pytest tests/phase_05/test_notifications.py::test_config_toggles -x` | Wave 0 |
| HIST-03 | Mark finding as FP, suppressed in future scans | integration | `python -m pytest tests/phase_05/test_suppression.py -x` | Wave 0 |
| HIST-04 | Scan history queryable via API | integration | `python -m pytest tests/phase_05/test_scan_api.py::test_list_scans -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/phase_05/ -x -q`
- **Per wave merge:** `python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/phase_05/__init__.py` -- package init
- [ ] `tests/phase_05/conftest.py` -- shared fixtures (authenticated client, sample DB data)
- [ ] `tests/phase_05/test_auth.py` -- API key auth tests
- [ ] `tests/phase_05/test_scan_api.py` -- scan lifecycle API tests
- [ ] `tests/phase_05/test_dashboard.py` -- dashboard rendering tests
- [ ] `tests/phase_05/test_dashboard_auth.py` -- dashboard cookie auth tests
- [ ] `tests/phase_05/test_notifications.py` -- Slack + email notification tests (mocked)
- [ ] `tests/phase_05/test_suppression.py` -- false positive suppression tests

### Test Patterns (from existing phases)
- Use `_lifespan_client(app)` pattern from `test_health.py` for integration tests
- Use `monkeypatch.setenv("SCANNER_*", ...)` for config in tests
- Use `tmp_path` for temporary DB
- Mock `run_scan()` in API tests (don't actually run scanner tools)
- Mock `httpx.AsyncClient.post` for Slack webhook tests
- Mock `smtplib.SMTP` for email tests
- Use `AsyncMock` from `unittest.mock` (established pattern, no pytest-mock)

## Sources

### Primary (HIGH confidence)
- Codebase inspection: `src/scanner/main.py`, `src/scanner/api/`, `src/scanner/config.py`, `src/scanner/core/orchestrator.py`, `src/scanner/models/`, `src/scanner/schemas/`, `src/scanner/reports/`
- Installed package versions verified via `pip show`
- FastAPI BackgroundTasks API verified via `help(fastapi.BackgroundTasks)`
- Existing test patterns from `tests/phase_01/`, `tests/phase_04/`

### Secondary (MEDIUM confidence)
- Slack Block Kit structure based on Slack API documentation patterns
- Jenkins declarative pipeline syntax based on standard Jenkins docs

### Tertiary (LOW confidence)
- None -- all findings verified against codebase or installed packages

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already installed and in use; no new dependencies
- Architecture: HIGH -- patterns derived from existing codebase; FastAPI dependency injection, Jinja2 PackageLoader, asyncio patterns all proven in prior phases
- Pitfalls: HIGH -- identified from direct code inspection (orchestrator engine management, Finding.false_positive column semantics, async SMTP blocking)
- Notifications: MEDIUM -- Slack Block Kit structure and SMTP patterns are standard but exact field names should be verified during implementation

**Research date:** 2026-03-19
**Valid until:** 2026-04-19 (stable stack, no fast-moving dependencies)
