---
phase: 10
slug: infrastructure-and-documentation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-22
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (existing) |
| **Config file** | pyproject.toml (existing) |
| **Quick run command** | `python -m pytest tests/phase_10/ -x -v` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/phase_10/ -x -v`
- **After every plan wave:** Run `python -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 10-01-01 | 01 | 1 | INFRA-01 | smoke | `make verify-scanners` | ❌ W0 | ⬜ pending |
| 10-01-02 | 01 | 1 | INFRA-02 | integration | `make docker-multiarch` | ❌ W0 | ⬜ pending |
| 10-02-01 | 02 | 2 | DOCS-01 | unit | `python -m pytest tests/phase_10/test_docs_consistency.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/phase_10/__init__.py` — package init
- [ ] `tests/phase_10/conftest.py` — shared fixtures (doc file paths, scanner name list)
- [ ] `tests/phase_10/test_docs_consistency.py` — grep-based test that all doc files reference correct scanner count and all 12 scanner names
- [ ] `tests/smoke/` — sample project files for scanner verification (Go, Python, Ruby, Rust)
- [ ] Makefile `verify-scanners` target — scanner binary availability and smoke test

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Docker image runs with all 12 scanners | INFRA-01 | Requires Docker daemon | `docker-compose up -d && docker exec naveksoft-security make verify-scanners` |
| Multi-arch build succeeds | INFRA-02 | Requires Docker buildx + QEMU | `docker buildx build --platform linux/amd64,linux/arm64 .` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
