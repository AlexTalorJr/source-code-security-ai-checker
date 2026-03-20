# Coding Conventions

**Analysis Date:** 2026-03-20

## Naming Patterns

**Files:**
- Module files use `snake_case.py`: `scan_queue.py`, `html_report.py`, `email_sender.py`
- Adapter files are named after the tool: `semgrep.py`, `checkov.py`, `gitleaks.py`
- Schema files match their domain entity: `finding.py`, `scan.py`, `severity.py`
- ORM model files match the entity: `finding.py`, `scan.py`, `compound_risk.py`

**Classes:**
- PascalCase throughout: `ScannerAdapter`, `SemgrepAdapter`, `AIAnalyzer`, `ScannerSettings`
- Suffix conventions:
  - `*Adapter` for scanner tool wrappers: `SemgrepAdapter`, `CheckovAdapter`
  - `*Schema` for Pydantic data transfer objects: `FindingSchema`, `ScanResultSchema`
  - `*Settings` for configuration classes: `ScannerSettings`
  - `*Config` for nested configuration models: `AIConfig`, `GateConfig`, `ScannersConfig`
  - `*Error` for custom exceptions: `ScannerTimeoutError`, `ScannerExecutionError`
  - `*Response` for FastAPI response models: `ScanResponse`, `FindingResponse`
  - `*Request` for FastAPI request bodies: `ScanRequest`

**Functions:**
- `snake_case` throughout: `deduplicate_findings`, `run_scan`, `group_by_component`
- Private helpers prefixed with `_`: `_run_adapter`, `_normalize_path`, `_gate_int_to_bool`
- Internal module helpers use leading underscore: `_make_finding`, `_mock_create_response` (test helpers)
- Async functions that are private: `_execute`, `_run_adapter`

**Variables:**
- `snake_case`: `target_path`, `scan_result`, `enriched_findings`
- Constants in `UPPER_SNAKE_CASE`: `SEMGREP_SEVERITY_MAP`, `ALL_ADAPTERS`, `ALL_EN_DOCS`
- Loop variables are short and descriptive: `adapter`, `finding`, `scan`

**Types:**
- Type annotations are used consistently throughout the codebase
- Modern union syntax (`X | Y`) used instead of `Optional[X]` (Python 3.12)
- Return types always annotated on public functions
- `list[str]` not `List[str]`, `dict[str, int]` not `Dict[str, int]`

## Code Style

**Formatting:**
- No explicit formatter config detected (no `.prettierrc`, `pyproject.toml` has no `[tool.ruff]` or `[tool.black]`)
- Indentation: 4 spaces
- Maximum line length appears to follow ~100 chars based on observed code

**Linting:**
- One `# noqa: SIM115` suppression found in `src/scanner/adapters/gitleaks.py:59`
- No linting config found in `pyproject.toml`

## Import Organization

**Order:**
1. Standard library imports (`import asyncio`, `import json`, `from datetime import datetime`)
2. Third-party imports (`from fastapi import ...`, `from sqlalchemy import ...`, `from anthropic import ...`)
3. Local application imports (`from scanner.adapters.base import ...`, `from scanner.schemas.finding import ...`)

**Path Aliases:**
- None — all imports use full package path: `from scanner.core.exceptions import ScannerExecutionError`
- Package installed in development mode, so `scanner.*` resolves from `src/scanner/`

**Example from `src/scanner/core/orchestrator.py`:**
```python
import asyncio
import json
import logging
from datetime import datetime

from scanner.adapters import ALL_ADAPTERS
from scanner.adapters.base import ScannerAdapter
from scanner.ai.schemas import AIAnalysisResult
from scanner.config import ScannerSettings
```

## Error Handling

**Custom Exception Hierarchy:**
- Base: `ScannerError(Exception)` in `src/scanner/core/exceptions.py`
- Subclasses carry context in `__init__`: `ScannerTimeoutError(tool_name, timeout)`, `ScannerExecutionError(tool_name, message, returncode)`
- Raised as concrete types, caught as broad `Exception` at integration boundaries

