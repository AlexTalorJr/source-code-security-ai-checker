---
phase: 15
slug: scan-profiles-and-documentation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-23
---

# Phase 15 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `tests/conftest.py` |
| **Quick run command** | `python -m pytest tests/phase15/ -x -q` |
| **Full suite command** | `python -m pytest tests/phase15/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/phase15/ -x -q`
- **After every plan wave:** Run `python -m pytest tests/phase15/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 15-01-01 | 01 | 1 | CONF-04 | unit | `pytest tests/phase15/test_profile_models.py` | ❌ W0 | ⬜ pending |
| 15-01-02 | 01 | 1 | CONF-04 | unit | `pytest tests/phase15/test_profile_config.py` | ❌ W0 | ⬜ pending |
| 15-01-03 | 01 | 1 | CONF-05 | integration | `pytest tests/phase15/test_profile_api.py` | ❌ W0 | ⬜ pending |
| 15-01-04 | 01 | 1 | CONF-05 | integration | `pytest tests/phase15/test_profile_scan.py` | ❌ W0 | ⬜ pending |
| 15-02-01 | 02 | 1 | CONF-04 | unit | `pytest tests/phase15/test_profile_dashboard.py` | ❌ W0 | ⬜ pending |
| 15-03-01 | 03 | 2 | INFRA-04 | unit | `pytest tests/phase15/test_docs_content.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/phase15/` — directory and `__init__.py`
- [ ] `tests/phase15/conftest.py` — shared fixtures (test config, mock profiles)
- [ ] `tests/phase15/test_profile_models.py` — stubs for CONF-04 (Pydantic model validation)
- [ ] `tests/phase15/test_profile_config.py` — stubs for CONF-04 (config.yml read/write)
- [ ] `tests/phase15/test_profile_api.py` — stubs for CONF-05 (CRUD endpoints)
- [ ] `tests/phase15/test_profile_scan.py` — stubs for CONF-05 (profile-filtered scan execution)
- [ ] `tests/phase15/test_profile_dashboard.py` — stubs for CONF-04 (dashboard profile tab)
- [ ] `tests/phase15/test_docs_content.py` — stubs for INFRA-04 (doc section existence)

*Existing infrastructure covers pytest framework; only phase-specific test files needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Profile card visual layout | CONF-04 | CSS/visual rendering | Open /dashboard/scanners, click Profiles tab, verify card grid displays |
| Doc translation quality | INFRA-04 | Language correctness | Spot-check RU/FR/ES/IT docs for coherent translations |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
