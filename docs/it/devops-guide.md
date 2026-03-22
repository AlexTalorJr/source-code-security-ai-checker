# Guida DevOps

## Deployment con Docker

### Avvio Rapido

```bash
cp config.yml.example config.yml
cp .env.example .env
# Edit .env with real secrets
make install   # builds Docker images
make run       # starts scanner in background
```

Oppure direttamente con Docker Compose:

```bash
docker compose up -d --build
```

### Configurazione del Container

Il file `docker-compose.yml` definisce un singolo servizio `scanner`:

```yaml
services:
  scanner:
    build: .
    ports:
      - "${SCANNER_PORT:-8000}:8000"
    volumes:
      - scanner_data:/data           # Persistent DB and reports
      - ./config.yml:/app/config.yml:ro  # Read-only config mount
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    restart: unless-stopped

volumes:
  scanner_data:  # Named volume for SQLite persistence
```

- **Volume `scanner_data`** montato su `/data` all'interno del container -- archivia il database SQLite e i report generati. I dati sopravvivono ai riavvii e alle ricostruzioni del container.
- **Mount della configurazione** collega `config.yml` in sola lettura nel container su `/app/config.yml`.
- **Mappatura della porta** predefinita a `8000`, ma può essere cambiata tramite la variabile d'ambiente `SCANNER_PORT`.
- **Policy di riavvio** `unless-stopped` garantisce il riavvio dello scanner dopo i riavvii dell'host.

## Dockerfile

L'immagine e basata su `python:3.12-slim` e include tutti i 12 strumenti di scansione:

1. **Dipendenze di sistema** -- `curl` (healthcheck), `libpango` e `libharfbuzz` (generazione PDF con WeasyPrint), `ruby` (Brakeman)
2. **Utente non-root** -- vengono creati utente e gruppo `scanner` per la sicurezza; la directory `/data` e di proprieta di questo utente
3. **Binari degli scanner** -- consultare la sezione Binari degli scanner di seguito per l'elenco completo
4. **Flusso di installazione** -- vengono copiati `pyproject.toml` e `src/`, quindi `pip install --no-cache-dir .` usando il build backend hatchling
5. **File applicazione** -- vengono copiati `alembic.ini`, le migrazioni `alembic/` e `config.yml.example` (come `config.yml` predefinito)
6. **Entrypoint** -- `uvicorn scanner.main:app --host 0.0.0.0 --port 8000`

## Binari degli scanner

Tutti i 12 strumenti di scansione vengono installati all'interno dell'immagine Docker:

| Scanner | Metodo di installazione | Note |
|---------|------------------------|------|
| **Semgrep** | `pip install semgrep` | Pacchetto Python, installato insieme all'applicazione |
| **cppcheck** | `apt-get install cppcheck` | Pacchetto di sistema |
| **Gitleaks** | Binario precompilato da GitHub releases | Scaricato in `/usr/local/bin`, supporta amd64/arm64 |
| **Trivy** | Binario precompilato da GitHub releases | Scaricato in `/usr/local/bin`, supporta amd64/arm64 |
| **Checkov** | `pip install checkov` | Pacchetto Python, installato con `--no-cache-dir` |
| **Psalm** | `composer global require vimeo/psalm` | Pacchetto PHP Composer, richiede `php-cli` |
| **Enlightn** | `composer global require enlightn/enlightn` | Pacchetto PHP Composer |
| **PHP Security Checker** | Binario precompilato da GitHub releases | Scaricato in `/usr/local/bin` |
| **gosec** | Binario precompilato da GitHub releases | Scaricato in `/usr/local/bin`, supporta amd64/arm64 |
| **Bandit** | `pip install bandit` | Pacchetto Python, installato insieme a Semgrep e Checkov |
| **Brakeman** | `gem install brakeman` | Gem Ruby, richiede il pacchetto `ruby` (~80 MB) |
| **cargo-audit** | Binario precompilato da GitHub releases | Scaricato in `/usr/local/bin`, supporta amd64/arm64 |

### Verifica della disponibilita degli scanner

Dopo aver compilato l'immagine Docker, verificare che tutti gli scanner siano installati correttamente:

```bash
make verify-scanners
```

Questo target esegue un smoke test all'interno del container, verificando che ciascuno dei 12 binari degli scanner sia disponibile e risponda ai comandi version/help. Utilizzarlo dopo qualsiasi modifica al Dockerfile per assicurarsi che nessuno scanner sia stato compromesso.

## Variabili d'Ambiente

Tutta la configurazione può essere impostata tramite variabili d'ambiente con il prefisso `SCANNER_`. Passare i segreti tramite il file `.env` (non committato in git).

| Variabile | Obbligatoria | Predefinito | Descrizione |
|-----------|-------------|-------------|-------------|
| `SCANNER_API_KEY` | Sì | -- | Chiave API per autenticare le richieste REST API |
| `SCANNER_CLAUDE_API_KEY` | Sì | -- | Chiave API Anthropic per l'analisi AI |
| `SCANNER_PORT` | No | `8000` | Porta esterna per il servizio scanner |
| `SCANNER_DB_PATH` | No | `/data/scanner.db` | Percorso del file database SQLite |
| `SCANNER_CONFIG_PATH` | No | `config.yml` | Percorso del file di configurazione YAML |
| `SCANNER_GIT_TOKEN` | No | -- | Token per clonare repository Git privati |
| `SCANNER_SLACK_WEBHOOK_URL` | No | -- | URL webhook Slack in entrata per le notifiche |
| `SCANNER_EMAIL_SMTP_HOST` | No | -- | Hostname del server SMTP per le notifiche email |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PORT` | No | `587` | Porta del server SMTP |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_USER` | No | -- | Nome utente per l'autenticazione SMTP |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PASSWORD` | No | -- | Password per l'autenticazione SMTP |
| `SCANNER_NOTIFICATIONS__EMAIL__RECIPIENTS` | No | `[]` | Array JSON dei destinatari email |

