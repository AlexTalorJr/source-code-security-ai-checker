# Testing Patterns

**Analysis Date:** 2026-03-20

## Test Framework

**Runner:**
- `pytest` (version from `.venv`, pytest-asyncio 9.0.2 detected in pycache)
- Config: `pyproject.toml` under `[tool.pytest.ini_options]`
- `asyncio_mode = "auto"` — all async test functions and fixtures run automatically without explicit `@pytest.mark.asyncio` decoration (though some tests still include the marker redundantly)

**Assertion Library:**
- pytest built-in `assert` — no additional assertion library

**Run Commands:**
```bash
.venv/bin/python -m pytest                   # Run all tests (320 tests)
.venv/bin/python -m pytest tests/phase_05/  # Run a specific phase
.venv/bin/python -m pytest -k test_semgrep  # Run tests matching a keyword
.venv/bin/python -m pytest --collect-only -q # List collected tests
```

## Test File Organization

**Location:**
- Separate `tests/` directory at project root — NOT co-located with source
- Tests are organized into phase subdirectories: `tests/phase_01/` through `tests/phase_06/`
- Each phase directory has its own `conftest.py` with phase-specific fixtures
- Fixtures JSON files live in `tests/phase_02/fixtures/`

**Naming:**
- Test files: `test_<subject>.py` — e.g., `test_adapter_semgrep.py`, `test_orchestrator_ai.py`
- Test classes: `Test<Subject>` — e.g., `TestGroupByComponent`, `TestAnalyzeComponentCalls`
- Test functions: `test_<behavior>` — e.g., `test_semgrep_severity_mapping`, `test_create_and_read_scan`

**Structure:**
```
tests/
├── __init__.py
├── conftest.py                         # (root-level, currently minimal)
├── phase_01/
│   ├── __init__.py
│   ├── conftest.py                     # Phase fixtures (config, env cleanup)
│   ├── test_config.py
│   ├── test_fingerprint.py
│   ├── test_health.py
│   └── test_models.py
├── phase_02/
│   ├── conftest.py                     # Fixture loaders for tool outputs
│   ├── fixtures/                       # Real tool output JSON/XML files
│   │   ├── semgrep_output.json
│   │   ├── trivy_output.json
│   │   ├── gitleaks_output.json
│   │   ├── checkov_output.json
│   │   └── cppcheck_output.xml
│   ├── test_adapter_semgrep.py
│   ├── test_adapter_trivy.py
│   └── ...
├── phase_03/
│   ├── conftest.py                     # sample_findings, mock AI responses
│   └── test_analyzer.py
├── phase_04/
│   ├── conftest.py                     # sample_findings, sample_scan_result
│   └── test_charts.py, test_delta.py, ...
├── phase_05/
│   ├── conftest.py                     # auth_client, seed_scan, seed_findings
│   └── test_scan_api.py, test_auth.py, ...
└── phase_06/
    └── test_docs.py, test_makefile.py, test_package.py, test_backup_restore.py
```

## Test Structure

**Suite Organization:**
```python
class TestGroupByComponent:
    def test_groups_by_top_level_directory(self, sample_findings):
        """Group description."""
        groups = group_by_component(sample_findings)
        assert "vms" in groups

    def test_files_without_slash_go_to_root(self):
        findings = [_make_finding("f" * 64, "Makefile")]
        groups = group_by_component(findings)
        assert "root" in groups
```

- Classes group related tests for a single function/behavior area
- Standalone `async def test_*()` functions used for simple adapter tests (phase_02)
- Test docstrings describe the expected behavior (used as test descriptions)

**Patterns:**
- Database tests use async fixtures that create real SQLite in `tmp_path`
- API tests use `httpx.AsyncClient` with `ASGITransport` against real FastAPI app
- Unit tests mock at the method level (`adapter._execute = AsyncMock(...)`)
- Each test method is self-contained — no shared state between tests

## Mocking

**Framework:** `unittest.mock` — `AsyncMock`, `MagicMock`, `patch`

**Patterns:**

Replacing async subprocess execution on adapters:
```python
adapter._execute = AsyncMock(return_value=(json.dumps(semgrep_output), "", 0))
findings = await adapter.run("/tmp/target", timeout=60)
```

Mocking the Anthropic client constructor via `patch`:
```python
with patch("scanner.ai.analyzer.AsyncAnthropic", return_value=mock_client):
    analyzer = AIAnalyzer(settings)
    findings, compound_risks, cost = await analyzer.analyze(sample_findings)
```

Chaining multiple mock responses in sequence:
```python
mock_client.messages.create.side_effect = [
    vms_response,       # first call
    ms_response,        # second call
    infra_response,     # third call
    corr_response,      # fourth call (correlation)
]
```

Building mock Claude tool_use responses:
```python
def _mock_create_response(analysis_data: dict, input_tokens: int = 500, output_tokens: int = 150):
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.input = analysis_data
    response = MagicMock()
    response.content = [text_block, tool_block]  # tool_use NOT at index 0
    response.usage = MagicMock(input_tokens=input_tokens, output_tokens=output_tokens)
    return response
```

