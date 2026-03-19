---
phase: 3
slug: ai-analysis
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-19
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x + pytest-asyncio |
| **Config file** | `pyproject.toml` [tool.pytest.ini_options] |
| **Quick run command** | `python -m pytest tests/phase_03/ -x -q` |
| **Full suite command** | `python -m pytest tests/ -x -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/phase_03/ -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | AI-01 | unit (mocked API) | `python -m pytest tests/phase_03/test_analyzer.py::test_component_analysis -x` | ❌ W0 | ⬜ pending |
| 03-01-02 | 01 | 1 | AI-01 | unit | `python -m pytest tests/phase_03/test_prompts.py::test_system_prompt_content -x` | ❌ W0 | ⬜ pending |
| 03-01-03 | 01 | 1 | AI-02 | unit (mocked API) | `python -m pytest tests/phase_03/test_analyzer.py::test_fix_suggestion_format -x` | ❌ W0 | ⬜ pending |
| 03-01-04 | 01 | 1 | AI-02 | unit (mocked API) | `python -m pytest tests/phase_03/test_analyzer.py::test_null_fix_with_recommendation -x` | ❌ W0 | ⬜ pending |
| 03-02-01 | 02 | 1 | AI-03 | unit (mocked API) | `python -m pytest tests/phase_03/test_correlation.py::test_compound_risk_creation -x` | ❌ W0 | ⬜ pending |
| 03-02-02 | 02 | 1 | AI-03 | unit | `python -m pytest tests/phase_03/test_correlation.py::test_compound_risk_gate -x` | ❌ W0 | ⬜ pending |
| 03-03-01 | 03 | 1 | AI-04 | unit | `python -m pytest tests/phase_03/test_budget.py::test_budget_cutoff -x` | ❌ W0 | ⬜ pending |
| 03-03-02 | 03 | 1 | AI-04 | unit | `python -m pytest tests/phase_03/test_budget.py::test_severity_priority_order -x` | ❌ W0 | ⬜ pending |
| 03-03-03 | 03 | 1 | AI-04 | unit | `python -m pytest tests/phase_03/test_budget.py::test_cost_tracking -x` | ❌ W0 | ⬜ pending |
| 03-04-01 | 04 | 1 | AI-05 | unit | `python -m pytest tests/phase_03/test_graceful_degradation.py::test_api_unavailable -x` | ❌ W0 | ⬜ pending |
| 03-04-02 | 04 | 1 | AI-05 | unit | `python -m pytest tests/phase_03/test_graceful_degradation.py::test_no_api_key -x` | ❌ W0 | ⬜ pending |
| 03-04-03 | 04 | 1 | AI-05 | unit | `python -m pytest tests/phase_03/test_graceful_degradation.py::test_skip_reason_recorded -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/phase_03/__init__.py` — package init
- [ ] `tests/phase_03/conftest.py` — shared fixtures (mock AsyncAnthropic, sample findings, mock responses)
- [ ] `tests/phase_03/test_analyzer.py` — covers AI-01, AI-02 (component analysis, fix suggestions)
- [ ] `tests/phase_03/test_correlation.py` — covers AI-03 (compound risks, gate impact)
- [ ] `tests/phase_03/test_budget.py` — covers AI-04 (cost tracking, budget cutoff, priority ordering)
- [ ] `tests/phase_03/test_graceful_degradation.py` — covers AI-05 (API unavailable, missing key, skip reason)
- [ ] `tests/phase_03/test_prompts.py` — covers AI-01 (system prompt content, component context)
- [ ] `tests/phase_03/test_schemas.py` — AI response schema validation

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| AI analysis quality on real findings | AI-01 | Requires subjective assessment of AI output quality | Run scan against test repo, review AI analysis for accuracy and completeness |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
