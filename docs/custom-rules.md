# Custom Rules Guide / Руководство по пользовательским правилам

## Overview / Обзор

*(Phase 2 — scanner adapters not yet implemented / адаптеры сканеров ещё не реализованы)*

This guide will cover writing custom Semgrep rules for the aipix platform components. Custom rules allow detection of platform-specific vulnerabilities that generic rules miss.

Это руководство будет описывать создание пользовательских правил Semgrep для компонентов платформы aipix. Пользовательские правила позволяют находить специфичные для платформы уязвимости, которые пропускают стандартные правила.

## Target Components / Целевые компоненты

| Component | Language | Key Concerns / Ключевые риски |
|-----------|----------|-------------------------------|
| VMS (Video Management) | PHP/Laravel | SQL injection, broken auth, IDOR |
| Mediaserver | C++ | Buffer overflow, format strings, memory safety |
| REST API | PHP/Laravel | API token exposure, SSRF, mass assignment |
| Webhooks | PHP | Missing signature verification |
| Desktop Client | C# | Insecure deserialization, credential storage |

## Planned Rule Categories / Планируемые категории правил

### RTSP Authentication / RTSP-аутентификация
- Unauthorized stream access detection
- Credential hardcoding in RTSP URLs
- Missing TLS for stream transport

### VMS API Security / Безопасность VMS API
- API token exposure in logs/responses
- Broken authorization checks
- Insecure direct object references on video endpoints

### Webhook Validation / Валидация вебхуков
- Missing HMAC signature verification
- Unvalidated webhook payloads
- Open redirect via webhook callbacks

### C++ Memory Safety / Безопасность памяти C++
- Buffer overflow patterns
- Format string vulnerabilities
- Use-after-free patterns
- Unchecked array bounds

### Kubernetes/Infrastructure / Kubernetes/Инфраструктура
- Exposed services without network policies
- Weak RBAC configurations
- Secrets in ConfigMaps

## Rule File Structure / Структура файла правил

*(Will be implemented in Phase 2 / Будет реализовано в Фазе 2)*

```yaml
# rules/aipix-rtsp-auth.yml
rules:
  - id: aipix.rtsp-hardcoded-credentials
    pattern: rtsp://$USER:$PASS@$HOST
    message: "Hardcoded RTSP credentials detected"
    severity: CRITICAL
    languages: [php, python, yaml]
    metadata:
      category: authentication
      component: mediaserver
```

## How Rules Will Be Used / Как будут использоваться правила

1. Custom rules stored in `rules/` directory / Правила в папке `rules/`
2. Semgrep adapter loads project rules + custom rules / Адаптер Semgrep загружает правила
3. Findings tagged with rule metadata / Находки маркируются метаданными правил
4. AI analysis provides additional context / ИИ-анализ добавляет контекст

## Contributing Rules / Добавление правил

*(Detailed instructions will be added when scanner adapters are implemented)*

*(Подробные инструкции будут добавлены при реализации адаптеров сканеров)*
