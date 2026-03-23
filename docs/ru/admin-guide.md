# Руководство администратора

## Конфигурация

### Источники конфигурации (в порядке приоритета)

1. **Аргументы конструктора** -- программные переопределения
2. **Переменные окружения** -- префикс `SCANNER_*`
3. **Файл dotenv** -- файл `.env`
4. **Файловые секреты** -- секреты Docker/K8s
5. **YAML-файл конфигурации** -- `config.yml` (наименьший приоритет)

### Файл конфигурации

Скопируйте пример и настройте:

```bash
cp config.yml.example config.yml
```

## Настройка сканеров

Каждый из двенадцати инструментов сканирования может быть независимо настроен: включение/выключение, таймаут, дополнительные аргументы и автоопределение по языкам. Сканеры с `enabled: "auto"` активируются автоматически при обнаружении соответствующих файлов проекта.

```yaml
scanners:
  semgrep:
    adapter_class: "scanner.adapters.semgrep.SemgrepAdapter"
    enabled: true
    timeout: 180
    extra_args: ["--exclude", ".venv", "--exclude", "node_modules"]
    languages: ["python", "php", "javascript", "typescript", "go", "java", "kotlin", "ruby", "csharp", "rust"]
  cppcheck:
    adapter_class: "scanner.adapters.cppcheck.CppcheckAdapter"
    enabled: true
    timeout: 120
    extra_args: ["-i.venv", "-inode_modules"]
    languages: ["cpp"]
  gitleaks:
    adapter_class: "scanner.adapters.gitleaks.GitleaksAdapter"
    enabled: true
    timeout: 120
    extra_args: []
    languages: []
  trivy:
    adapter_class: "scanner.adapters.trivy.TrivyAdapter"
    enabled: true
    timeout: 120
    extra_args: []
    languages: ["docker", "terraform", "yaml"]
  checkov:
    adapter_class: "scanner.adapters.checkov.CheckovAdapter"
    enabled: true
    timeout: 120
    extra_args: ["--skip-path", ".venv", "--skip-path", "node_modules"]
    languages: ["docker", "terraform", "yaml", "ci"]
  psalm:
    adapter_class: "scanner.adapters.psalm.PsalmAdapter"
    enabled: "auto"
    timeout: 300
    extra_args: []
    languages: ["php"]
  enlightn:
    adapter_class: "scanner.adapters.enlightn.EnlightnAdapter"
    enabled: "auto"
    timeout: 120
    extra_args: []
    languages: ["laravel"]
  php_security_checker:
    adapter_class: "scanner.adapters.php_security_checker.PhpSecurityCheckerAdapter"
    enabled: "auto"
    timeout: 30
    extra_args: []
    languages: ["php"]
  gosec:
    adapter_class: "scanner.adapters.gosec.GosecAdapter"
    enabled: "auto"
    timeout: 120
    extra_args: []
    languages: ["go"]
  bandit:
    adapter_class: "scanner.adapters.bandit.BanditAdapter"
    enabled: "auto"
    timeout: 120
    extra_args: []
    languages: ["python"]
  brakeman:
    adapter_class: "scanner.adapters.brakeman.BrakemanAdapter"
    enabled: "auto"
    timeout: 120
    extra_args: []
    languages: ["ruby"]
  cargo_audit:
    adapter_class: "scanner.adapters.cargo_audit.CargoAuditAdapter"
    enabled: "auto"
    timeout: 60
    extra_args: []
    languages: ["rust"]
```

- **adapter_class** -- полный путь к Python-классу, реализующему адаптер сканера (см. раздел Реестр плагинов ниже)
- **enabled** -- установите `true` (всегда включён), `false` (всегда выключен) или `"auto"` (включается при обнаружении соответствующих файлов)
- **timeout** -- максимальное время выполнения в секундах до принудительной остановки
- **extra_args** -- дополнительные аргументы командной строки, передаваемые инструменту
- **languages** -- типы файлов, запускающие автоопределение; сканеры с пустым списком (например, Gitleaks) работают для всех проектов

