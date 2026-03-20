# Source Code Security AI Scanner

Scanner di vulnerabilità di sicurezza basato su intelligenza artificiale per l'analisi del codice sorgente.

## Avvio Rapido

Esegua la prima scansione in meno di 5 minuti.

### Prerequisiti

- Docker & Docker Compose
- Una chiave API Anthropic (per l'analisi AI)

### Configurazione

```bash
# 1. Clone
git clone https://github.com/AlexTalorJr/source-code-security-ai-checker.git
cd source-code-security-ai-checker

# 2. Configure
cp config.yml.example config.yml
cp .env.example .env

# 3. Set secrets in .env
#    SCANNER_API_KEY=<your-api-key>
#    SCANNER_CLAUDE_API_KEY=<your-anthropic-key>

# 4. Launch
docker compose up -d

# 5. Verify
curl http://localhost:8000/api/health
```

Risposta attesa:

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime_seconds": 5.23,
  "database": "ok"
}
```

## Dashboard Web

Lo scanner include un'interfaccia web integrata disponibile su `http://localhost:8000/dashboard/`.

**Accesso:** utilizzare la chiave API impostata in `SCANNER_API_KEY`.

### Avvio di una scansione dalla dashboard

1. Aprire **Cronologia scansioni** (`/dashboard/history`)
2. Fare clic su **"Start New Scan"** — il modulo si espande
3. Compilare il campo **Local Path** oppure **Repository URL** + **Branch**
4. Opzionalmente spuntare **"Skip AI Analysis"** per eseguire senza l'API Claude (più veloce, nessun costo)
5. Fare clic su **"Start Scan"**

La scansione viene eseguita in background. La pagina di dettaglio mostra l'avanzamento in tempo reale con polling live; i risultati appaiono automaticamente al completamento.

### Pagine della dashboard

| Pagina | URL | Descrizione |
|--------|-----|-------------|
| Cronologia scansioni | `/dashboard/history` | Elenco di tutte le scansioni + modulo per avviarne una nuova |
| Dettaglio scansione | `/dashboard/scans/{id}` | Risultati, riepilogo per gravità, controlli di soppressione |
| Tendenze | `/dashboard/trends` | Grafici: gravità nel tempo, distribuzione per strumento |

### Eseguire una scansione tramite API

```bash
curl -X POST http://localhost:8000/api/scans \
  -H "X-API-Key: $SCANNER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/your-org/your-repo.git", "branch": "main"}'
```

Per saltare l'analisi AI in una scansione specifica:

```bash
curl -X POST http://localhost:8000/api/scans \
  -H "X-API-Key: $SCANNER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/your-org/repo.git", "branch": "main", "skip_ai": true}'
```

## Integrazione con Jenkins Pipeline

Aggiunga lo scanner come stage nel proprio `Jenkinsfile` per bloccare i deployment in presenza di risultati Critical/High.

### Stage base per Jenkinsfile

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

### Note chiave

- **Quality gate** blocca la build in caso di risultati Critical o High (configurabile in `config.yml` sotto `gate.fail_on`)
- **Scansione tramite percorso locale** — se Jenkins e lo scanner condividono un filesystem, usare `"path": "${WORKSPACE}"` al posto di `repo_url`
- **Skip analisi AI** — aggiungere `"skip_ai": true` al corpo della richiesta per scansioni più veloci senza costi API Claude
- **Notifiche** — configurare Slack/email in `config.yml` per ricevere avvisi al completamento delle scansioni
- **Report** — i report HTML e PDF vengono generati automaticamente, accessibili tramite `/api/scans/{id}/report` o dalla dashboard

Consultare la [Guida DevOps](docs/it/devops-guide.md) per i dettagli completi sull'integrazione con Jenkins, inclusi esempi di pipeline con stage paralleli.

## Funzionalità

- **5 scanner di sicurezza in parallelo** -- Semgrep, cppcheck, Gitleaks, Trivy, Checkov
- **Analisi basata su AI** -- Claude esamina i risultati per contesto, rischi composti e suggerimenti di correzione
- **Report interattivi HTML e PDF** -- risultati filtrabili con contesto del codice e grafici
- **Quality gate configurabile** -- blocco del deployment in caso di risultati Critical/High
- **Dashboard web** -- gestione scansioni, avanzamento in tempo reale, cronologia, controlli di soppressione
- **REST API** -- avvio scansioni, recupero risultati, gestione dei risultati in modo programmatico
- **Notifiche Slack ed email** -- avvisi in tempo reale con identificazione della destinazione di scansione
- **Integrazione CI con Jenkins** -- stage pipeline con controlli quality gate
- **Cronologia scansioni con confronto delta** -- tracciamento di risultati nuovi, risolti e persistenti
- **Skip AI per scansione** -- esecuzione senza API Claude quando la velocità o il costo sono prioritari

## Documentazione

| Documento | Descrizione |
|-----------|-------------|
| [Architettura](docs/it/architecture.md) | Design del sistema, diagramma dei componenti, flusso dei dati |
| [Schema del database](docs/it/database-schema.md) | Schema SQLite, diagramma ER, indici |
| [Riferimento API](docs/it/api.md) | Endpoint REST API e autenticazione |
| [Guida utente](docs/it/user-guide.md) | Report, risultati, quality gate, soppressioni |
| [Guida amministratore](docs/it/admin-guide.md) | Configurazione, variabili d'ambiente, ottimizzazione |
| [Guida DevOps](docs/it/devops-guide.md) | Deployment Docker, Jenkins, backup |
| [Guida al trasferimento](docs/it/transfer-guide.md) | Procedure di migrazione del server |
| [Regole personalizzate](docs/it/custom-rules.md) | Scrittura di regole Semgrep personalizzate |

## Stato del Progetto

Tutte le fasi v1.0 completate.

| Fase | Descrizione | Stato |
|------|-------------|-------|
| 1 | Foundation & Data Models | Done |
| 2 | Scanner Adapters & Orchestration | Done |
| 3 | AI Analysis (Claude API) | Done |
| 4 | Report Generation (HTML/PDF) | Done |
| 5 | Dashboard, Notifications & Quality Gate | Done |
| 6 | Packaging, Portability & Documentation | Done |

## Stack Tecnologico

- **Python 3.12** -- linguaggio principale
- **FastAPI** -- REST API e dashboard web
- **SQLAlchemy 2.0** -- ORM asincrono con SQLite
- **SQLite (WAL mode)** -- database incorporato
- **Pydantic v2** -- validazione dei dati e configurazione
- **Docker** -- containerizzazione
- **Alembic** -- migrazioni del database
- **Anthropic Claude** -- analisi delle vulnerabilità basata su AI
- **WeasyPrint** -- generazione di report PDF
- **Jinja2** -- template HTML per report e dashboard
- **Typer** -- interfaccia CLI

## Licenza

Apache 2.0

---

Documentazione in altre lingue: [English](README.md) | [Русский](README.ru.md) | [Italiano](README.it.md)
