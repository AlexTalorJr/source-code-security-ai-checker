---
phase: 8
slug: plugin-registry-architecture
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-21
---

# Phase 8 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `python -m pytest tests/phase_08/ -x -q` |
| **Full suite command** | `python -m pytest tests/ -x -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/phase_08/ -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 08-01-01 | 01 | 0 | PLUG-01 | unit | `python -m pytest tests/phase_08/test_registry.py::test_load_adapter_from_config -x` | ❌ W0 | ⬜ pending |
| 08-01-02 | 01 | 0 | PLUG-01 | integration | `python -m pytest tests/phase_08/test_registry.py::test_register_new_scanner_config_only -x` | ❌ W0 | ⬜ pending |
| 08-01-03 | 01 | 0 | PLUG-02 | integration | `python -m pytest tests/phase_08/test_registry.py::test_all_existing_scanners_load -x` | ❌ W0 | ⬜ pending |
| 08-01-04 | 01 | 0 | PLUG-02 | unit | `python -m pytest tests/phase_08/test_orchestrator_registry.py::test_orchestrator_uses_registry -x` | ❌ W0 | ⬜ pending |
| 08-01-05 | 01 | 0 | PLUG-03 | unit | `python -m pytest tests/phase_08/test_registry.py::test_missing_adapter_class_warns -x` | ❌ W0 | ⬜ pending |
| 08-01-06 | 01 | 0 | PLUG-03 | unit | `python -m pytest tests/phase_08/test_registry.py::test_invalid_adapter_class_warns -x` | ❌ W0 | ⬜ pending |
| 08-01-07 | 01 | 0 | PLUG-03 | unit | `python -m pytest tests/phase_08/test_registry.py::test_non_subclass_rejected -x` | ❌ W0 | ⬜ pending |
| 08-01-08 | 01 | 0 | PLUG-03 | integration | `python -m pytest tests/phase_08/test_api_scanners.py::test_load_error_in_api -x` | ❌ W0 | ⬜ pending |
| 08-01-09 | 01 | 0 | PLUG-04 | unit | `python -m pytest tests/phase_08/test_registry.py::test_language_filtering -x` | ❌ W0 | ⬜ pending |
| 08-01-10 | 01 | 0 | PLUG-04 | unit | `python -m pytest tests/phase_08/test_registry.py::test_universal_scanner -x` | ❌ W0 | ⬜ pending |
| 08-01-11 | 01 | 0 | PLUG-04 | unit | `python -m pytest tests/phase_08/test_language_detect.py::test_config_driven_languages -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/phase_08/__init__.py` — package init
- [ ] `tests/phase_08/test_registry.py` — registry loading, validation, language filtering
- [ ] `tests/phase_08/test_orchestrator_registry.py` — orchestrator using registry instead of ALL_ADAPTERS
- [ ] `tests/phase_08/test_api_scanners.py` — GET /api/scanners endpoint
- [ ] `tests/phase_08/test_language_detect.py` — config-driven language detection
- [ ] `tests/phase_08/test_config_migration.py` — all 8 scanners parse from updated config.yml
- [ ] Update `tests/phase_02/test_orchestrator.py` — remove ALL_ADAPTERS mocking, use registry mocking

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Config migration from old format | PLUG-02 | One-time migration path | 1. Backup config.yml 2. Run app with old format 3. Verify warning + auto-migration |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