## Integrazione con Jenkins

Il progetto include `Jenkinsfile.security` per integrare le scansioni di sicurezza in una pipeline Jenkins. Utilizza il plugin Jenkins `httpRequest` per le chiamate API.

### Configurazione

1. Installare il plugin **HTTP Request** in Jenkins
2. Aggiungere `SCANNER_URL` (es. `http://scanner:8000`) come credenziale o variabile d'ambiente Jenkins
3. Aggiungere `SCANNER_API_KEY` come credenziale di testo segreto Jenkins

### Utilizzo

Aggiungere lo stage di scansione di sicurezza al proprio `Jenkinsfile` esistente:

```groovy
stage('Security Scan') {
    steps {
        script {
            def response = httpRequest(
                url: "${SCANNER_URL}/api/scans",
                httpMode: 'POST',
                customHeaders: [[name: 'X-API-Key', value: "${SCANNER_API_KEY}"]],
                contentType: 'APPLICATION_JSON',
                requestBody: """{"repo_url": "${GIT_URL}", "branch": "${GIT_BRANCH}"}"""
            )
            def scanResult = readJSON(text: response.content)
            def scanId = scanResult.id
            // Poll for completion, then check quality gate
        }
    }
}
```

### Quality Gate

Lo scanner valuta un quality gate dopo ogni scansione. Configurare i criteri di pass/fail in `config.yml`:

```yaml
gate:
  fail_on:
    - critical
    - high
  include_compound_risks: true
```

Se il gate fallisce, lo stage Jenkins dovrebbe far fallire la build. Interrogare il risultato della scansione per verificare `gate_passed`.

## Backup

### Utilizzo dei Target Make

```bash
# Create a timestamped backup (DB + reports + config)
make backup
# Output: backups/backup-20260320_143000.tar.gz

# Restore from a backup file
make restore BACKUP=backups/backup-20260320_143000.tar.gz
```

### Cosa Viene Incluso nel Backup

- **Database SQLite** -- eseguito il backup utilizzando il comando `sqlite3 .backup` (sicuro con WAL, nessun downtime richiesto)
- **Report** -- report HTML/PDF generati da `/data/reports`
- **Configurazione** -- `config.yml`

### Sicurezza in Modalità WAL

Il database funziona in modalità WAL (Write-Ahead Logging). Il target `make backup` utilizza il comando `.backup` di SQLite all'interno del container, che gestisce in modo sicuro il checkpointing WAL. Non copiare semplicemente il file `.db` -- utilizzare il target make oppure il comando `sqlite3 .backup`.

### Pianificazione Raccomandata

Configurare un cron job giornaliero per i backup automatici:

```bash
# Daily at 2 AM
0 2 * * * cd /path/to/naveksoft-security && make backup
```

## Build Multi-Architettura

Creare immagini Docker per entrambe le architetture `amd64` e `arm64` utilizzando Docker Buildx.

### Prerequisiti

- Docker Desktop 4.x+ (include buildx) o plugin `docker-buildx` installato manualmente
- QEMU user-static per l'emulazione cross-platform (Docker Desktop lo gestisce automaticamente)

### Build di Immagini Multi-Arch

```bash
# Build for amd64 + arm64, save as OCI archive
make docker-multiarch
# Output: Security AI Scanner-{version}-multiarch.tar

# Build and push to a container registry
make docker-push REGISTRY=your-registry.example.com
```

Il target `docker-multiarch` crea un builder buildx denominato `multiarch` se non esiste già.

## Monitoraggio

### Endpoint di Integrità

Eseguire il polling dell'endpoint di integrità per monitorare lo stato dello scanner:

```bash
curl http://localhost:8000/api/health
# {"status": "healthy", "version": "0.1.0", "uptime_seconds": 3600.5, "database": "ok"}
```

Uno stato `"degraded"` o una risposta `"database": "error"` indica un problema con la connessione al database.

### Healthcheck Docker

Il container include un healthcheck integrato che viene eseguito ogni 30 secondi. Verificare lo stato di integrità del container:

```bash
docker compose ps
# Shows "healthy" or "unhealthy" in the STATUS column
```

### Log

```bash
# Follow logs in real time
docker compose logs -f scanner

# Last 100 lines
docker compose logs scanner --tail 100
```

Il livello di log è configurato in `config.yml` tramite il campo `log_level` (predefinito: `info`).

### Policy di Riavvio

Il container utilizza `restart: unless-stopped`, quindi si riavvia automaticamente dopo crash o riavvii dell'host. Solo un `docker compose stop` o `docker compose down` manuale lo manterrà fermo.

## Aggiornamento

1. Estrarre il codice più recente:
   ```bash
   git pull origin main
   ```

2. Ricostruire e riavviare:
   ```bash
   make install   # rebuilds Docker image
   make run       # starts updated container
   ```

3. Eseguire le migrazioni del database:
   ```bash
   make migrate
   ```

4. Verificare l'aggiornamento:
   ```bash
   curl http://localhost:8000/api/health
   ```

Se l'endpoint di integrità restituisce il nuovo numero di versione e `"status": "healthy"`, l'aggiornamento è completo.