## Реестр плагинов

Сканер использует конфигурационный реестр плагинов для динамической загрузки адаптеров сканеров из `config.yml`. Эта архитектура позволяет добавлять новые сканеры без изменения кода приложения.

### Как регистрируются сканеры

Каждая запись сканера в `config.yml` содержит поле `adapter_class`, указывающее полный путь к Python-классу, реализующему интерфейс `ScannerAdapter`. При запуске `ScannerRegistry` считывает все записи из раздела `scanners` и динамически импортирует каждый класс адаптера.

Поле `adapter_class` следует формату:

```
scanner.adapters.<module_name>.<ClassName>
```

Например: `scanner.adapters.gosec.GosecAdapter`

### Автоопределение языков

Сканеры с полем `languages` автоматически включаются, когда сканируемый репозиторий содержит соответствующие файлы. Оркестратор определяет расширения файлов в целевом репозитории и активирует сканеры, чей список `languages` пересекается с обнаруженными языками. Сканеры с пустым списком `languages` (как Gitleaks) всегда работают независимо от типа проекта.

### Добавление нового сканера

Чтобы добавить новый сканер на платформу:

1. **Создайте класс адаптера**, реализующий интерфейс `ScannerAdapter`:

```python
# src/scanner/adapters/my_scanner.py
from scanner.adapters.base import ScannerAdapter
from scanner.schemas.finding import FindingSchema

class MyScannerAdapter(ScannerAdapter):
    async def run(self, target_path: str, timeout: int, extra_args: list[str] | None = None) -> list[FindingSchema]:
        # Execute scanner binary and parse output
        ...
        return findings
```

2. **Добавьте запись в `config.yml`** в раздел `scanners`:

```yaml
scanners:
  my_scanner:
    adapter_class: "scanner.adapters.my_scanner.MyScannerAdapter"
    enabled: "auto"
    timeout: 120
    extra_args: []
    languages: ["python"]
```

3. **Установите бинарный файл сканера** в Dockerfile, если это внешний инструмент.

Никаких других изменений кода не требуется. Реестр автоматически обнаруживает и загружает новый адаптер из конфигурации.

### Список зарегистрированных сканеров

Эндпоинт `/api/scanners` возвращает все зарегистрированные сканеры с их конфигурацией:

```bash
curl -H "Authorization: Bearer nvsec_your_token" http://localhost:8000/api/scanners
```

Ответ включает название, статус включения, настроенные языки и класс адаптера каждого сканера.

## Настройка ИИ

```yaml
ai:
  max_cost_per_scan: 5.0
  model: "claude-sonnet-4-6"
  max_findings_per_batch: 50
  max_tokens_per_response: 4096
```

| Параметр | Описание | По умолчанию |
|---------|----------|-------------|
| `max_cost_per_scan` | Максимальные затраты в USD на ИИ-анализ за сканирование | `5.0` |
| `model` | Идентификатор модели Claude | `claude-sonnet-4-6` |
| `max_findings_per_batch` | Максимум находок, отправляемых Claude за один запрос | `50` |
| `max_tokens_per_response` | Максимум токенов ответа от Claude | `4096` |

## Настройка шлюза качества

```yaml
gate:
  fail_on:
    - critical
    - high
  include_compound_risks: true
```

- **fail_on** -- список уровней серьёзности, при которых шлюз не проходит
- **include_compound_risks** -- при значении `true` составные риски с соответствующей серьёзностью также приводят к непрохождению шлюза

## Настройка уведомлений

### Slack

```yaml
notifications:
  slack:
    enabled: false
```

Укажите URL вебхука на верхнем уровне:

```yaml
slack_webhook_url: "https://hooks.slack.com/services/T.../B.../xxx"
```

Или через переменную окружения: `SCANNER_SLACK_WEBHOOK_URL`

### Электронная почта

```yaml
notifications:
  email:
    enabled: false
    recipients: ["security@example.com"]
    smtp_port: 587
    smtp_user: ""
    smtp_password: ""  # Используйте переменную окружения
    use_tls: true
```

