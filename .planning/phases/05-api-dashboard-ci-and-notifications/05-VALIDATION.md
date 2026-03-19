---
phase: 5
slug: api-dashboard-ci-and-notifications
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-19
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `tests/conftest.py` (existing) |
| **Quick run command** | `python -m pytest tests/ -x -q --timeout=30` |
| **Full suite command** | `python -m pytest tests/ -v --timeout=60` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -x -q --timeout=30`
- **After every plan wave:** Run `python -m pytest tests/ -v --timeout=60`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | API-01 | integration | `pytest tests/test_api_scans.py -k "test_post_scan"` | ❌ W0 | ⬜ pending |
| 05-01-02 | 01 | 1 | API-02 | integration | `pytest tests/test_api_scans.py -k "test_get_scan"` | ❌ W0 | ⬜ pending |
| 05-01-03 | 01 | 1 | API-03 | integration | `pytest tests/test_api_auth.py -k "test_api_key"` | ❌ W0 | ⬜ pending |
| 05-01-04 | 01 | 1 | API-05 | integration | `pytest tests/test_api_suppression.py -k "test_false_positive"` | ❌ W0 | ⬜ pending |
| 05-01-05 | 01 | 1 | API-06 | integration | `pytest tests/test_api_scans.py -k "test_scan_queue"` | ❌ W0 | ⬜ pending |
| 05-02-01 | 02 | 1 | HIST-03 | integration | `pytest tests/test_dashboard.py -k "test_scan_history"` | ❌ W0 | ⬜ pending |
| 05-02-02 | 02 | 1 | HIST-04 | integration | `pytest tests/test_dashboard.py -k "test_trend_chart"` | ❌ W0 | ⬜ pending |
| 05-03-01 | 03 | 2 | CI-01 | unit | `pytest tests/test_ci_integration.py -k "test_jenkinsfile"` | ❌ W0 | ⬜ pending |
| 05-03-02 | 03 | 2 | CI-02 | unit | `pytest tests/test_ci_integration.py -k "test_workspace_path"` | ❌ W0 | ⬜ pending |
| 05-03-03 | 03 | 2 | CI-03 | unit | `pytest tests/test_ci_integration.py -k "test_quality_gate_fail"` | ❌ W0 | ⬜ pending |
| 05-04-01 | 04 | 2 | NOTF-01 | integration | `pytest tests/test_notifications.py -k "test_slack"` | ❌ W0 | ⬜ pending |
| 05-04-02 | 04 | 2 | NOTF-02 | integration | `pytest tests/test_notifications.py -k "test_email"` | ❌ W0 | ⬜ pending |
| 05-04-03 | 04 | 2 | NOTF-03 | integration | `pytest tests/test_notifications.py -k "test_channel_config"` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_api_scans.py` — stubs for API-01, API-02, API-06
- [ ] `tests/test_api_auth.py` — stubs for API-03
- [ ] `tests/test_api_suppression.py` — stubs for API-05
- [ ] `tests/test_dashboard.py` — stubs for HIST-03, HIST-04
- [ ] `tests/test_ci_integration.py` — stubs for CI-01, CI-02, CI-03
- [ ] `tests/test_notifications.py` — stubs for NOTF-01, NOTF-02, NOTF-03
- [ ] `tests/conftest.py` — shared fixtures (API test client, mock scan data, temp DB)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Dashboard visual layout | HIST-03 | Jinja2 template rendering needs browser | Open http://localhost:8000/dashboard, verify scan history table renders |
| Slack message formatting | NOTF-01 | Requires actual Slack webhook | Send test notification to dev webhook, verify Block Kit formatting |
| Email delivery | NOTF-02 | Requires SMTP server | Configure test SMTP, trigger scan, verify email received |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
