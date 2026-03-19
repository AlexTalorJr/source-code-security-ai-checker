---
phase: 05-api-dashboard-ci-and-notifications
verified: 2026-03-19T14:00:00Z
status: gaps_found
score: 4/5 success criteria verified
re_verification: false
gaps:
  - truth: "Notifications fire on every scan completion (both pass and fail)"
    status: failed
    reason: "scan_queue.py calls notify_scan_complete with wrong argument order and passes scan_id (int) where delta (DeltaResult | None) is expected"
    artifacts:
      - path: "src/scanner/core/scan_queue.py"
        issue: "Line 114-116: calls notify_scan_complete(app.state.settings, scan_id, scan_result) but function signature is notify_scan_complete(scan_result, delta, settings)"
    missing:
      - "Fix call site in scan_queue.py line 114-116 to: await notify_scan_complete(scan_result, None, app.state.settings)"
      - "Optionally thread delta computation through the worker to pass real delta instead of None"
human_verification:
  - test: "Run an actual scan end-to-end with Slack webhook configured"
    expected: "Slack Block Kit message arrives with gate status, severity counts, and dashboard link"
    why_human: "Cannot verify real HTTP call to external Slack webhook without network access and credentials"
  - test: "Run an actual scan with SMTP email configured"
    expected: "HTML email received with gate banner, severity table, and View Full Report button"
    why_human: "Cannot verify real SMTP delivery without mail server access"
---

# Phase 5: API, Dashboard, CI, and Notifications — Verification Report

**Phase Goal:** The scanner is fully operational as both a CI pipeline stage and a standalone service with web dashboard and notifications
**Verified:** 2026-03-19
**Status:** gaps_found — 1 wiring bug found (notify_scan_complete call signature mismatch)
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (Success Criteria from ROADMAP.md)

| #   | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| SC1 | POST /api/scans triggers a scan, GET /api/scans/{id} returns status/results; all API endpoints require API key auth | ✓ VERIFIED | scans.py has POST 202 + GET with require_api_key; findings.py, scans.py all Depend(require_api_key); /api/health excluded from auth |
| SC2 | Web dashboard shows scan history, finding trends, release-to-release comparison | ✓ VERIFIED | history.html.j2 shows scan table with badges; trends.html.j2 generates matplotlib severity-over-time + branch comparison charts; detail.html.j2 has delta tab |
| SC3 | Jenkinsfile.security stage can be dropped in, passes workspace path, fails build on gate failure | ✓ VERIFIED | Jenkinsfile.security at project root, contains `${WORKSPACE}`, `gate_passed`, poll loop with `while`, `sleep(time: 10)`, `error(...)` on gate fail |
| SC4 | Slack and email notifications fire on scan completion with severity summary, each channel independently configurable | ✗ FAILED | Notification code exists and is wired correctly in service.py, but scan_queue.py calls `notify_scan_complete(app.state.settings, scan_id, scan_result)` — wrong argument order; function expects `(scan_result, delta, settings)`. This means notifications NEVER fire in production (silently swallowed by except Exception). |
| SC5 | Users can mark findings as false positive via API; suppressed findings excluded from quality gate decisions | ✓ VERIFIED | PUT/DELETE /api/findings/{fp}/suppress exist; get_suppressed_fingerprints called in GET /api/scans/{id}/findings; suppression model stores globally scoped fingerprints |

**Score:** 4/5 success criteria verified

---

## Required Artifacts