Укажите хост SMTP на верхнем уровне:

```yaml
email_smtp_host: "smtp.example.com"
```

Или через переменную окружения: `SCANNER_EMAIL_SMTP_HOST`

Пароль SMTP следует задавать через вложенную переменную окружения: `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PASSWORD`

### URL панели управления

```yaml
dashboard_url: ""  # Например, http://scanner:8000/dashboard
```

Используется в сообщениях уведомлений для ссылки на результаты сканирования. Если пусто, определяется автоматически из хоста и порта.

## Переменные окружения

Все настройки могут быть переопределены с помощью префикса `SCANNER_`:

| Переменная | Описание | По умолчанию |
|-----------|----------|-------------|
| `SCANNER_HOST` | Адрес прослушивания | `0.0.0.0` |
| `SCANNER_PORT` | Порт прослушивания | `8000` |
| `SCANNER_DB_PATH` | Путь к файлу базы данных SQLite | `/data/scanner.db` |
| `SCANNER_API_KEY` | Ключ аутентификации API | `""` (пусто) |
| `SCANNER_CLAUDE_API_KEY` | API-ключ Anthropic для ИИ-анализа | `""` (пусто) |
| `SCANNER_SLACK_WEBHOOK_URL` | URL вебхука Slack | `""` |
| `SCANNER_EMAIL_SMTP_HOST` | Имя хоста SMTP-сервера | `""` |
| `SCANNER_LOG_LEVEL` | Уровень логирования (debug/info/warning/error) | `info` |
| `SCANNER_SCAN_TIMEOUT` | Глобальный таймаут сканирования в секундах | `600` |
| `SCANNER_CONFIG_PATH` | Путь к YAML-файлу конфигурации | `config.yml` |

### Вложенные переменные окружения

Для вложенных разделов конфигурации используйте двойное подчёркивание:

| Переменная | Соответствует |
|-----------|-------------|
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PASSWORD` | `notifications.email.smtp_password` |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PORT` | `notifications.email.smtp_port` |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_USER` | `notifications.email.smtp_user` |
| `SCANNER_NOTIFICATIONS__SLACK__ENABLED` | `notifications.slack.enabled` |

## Управление секретами

Никогда не храните секреты в `config.yml` и не коммитьте их в git.

```bash
# Установка секретов через переменные окружения:
export SCANNER_API_KEY="your-secure-key"
export SCANNER_CLAUDE_API_KEY="sk-ant-..."

# Или в docker-compose через файл .env:
echo "SCANNER_API_KEY=your-secure-key" >> .env
echo "SCANNER_CLAUDE_API_KEY=sk-ant-..." >> .env
```

## Управление базой данных

### Расположение

- Docker: `/data/scanner.db` (постоянный том `scanner_data`)
- Локально: настраивается через `SCANNER_DB_PATH`

### Режим WAL

SQLite работает в режиме WAL (Write-Ahead Logging) для повышения производительности параллельного чтения. Режим устанавливается автоматически при каждом соединении через обработчики событий SQLAlchemy.

### Резервное копирование

```bash
# Режим WAL позволяет горячее копирование (без остановки сканера)
docker cp naveksoft-security-scanner-1:/data/scanner.db ./backup/
```

## Настройка порогов

### Шлюз качества

Настройте уровни серьёзности, при которых шлюз не проходит:

```yaml
gate:
  fail_on:
    - critical        # Блокировать только при критических (мягкая политика)
```

Или включите medium:

```yaml
gate:
  fail_on:
    - critical
    - high
    - medium           # Более строгая политика
```

### Управление инструментами сканирования

Отключите инструменты, не относящиеся к вашей кодовой базе:

```yaml
scanners:
  cppcheck:
    enabled: false     # Нет кода на C/C++
  checkov:
    enabled: false     # Нет файлов IaC
