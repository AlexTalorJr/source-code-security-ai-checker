# Riferimento API

## URL Base

```
http://localhost:8000
```

## Autenticazione

Tutti gli endpoint API eccetto `/api/health` richiedono una chiave API passata nell'header `X-API-Key`. La chiave è impostata tramite la variabile d'ambiente `SCANNER_API_KEY` e validata utilizzando un confronto sicuro rispetto al timing attack (`secrets.compare_digest`).

```bash
curl -H "X-API-Key: your-key" http://localhost:8000/api/scans
```

Le richieste senza una chiave valida ricevono una risposta `401 Unauthorized`.

## Endpoint

### GET /api/health

Endpoint di controllo integrità. Non richiede autenticazione.

**Risposta 200:**

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime_seconds": 3600.5,
  "database": "ok"
}
```

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `status` | string | `"healthy"` oppure `"degraded"` |
| `version` | string | Versione dello scanner da pyproject.toml |
| `uptime_seconds` | float | Secondi dall'avvio dell'applicazione |
| `database` | string | `"ok"` oppure `"error"` |

**Esempio:**

```bash
curl http://localhost:8000/api/health
```

---

### POST /api/scans

Avvia una nuova scansione di sicurezza. La scansione viene accodata e viene eseguita in modo asincrono in background.

**Corpo della richiesta:**

```json
{
  "path": "/path/to/local/code",
  "repo_url": "https://github.com/org/repo.git",
  "branch": "main"
}
```

| Campo | Tipo | Obbligatorio | Descrizione |
|-------|------|-------------|-------------|
| `path` | string | No | Percorso del filesystem locale da scansionare |
| `repo_url` | string | No | URL del repository Git da clonare e scansionare |
| `branch` | string | No | Branch da estrarre (predefinito: branch predefinito del repository) |

Fornire `path` oppure `repo_url`. Se viene fornito `repo_url`, lo scanner clona il repository prima della scansione.

**Risposta 202:**

```json
{
  "id": 1,
  "status": "queued"
}
```

**Codici di stato:** `202` Creato, `401` Non autorizzato, `422` Errore di validazione

**Esempio:**

```bash
curl -X POST http://localhost:8000/api/scans \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/org/repo.git", "branch": "main"}'
```

---

### GET /api/scans

Elenca tutte le scansioni, ordinate per data di creazione (dalla più recente).

**Risposta 200:**

```json
[
  {
    "id": 1,
    "repo_url": "https://github.com/org/repo.git",
    "branch": "main",
    "status": "completed",
    "started_at": "2026-03-20T10:00:00Z",
    "completed_at": "2026-03-20T10:05:00Z",
    "gate_passed": true
  }
]
```

**Esempio:**

```bash
curl -H "X-API-Key: your-key" http://localhost:8000/api/scans
```

---

### GET /api/scans/{id}

Ottiene i risultati dettagliati della scansione inclusi i risultati.

**Parametri di percorso:**

| Parametro | Tipo | Descrizione |
|-----------|------|-------------|
| `id` | integer | ID della scansione |

**Risposta 200:**

```json
{
  "id": 1,
  "repo_url": "https://github.com/org/repo.git",
  "branch": "main",
  "status": "completed",
  "started_at": "2026-03-20T10:00:00Z",
  "completed_at": "2026-03-20T10:05:00Z",
  "gate_passed": true,
  "findings": [
    {
      "id": 1,
      "tool": "semgrep",
      "rule_id": "python.lang.security.audit.exec-detected",
      "severity": "high",
      "file_path": "src/app.py",
      "line": 42,
      "message": "Use of exec() detected",
      "fingerprint": "abc123..."
    }
  ]
}
```

**Codici di stato:** `200` OK, `401` Non autorizzato, `404` Scansione non trovata

**Esempio:**

```bash
curl -H "X-API-Key: your-key" http://localhost:8000/api/scans/1
```

---

### POST /api/scans/{scan_id}/findings/{finding_id}/suppress

Sopprime un risultato (contrassegna come falso positivo).

**Parametri di percorso:**

| Parametro | Tipo | Descrizione |
|-----------|------|-------------|
| `scan_id` | integer | ID della scansione |
| `finding_id` | integer | ID del risultato |

**Corpo della richiesta:**

```json
{
  "reason": "False positive: test fixture data"
}
```

**Risposta 200:**

```json
{
  "status": "suppressed",
  "finding_id": 1,
  "reason": "False positive: test fixture data"
}
```

**Esempio:**

```bash
curl -X POST http://localhost:8000/api/scans/1/findings/5/suppress \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"reason": "False positive: test fixture"}'
```

---

### DELETE /api/scans/{scan_id}/findings/{finding_id}/suppress

Rimuove la soppressione da un risultato.

**Parametri di percorso:**

| Parametro | Tipo | Descrizione |
|-----------|------|-------------|
| `scan_id` | integer | ID della scansione |
| `finding_id` | integer | ID del risultato |

**Risposta 200:**

```json
{
  "status": "unsuppressed",
  "finding_id": 1
}
```

**Esempio:**

```bash
curl -X DELETE http://localhost:8000/api/scans/1/findings/5/suppress \
  -H "X-API-Key: your-key"
