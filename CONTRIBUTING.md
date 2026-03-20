# Contributing to aipix-security-scanner

Thank you for your interest in contributing to the aipix-security-scanner project. This document provides guidelines for development setup, code style, and the pull request process.

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/AlexTalorJr/naveksoft-security.git
   cd naveksoft-security
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install the package in development mode with dev dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

4. Copy the example configuration:
   ```bash
   cp config.yml.example config.yml
   cp .env.example .env
   ```

5. Start a development server:
   ```bash
   SCANNER_DB_PATH=./dev.db uvicorn scanner.main:app --reload
   ```

## Running Tests

Run the full test suite:

```bash
make test
# or directly:
python -m pytest tests/ -v
```

Run tests for a specific phase:

```bash
python -m pytest tests/phase_01/ -v
python -m pytest tests/phase_02/ -v
python -m pytest tests/phase_03/ -v
python -m pytest tests/phase_04/ -v
python -m pytest tests/phase_05/ -v
python -m pytest tests/phase_06/ -v
```

Run a single test file:

```bash
python -m pytest tests/phase_01/test_schemas.py -v
```

## Code Style

- **Python version:** 3.12+ required
- **Type hints:** Required for all function signatures and public APIs
- **Async/await:** Use for all I/O operations (database, HTTP, file system)
- **Data validation:** Use Pydantic models for request/response schemas and configuration
- **Imports:** Standard library first, then third-party, then local -- separated by blank lines
- **Docstrings:** Google-style docstrings for public classes and functions

## Project Structure

```
src/scanner/           # Main application package
  api/                 # REST API routes and middleware
  dashboard/           # Web dashboard templates and routes
  reports/             # HTML/PDF report generation
  core/                # Business logic (orchestrator, AI analyzer)
  models/              # SQLAlchemy ORM models
  schemas/             # Pydantic data schemas

tests/phase_XX/        # Tests organized by implementation phase

docs/en/               # English documentation
docs/ru/               # Russian documentation

alembic/               # Database migration scripts
```

## Pull Request Process

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and add tests for new functionality

3. Ensure all tests pass:
   ```bash
   make test
   ```

4. Update documentation if your changes affect:
   - API endpoints (update `docs/en/api.md` and `docs/ru/api.md`)
   - Configuration options (update `config.yml.example` and `.env.example`)
   - Deployment or operations (update relevant guide in `docs/en/` and `docs/ru/`)

5. Submit a pull request with a clear description of:
   - What the change does
   - Why it is needed
   - How to test it

## Reporting Issues

When reporting a bug or requesting a feature, please include:

- A clear description of the issue or feature request
- Steps to reproduce (for bugs)
- Expected vs actual behavior
- Error output or logs if applicable
- Scanner version (`curl http://localhost:8000/api/health` shows the version)
- Environment details (OS, Docker version, Python version)
