# aipix-security-scanner

**AI-powered security vulnerability scanner for the aipix.ai VSaaS platform.**

*Сканер безопасности с ИИ-анализом для платформы aipix.ai VSaaS.*

---

## Quick Start / Быстрый старт

### Prerequisites / Требования

- Docker & Docker Compose
- (Optional) Python 3.12+ for local development

### 5 minutes to first launch / 5 минут до первого запуска

```bash
# 1. Clone / Клонировать
git clone https://github.com/AlexTalorJr/naveksoft-security.git
cd naveksoft-security

# 2. Configure / Настроить
cp config.yml.example config.yml
# Edit config.yml as needed / Отредактируйте config.yml по необходимости

# 3. Set secrets / Установить секреты
export SCANNER_API_KEY="your-api-key"
export SCANNER_CLAUDE_API_KEY="your-claude-key"

# 4. Launch / Запустить
docker compose up -d

# 5. Verify / Проверить
curl http://localhost:8000/api/health
```

Expected response / Ожидаемый ответ:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime_seconds": 5.23,
  "database": "ok"
}
```

### Local Development / Локальная разработка

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run tests / Запуск тестов
python -m pytest tests/ -v

# Run specific phase tests / Тесты конкретной фазы
python -m pytest tests/phase_01/ -v

# Start dev server / Запуск dev-сервера
uvicorn scanner.main:app --reload
```

## Project Status / Статус проекта

| Phase | Description | Status |
|-------|------------|--------|
| 1 | Foundation & Data Models | Done |
| 2 | Scanner Adapters & Orchestration | Planned |
| 3 | AI Analysis (Claude API) | Planned |
| 4 | Report Generation (HTML/PDF) | Planned |
| 5 | Dashboard & Quality Gate | Planned |
| 6 | CI/CD Integration (Jenkins) | Planned |

## Documentation / Документация

| Document | Description / Описание |
|----------|----------------------|
| [Architecture](docs/architecture.md) | System design, data flow / Архитектура, потоки данных |
| [Database Schema](docs/database-schema.md) | SQLite schema, ER diagram / Схема БД, ER-диаграмма |
| [API Reference](docs/api.md) | REST API endpoints / Справочник API |
| [User Guide](docs/user-guide.md) | Reports, findings / Отчёты, результаты |
| [Admin Guide](docs/admin-guide.md) | Configuration, tuning / Настройка, конфигурация |
| [DevOps Guide](docs/devops-guide.md) | Docker, Jenkins, backups / Деплой, бэкапы |
| [Transfer Guide](docs/transfer-guide.md) | Migration to new server / Миграция на новый сервер |
| [Custom Rules](docs/custom-rules.md) | Writing Semgrep rules / Написание правил Semgrep |
| [Changelog](CHANGELOG.md) | Version history / История версий |

## Tech Stack / Стек технологий

- **Python 3.12** — core language
- **FastAPI** — REST API + web dashboard
- **SQLAlchemy 2.0** — async ORM
- **SQLite (WAL mode)** — local database
- **Pydantic v2** — data validation & settings
- **Docker** — containerization
- **Alembic** — database migrations

## License / Лицензия

Apache 2.0
