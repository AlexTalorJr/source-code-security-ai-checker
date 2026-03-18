# Changelog / История изменений

All notable changes to this project will be documented in this file.

Все значимые изменения в проекте документируются в этом файле.

## [0.1.0] - 2026-03-18

### Phase 1: Foundation & Data Models / Фаза 1: Основы и модели данных

#### Added / Добавлено

- **Project skeleton** — Python package with `pyproject.toml`, hatchling build system
  Скелет проекта — Python-пакет с `pyproject.toml`, система сборки hatchling

- **Configuration system** — YAML config file + environment variable overrides (`SCANNER_*` prefix), Pydantic Settings
  Система конфигурации — YAML файл + переопределение через переменные окружения (префикс `SCANNER_`), Pydantic Settings

- **Pydantic schemas** — `FindingSchema`, `ScanResultSchema`, `Severity` IntEnum (CRITICAL=5 to INFO=1)
  Pydantic-схемы — `FindingSchema`, `ScanResultSchema`, `Severity` IntEnum (CRITICAL=5 до INFO=1)

- **Fingerprint module** — deterministic SHA-256 hashing for finding deduplication (normalizes paths, rules, snippets)
  Модуль отпечатков — детерминированное SHA-256 хеширование для дедупликации находок

- **SQLAlchemy ORM models** — `Finding` and `ScanResult` with async SQLite engine, WAL mode, foreign key enforcement
  SQLAlchemy ORM модели — `Finding` и `ScanResult` с асинхронным SQLite, WAL режим, внешние ключи

- **FastAPI application** — app factory with lifespan management, health endpoint (`GET /api/health`) with DB probe
  FastAPI приложение — фабрика с управлением жизненным циклом, эндпоинт здоровья с проверкой БД

- **Alembic** — migration skeleton configured for async SQLAlchemy (tables auto-created on startup for now)
  Alembic — скелет миграций для async SQLAlchemy (таблицы пока создаются автоматически при запуске)

- **Docker packaging** — `Dockerfile` (python:3.12-slim, non-root user), `docker-compose.yml` with persistent volume, health checks
  Docker-пакетирование — `Dockerfile` (python:3.12-slim, не-root пользователь), `docker-compose.yml` с persistent volume, health checks

- **Test suite** — 39 tests across 4 test files in `tests/phase_01/`
  Набор тестов — 39 тестов в 4 файлах в `tests/phase_01/`

- **Documentation** — full bilingual documentation suite (Russian/English)
  Документация — полный двуязычный набор документации (русский/английский)

#### Fixed / Исправлено

- Dockerfile: source code must be copied before `pip install .` (was causing `ModuleNotFoundError` at runtime)
  Dockerfile: исходный код должен копироваться до `pip install .` (вызывало `ModuleNotFoundError`)
