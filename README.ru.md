# Source Code Security AI Scanner

Сканер безопасности исходного кода с ИИ-анализом.

> English documentation: [README.md](README.md)

## Быстрый старт

Запустите первое сканирование менее чем за 5 минут.

### Предварительные требования

- Docker и Docker Compose
- API-ключ Anthropic (для ИИ-анализа)

### Установка

```bash
# 1. Клонирование
git clone https://github.com/AlexTalorJr/source-code-security-ai-checker.git
cd source-code-security-ai-checker

# 2. Настройка конфигурации
cp config.yml.example config.yml
cp .env.example .env

# 3. Укажите секреты в .env
#    SCANNER_API_KEY=<ваш-api-ключ>
#    SCANNER_CLAUDE_API_KEY=<ваш-ключ-anthropic>

# 4. Запуск
docker compose up -d

# 5. Проверка
curl http://localhost:8000/api/health
```

Ожидаемый ответ:

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime_seconds": 5.23,
  "database": "ok"
}
```

## Веб-панель управления

Сканер включает встроенный веб-интерфейс по адресу `http://localhost:8000/dashboard/`.

**Вход:** используйте API-ключ, указанный в `SCANNER_API_KEY`.

### Запуск сканирования через панель управления

1. Откройте **История сканирований** (`/dashboard/history`)
2. Нажмите **"Start New Scan"** — форма развернётся
3. Заполните поле **Local Path** или **Repository URL** + **Branch**
4. Опционально отметьте **"Skip AI Analysis"** для запуска без Claude API (быстрее, без затрат)
5. Нажмите **"Start Scan"**

Сканирование выполняется в фоновом режиме. На странице подробностей отображается ход выполнения в реальном времени, результаты появляются автоматически по завершении.

### Страницы панели управления

| Страница | URL | Описание |
|----------|-----|----------|
| История сканирований | `/dashboard/history` | Список всех сканирований + форма запуска нового |
| Детали сканирования | `/dashboard/scans/{id}` | Уязвимости, разбивка по уровню, элементы управления подавлением |
| Тенденции | `/dashboard/trends` | Графики: уровень угроз во времени, распределение по инструментам |

### Запуск сканирования через API

```bash
curl -X POST http://localhost:8000/api/scans \
  -H "X-API-Key: $SCANNER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/your-org/your-repo.git", "branch": "main"}'
```

Чтобы пропустить ИИ-анализ для конкретного сканирования:

```bash
curl -X POST http://localhost:8000/api/scans \
  -H "X-API-Key: $SCANNER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/your-org/repo.git", "branch": "main", "skip_ai": true}'
```

## Интеграция с Jenkins Pipeline

Добавьте сканер как этап в ваш `Jenkinsfile` для блокировки деплоя при обнаружении уязвимостей уровня Critical/High.

### Базовый этап Jenkinsfile

```groovy
pipeline {
    agent any

    environment {
        SCANNER_URL = 'http://scanner-host:8000'
        SCANNER_API_KEY = credentials('scanner-api-key')
    }

    stages {
        stage('Security Scan') {
            steps {
                script {
                    // Trigger scan
                    def response = httpRequest(
                        url: "${SCANNER_URL}/api/scans",
                        httpMode: 'POST',
                        contentType: 'APPLICATION_JSON',
                        customHeaders: [[name: 'X-API-Key', value: "${SCANNER_API_KEY}"]],
                        requestBody: """{"repo_url": "${env.GIT_URL}", "branch": "${env.GIT_BRANCH}"}"""
                    )

                    def scan = readJSON text: response.content
                    def scanId = scan.id
                    echo "Scan started: #${scanId}"

                    // Poll until complete
                    def status = 'queued'
                    while (status == 'queued' || status == 'running') {
                        sleep 10
                        def progress = httpRequest(
                            url: "${SCANNER_URL}/api/scans/${scanId}/progress",
                            httpMode: 'GET'
                        )
                        status = readJSON(text: progress.content).stage
                    }

                    // Check quality gate
                    def result = httpRequest(
                        url: "${SCANNER_URL}/api/scans/${scanId}",
                        httpMode: 'GET',
                        customHeaders: [[name: 'X-API-Key', value: "${SCANNER_API_KEY}"]]
                    )
                    def scanResult = readJSON text: result.content

                    if (!scanResult.gate_passed) {
                        error "Security scan FAILED: ${scanResult.critical_count} Critical, ${scanResult.high_count} High findings"
                    }

                    echo "Security scan PASSED (${scanResult.total_findings} findings, gate passed)"
                }
            }
        }
    }
}
```

### Ключевые моменты

- **Quality gate** блокирует сборку при обнаружении уязвимостей уровня Critical или High (настраивается в `config.yml` в разделе `gate.fail_on`)
- **Сканирование по локальному пути** — если Jenkins и сканер используют общую файловую систему, укажите `"path": "${WORKSPACE}"` вместо `repo_url`
- **Пропуск ИИ-анализа** — добавьте `"skip_ai": true` в тело запроса для более быстрых сканирований без затрат на Claude API
- **Уведомления** — настройте Slack/email в `config.yml` для получения оповещений по завершении сканирования
- **Отчёты** — HTML и PDF отчёты создаются автоматически и доступны через `/api/scans/{id}/report` или панель управления