### Plan 01 Artifacts (API layer)

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `src/scanner/api/auth.py` | API key auth dependency | ✓ VERIFIED | `require_api_key` with `secrets.compare_digest`, 503 if unconfigured, 401 on mismatch |
| `src/scanner/api/scans.py` | Scan lifecycle endpoints | ✓ VERIFIED | POST 202, GET list, GET /{id}, GET /{id}/report, GET /{id}/findings — all with auth |
| `src/scanner/api/findings.py` | Suppression endpoints | ✓ VERIFIED | PUT /{fp}/suppress and DELETE /{fp}/suppress with auth |
| `src/scanner/api/schemas.py` | API schemas | ✓ VERIFIED | ScanRequest, ScanResponse, ScanDetailResponse, FindingResponse, PaginatedResponse, SuppressionRequest |
| `src/scanner/core/scan_queue.py` | Background scan worker | ✓ VERIFIED | ScanQueue with enqueue, worker, recover_stuck_scans, asyncio.Queue |
| `src/scanner/core/suppression.py` | Suppression query logic | ✓ VERIFIED | get_suppressed_fingerprints, suppress_fingerprint, unsuppress_fingerprint, is_suppressed |
| `src/scanner/models/suppression.py` | Suppression ORM model | ✓ VERIFIED | class Suppression(Base) with `__tablename__ = "suppressions"`, fingerprint unique+indexed |

### Plan 02 Artifacts (Notifications + CI)

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `src/scanner/notifications/service.py` | Notification dispatcher | ✓ VERIFIED | notify_scan_complete with independent slack/email channel checks |
| `src/scanner/notifications/slack.py` | Slack webhook sender | ✓ VERIFIED | send_slack_notification with Block Kit: header, section fields, context delta, actions button |
| `src/scanner/notifications/email_sender.py` | SMTP email sender | ✓ VERIFIED | send_email_sync (sync SMTP), send_email_notification (async via to_thread), render_email_html |
| `src/scanner/notifications/templates/email.html.j2` | HTML email template | ✓ VERIFIED | Contains "Quality Gate", "aipix-security-scanner", `background-color:#0d6efd`, "Configure notifications in config.yml" |
| `Jenkinsfile.security` | Jenkins pipeline stage | ✓ VERIFIED | Declarative pipeline with X-API-Key header, ${WORKSPACE}, while poll loop, gate_passed check, error() call |

### Plan 03 Artifacts (Dashboard)

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `src/scanner/dashboard/router.py` | Dashboard route handlers | ✓ VERIFIED | login, logout, history, /scans/{id}, trends, start-scan, suppress, unsuppress routes |
| `src/scanner/dashboard/auth.py` | Dashboard cookie auth | ✓ VERIFIED | make_session_token (SHA-256), require_dashboard_auth with secrets.compare_digest |
| `src/scanner/dashboard/templates/base.html.j2` | Base template | ✓ VERIFIED | Contains "Scan History", "Trends", "Log Out", `--color-accent: #0d6efd` |
| `src/scanner/dashboard/templates/login.html.j2` | Login page | ✓ VERIFIED | Contains "Security Scanner", "API Key", "Log In", "Invalid API key" |
| `src/scanner/dashboard/templates/history.html.j2` | Scan history page | ✓ VERIFIED | Contains "Start New Scan", "No scans yet" |
| `src/scanner/dashboard/templates/detail.html.j2` | Scan detail page | ✓ VERIFIED | Contains "Quality Gate", "Suppress", "Restore", tab-findings, tab-delta, tab-suppressed |
| `src/scanner/dashboard/templates/trends.html.j2` | Trends page | ✓ VERIFIED | Contains "Finding Trends", "Severity Over Time", "Branch Comparison", "Not enough data" |

---

## Key Link Verification

### Plan 01 Key Links

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `src/scanner/api/scans.py` | `src/scanner/core/scan_queue.py` | enqueue scan ID after creating DB record | ✓ WIRED | Line 78: `await request.app.state.scan_queue.enqueue(scan_id)` |
| `src/scanner/core/scan_queue.py` | `src/scanner/core/orchestrator.py` | worker calls run_scan | ✓ WIRED | Line 72: `scan_result, findings, compound_risks = await run_scan(...)` |
| `src/scanner/api/auth.py` | `src/scanner/config.py` | reads settings.api_key from app.state.settings | ✓ WIRED | Line 26: `configured_key = request.app.state.settings.api_key` |
| `src/scanner/core/suppression.py` | `src/scanner/models/suppression.py` | queries Suppression table by fingerprint | ✓ WIRED | Line 18: `select(Suppression.fingerprint)` and throughout |

