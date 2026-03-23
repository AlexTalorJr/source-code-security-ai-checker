# Riferimento API

## URL Base

```
http://localhost:8000
```

## Autenticazione

Tutti gli endpoint API eccetto `/api/health` richiedono un token Bearer nell'header Authorization. Generare i token dalla dashboard (`/dashboard/tokens`) o tramite l'API di gestione dei token.

```bash
curl -H "Authorization: Bearer nvsec_your_token_here" http://localhost:8000/api/scans
```

Le richieste senza un token valido ricevono una risposta `401 Unauthorized`.

## Endpoint

### GET /api/health

Endpoint di controllo integrita. Non richiede autenticazione.

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

---

### POST /api/scans

Avviare una nuova scansione di sicurezza. La scansione viene accodata e viene eseguita in modo asincrono.

**Corpo della richiesta:**

```json
{
  "path": "/path/to/local/code",
  "repo_url": "https://github.com/org/repo.git",
  "branch": "main",
  "target_url": "https://example.com",
  "profile": "quick_scan"
}
```

| Campo | Tipo | Obbligatorio | Descrizione |
|-------|------|-------------|-------------|
| `path` | string | No | Percorso locale da scansionare |
| `repo_url` | string | No | URL del repository Git da clonare e scansionare |
| `branch` | string | No | Branch da estrarre (predefinito: branch predefinito) |
| `target_url` | string | No | URL per scansione DAST (esclusivo con `path`/`repo_url`) |
| `profile` | string | No | Nome del profilo di scansione da usare |
| `skip_ai` | boolean | No | Saltare l'analisi AI (predefinito: false) |

Fornire `path`, `repo_url` o `target_url`. Il campo `target_url` avvia una scansione DAST e non puo essere combinato con `path` o `repo_url`.

**Risposta 202:**

```json
{
  "id": 1,
  "status": "queued"
}
```

**Codici di stato:** `202` Creato, `400` Profilo non valido, `401` Non autorizzato, `422` Errore di validazione

**Esempi:**

```bash
# Scansione SAST
curl -X POST http://localhost:8000/api/scans \
  -H "Authorization: Bearer nvsec_your_token" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/org/repo.git", "branch": "main"}'

# Scansione SAST con profilo
curl -X POST http://localhost:8000/api/scans \
  -H "Authorization: Bearer nvsec_your_token" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/org/repo.git", "profile": "quick_scan"}'

# Scansione DAST
curl -X POST http://localhost:8000/api/scans \
  -H "Authorization: Bearer nvsec_your_token" \
  -H "Content-Type: application/json" \
  -d '{"target_url": "https://example.com"}'
```

---

### GET /api/scans

Elencare le scansioni con paginazione, ordinate per data di creazione (dalla piu recente).

---

### GET /api/scans/{id}

Ottenere informazioni dettagliate su una scansione.

---

### GET /api/scans/{scan_id}/findings

Risultati paginati per una scansione specifica.

---

### POST /api/scans/{scan_id}/findings/{finding_id}/suppress

Sopprimere un risultato (contrassegnare come falso positivo).

**Corpo della richiesta:**

```json
{
  "reason": "False positive: test fixture data"
}
```

---

### DELETE /api/scans/{scan_id}/findings/{finding_id}/suppress

Rimuovere la soppressione da un risultato.

---

### GET /api/scanners

Elenco di tutti gli scanner registrati con la loro configurazione.

---

### GET /api/trends

Tendenze dei risultati nel tempo per i grafici.

---

## Endpoint di Configurazione

### GET /api/config

Configurazione completa dello scanner in JSON. Solo admin.

```bash
curl -H "Authorization: Bearer nvsec_your_token" http://localhost:8000/api/config
```

---

### GET /api/config/yaml

Contenuto grezzo di `config.yml` come testo. Solo admin.

---

### PATCH /api/config/scanners/{scanner_name}

Aggiornare i parametri di un singolo scanner. Solo admin.

**Corpo della richiesta:**

```json
{
  "enabled": true,
  "timeout": 300,
  "extra_args": ["--exclude", ".venv"]
}
```

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `enabled` | bool/string | `true`, `false` o `"auto"` |
| `timeout` | integer | 30-900 secondi |
| `extra_args` | string[] | Argomenti CLI aggiuntivi |

---

### PUT /api/config/yaml

Sostituire `config.yml` con nuovo contenuto YAML. Solo admin. Il YAML viene validato prima della scrittura.

---

## Endpoint di Gestione dei Profili

### GET /api/config/profiles

Elenco di tutti i profili di scansione. Solo admin.

**Risposta 200:**

```json
{
  "profiles": {
    "quick_scan": {
      "description": "Fast scan with essential tools only",
      "scanners": {
        "semgrep": {},
        "gitleaks": {}
      }
    }
  }
}
```

---

### POST /api/config/profiles

Creare un nuovo profilo di scansione. Solo admin.

**Corpo della richiesta:**

```json
{
  "name": "quick_scan",
  "description": "Fast scan with essential tools only",
  "scanners": {
    "semgrep": {},
    "gitleaks": {}
  }
}
```

**Codici di stato:** `201` Creato, `400` Limite raggiunto, `409` Profilo esistente, `422` Errore di validazione

---

### GET /api/config/profiles/{name}

Ottenere un profilo per nome. Solo admin.

### PUT /api/config/profiles/{name}

Aggiornare un profilo esistente. Solo admin.

### DELETE /api/config/profiles/{name}

Eliminare un profilo di scansione. Solo admin.

---

## Endpoint di Gestione Utenti

### GET /api/users

Elenco di tutti gli utenti. Solo admin.

### POST /api/users

Creare un nuovo utente. Solo admin.

```json
{
  "username": "newuser",
  "password": "securepassword",
  "role": "viewer"
}
```

### GET /api/users/{id}

Ottenere un utente. Solo admin.

### PUT /api/users/{id}

Aggiornare un utente. Solo admin.

### DELETE /api/users/{id}

Disattivare un utente. Solo admin.

---

## Endpoint di Gestione dei Token

### GET /api/tokens

Elenco dei propri token API.

### POST /api/tokens

Creare un nuovo token API.

```json
{
  "name": "CI Pipeline",
  "expires_days": 90
}
```

### DELETE /api/tokens/{id}

Revocare un token API.

---

## Dashboard

Una dashboard web e disponibile su `/dashboard`:

| Route | Descrizione |
|-------|-------------|
| `GET /dashboard/login` | Pagina di accesso |
| `POST /dashboard/login` | Autenticazione con nome utente e password |
| `GET /dashboard/` | Panoramica della cronologia delle scansioni |
| `GET /dashboard/scans/{id}` | Dettaglio della scansione con risultati |
| `GET /dashboard/trends` | Grafici di andamento |
| `GET /dashboard/users` | Gestione utenti (solo admin) |
| `GET /dashboard/tokens` | Gestione token |
| `GET /dashboard/scanners` | Configurazione degli scanner (solo admin) |

La dashboard utilizza cookie di sessione per l'autenticazione (scadenza 7 giorni).

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
| `401` | Token Bearer mancante o non valido |
| `403` | Permessi insufficienti (verifica del ruolo fallita) |
| `404` | Risorsa non trovata (ID scansione, ID risultato, nome profilo) |
| `422` | Errore di validazione (corpo della richiesta non valido) |

## Documentazione OpenAPI

FastAPI genera automaticamente la documentazione interattiva delle API:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json
