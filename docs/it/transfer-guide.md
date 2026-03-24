# Guida al Trasferimento

## Panoramica

Questa guida copre la migrazione di Security AI Scanner a un nuovo server, il trasferimento del progetto a un nuovo team, o la configurazione di un'installazione completamente nuova.

**Cosa viene trasferito:**
- Database SQLite (cronologia scansioni, risultati, soppressioni)
- File di configurazione (`config.yml`, `.env`)
- Report generati (HTML/PDF)

**Cosa NON viene trasferito:**
- Immagini Docker -- vengono ricostruite sull'host di destinazione dal sorgente
- Ambienti virtuali Python -- vengono ricreati durante `make install`

## Prerequisiti

L'host di destinazione necessita di:

- Docker Engine 20.10+
- Docker Compose v2+
- GNU Make
- Git (per clonare il repository)
- 2 GB RAM minimo
- 10 GB di spazio su disco

## Esportazione dalla Sorgente

Creare un archivio di backup sul server di origine:

```bash
cd /path/to/naveksoft-security

# Create timestamped backup (DB + reports + config)
make backup
# Output: backups/backup-YYYYMMDD_HHMMSS.tar.gz
```

Copiare l'archivio sull'host di destinazione:

```bash
scp backups/backup-*.tar.gz user@target-server:/tmp/
```

## Importazione nella Destinazione

### Installazione Nuova (Clone Git)

```bash
# On target server
git clone https://github.com/AlexTalorJr/naveksoft-security.git
cd naveksoft-security

# Configure
cp .env.example .env
# Edit .env with real values (see Environment Variables Reference below)

cp config.yml.example config.yml
# Edit config.yml if needed

# Build and start
make install
make run

# Run migrations
make migrate

# Verify
curl http://localhost:8000/api/health
```

### Ripristino dei Dati dal Backup

Se si dispone di un archivio di backup dal server di origine:

```bash
# After make install and make run:
make restore BACKUP=/tmp/backup-20260320_143000.tar.gz

# Restart to pick up restored data
docker compose restart

# Verify
curl http://localhost:8000/api/health
```

## Checklist di Onboarding

Seguire questi passaggi per mettere in funzione una nuova installazione:

1. Installare Docker e Docker Compose sull'host di destinazione
2. Clonare il repository:
   ```bash
   git clone https://github.com/AlexTalorJr/naveksoft-security.git
   cd naveksoft-security
   ```
3. Copiare i template di configurazione:
   ```bash
   cp config.yml.example config.yml
   cp .env.example .env
   ```
4. Impostare `SCANNER_API_KEY` -- generare una chiave sicura:
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
5. Impostare `SCANNER_CLAUDE_API_KEY` -- ottenere dalla [Console Anthropic](https://console.anthropic.com/)
6. Configurare le impostazioni di notifica se necessario:
   - Slack: impostare `SCANNER_SLACK_WEBHOOK_URL` in `.env`
   - Email: impostare `SCANNER_EMAIL_SMTP_HOST`, `SCANNER_NOTIFICATIONS__EMAIL__SMTP_USER`, `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PASSWORD` e `SCANNER_NOTIFICATIONS__EMAIL__RECIPIENTS` in `.env`
7. Costruire le immagini Docker:
   ```bash
   make install
   ```
8. Avviare lo scanner:
   ```bash
   make run
   ```
9. Eseguire le migrazioni del database:
   ```bash
   make migrate
   ```
10. Verificare l'endpoint di integrità:
    ```bash
    curl http://localhost:8000/api/health
    # Expected: {"status": "healthy", ...}
    ```
11. Eseguire la prima scansione:
    ```bash
    curl -X POST http://localhost:8000/api/scans \
      -H "Authorization: Bearer nvsec_your_token" \
      -H "Content-Type: application/json" \
      -d '{"path": "/path/to/code"}'
    ```

## Riferimento Variabili d'Ambiente

Tutte le variabili utilizzano il prefisso `SCANNER_`. Impostarle nel file `.env`.

| Variabile | Obbligatoria | Predefinito | Descrizione | Esempio |
|-----------|-------------|-------------|-------------|---------|
| `SCANNER_API_KEY` | Sì | -- | Chiave API per l'autenticazione REST API | `dGhpcyBpcyBhIHRlc3Q` |
| `SCANNER_CLAUDE_API_KEY` | Sì | -- | Chiave API Anthropic per l'analisi AI | `sk-ant-api03-...` |
| `SCANNER_PORT` | No | `8000` | Porta esterna per lo scanner | `9000` |
| `SCANNER_DB_PATH` | No | `/data/scanner.db` | Percorso del file database SQLite | `/data/scanner.db` |
| `SCANNER_CONFIG_PATH` | No | `config.yml` | Percorso del file di configurazione YAML | `config.yml` |
| `SCANNER_GIT_TOKEN` | No | -- | Token per clonare repository privati | `ghp_xxxxxxxxxxxx` |
| `SCANNER_SLACK_WEBHOOK_URL` | No | -- | Webhook Slack per le notifiche | `https://hooks.slack.com/...` |
| `SCANNER_EMAIL_SMTP_HOST` | No | -- | Server SMTP per le notifiche email | `smtp.gmail.com` |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PORT` | No | `587` | Porta SMTP | `587` |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_USER` | No | -- | Nome utente SMTP | `alerts@example.com` |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PASSWORD` | No | -- | Password SMTP | -- |
| `SCANNER_NOTIFICATIONS__EMAIL__RECIPIENTS` | No | `[]` | Array JSON di email dei destinatari | `["dev@example.com"]` |

## Risoluzione dei Problemi

### Il Container Non Si Avvia

```bash
docker compose logs scanner
```

Cause comuni:
- Porta già in uso -- modificare `SCANNER_PORT` in `.env`
- File `.env` mancante -- copiare da `.env.example`
- Docker non in esecuzione -- avviare il daemon Docker

### L'Endpoint di Integrità Restituisce un Errore

```bash
curl http://localhost:8000/api/health
# {"status": "degraded", "database": "error"}
```

Verificare che `SCANNER_DB_PATH` punti a una posizione scrivibile all'interno del container. Il valore predefinito `/data/scanner.db` richiede che il volume `scanner_data` sia montato.

### Le Scansioni Falliscono o Vanno in Timeout

- Verificare che tutti i 12 strumenti di scansione (semgrep, cppcheck, gitleaks, trivy, checkov, psalm, enlightn, php-security-checker, gosec, bandit, brakeman, cargo-audit) siano disponibili all'interno dell'immagine Docker. Eseguire `make verify-scanners` per conferma
- Aumentare `scan_timeout` in `config.yml` per repository di grandi dimensioni
- Per i repository privati, assicurarsi che `SCANNER_GIT_TOKEN` sia impostato

### Errori di Database Bloccato

Il database utilizza la modalità WAL per l'accesso in lettura concorrente. Se si verificano errori "database is locked":
- Assicurarsi che sia in esecuzione un solo container scanner
- Non accedere direttamente al file SQLite mentre il container è in esecuzione
- Usare `make backup` per copie sicure del database

### Permesso Negato su /data

Il container viene eseguito come utente non-root `scanner`. Assicurarsi che il volume Docker abbia la proprietà corretta:

```bash
docker compose down
docker volume rm naveksoft-security_scanner_data
docker compose up -d  # Recreates volume with correct permissions
```

Nota: questa operazione rimuove i dati di scansione esistenti. Eseguire prima un backup con `make backup`.
