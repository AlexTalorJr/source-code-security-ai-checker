---
phase: 06
slug: packaging-portability-and-documentation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-20
---

# Phase 06 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `python -m pytest tests/phase_06/ -x -v` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/phase_06/ -x -v`
- **After every plan wave:** Run `python -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | INFRA-06 | unit | `python -m pytest tests/phase_06/test_makefile.py -x` | ❌ W0 | ⬜ pending |
| 06-01-02 | 01 | 1 | INFRA-08 | integration | `python -m pytest tests/phase_06/test_package.py -x` | ❌ W0 | ⬜ pending |
| 06-01-03 | 01 | 1 | INFRA-07 | integration | `python -m pytest tests/phase_06/test_backup_restore.py -x` | ❌ W0 | ⬜ pending |
| 06-01-04 | 01 | 1 | INFRA-02 | manual-only | N/A (requires Docker daemon with buildx) | N/A | ⬜ pending |
| 06-02-01 | 02 | 2 | DOC-01 | unit | `python -m pytest tests/phase_06/test_docs.py::test_readme -x` | ❌ W0 | ⬜ pending |
| 06-02-02 | 02 | 2 | DOC-02-09 | unit | `python -m pytest tests/phase_06/test_docs.py::test_docs_structure -x` | ❌ W0 | ⬜ pending |
| 06-02-03 | 02 | 2 | DOC-10 | unit | `python -m pytest tests/phase_06/test_docs.py::test_russian_docs -x` | ❌ W0 | ⬜ pending |
| 06-02-04 | 02 | 2 | DOC-11 | unit | `python -m pytest tests/phase_06/test_docs.py::test_meta_files -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/phase_06/` directory and `__init__.py`
- [ ] `tests/phase_06/test_makefile.py` — validates Makefile targets parse correctly
- [ ] `tests/phase_06/test_package.py` — validates package tarball contents
- [ ] `tests/phase_06/test_backup_restore.py` — validates backup/restore archive structure
- [ ] `tests/phase_06/test_docs.py` — validates documentation structure and completeness

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Docker multi-arch build | INFRA-02 | Requires Docker daemon with buildx and QEMU emulation | Run `docker buildx build --platform linux/amd64,linux/arm64 -t test .` and verify both manifests |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
