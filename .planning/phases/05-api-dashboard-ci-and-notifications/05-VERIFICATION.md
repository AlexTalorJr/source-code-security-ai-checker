---
phase: 05-api-dashboard-ci-and-notifications
verified: 2026-03-19T15:00:00Z
status: human_needed
score: 5/5 success criteria verified
re_verification: true
previous_status: gaps_found
previous_score: 4/5
gaps_closed:
  - "SC4: Notifications fire on every scan completion — notify_scan_complete now called with correct argument order (scan_result, None, app.state.settings)"
gaps_remaining: []
regressions: []
human_verification:
  - test: "Configure SCANNER_SLACK_WEBHOOK_URL and set notifications.slack.enabled: true in config.yml, then trigger a scan"
    expected: "Slack Block Kit message arrives with gate emoji (pass/fail), Branch, Duration, severity counts, and View Details button"
    why_human: "Cannot verify real HTTP call to external Slack webhook without live credentials and network access"
  - test: "Configure SMTP settings and recipients, set notifications.email.enabled: true, trigger a scan"
    expected: "HTML email with gate banner (green/red), severity table, delta badges, and View Full Report button"
    why_human: "Cannot verify SMTP delivery without a live mail server"
  - test: "Trigger a long-running scan, navigate to /dashboard/scans/{id} in a browser"
    expected: "Page auto-refreshes every 5 seconds while scan is running or queued, stops when completed"
    why_human: "The meta refresh tag is in the template (verified), but browser auto-refresh behavior requires manual observation"
---

# Phase 5: API, Dashboard, CI, and Notifications — Verification Report

**Phase Goal:** The scanner is fully operational as both a CI pipeline stage and a standalone service with web dashboard and notifications
**Verified:** 2026-03-19
**Status:** human_needed — all automated checks pass; external delivery (Slack webhook, SMTP) requires live credentials
**Re-verification:** Yes — after gap closure (commit fce4392)

## Re-Verification Summary

Previous verification (gaps_found, score 4/5) identified one root-cause bug:

- `src/scanner/core/scan_queue.py` lines 114-116 called `notify_scan_complete(app.state.settings, scan_id, scan_result)` — wrong argument order causing a silent TypeError at runtime.

**Fix applied in commit fce4392:** line 114-116 now reads:

```python
await notify_scan_complete(
    scan_result, None, app.state.settings
)
```

**Regression test added** in `tests/phase_05/test_scan_queue_notifications.py`:
- `test_worker_calls_notify_with_correct_arg_order` — asserts mock Slack sender receives a `ScanResultSchema` as its first positional argument, not `ScannerSettings` or `int`.
- `test_worker_notification_failure_does_not_crash_worker` — asserts worker survives a notification exception gracefully.

Both tests pass. Full suite: **271 passed, 0 failed**.

---

## Goal Achievement

### Observable Truths (Success Criteria from ROADMAP.md)

| #   | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| SC1 | POST /api/scans triggers a scan, GET /api/scans/{id} returns status/results; all API endpoints require API key auth | ✓ VERIFIED | `scans.py` POST 202 + GET with `require_api_key`; `findings.py`, `scans.py` all `Depend(require_api_key)`; /api/health excluded from auth |
| SC2 | Web dashboard shows scan history, finding trends, release-to-release comparison | ✓ VERIFIED | `history.html.j2` shows scan table with badges; `trends.html.j2` generates matplotlib severity-over-time + branch comparison charts; `detail.html.j2` has delta tab |
| SC3 | Jenkinsfile.security stage can be dropped in, passes workspace path, fails build on gate failure | ✓ VERIFIED | `Jenkinsfile.security` at project root, contains `${WORKSPACE}`, `gate_passed`, poll loop with `while`, `sleep(time: 10)`, `error(...)` on gate fail |
| SC4 | Slack and email notifications fire on scan completion with severity summary, each channel independently configurable | ✓ VERIFIED | Fix confirmed: `scan_queue.py` lines 114-116 now call `notify_scan_complete(scan_result, None, app.state.settings)`; regression test `test_worker_calls_notify_with_correct_arg_order` passes asserting `ScanResultSchema` is first arg to Slack sender |
| SC5 | Users can mark findings as false positive via API; suppressed findings excluded from quality gate decisions | ✓ VERIFIED | `PUT/DELETE /api/findings/{fp}/suppress` exist; `get_suppressed_fingerprints` called in `GET /api/scans/{id}/findings`; suppression model stores globally scoped fingerprints |