```

---

### GET /api/scanners

Elenco di tutti gli scanner registrati con la loro configurazione. Richiede autenticazione.

**Risposta 200:**

```json
[
  {
    "name": "semgrep",
    "enabled": true,
    "languages": ["python", "php", "javascript", "typescript", "go", "java", "kotlin", "ruby", "csharp", "rust"],
    "adapter_class": "scanner.adapters.semgrep.SemgrepAdapter"
  },
  {
    "name": "gosec",
    "enabled": "auto",
    "languages": ["go"],
    "adapter_class": "scanner.adapters.gosec.GosecAdapter"
  },
  {
    "name": "cargo_audit",
    "enabled": "auto",
    "languages": ["rust"],
    "adapter_class": "scanner.adapters.cargo_audit.CargoAuditAdapter"
  }
]
```

La risposta include tutti i 12 scanner registrati. L'esempio sopra mostra un sottoinsieme per brevita.

**Esempio:**

```bash
curl -H "X-API-Key: your-key" http://localhost:8000/api/scanners
```

---

### GET /api/trends

Ottiene le tendenze dei risultati nel tempo per i grafici di andamento.

**Risposta 200:**

```json
{
  "scans": [
    {
      "id": 1,
      "completed_at": "2026-03-20T10:05:00Z",
      "total_findings": 15,
      "critical": 1,
      "high": 3,
      "medium": 7,
      "low": 4
    }
  ]
}
```

**Esempio:**

```bash
curl -H "X-API-Key: your-key" http://localhost:8000/api/trends
```

## Dashboard

Una dashboard web è disponibile su `/dashboard` e fornisce un'interfaccia grafica per lo scanner:

| Route | Descrizione |
|-------|-------------|
| `GET /dashboard/login` | Pagina di accesso |
| `POST /dashboard/login` | Autenticazione con chiave API |
| `GET /dashboard/` | Panoramica della cronologia delle scansioni |
| `GET /dashboard/scans/{id}` | Dettaglio della scansione con risultati |
| `GET /dashboard/trends` | Grafici di andamento nel tempo |

La dashboard utilizza la stessa chiave API per l'autenticazione, memorizzata in un cookie di sessione dopo l'accesso. La soppressione e la rimozione della soppressione dei risultati sono disponibili direttamente dalla pagina di dettaglio della scansione.

## Risposte di Errore

Tutte le risposte di errore seguono un formato standard:

```json
{
  "detail": "Description of the error"
}
```

**Codici di stato comuni:**

| Codice | Significato |
|--------|------------|
| `401` | Chiave API mancante o non valida |
| `404` | Risorsa non trovata (ID scansione, ID risultato) |
| `422` | Errore di validazione (corpo della richiesta non valido) |

## Documentazione OpenAPI

FastAPI genera automaticamente la documentazione interattiva delle API:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json
