# User Guide / Руководство пользователя

## What is aipix-security-scanner? / Что такое aipix-security-scanner?

A security scanning tool that analyzes source code for vulnerabilities, enriches findings with AI analysis, and produces actionable reports.

Инструмент сканирования безопасности, который анализирует исходный код на уязвимости, обогащает результаты ИИ-анализом и формирует отчёты с рекомендациями.

## Severity Levels / Уровни серьёзности

| Level | Action Required | Действие |
|-------|----------------|----------|
| **CRITICAL (5)** | Fix immediately, blocks deployment | Исправить немедленно, блокирует деплой |
| **HIGH (4)** | Fix before release | Исправить до релиза |
| **MEDIUM (3)** | Fix in current sprint | Исправить в текущем спринте |
| **LOW (2)** | Fix when convenient | Исправить при возможности |
| **INFO (1)** | Review, no action needed | Ознакомиться, действий не требуется |

## Checking Scanner Health / Проверка состояния сканера

```bash
curl http://localhost:8000/api/health
```

| Status | Meaning | Значение |
|--------|---------|----------|
| `healthy` | All systems operational | Все системы работают |
| `degraded` | Scanner running, database issue | Сканер работает, проблема с БД |

## Understanding Findings / Понимание результатов

Each finding contains / Каждая находка содержит:

| Field | Description | Описание |
|-------|-------------|----------|
| **tool** | Which scanner found it (semgrep, gitleaks, etc.) | Какой сканер нашёл (semgrep, gitleaks и т.д.) |
| **rule_id** | Specific rule that triggered | Конкретное правило, которое сработало |
| **file_path** | File where the issue is | Файл с проблемой |
| **line_start/end** | Exact location in file | Точное расположение в файле |
| **snippet** | Code fragment with the issue | Фрагмент кода с проблемой |
| **severity** | How serious (CRITICAL to INFO) | Серьёзность (CRITICAL до INFO) |
| **title** | Short summary | Краткое описание |
| **description** | Detailed explanation | Подробное объяснение |
| **recommendation** | How to fix | Как исправить |
| **ai_analysis** | AI-powered context (Phase 3) | ИИ-контекст (Фаза 3) |
| **fingerprint** | Unique ID for deduplication | Уникальный ID для дедупликации |

## Finding Deduplication / Дедупликация находок

Findings are deduplicated using a SHA-256 fingerprint computed from:
- File path (normalized)
- Rule ID (case-insensitive)
- Code snippet (whitespace-normalized)

Находки дедуплицируются с помощью SHA-256 отпечатка, вычисленного из пути к файлу, ID правила и фрагмента кода.

This means the same vulnerability won't appear twice across scans, even if whitespace or casing changes.

Одна и та же уязвимость не появится дважды в разных сканах, даже при изменении пробелов или регистра.

## Quality Gate / Контроль качества

*(Phase 5 — planned / планируется)*

The quality gate will block deployments when Critical or High severity findings are present.

Контроль качества будет блокировать деплой при наличии находок уровня Critical или High.

## Reports / Отчёты

*(Phase 4 — planned / планируется)*

- **HTML** — interactive report with code diffs and navigation
- **PDF** — formal report for management

- **HTML** — интерактивный отчёт с diff-ами кода и навигацией
- **PDF** — формальный отчёт для руководства
