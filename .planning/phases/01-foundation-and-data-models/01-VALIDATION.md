---
phase: 1
slug: foundation-and-data-models
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-18
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio + httpx |
| **Config file** | pyproject.toml [tool.pytest.ini_options] |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v --tb=short` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ -v --tb=short`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | INFRA-01 | smoke | `docker-compose up -d && curl -f http://localhost:8000/api/health` | No -- manual | ⬜ pending |
| 01-01-02 | 01 | 1 | INFRA-03 | unit | `pytest tests/test_config.py::test_yaml_loading -x` | ❌ W0 | ⬜ pending |
| 01-01-03 | 01 | 1 | INFRA-03 | unit | `pytest tests/test_config.py::test_env_override -x` | ❌ W0 | ⬜ pending |
| 01-01-04 | 01 | 1 | INFRA-04 | unit | `pytest tests/test_config.py::test_no_hardcoded_secrets -x` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 1 | SCAN-02 | unit | `pytest tests/test_models.py::test_severity_enum -x` | ❌ W0 | ⬜ pending |
| 01-02-02 | 02 | 1 | SCAN-02 | unit | `pytest tests/test_models.py::test_finding_severity -x` | ❌ W0 | ⬜ pending |
| 01-02-03 | 02 | 1 | INFRA-05 | integration | `pytest tests/test_models.py::test_sqlite_wal_mode -x` | ❌ W0 | ⬜ pending |
| 01-02-04 | 02 | 1 | INFRA-05 | integration | `pytest tests/test_models.py::test_db_persistence -x` | ❌ W0 | ⬜ pending |
| 01-03-01 | 03 | 2 | API-04 | integration | `pytest tests/test_health.py::test_health_endpoint -x` | ❌ W0 | ⬜ pending |
| 01-03-02 | 03 | 2 | SCAN-02 | unit | `pytest tests/test_fingerprint.py::test_fingerprint_determinism -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/conftest.py` — shared fixtures (async engine, test DB, test client)
- [ ] `tests/test_config.py` — config loading tests (YAML, env override, no secrets)
- [ ] `tests/test_health.py` — health endpoint test
- [ ] `tests/test_models.py` — model, severity enum, DB persistence, WAL mode tests
- [ ] `tests/test_fingerprint.py` — fingerprint determinism and normalization tests
- [ ] Framework install: `pip install pytest pytest-asyncio httpx` — none detected in project

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| docker-compose up starts FastAPI server | INFRA-01 | Requires Docker daemon | Run `docker-compose up -d`, then `curl -f http://localhost:8000/api/health`, verify 200 response |
| DB persists across container restarts | INFRA-05 | Requires Docker volume mount | Insert test data, `docker-compose down && docker-compose up -d`, verify data still present |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
