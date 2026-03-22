# Руководство по пользовательским правилам

## Обзор

Данное руководство описывает создание пользовательских правил Semgrep для компонентов платформы aipix. Пользовательские правила позволяют обнаруживать специфичные для платформы уязвимости, которые универсальные правила пропускают.

## Целевые компоненты

| Компонент | Язык | Основные угрозы |
|-----------|------|----------------|
| VMS (Video Management) | PHP/Laravel | SQL-инъекции, обход аутентификации, IDOR |
| Mediaserver | C++ | Переполнение буфера, форматные строки, безопасность памяти |
| REST API | PHP/Laravel | Утечка API-токенов, SSRF, массовое присваивание |
| Webhooks | PHP | Отсутствие проверки подписи |
| Desktop Client | C# | Небезопасная десериализация, хранение учётных данных |

## Формат правил Semgrep

Правила Semgrep описываются в YAML-файлах с определениями сопоставления шаблонов. Каждое правило содержит:

- **id** -- уникальный идентификатор правила (используйте префикс `aipix.` для пользовательских правил)
- **pattern** -- шаблон кода для сопоставления (поддерживает метапеременные, например `$VAR`)
- **message** -- описание находки в читаемом виде
- **severity** -- `ERROR` (Critical/High), `WARNING` (Medium) или `INFO` (Low/Info)
- **languages** -- список языков, к которым применяется правило

## Расположение файлов правил

Пользовательские правила хранятся в директории `rules/` в корне проекта. Адаптер Semgrep автоматически загружает все файлы `.yml` из этой директории наряду с набором правил по умолчанию.

```
rules/
  aipix-rtsp-auth.yml
  aipix-api-security.yml
  aipix-memory-safety.yml
```

## Примеры правил

### Захардкоженные учётные данные RTSP

```yaml
rules:
  - id: aipix.rtsp-hardcoded-credentials
    pattern: rtsp://$USER:$PASS@$HOST
    message: "Hardcoded RTSP credentials detected"
    severity: ERROR
    languages: [php, python, yaml]
    metadata:
      category: authentication
      component: mediaserver
```

### API-токен в логах

```yaml
rules:
  - id: aipix.api-token-in-log
    patterns:
      - pattern: |
          Log::$METHOD(..., $TOKEN, ...)
      - metavariable-regex:
          metavariable: $TOKEN
          regex: ".*token.*|.*api_key.*|.*secret.*"
    message: "Possible API token logged -- check for sensitive data exposure"
    severity: WARNING
    languages: [php]
    metadata:
      category: data-exposure
      component: vms
```

### Отсутствие проверки подписи вебхука

```yaml
rules:
  - id: aipix.webhook-no-signature-check
    patterns:
      - pattern: |
          function $HANDLER(Request $request) {
            ...
          }
      - pattern-not: |
          function $HANDLER(Request $request) {
            ...
            $request->header('X-Signature', ...)
            ...
          }
    message: "Webhook handler missing signature verification"
    severity: ERROR
    languages: [php]
    metadata:
      category: authentication
      component: webhooks
```

### SQL-инъекция через необработанный запрос

```yaml
rules:
  - id: aipix.sql-injection-raw
    patterns:
      - pattern: DB::raw("..." . $VAR . "...")
    message: "Potential SQL injection via string concatenation in raw query"
    severity: ERROR
    languages: [php]
    metadata:
      category: injection
      component: vms
```

## Тестирование правил

Протестируйте пользовательские правила на примерах кода перед развёртыванием:

```bash
# Тестирование одного файла правил на целевой директории
semgrep --config rules/aipix-rtsp-auth.yml /path/to/code

# Тестирование всех пользовательских правил
semgrep --config rules/ /path/to/code

# Пробный запуск (показать совпадения без полного вывода)
semgrep --config rules/ --json /path/to/code | python3 -m json.tool
```

## Пользовательские правила для других сканеров

Помимо Semgrep, несколько других сканеров поддерживают настройку правил:

### gosec (Go)

gosec поддерживает включение и исключение определённых идентификаторов правил:

```yaml
scanners:
  gosec:
    extra_args: ["-include=G101,G201,G301"]
```

Используйте `-include` для запуска только определённых правил или `-exclude` для пропуска правил. Идентификаторы правил следуют шаблону `G1xx` (инъекции), `G2xx` (криптография), `G3xx` (файловый ввод/вывод), `G4xx` (сеть), `G5xx` (чёрный список).

### Bandit (Python)

Bandit поддерживает пользовательские профили через файлы конфигурации:

```yaml
scanners:
  bandit:
    extra_args: ["-c", "bandit.yml"]
```

Создайте профиль `bandit.yml` для включения/исключения определённых тестов (например, `B105`, `B201`) или настройки порогов серьёзности.

### Brakeman (Ruby/Rails)

Brakeman поддерживает фильтрацию по типам для фокусировки на определённых категориях уязвимостей:

```yaml
scanners:
  brakeman:
    extra_args: ["-t", "SQL,XSS,CommandInjection"]
```

Используйте `-t` для запуска только определённых типов проверок или `--except` для исключения типов.

## Рекомендации по разработке правил

1. **Начинайте с конкретного, расширяйте позже** -- начните с точных шаблонов и ослабляйте ограничения по мере необходимости
2. **Используйте метапеременные** -- `$VAR` сопоставляется с любым выражением, `$...ARGS` сопоставляется с несколькими аргументами
3. **Тестируйте на реальном коде** -- используйте реальные исходные файлы aipix для проверки правил
4. **Устанавливайте подходящую серьёзность** -- `ERROR` для эксплуатируемых проблем, `WARNING` для потенциальных рисков, `INFO` для качества кода
5. **Добавляйте метаданные** -- поля `category` и `component` помогают при фильтрации и формировании отчётов