Смотрите [Руководство по DevOps](docs/ru/devops-guide.md) для получения полных сведений об интеграции с Jenkins, включая примеры пайплайнов с параллельными этапами.

## Возможности

- **12 сканеров безопасности с автоопределением** -- сканеры активируются автоматически на основе языков проекта через конфигурационный реестр плагинов
- **Поддержка множества языков** -- Python, PHP/Laravel, C/C++, JavaScript/TypeScript, Go, Rust, Java, C#, Ruby, Kotlin
- **ИИ-анализ** -- Claude анализирует результаты с учётом контекста, выявляет составные риски и предлагает исправления
- **Интерактивные отчёты в HTML и PDF** -- фильтрация результатов с контекстом кода и диаграммами
- **Настраиваемый шлюз качества** -- блокировка деплоя при обнаружении уязвимостей уровня Critical/High
- **Веб-панель управления** -- управление сканированиями, прогресс в реальном времени, история, контроль подавления ложных срабатываний
- **REST API** -- запуск сканирований, получение результатов, управление уязвимостями программным способом
- **Уведомления в Slack и по электронной почте** -- оповещения о завершении сканирования в реальном времени
- **Интеграция с Jenkins CI** -- этап пайплайна с проверкой шлюза качества
- **История сканирований с дельта-сравнением** -- отслеживание новых, исправленных и сохраняющихся уязвимостей
- **Пропуск ИИ для отдельного сканирования** -- запуск без Claude API, когда важна скорость или стоимость

## Поддерживаемые сканеры

Сканеры активируются автоматически на основе обнаруженных языков (`enabled: auto`). Можно переопределить для каждого сканера в `config.yml`.

| Сканер | Языки | Что обнаруживает |
|--------|-------|-----------------|
| **Semgrep** | Python, PHP, JS/TS, Go, Java, Ruby, C#, Rust | SAST — инъекции, проблемы аутентификации, небезопасные паттерны |
| **cppcheck** | C/C++ | Безопасность памяти, переполнение буфера, неопределённое поведение |
| **Gitleaks** | Любые | Захардкоженные секреты, API-ключи, токены в коде и истории git |
| **Trivy** | Docker, Terraform, K8s | CVE в образах контейнеров и некорректные конфигурации IaC |
| **Checkov** | Docker, Terraform, CI configs | Лучшие практики безопасности для Infrastructure-as-code |
| **Psalm** | PHP | Taint-анализ — SQL-инъекции, XSS через отслеживание потока данных |
| **Enlightn** | Laravel | CSRF, mass assignment, режим отладки, открытый .env (более 120 проверок) |
| **PHP Security Checker** | PHP (composer) | Известные CVE в зависимостях composer |
| **gosec** | Go | Захардкоженные учётные данные, SQL-инъекции, небезопасная криптография, небезопасные права файлов |
| **Bandit** | Python | Захардкоженные пароли, SQL-инъекции, eval, слабая криптография |
| **Brakeman** | Ruby/Rails | SQL-инъекции, XSS, mass assignment, инъекции команд |
| **cargo-audit** | Rust | Известные уязвимые зависимости через базу данных RustSec |

## Документация

| Документ | Описание |
|----------|----------|
| [Архитектура](docs/ru/architecture.md) | Архитектура системы, диаграмма компонентов, поток данных |
| [Схема базы данных](docs/ru/database-schema.md) | Схема SQLite, ER-диаграмма, индексы |
| [Справочник API](docs/ru/api.md) | REST API эндпоинты и аутентификация |
| [Руководство пользователя](docs/ru/user-guide.md) | Отчёты, уязвимости, шлюз качества, подавление |
| [Руководство администратора](docs/ru/admin-guide.md) | Конфигурация, переменные окружения, настройка |
| [Руководство по DevOps](docs/ru/devops-guide.md) | Развёртывание Docker, Jenkins, резервное копирование |
| [Руководство по переносу](docs/ru/transfer-guide.md) | Процедуры миграции сервера |
| [Пользовательские правила](docs/ru/custom-rules.md) | Написание правил Semgrep для aipix |

## Статус проекта

Все фазы v1.0 завершены.

| Фаза | Описание | Статус |
|------|----------|--------|
| 1 | Основа и модели данных | Готово |
| 2 | Адаптеры сканеров и оркестрация | Готово |
| 3 | ИИ-анализ (Claude API) | Готово |
| 4 | Генерация отчётов (HTML/PDF) | Готово |
| 5 | Панель управления, уведомления и шлюз качества | Готово |
| 6 | Упаковка, переносимость и документация | Готово |

## Стек технологий

- **Python 3.12** -- основной язык
- **FastAPI** -- REST API и веб-панель управления
- **SQLAlchemy 2.0** -- асинхронный ORM с SQLite
- **SQLite (WAL mode)** -- встроенная база данных
- **Pydantic v2** -- валидация данных и настройки
- **Docker** -- контейнеризация
- **Alembic** -- миграции базы данных
- **Anthropic Claude** -- ИИ-анализ уязвимостей
- **WeasyPrint** -- генерация PDF-отчётов
- **Jinja2** -- HTML-шаблонизация для отчётов и панели управления
- **Typer** -- интерфейс командной строки

## Лицензия

Apache 2.0

---

Другие языки: [English](README.md) | [Français](README.fr.md) | [Español](README.es.md) | [Italiano](README.it.md)
