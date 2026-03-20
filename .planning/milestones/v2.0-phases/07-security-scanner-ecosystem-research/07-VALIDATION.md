---
phase: 7
slug: security-scanner-ecosystem-research
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-20
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (existing) |
| **Config file** | `tests/pytest.ini` or `pytest` section in `setup.cfg` |
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
| 7-01-01 | 01 | 1 | SCAN-01 | content validation | `grep -c "## SAST" .planning/phases/07-*/07-RESEARCH.md` | ❌ W0 | ⬜ pending |
| 7-01-02 | 01 | 1 | SCAN-02 | content validation | `grep -c "false positive" .planning/phases/07-*/07-RESEARCH.md` | ❌ W0 | ⬜ pending |
| 7-01-03 | 01 | 1 | SCAN-03 | content validation | `grep -c "DAST" .planning/phases/07-*/07-RESEARCH.md` | ❌ W0 | ⬜ pending |
| 7-01-04 | 01 | 1 | SCAN-04 | content validation | `grep -c "plugin\|adapter" .planning/phases/07-*/07-RESEARCH.md` | ❌ W0 | ⬜ pending |
| 7-01-05 | 01 | 1 | SCAN-05 | content validation | `grep -c "priority" .planning/phases/07-*/07-RESEARCH.md` | ❌ W0 | ⬜ pending |
| 7-01-06 | 01 | 1 | SCAN-06 | content validation | `grep -c "integration requirement" .planning/phases/07-*/07-RESEARCH.md` | ❌ W0 | ⬜ pending |
| 7-01-07 | 01 | 1 | SCAN-07 | content validation | `grep -c "license" .planning/phases/07-*/07-RESEARCH.md` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- Existing infrastructure covers all phase requirements — this is a research/documentation phase.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Tool research accuracy | SCAN-01 through SCAN-07 | Research quality requires human review | Review report sections for completeness, accuracy, and actionability |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