### Plan 02 Key Links

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `src/scanner/notifications/service.py` | `src/scanner/notifications/slack.py` | calls send_slack_notification when slack.enabled | ✓ WIRED | Line 34-38: conditional call with config check |
| `src/scanner/notifications/service.py` | `src/scanner/notifications/email_sender.py` | calls send_email_notification when email.enabled | ✓ WIRED | Line 50-57: conditional call with config check |
| `src/scanner/notifications/service.py` | `src/scanner/config.py` | reads settings.notifications.slack/email.enabled | ✓ WIRED | Lines 33, 46: `settings.notifications.slack.enabled`, `settings.notifications.email.enabled` |
| `src/scanner/core/scan_queue.py` | `src/scanner/notifications/service.py` | calls notify_scan_complete after scan completion | ✗ BROKEN | Line 114-116: `notify_scan_complete(app.state.settings, scan_id, scan_result)` — wrong arg order. Function signature is `(scan_result, delta, settings)`. Result: TypeError raised at runtime, swallowed silently by `except Exception`. Notifications never fire. |

### Plan 03 Key Links

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `src/scanner/dashboard/router.py` | `src/scanner/dashboard/auth.py` | require_dashboard_auth on all protected routes | ✓ WIRED | Lines 111, 146, 269(implicit), 314, 355, 381, 397: `redirect = await require_dashboard_auth(request)` |
| `src/scanner/dashboard/router.py` | `src/scanner/models/scan.py` | queries ScanResult for history/detail | ✓ WIRED | Lines 117, 152, 320-322: `select(ScanResult)` throughout |
| `src/scanner/main.py` | `src/scanner/dashboard/router.py` | app.include_router(dashboard_router, prefix='/dashboard') | ✓ WIRED | Line 64: `app.include_router(dashboard_router, prefix="/dashboard")` |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| API-01 | 05-01 | POST /api/scans triggers scan | ✓ SATISFIED | scans.py POST "" returns 202 with scan ID |
| API-02 | 05-01 | GET /api/scans/{id} returns status and results | ✓ SATISFIED | scans.py GET /{scan_id} returns ScanDetailResponse |
| API-03 | 05-01 | API authenticated via API key in header | ✓ SATISFIED | auth.py require_api_key applied to all endpoints except /health |
| API-05 | 05-03 | Live web dashboard showing history, trends, release comparison | ✓ SATISFIED | Dashboard router with history, detail, trends pages; matplotlib charts |
| API-06 | 05-03 | Dashboard accessible via browser with API key authentication | ✓ SATISFIED | Cookie-based session auth via SHA-256 token from API key |
| CI-01 | 05-02 | Jenkinsfile.security drop-in stage | ✓ SATISFIED | Jenkinsfile.security exists at project root with declarative pipeline |
| CI-02 | 05-02 | Jenkins stage passes workspace path | ✓ SATISFIED | `requestBody: """{"path": "${WORKSPACE}"}"""` |
| CI-03 | 05-02 | Quality gate result determines Jenkins pass/fail | ✓ SATISFIED | `if (!result.gate_passed) { error(...) }` |
| NOTF-01 | 05-02 | Slack notification on scan completion | ✗ BLOCKED | Dispatcher code correct; call site in scan_queue.py uses wrong arg order, causing TypeError swallowed silently |
| NOTF-02 | 05-02 | Email notification on scan completion | ✗ BLOCKED | Same root cause as NOTF-01 — notifications never reach service.py from scan_queue.py |
| NOTF-03 | 05-02 | Both channels independently configurable | ? NEEDS HUMAN | Config toggles wired correctly in service.py; blocked by same runtime bug |
| HIST-03 | 05-01 | Mark findings as false positive, suppressed across future scans | ✓ SATISFIED | PUT/DELETE /api/findings/{fp}/suppress; global Suppression table |
| HIST-04 | 05-01 | Scan history queryable via API (list, detail, trends) | ✓ SATISFIED | GET /api/scans (paginated), GET /api/scans/{id}, GET /api/scans/{id}/findings |

