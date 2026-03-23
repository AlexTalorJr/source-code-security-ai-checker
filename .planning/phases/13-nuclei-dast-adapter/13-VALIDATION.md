---
phase: 13
slug: nuclei-dast-adapter
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-23
---

# Phase 13 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x + pytest-asyncio |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `python -m pytest tests/phase_13/ -x -q` |
| **Full suite command** | `python -m pytest tests/ -x -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/phase_13/ -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 13-01-01 | 01 | 0 | DAST-01 | unit | `python -m pytest tests/phase_13/test_nuclei_adapter.py -x` | ❌ W0 | ⬜ pending |
| 13-01-02 | 01 | 0 | DAST-01 | unit | `python -m pytest tests/phase_13/test_nuclei_adapter.py::test_severity_mapping -x` | ❌ W0 | ⬜ pending |
| 13-01-03 | 01 | 0 | DAST-01 | unit | `python -m pytest tests/phase_13/test_nuclei_adapter.py::test_fingerprint -x` | ❌ W0 | ⬜ pending |
| 13-01-04 | 01 | 0 | DAST-01 | unit | `python -m pytest tests/phase_13/test_nuclei_adapter.py::test_execution_error -x` | ❌ W0 | ⬜ pending |
| 13-02-01 | 02 | 0 | DAST-02 | unit | `python -m pytest tests/phase_13/test_scan_request.py -x` | ❌ W0 | ⬜ pending |
| 13-02-02 | 02 | 0 | DAST-02 | unit | `python -m pytest tests/phase_13/test_dast_routing.py -x` | ❌ W0 | ⬜ pending |
| 13-02-03 | 02 | 0 | DAST-02 | unit | `python -m pytest tests/phase_13/test_dast_routing.py::test_sast_mode -x` | ❌ W0 | ⬜ pending |
| 13-03-01 | 03 | 2 | DAST-03 | manual | N/A — requires Docker build | N/A | ⬜ pending |
| 13-04-01 | 04 | 2 | DAST-04 | manual | N/A — visual verification | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/phase_13/__init__.py` — package init
- [ ] `tests/phase_13/conftest.py` — shared fixtures (sample JSONL output, mock subprocess)
- [ ] `tests/phase_13/fixtures/nuclei_output.jsonl` — sample Nuclei JSONL output
- [ ] `tests/phase_13/test_nuclei_adapter.py` — covers DAST-01
- [ ] `tests/phase_13/test_scan_request.py` — covers DAST-02 (API schema validation)
- [ ] `tests/phase_13/test_dast_routing.py` — covers DAST-02 (orchestrator routing)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Nuclei binary installs in Docker (x86_64 + ARM64) | DAST-03 | Requires Docker multi-arch build | Build image, run `nuclei -version` inside container on both architectures |
| Nuclei findings render in HTML report with tool badge | DAST-04 | Visual verification of report layout | Run DAST scan, open HTML report, verify nuclei findings appear with severity and template info |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
