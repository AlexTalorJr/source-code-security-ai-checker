---
phase: 12
slug: rbac-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-22
---

# Phase 12 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio |
| **Config file** | `pyproject.toml` [tool.pytest.ini_options] |
| **Quick run command** | `pytest tests/phase_12/ -x -q` |
| **Full suite command** | `pytest tests/ -x -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/phase_12/ -x -q`
- **After every plan wave:** Run `pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 12-01-01 | 01 | 1 | INFRA-03 | unit | `pytest tests/phase_12/test_db_pragmas.py::test_busy_timeout -x` | ❌ W0 | ⬜ pending |
| 12-01-02 | 01 | 1 | AUTH-01 | integration | `pytest tests/phase_12/test_user_crud.py::test_admin_creates_user -x` | ❌ W0 | ⬜ pending |
| 12-01-03 | 01 | 1 | AUTH-02 | integration | `pytest tests/phase_12/test_dashboard_login.py::test_login_with_credentials -x` | ❌ W0 | ⬜ pending |
| 12-01-04 | 01 | 1 | AUTH-03 | integration | `pytest tests/phase_12/test_tokens.py::test_create_and_revoke_token -x` | ❌ W0 | ⬜ pending |
| 12-01-05 | 01 | 1 | AUTH-07 | integration | `pytest tests/phase_12/test_auth.py::test_unauthenticated_returns_401 -x` | ❌ W0 | ⬜ pending |
| 12-02-01 | 02 | 2 | AUTH-04 | integration | `pytest tests/phase_12/test_roles.py::test_admin_full_access -x` | ❌ W0 | ⬜ pending |
| 12-02-02 | 02 | 2 | AUTH-05 | integration | `pytest tests/phase_12/test_roles.py::test_viewer_restricted -x` | ❌ W0 | ⬜ pending |
| 12-02-03 | 02 | 2 | AUTH-06 | integration | `pytest tests/phase_12/test_roles.py::test_scanner_role_limits -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/phase_12/__init__.py` — package init
- [ ] `tests/phase_12/conftest.py` — shared fixtures (test user creation, auth_client with Bearer token, session factory)
- [ ] `tests/phase_12/test_db_pragmas.py` — INFRA-03 busy_timeout verification
- [ ] `tests/phase_12/test_auth.py` — AUTH-07 unauthenticated 401 + Bearer token auth flow
- [ ] `tests/phase_12/test_user_crud.py` — AUTH-01 admin user creation
- [ ] `tests/phase_12/test_dashboard_login.py` — AUTH-02 username/password login
- [ ] `tests/phase_12/test_tokens.py` — AUTH-03 token generation and revocation
- [ ] `tests/phase_12/test_roles.py` — AUTH-04, AUTH-05, AUTH-06 role enforcement
- [ ] Update `tests/phase_05/conftest.py` — migrate test fixtures from X-API-Key to Bearer auth

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Dashboard login page renders correctly | AUTH-02 | Visual layout verification | Navigate to /login, verify centered form with username/password fields matching dashboard CSS |
| Dashboard header shows role badge | AUTH-02 | Visual element | Log in, verify header shows "username (admin)" with logout link |
| Navigation hides forbidden links | AUTH-05 | Visual conditional rendering | Log in as viewer, verify no scan/config links visible |
| 403 page shows friendly message | AUTH-05 | Visual page content | As viewer, navigate to /settings directly, verify styled 403 with role explanation |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