**Score:** 5/5 success criteria verified

---

## Required Artifacts

### Plan 01 Artifacts (API layer)

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `src/scanner/api/auth.py` | API key auth dependency | ✓ VERIFIED | `require_api_key` with `secrets.compare_digest`, 503 if unconfigured, 401 on mismatch |
| `src/scanner/api/scans.py` | Scan lifecycle endpoints | ✓ VERIFIED | POST 202, GET list, GET /{id}, GET /{id}/report, GET /{id}/findings — all with auth |
| `src/scanner/api/findings.py` | Suppression endpoints | ✓ VERIFIED | PUT /{fp}/suppress and DELETE /{fp}/suppress with auth |
| `src/scanner/api/schemas.py` | API schemas | ✓ VERIFIED | ScanRequest, ScanResponse, ScanDetailResponse, FindingResponse, PaginatedResponse, SuppressionRequest |
| `src/scanner/core/scan_queue.py` | Background scan worker | ✓ VERIFIED | ScanQueue with enqueue, worker, recover_stuck_scans, asyncio.Queue; notify call fixed |
| `src/scanner/core/suppression.py` | Suppression query logic | ✓ VERIFIED | get_suppressed_fingerprints, suppress_fingerprint, unsuppress_fingerprint, is_suppressed |
| `src/scanner/models/suppression.py` | Suppression ORM model | ✓ VERIFIED | class Suppression(Base) with `__tablename__ = "suppressions"`, fingerprint unique+indexed |

### Plan 02 Artifacts (Notifications + CI)

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `src/scanner/notifications/service.py` | Notification dispatcher | ✓ VERIFIED | `notify_scan_complete(scan_result, delta, settings)` with independent slack/email channel checks |
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

### Plan 04 Artifacts (Gap Closure)

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `tests/phase_05/test_scan_queue_notifications.py` | Regression test for notification arg order | ✓ VERIFIED | 2 tests: correct arg order assertion + graceful failure handling |

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
| `src/scanner/notifications/service.py` | `src/scanner/notifications/slack.py` | calls send_slack_notification when slack.enabled | ✓ WIRED | Conditional call with `settings.notifications.slack.enabled` check |
| `src/scanner/notifications/service.py` | `src/scanner/notifications/email_sender.py` | calls send_email_notification when email.enabled | ✓ WIRED | Conditional call with `settings.notifications.email.enabled` check |
| `src/scanner/notifications/service.py` | `src/scanner/config.py` | reads settings.notifications.slack/email.enabled | ✓ WIRED | `settings.notifications.slack.enabled`, `settings.notifications.email.enabled` |
| `src/scanner/core/scan_queue.py` | `src/scanner/notifications/service.py` | calls notify_scan_complete after scan completion | ✓ WIRED (FIXED) | Lines 114-116: `await notify_scan_complete(scan_result, None, app.state.settings)` — argument order corrected in commit fce4392 |