```

## Настройка производительности

### Таймауты

- `scan_timeout` (глобальный): максимальная общая продолжительность сканирования (по умолчанию: 600 с)
- `timeout` для каждого сканера: максимальное время выполнения инструмента (по умолчанию: 120-180 с)

Если сканирования завершаются по таймауту, увеличьте таймаут для медленного сканера, а не глобальный таймаут.

### Размер пакета ИИ

Для больших сканирований с множеством находок настройте:

```yaml
ai:
  max_findings_per_batch: 25   # Меньшие пакеты для более быстрых ответов
  max_tokens_per_response: 8192  # Больше места для детального анализа
```

### Мониторинг

```bash
# Проверка состояния
curl http://localhost:8000/api/health

# Статус контейнера
docker compose ps

# Логи
docker compose logs scanner --tail 50
```

Docker Compose выполняет автоматические проверки состояния каждые 30 секунд.

## Управление пользователями (RBAC)

Security AI Scanner использует управление доступом на основе ролей (RBAC) для управления правами пользователей. Доступны три роли:

### Роли

| Действие | Admin | Viewer | Scanner |
|----------|-------|--------|---------|
| Запуск сканирования | Да | Нет | Да (только API) |
| Просмотр результатов | Да | Да | Да (только API) |
| Управление пользователями | Да | Нет | Нет |
| Настройка сканеров | Да | Нет | Нет |
| Управление профилями | Да | Нет | Нет |

- **Admin** -- полный доступ ко всем функциям, включая управление пользователями, настройку сканеров и управление профилями
- **Viewer** -- доступ только для чтения к результатам сканирования и отчётам через панель управления
- **Scanner** -- роль только для API: запуск сканирований и просмотр результатов программно

### Создание пользователей

Пользователи могут быть созданы двумя способами:

1. **Через панель управления** -- перейдите на `/dashboard/users` (только для админа) и заполните форму создания пользователя
2. **Через переменные окружения** -- установите `SCANNER_ADMIN_USER` и `SCANNER_ADMIN_PASSWORD` для создания учётной записи админа при первом запуске

Требования к паролю: минимум 8 символов.

### Деактивация пользователей

Админы могут деактивировать пользователей через панель управления или через API (`DELETE /api/users/{id}`). Деактивированные пользователи не могут входить в систему или использовать API-токены. Существующие токены деактивированных пользователей автоматически аннулируются.

## API-токены

API-токены обеспечивают программный доступ к API сканера с использованием Bearer-аутентификации.

### Генерация токенов

Перейдите на `/dashboard/tokens` для управления токенами. Нажмите "Создать токен" и укажите имя токена.

### Формат токена

Все токены используют префикс `nvsec_`:

```
nvsec_a1b2c3d4e5f6...
```

### Использование

Включите токен в заголовок `Authorization`:

```bash
curl -H "Authorization: Bearer nvsec_your_token_here" http://localhost:8000/api/scans
```

### Сроки действия

При создании токена выберите срок действия:

- 30 дней
- 90 дней
- 365 дней
- Без ограничения (бессрочный)

### Лимиты токенов

Каждый пользователь может иметь до 10 активных токенов (мягкий лимит).

### Отзыв токенов

Токены можно отозвать через панель управления (`/dashboard/tokens`) или через API (`DELETE /api/tokens/{id}`). Отозванные токены немедленно аннулируются.

## Интерфейс настройки сканеров

Веб-интерфейс настройки сканеров позволяет админам управлять параметрами сканеров, редактировать YAML-конфигурацию и управлять профилями сканирования -- всё из панели управления.

### Доступ к интерфейсу настройки

Перейдите на `/dashboard/scanners` (только для админа). Страница имеет три вкладки:

### Вкладка "Сканеры"

Отображает все зарегистрированные сканеры в виде карточек с:

- **Переключатель включения/выключения** -- переключение между ON, AUTO и OFF
- **Таймаут** -- максимальное время выполнения в секундах (30-900)
- **Дополнительные аргументы** -- дополнительные CLI-флаги, передаваемые инструменту

Изменения сохраняются индивидуально для каждого сканера и вступают в силу при следующем сканировании.

### Вкладка "YAML-редактор"

Редактор на основе CodeMirror для прямого редактирования `config.yml` с:

- Подсветкой синтаксиса YAML
- Полной валидацией конфигурации перед сохранением
- Сохранением форматирования исходного текста (форматирование и комментарии сохраняются)

### Вкладка "Профили"

Управление профилями сканирования (см. раздел "Профили сканирования" ниже).

## Профили сканирования

Профили сканирования -- это именованные пресеты сканеров, хранящиеся в `config.yml`. Каждый профиль определяет, какие сканеры запускать, и опционально переопределяет параметры для каждого сканера, такие как таймаут.

### Обзор

Профиль -- это явный список разрешений -- при выборе профиля запускаются только указанные в нём сканеры. Сканеры, не указанные в профиле, отключаются для данного сканирования.

### Создание профилей

Перейдите на `/dashboard/scanners` и выберите вкладку "Профили". Нажмите "Новый профиль" и укажите:

- **Имя** -- только буквы, цифры, дефисы и подчёркивания (например, `quick_scan`, `full-audit`)
- **Описание** -- необязательное описание
- **Сканеры** -- выберите сканеры для включения с опциональным переопределением таймаута

### Пример профилей в config.yml

```yaml
profiles:
  quick_scan:
    description: "Fast scan with essential tools only"
    scanners:
      semgrep: {}
      gitleaks: {}
  full_audit:
    description: "Comprehensive scan with all available tools"
    scanners:
      semgrep: {}
      gitleaks: {}
      trivy: {}
      checkov: {}
      cppcheck: {}
      bandit: {}
      gosec: {}
      brakeman: {}
      cargo_audit: {}
      psalm: {}
      enlightn: {}
      php_security_checker: {}
  dast_only:
    description: "DAST scan using Nuclei only"
    scanners:
      nuclei:
        timeout: 300
