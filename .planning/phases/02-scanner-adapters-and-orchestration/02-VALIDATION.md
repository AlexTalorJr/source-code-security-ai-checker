---
phase: 2
slug: scanner-adapters-and-orchestration
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-18
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio (already installed) |
| **Config file** | `pyproject.toml` [tool.pytest.ini_options] |
| **Quick run command** | `pytest tests/phase_02/ -x -q` |
| **Full suite command** | `pytest tests/ -x -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/phase_02/ -x -q`
- **After every plan wave:** Run `pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | SCAN-01 | integration | `pytest tests/phase_02/test_orchestrator.py -x` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | SCAN-03 | unit | `pytest tests/phase_02/test_dedup.py -x` | ❌ W0 | ⬜ pending |
| 02-01-03 | 01 | 1 | SCAN-04 | unit | `pytest tests/phase_02/test_cli.py::test_scan_local_path -x` | ❌ W0 | ⬜ pending |
| 02-01-04 | 01 | 1 | SCAN-05 | unit | `pytest tests/phase_02/test_git.py -x` | ❌ W0 | ⬜ pending |
| 02-01-05 | 01 | 1 | SCAN-06 | unit | `pytest tests/phase_02/test_orchestrator.py::test_timeout_graceful -x` | ❌ W0 | ⬜ pending |
| 02-01-06 | 01 | 1 | SCAN-07 | manual-only | Manual timing test against aipix repo | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/phase_02/__init__.py` — package init
- [ ] `tests/phase_02/conftest.py` — shared fixtures (mock subprocess, temp dirs)
- [ ] `tests/phase_02/fixtures/` — sample tool output files for each adapter
- [ ] `tests/phase_02/test_adapter_semgrep.py` — Semgrep adapter parse tests
- [ ] `tests/phase_02/test_adapter_cppcheck.py` — cppcheck adapter parse tests
- [ ] `tests/phase_02/test_adapter_gitleaks.py` — Gitleaks adapter parse tests
- [ ] `tests/phase_02/test_adapter_trivy.py` — Trivy adapter parse tests
- [ ] `tests/phase_02/test_adapter_checkov.py` — Checkov adapter parse tests
- [ ] `tests/phase_02/test_orchestrator.py` — parallel exec, dedup, graceful degradation
- [ ] `tests/phase_02/test_dedup.py` — deduplication logic
- [ ] `tests/phase_02/test_git.py` — git clone module
- [ ] `tests/phase_02/test_cli.py` — CLI commands

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Total scan time under 10 minutes | SCAN-07 | Requires real aipix repo and all tools installed | Run `python -m scanner scan --path /path/to/aipix` and time the execution |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