### Plan 03 Key Links

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `src/scanner/dashboard/router.py` | `src/scanner/dashboard/auth.py` | require_dashboard_auth on all protected routes | ✓ WIRED | `redirect = await require_dashboard_auth(request)` on history, detail, trends, suppress routes |
| `src/scanner/dashboard/router.py` | `src/scanner/models/scan.py` | queries ScanResult for history/detail | ✓ WIRED | `select(ScanResult)` throughout |
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
| NOTF-01 | 05-02 | Slack notification on scan completion | ✓ SATISFIED | Call site fixed; regression test asserts ScanResultSchema reaches send_slack_notification as first arg |
| NOTF-02 | 05-02 | Email notification on scan completion | ✓ SATISFIED | Same fix resolves email path; service.py sends email when email.enabled |
| NOTF-03 | 05-02 | Both channels independently configurable | ? NEEDS HUMAN | Config toggles wired correctly in service.py; independent channel logic verified; live delivery needs credentials |
| HIST-03 | 05-01 | Mark findings as false positive, suppressed across future scans | ✓ SATISFIED | PUT/DELETE /api/findings/{fp}/suppress; global Suppression table |
| HIST-04 | 05-01 | Scan history queryable via API (list, detail, trends) | ✓ SATISFIED | GET /api/scans (paginated), GET /api/scans/{id}, GET /api/scans/{id}/findings |

**Requirements satisfied:** 12/13
**Requirements needs human:** 1 (NOTF-03 — independent toggle behavior requires live delivery test)

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| `src/scanner/api/scans.py` | 165-174 | Report endpoint returns bare HTML stub ("Simple HTML summary for now") | ⚠️ Warning | GET /api/scans/{id}/report returns minimal content. Not in phase 5 success criteria; not a blocker. |

No blocker anti-patterns remain. The previously identified blocker (wrong notify argument order) has been resolved.

---

## Test Suite Results

- **Regression tests (new):** 2 passed (`tests/phase_05/test_scan_queue_notifications.py`)
- **Phase 05 tests:** 57 passed, 0 failed (`python3 -m pytest tests/phase_05/ -q`)
- **Full regression suite:** 271 passed, 0 failed (`python3 -m pytest tests/ -q`)

---

## Human Verification Required

### 1. Slack Notification End-to-End

**Test:** Configure `SCANNER_SLACK_WEBHOOK_URL` and set `notifications.slack.enabled: true` in config.yml, then trigger a scan via POST /api/scans.
**Expected:** Slack Block Kit message arrives with gate emoji (pass/fail), Branch, Duration, severity counts, optional delta context, and View Details button linking to the dashboard.
**Why human:** Cannot verify real HTTP call to external Slack webhook without live credentials and network access.

### 2. Email Notification End-to-End

**Test:** Configure SMTP settings and recipients, set `notifications.email.enabled: true` in config.yml, trigger a scan.
**Expected:** HTML email with gate banner (green/red), severity table, delta badges, and View Full Report button linking to the dashboard.
**Why human:** Cannot verify SMTP delivery without a live mail server.

### 3. Dashboard Running Scan Auto-Refresh

**Test:** Trigger a long-running scan, navigate to `/dashboard/scans/{id}` in a browser.
**Expected:** Page auto-refreshes every 5 seconds while scan is in "running" or "queued" status, stops refreshing when completed.
**Why human:** The meta refresh tag is in the template (verified), but browser auto-refresh behavior requires manual observation.

---

## Gap Closure Confirmation

The single gap from initial verification is closed:

| Gap | Previous State | Current State |
| --- | -------------- | ------------- |
| `scan_queue.py` notify call: wrong arg order | `notify_scan_complete(app.state.settings, scan_id, scan_result)` — TypeError at runtime, notifications never fire | `notify_scan_complete(scan_result, None, app.state.settings)` — correct order, matches function signature `(scan_result, delta, settings)` |
| Regression test coverage | Not tested | `test_worker_calls_notify_with_correct_arg_order` asserts ScanResultSchema is first positional arg to Slack sender |

All 5 success criteria are now verified. Phase 5 goal is achieved. Remaining human verification items (live Slack/email delivery) are operational concerns, not implementation gaps.

---

_Verified: 2026-03-19_
_Verifier: Claude (gsd-verifier)_