**Patterns:**
- Adapter errors are isolated per-tool and returned as exceptions inside tuples: `(tool_name, Exception)` — caller checks `isinstance(result, Exception)`
- AI analysis uses graceful degradation: `enrich_with_ai()` in `src/scanner/core/orchestrator.py` catches all exceptions and returns original findings unchanged
- Notification channels are independent: each channel wrapped in `try/except Exception` that logs warnings without propagating
- FastAPI endpoints raise `HTTPException` directly for HTTP error responses
- `finally` blocks used for cleanup (e.g., `cleanup_clone` always runs)

**Logging:**
- Module-level logger: `logger = logging.getLogger(__name__)`
- Used in orchestrator, AI analyzer, and notification service
- Log messages use `%s` format strings (not f-strings) with `logger.info("msg: %s", value)`
- Warnings include `exc_info=True` when logging caught exceptions

## Comments

**Module Docstrings:**
- Every `.py` file starts with a module-level docstring on line 1
- Format: one concise sentence describing the module's purpose
- Examples: `"""Semgrep scanner adapter -- parses JSON output into FindingSchema."""`
- Separator style: `--` used in adapter docstrings: `"""Scan orchestrator: parallel adapter execution, deduplication, and persistence."""`

**Class Docstrings:**
- All public classes have docstrings, typically 1–3 sentences
- Abstract base: `"""Base class defining the contract all scanner adapters must implement."""`

**Method Docstrings:**
- All public methods have Google-style docstrings with `Args:`, `Returns:`, `Raises:` sections
- Private methods use shorter inline comments
- Example from `src/scanner/adapters/base.py`:
```python
async def _execute(self, cmd: list[str], timeout: int) -> tuple[str, str, int]:
    """Execute a subprocess command with timeout.

    Args:
        cmd: Command and arguments to execute.
        timeout: Maximum execution time in seconds.

    Returns:
        Tuple of (stdout, stderr, returncode).

    Raises:
        ScannerTimeoutError: If the command exceeds the timeout.
    """
```

**Inline Comments:**
- Used sparingly for non-obvious logic: `# Exit code 1 means findings found (not an error).`
- Section separators in long functions: `# Deduplicate`, `# AI enrichment (graceful degradation)`
- Column inline comments for schema fields: `fingerprint: str  # SHA-256 hex, 64 chars`

## Function Design

**Size:** Functions are kept focused. The largest function is `run_scan` in `src/scanner/core/orchestrator.py` (~200 lines) — it is complex by necessity but well-commented with section headers.

**Parameters:**
- Settings objects passed explicitly: `settings: ScannerSettings` parameter style
- Optional parameters use `| None = None` default: `extra_args: list[str] | None = None`
- Callbacks passed as optional parameters: `progress_callback=None`, `on_complete=None`

**Return Values:**
- Tuples used for multi-value returns: `tuple[ScanResultSchema, list[FindingSchema], list[CompoundRiskSchema]]`
- Return types annotated on all public functions
- Predicates return `tuple[bool, list[str]]` (passed, reasons) — e.g., `GateConfig.evaluate()`

## Module Design

**Exports:**
- `__init__.py` files used to define public API for each package
- Adapters registry: `src/scanner/adapters/__init__.py` exports `ALL_ADAPTERS`
- Models: `src/scanner/models/__init__.py` exports `Base`, `Finding`, `ScanResult`

**Barrel Files:**
- Minimal use — only `adapters/__init__.py` and `models/__init__.py` consolidate exports
- Most modules are imported directly by full path

## Pydantic Usage

**Schemas:**
- Pydantic v2 `BaseModel` for data transfer objects in `src/scanner/schemas/`
- Pydantic `BaseSettings` (via `pydantic-settings`) for configuration in `src/scanner/config.py`
- Settings use `env_prefix="SCANNER_"` and `env_nested_delimiter="__"`
- YAML config loaded via `YamlConfigSettingsSource` at lowest priority
- Field metadata via `Field(default=..., description=...)`

**Two-Model Pattern:**
- Pydantic schemas (in `src/scanner/schemas/`) for in-process data and API contracts
- SQLAlchemy ORM models (in `src/scanner/models/`) for persistence
- Explicit mapping between them at persistence boundaries in `src/scanner/core/orchestrator.py`

---

*Convention analysis: 2026-03-20*
