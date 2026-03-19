---
phase: 4
slug: reports-and-quality-gate
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-19
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `python -m pytest tests/phase_04/ -x -q` |
| **Full suite command** | `python -m pytest tests/ -x -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/phase_04/ -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | GATE-01, GATE-02, GATE-03 | unit | `python -m pytest tests/phase_04/test_gate.py -x` | ❌ W0 | ⬜ pending |
| 04-01-02 | 01 | 1 | HIST-02 | unit | `python -m pytest tests/phase_04/test_delta.py -x` | ❌ W0 | ⬜ pending |
| 04-02-01 | 02 | 2 | RPT-01, RPT-02, RPT-04 | unit | `python -m pytest tests/phase_04/test_html_report.py -x` | ❌ W0 | ⬜ pending |
| 04-02-02 | 02 | 2 | RPT-03 | unit | `python -m pytest tests/phase_04/test_pdf_report.py -x` | ❌ W0 | ⬜ pending |
| 04-02-03 | 02 | 2 | RPT-03 | unit | `python -m pytest tests/phase_04/test_charts.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/phase_04/__init__.py` — package init
- [ ] `tests/phase_04/conftest.py` — shared fixtures (sample ScanResultSchema, FindingSchema list, CompoundRiskSchema list)
- [ ] `tests/phase_04/test_html_report.py` — stubs for RPT-01, RPT-02, RPT-04
- [ ] `tests/phase_04/test_pdf_report.py` — stubs for RPT-03
- [ ] `tests/phase_04/test_gate.py` — stubs for GATE-01, GATE-02, GATE-03
- [ ] `tests/phase_04/test_delta.py` — stubs for HIST-01, HIST-02
- [ ] `tests/phase_04/test_charts.py` — stubs for chart generation (RPT-03)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| HTML report renders correctly in browser | RPT-01 | Visual layout verification | Open generated HTML file in Chrome, verify sidebar filters work, severity grouping visible |
| PDF report is readable and professional | RPT-03 | Visual quality check | Open generated PDF, verify charts render, executive summary readable |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