```

### Редактирование и удаление профилей

На вкладке "Профили" нажмите на карточку профиля для раскрытия формы редактирования. Измените параметры и нажмите "Сохранить" или нажмите "Удалить" для удаления профиля.

### Ограничения

- Максимум 10 профилей (мягкий лимит)
- Имена профилей могут содержать только буквы, цифры, дефисы и подчёркивания
- Зарезервированные слова YAML (`true`, `false`, `null`, `yes`, `no`, `on`, `off`) нельзя использовать как имена профилей

## DAST-сканирование

Динамическое тестирование безопасности приложений (DAST) сканирует работающие веб-приложения на наличие уязвимостей, отправляя HTTP-запросы и анализируя ответы.

### Обзор

DAST-сканирование работает на основе Nuclei -- быстрого и настраиваемого сканера уязвимостей. В отличие от SAST-инструментов, которые анализируют исходный код, DAST тестирует приложение как чёрный ящик, проверяя живые эндпоинты.

### Настройка Nuclei

Убедитесь, что сканер Nuclei включён в `config.yml`:

```yaml
scanners:
  nuclei:
    adapter_class: "scanner.adapters.nuclei.NucleiAdapter"
    enabled: true
    timeout: 300
    extra_args: []
    languages: []
```

### Запуск DAST-сканирования

DAST-сканирования требуют параметр `target_url` вместо `path` или `repo_url`:

**Через API:**

```bash
curl -X POST http://localhost:8000/api/scans \
  -H "Authorization: Bearer nvsec_your_token" \
  -H "Content-Type: application/json" \
  -d '{"target_url": "https://example.com"}'
```

**Через панель управления:** Введите целевой URL в поле URL формы запуска сканирования.

### DAST vs SAST

Параметр `target_url` является взаимоисключающим с `path` и `repo_url`. Нельзя комбинировать DAST и SAST цели в одном запросе сканирования.

### Результаты DAST

Результаты DAST отображаются в отчётах вместе с результатами SAST. Каждый результат DAST включает:

- Уровень серьёзности (critical, high, medium, low, info)
- Идентификатор шаблона Nuclei, определяющий тип уязвимости
- Целевой URL, где была обнаружена уязвимость
