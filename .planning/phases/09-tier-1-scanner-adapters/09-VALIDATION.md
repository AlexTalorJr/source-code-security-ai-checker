---
phase: 9
slug: tier-1-scanner-adapters
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-21
---

# Phase 9 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `python -m pytest tests/phase_09/ -x -q` |
| **Full suite command** | `python -m pytest tests/ -x -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/phase_09/ -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 09-01-01 | 01 | 0 | ALL | scaffold | `python -m pytest tests/phase_09/ -x -q` | ❌ W0 | ⬜ pending |
| 09-02-01 | 02 | 1 | SCAN-01 | unit | `python -m pytest tests/phase_09/test_adapter_gosec.py -x` | ❌ W0 | ⬜ pending |
| 09-02-02 | 02 | 1 | SCAN-02 | unit | `python -m pytest tests/phase_09/test_adapter_bandit.py -x` | ❌ W0 | ⬜ pending |
| 09-02-03 | 02 | 1 | SCAN-03 | unit | `python -m pytest tests/phase_09/test_adapter_brakeman.py -x` | ❌ W0 | ⬜ pending |
| 09-02-04 | 02 | 1 | SCAN-04 | unit | `python -m pytest tests/phase_09/test_adapter_cargo_audit.py -x` | ❌ W0 | ⬜ pending |
| 09-03-01 | 03 | 2 | ALL | unit | `python -m pytest tests/phase_09/test_config_registration.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/phase_09/__init__.py` — package init
- [ ] `tests/phase_09/conftest.py` — shared fixtures (fixtures_dir, adapter instances, JSON loaders)
- [ ] `tests/phase_09/fixtures/gosec_output.json` — gosec sample with 2-3 findings
- [ ] `tests/phase_09/fixtures/bandit_output.json` — bandit sample with varying severity/confidence
- [ ] `tests/phase_09/fixtures/brakeman_output.json` — brakeman sample with High/Medium/Weak confidence
- [ ] `tests/phase_09/fixtures/cargo_audit_output.json` — cargo-audit sample with CVSS vectors and null CVSS
- [ ] `tests/phase_09/test_adapter_gosec.py` — stubs for SCAN-01
- [ ] `tests/phase_09/test_adapter_bandit.py` — stubs for SCAN-02
- [ ] `tests/phase_09/test_adapter_brakeman.py` — stubs for SCAN-03
- [ ] `tests/phase_09/test_adapter_cargo_audit.py` — stubs for SCAN-04
- [ ] `tests/phase_09/test_config_registration.py` — stubs for config.yml integration

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| HTML/PDF report includes scanner findings | ALL | Requires full pipeline execution with real tools | Run full scan on sample project, inspect generated report |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