**Requirements satisfied:** 10/13
**Requirements blocked:** 2 (NOTF-01, NOTF-02) due to single root-cause bug
**Requirements needs human:** 1 (NOTF-03 — toggle behavior needs live notification test to confirm)

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/scanner/core/scan_queue.py` | 114-116 | Wrong argument order to notify_scan_complete | 🛑 Blocker | Notifications silently fail in production; NOTF-01 and NOTF-02 never execute |
| `src/scanner/api/scans.py` | 165-174 | Report endpoint returns bare HTML stub ("Simple HTML summary for now") instead of full HTML report | ⚠️ Warning | GET /api/scans/{id}/report returns minimal content, not a proper scan report. Not in phase 5 success criteria but the plan task described using generate_html_report. |

---

## Test Suite Results

- **Phase 05 tests:** 55 passed, 0 failed (`python3 -m pytest tests/phase_05/ -x -q`)
- **Full regression suite:** 269 passed, 0 failed (`python3 -m pytest tests/ -q`)
- **Note:** The notify_scan_complete bug is NOT caught by tests because test_scan_api.py does not mock or exercise the notification path in the worker, and test_notifications.py tests `notify_scan_complete` directly with the correct call signature.

---

## Human Verification Required

### 1. Slack Notification End-to-End

**Test:** Configure SCANNER_SLACK_WEBHOOK_URL and set `notifications.slack.enabled: true` in config.yml, then trigger a scan. (After fixing the call site bug.)
**Expected:** Slack Block Kit message arrives with gate emoji (pass/fail), Branch, Duration, severity counts, optional delta context, and View Details button linking to dashboard.
**Why human:** Cannot verify real HTTP call to external Slack webhook without live credentials and network access.

### 2. Email Notification End-to-End

**Test:** Configure SMTP settings and recipients, set `notifications.email.enabled: true`, trigger a scan. (After fixing the call site bug.)
**Expected:** HTML email with gate banner (green/red), severity table, delta badges, and View Full Report button linking to dashboard.
**Why human:** Cannot verify SMTP delivery without a live mail server.

### 3. Dashboard Running Scan Auto-Refresh

**Test:** Trigger a long-running scan, navigate to /dashboard/scans/{id} in a browser.
**Expected:** Page auto-refreshes every 5 seconds while scan is in "running" or "queued" status, stops refreshing when completed.
**Why human:** The meta refresh tag is in the template (verified), but browser auto-refresh behavior requires manual observation.

---

## Gaps Summary

One root-cause bug blocks two requirements (NOTF-01, NOTF-02):

**`src/scanner/core/scan_queue.py` lines 114-116** calls:
```python
await notify_scan_complete(app.state.settings, scan_id, scan_result)
```
but the actual function signature in `src/scanner/notifications/service.py` is:
```python
async def notify_scan_complete(scan_result: ScanResultSchema, delta: DeltaResult | None, settings: ScannerSettings) -> None
```

The call passes `settings` as the first positional argument (expecting `ScanResultSchema`), `scan_id` (int) as the second (expecting `DeltaResult | None`), and `scan_result` (ScanResultSchema) as the third (expecting `ScannerSettings`). This will raise a TypeError at runtime which is silently swallowed by the `except Exception` handler in the worker, causing notifications to never fire.

**Fix required:**
```python
await notify_scan_complete(scan_result, None, app.state.settings)
```

All other phase 5 goals — REST API, dashboard, CI pipeline, false positive suppression — are fully implemented, wired, and verified by 269 passing tests.

---

_Verified: 2026-03-19_
_Verifier: Claude (gsd-verifier)_
