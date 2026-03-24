---
phase: 14
slug: scanner-configuration-ui
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-23
---

# Phase 14 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 + pytest-asyncio 1.3.0 |
| **Config file** | `pyproject.toml` ([tool.pytest.ini_options]) |
| **Quick run command** | `python -m pytest tests/phase_14/ -x -q` |
| **Full suite command** | `python -m pytest tests/ -x -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/phase_14/ -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 14-01-01 | 01 | 1 | CONF-01 | integration | `python -m pytest tests/phase_14/test_scanner_toggle.py -x` | ❌ W0 | ⬜ pending |
| 14-01-02 | 01 | 1 | CONF-01 | integration | `python -m pytest tests/phase_14/test_scanner_toggle.py::test_non_admin_forbidden -x` | ❌ W0 | ⬜ pending |
| 14-02-01 | 02 | 1 | CONF-02 | integration | `python -m pytest tests/phase_14/test_scanner_settings.py -x` | ❌ W0 | ⬜ pending |
| 14-02-02 | 02 | 1 | CONF-02 | unit | `python -m pytest tests/phase_14/test_scanner_settings.py::test_timeout_validation -x` | ❌ W0 | ⬜ pending |
| 14-02-03 | 02 | 1 | CONF-02 | unit | `python -m pytest tests/phase_14/test_scanner_settings.py::test_extra_args_validation -x` | ❌ W0 | ⬜ pending |
| 14-03-01 | 03 | 2 | CONF-03 | integration | `python -m pytest tests/phase_14/test_yaml_editor.py -x` | ❌ W0 | ⬜ pending |
| 14-03-02 | 03 | 2 | CONF-03 | integration | `python -m pytest tests/phase_14/test_yaml_editor.py::test_invalid_yaml -x` | ❌ W0 | ⬜ pending |
| 14-03-03 | 03 | 2 | CONF-03 | integration | `python -m pytest tests/phase_14/test_yaml_editor.py::test_schema_validation -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/phase_14/__init__.py` — package init
- [ ] `tests/phase_14/conftest.py` — shared fixtures (reuse Phase 12 pattern: test_env, auth_client, get_admin_token + add config.yml fixture)
- [ ] `tests/phase_14/test_scanner_toggle.py` — CONF-01 toggle tests
- [ ] `tests/phase_14/test_scanner_settings.py` — CONF-02 settings tests
- [ ] `tests/phase_14/test_yaml_editor.py` — CONF-03 YAML editor tests

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Card grid renders correctly with scanner data | CONF-01 | Visual layout | Load /dashboard/scanners, verify card grid displays all scanners |
| Three-state toggle visual feedback | CONF-01 | CSS interaction | Click toggle through On/Auto/Off states, verify visual indication |
| CodeMirror syntax highlighting | CONF-03 | Visual rendering | Open YAML tab, verify syntax colors and line numbers |
| Tab switching between Cards and YAML | CONF-03 | UI interaction | Switch tabs, verify content loads correctly each time |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