**What to Mock:**
- External subprocess calls (`_execute` on adapters)
- Anthropic API client (`AsyncAnthropic` constructor)
- SMTP and HTTP webhook calls (Slack, email)

**What NOT to Mock:**
- SQLite database (real async SQLite in `tmp_path` used throughout)
- FastAPI application (real app created with `create_app()` in tests)
- Pydantic validation

## Fixtures and Factories

**Test Data:**
```python
@pytest.fixture
def sample_findings() -> list[FindingSchema]:
    """Five findings spanning different components and severities."""
    return [
        FindingSchema(
            fingerprint="a" * 64,
            tool="semgrep",
            rule_id="php.lang.security.injection.sql-injection",
            file_path="vms/app/Http/Controllers/AuthController.php",
            severity=Severity.CRITICAL,
            title="SQL injection in authentication",
        ),
        ...
    ]
```

**Helper factories in test files** (not fixtures):
```python
def _make_finding(
    fingerprint: str,
    file_path: str,
    severity: Severity = Severity.HIGH,
    title: str = "Test finding",
) -> FindingSchema:
    return FindingSchema(fingerprint=fingerprint, tool="semgrep", ...)
```

**Seed helpers in conftest for DB integration tests:**
```python
async def seed_scan(session: AsyncSession, status: str = "completed", ...) -> int:
    """Insert a ScanResult row and return the scan ID."""

async def seed_findings(session: AsyncSession, scan_id: int, count: int = 3) -> list[str]:
    """Insert N Finding rows for a scan and return their fingerprints."""
```
Located in `tests/phase_05/conftest.py`. Called directly from tests:
```python
async with auth_client._transport.app.state.session_factory() as session:
    async with session.begin():
        scan_id = await seed_scan(session, status="completed")
```

**Fixture Locations:**
- Phase-scoped fixtures: `tests/phase_XX/conftest.py`
- Tool output JSON fixtures: `tests/phase_02/fixtures/*.json` and `*.xml`
- Shared mock response fixtures: inline in `tests/phase_03/conftest.py`

**Environment fixtures:**
```python
@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Clear all SCANNER_* environment variables before each test."""
    for key in list(os.environ.keys()):
        if key.startswith("SCANNER_"):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("SCANNER_CONFIG_PATH", "/tmp/nonexistent_config.yml")
```
This `autouse=True` fixture in `tests/phase_01/conftest.py` auto-applies to all phase_01 tests.

## Coverage

**Requirements:** None enforced — no coverage configuration in `pyproject.toml`

**View Coverage:**
```bash
.venv/bin/python -m pytest --cov=scanner --cov-report=html
```

## Test Types

**Unit Tests (majority):**
- Scope: single class or function in isolation
- Adapters: mock `_execute`, verify parsing and normalization
- AI analyzer: mock `AsyncAnthropic`, verify response handling and cost tracking
- Config: real settings loading with env var injection via `monkeypatch`
- Located in all phase directories

**Integration Tests:**
- Scope: real async SQLite + real FastAPI app
- Database: `db_engine`/`db_session` fixtures create real SQLite in `tmp_path`
- API: `auth_client` fixture creates `AsyncClient` with full ASGI transport
- Located primarily in `tests/phase_01/test_models.py` and `tests/phase_05/`

**Meta/Structural Tests (phase_06):**
- `tests/phase_06/test_docs.py` — validates docs directory structure and content
- `tests/phase_06/test_makefile.py` — validates Makefile targets
- `tests/phase_06/test_package.py` — validates package contents
- `tests/phase_06/test_backup_restore.py` — validates backup/restore functionality

**E2E Tests:** Not used

## Common Patterns

**Async Testing:**
```python
# asyncio_mode = "auto" means no decorator needed on async tests
async def test_create_and_read_scan(self, db_session):
    scan = ScanResult(target_path="/tmp/test-repo", status="completed")
    db_session.add(scan)
    await db_session.commit()
    await db_session.refresh(scan)
    assert scan.id is not None
```

**Error/Exception Testing:**
```python
@pytest.mark.asyncio
async def test_semgrep_exit_code_2_raises_error(adapter):
    adapter._execute = AsyncMock(return_value=("", "fatal error", 2))
    with pytest.raises(ScannerExecutionError):
        await adapter.run("/tmp/target", timeout=60)
```

**Parametrize for doc/file validation:**
```python
@pytest.mark.parametrize("filename", ALL_EN_DOCS)
def test_docs_en_has_all_files(filename):
    filepath = DOCS_EN / filename
    assert filepath.is_file(), f"Missing docs/en/{filename}"
```

**xfail for planned but not-yet-implemented features:**
```python
@pytest.mark.xfail(reason="Created in Plan 04")
def test_readme_ru_exists():
    assert README_RU.is_file()
```

**API test using lifespan context manager:**
```python
@asynccontextmanager
async def _lifespan_client(app):
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
```
Located in `tests/phase_05/conftest.py`. Required to trigger FastAPI lifespan events (DB initialization).

## Total Test Count

320 tests collected across 6 phase directories.

---

*Testing analysis: 2026-03-20*
