# Guida Amministratore

## Configurazione

### Sorgenti di Configurazione (Ordine di Priorità)

1. **Argomenti del costruttore** -- override programmatici
2. **Variabili d'ambiente** -- prefisso `SCANNER_*`
3. **File dotenv** -- file `.env`
4. **Segreti da file** -- Docker/K8s secrets
5. **File di configurazione YAML** -- `config.yml` (priorità più bassa)

### File di Configurazione

Copiare l'esempio e personalizzarlo:

```bash
cp config.yml.example config.yml
```

## Configurazione degli Scanner

Ciascuno dei dodici strumenti scanner puo essere configurato indipendentemente: abilitazione/disabilitazione, timeout, argomenti aggiuntivi e rilevamento automatico per linguaggio. Gli scanner con `enabled: "auto"` vengono attivati automaticamente quando vengono rilevati file corrispondenti.

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

- **adapter_class** -- percorso completo alla classe Python che implementa l'adattatore dello scanner (vedere Registro dei plugin di seguito)
- **enabled** -- impostare a `true` (sempre attivo), `false` (sempre disattivo) o `"auto"` (attivato quando vengono rilevati file corrispondenti)
- **timeout** -- numero massimo di secondi prima che lo strumento venga interrotto
- **extra_args** -- argomenti CLI aggiuntivi da passare allo strumento
- **languages** -- tipi di file che attivano il rilevamento automatico; gli scanner con lista vuota (es. Gitleaks) vengono eseguiti su tutti i progetti

## Registro dei plugin

Lo scanner utilizza un registro di plugin basato sulla configurazione per caricare dinamicamente gli adattatori degli scanner da `config.yml`. Questa architettura consente di aggiungere nuovi scanner senza modificare il codice dell'applicazione.

### Come vengono registrati gli scanner

Ogni voce di scanner in `config.yml` include un campo `adapter_class` che specifica il percorso completo alla classe Python che implementa l'interfaccia `ScannerAdapter`. All'avvio, il `ScannerRegistry` legge tutte le voci dalla sezione `scanners` e importa dinamicamente ogni classe di adattatore.

Il campo `adapter_class` segue il formato:

```
scanner.adapters.<module_name>.<ClassName>
```

Ad esempio: `scanner.adapters.gosec.GosecAdapter`

### Rilevamento automatico dei linguaggi

Gli scanner con un campo `languages` vengono automaticamente attivati quando il repository scansionato contiene file corrispondenti. L'orchestratore rileva le estensioni dei file nel repository di destinazione e attiva gli scanner la cui lista `languages` si sovrappone ai linguaggi rilevati. Gli scanner con una lista `languages` vuota (come Gitleaks) vengono sempre eseguiti indipendentemente dal tipo di progetto.

### Aggiungere un nuovo scanner

Per aggiungere un nuovo scanner alla piattaforma:

1. **Creare una classe adattatore** che implementi l'interfaccia `ScannerAdapter`:

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

2. **Aggiungere una voce in `config.yml`** nella sezione `scanners`:

```yaml
scanners:
  my_scanner:
    adapter_class: "scanner.adapters.my_scanner.MyScannerAdapter"
    enabled: "auto"
    timeout: 120
    extra_args: []
    languages: ["python"]
```

3. **Installare il binario dello scanner** nel Dockerfile se si tratta di uno strumento esterno.

Non sono necessarie altre modifiche al codice. Il registro scopre e carica automaticamente il nuovo adattatore dalla configurazione.

### Elenco degli scanner registrati

L'endpoint `/api/scanners` restituisce tutti gli scanner registrati con la loro configurazione:

```bash
curl -H "Authorization: Bearer nvsec_your_token" http://localhost:8000/api/scanners
```

La risposta include il nome, lo stato di abilitazione, i linguaggi configurati e la classe di adattatore di ciascuno scanner.

## Configurazione AI

```yaml
ai:
  max_cost_per_scan: 5.0
  model: "claude-sonnet-4-6"
  max_findings_per_batch: 50
  max_tokens_per_response: 4096
```

| Impostazione | Descrizione | Predefinito |
|--------------|-------------|-------------|
| `max_cost_per_scan` | Spesa massima in USD per l'analisi AI per scansione | `5.0` |
| `model` | Identificatore del modello Claude | `claude-sonnet-4-6` |
| `max_findings_per_batch` | Numero massimo di risultati inviati a Claude in una sola richiesta | `50` |
| `max_tokens_per_response` | Numero massimo di token di risposta da Claude | `4096` |

## Configurazione del Quality Gate

```yaml
gate:
  fail_on:
    - critical
    - high
  include_compound_risks: true
```

- **fail_on** -- elenco dei livelli di gravità che causano il fallimento del gate
- **include_compound_risks** -- quando `true`, i rischi composti con gravità corrispondente causano anch'essi il fallimento del gate

## Configurazione delle Notifiche

### Slack

```yaml
notifications:
  slack:
    enabled: false
```

Impostare l'URL del webhook al livello superiore:

```yaml
slack_webhook_url: "https://hooks.slack.com/services/T.../B.../xxx"
```

Oppure tramite variabile d'ambiente: `SCANNER_SLACK_WEBHOOK_URL`

### Email

```yaml
notifications:
  email:
    enabled: false
    recipients: ["security@example.com"]
    smtp_port: 587
    smtp_user: ""
    smtp_password: ""  # Use env var instead
    use_tls: true
```

Impostare l'host SMTP al livello superiore:

```yaml
email_smtp_host: "smtp.example.com"
```

Oppure tramite variabile d'ambiente: `SCANNER_EMAIL_SMTP_HOST`

La password SMTP dovrebbe utilizzare la variabile d'ambiente nidificata: `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PASSWORD`

### URL della Dashboard

```yaml
dashboard_url: ""  # e.g., http://scanner:8000/dashboard
```

Utilizzato nei messaggi di notifica per collegarsi ai risultati della scansione. Se vuoto, viene derivato automaticamente da host e porta.

## Variabili d'Ambiente

Tutte le impostazioni possono essere sovrascritte con il prefisso `SCANNER_`:

| Variabile | Descrizione | Predefinito |
|-----------|-------------|-------------|
| `SCANNER_HOST` | Indirizzo di ascolto | `0.0.0.0` |
| `SCANNER_PORT` | Porta di ascolto | `8000` |
| `SCANNER_DB_PATH` | Percorso del file database SQLite | `/data/scanner.db` |
| `SCANNER_API_KEY` | Chiave di autenticazione API | `""` (vuoto) |
| `SCANNER_CLAUDE_API_KEY` | Chiave API Anthropic per l'analisi AI | `""` (vuoto) |
| `SCANNER_SLACK_WEBHOOK_URL` | URL webhook Slack | `""` |
| `SCANNER_EMAIL_SMTP_HOST` | Hostname del server SMTP | `""` |
| `SCANNER_LOG_LEVEL` | Livello di log (debug/info/warning/error) | `info` |
| `SCANNER_SCAN_TIMEOUT` | Timeout globale della scansione in secondi | `600` |
| `SCANNER_CONFIG_PATH` | Percorso del file di configurazione YAML | `config.yml` |

### Variabili d'Ambiente Nidificate

Per le sezioni di configurazione nidificate, utilizzare il doppio underscore:

| Variabile | Corrispondenza |
|-----------|---------------|
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PASSWORD` | `notifications.email.smtp_password` |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PORT` | `notifications.email.smtp_port` |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_USER` | `notifications.email.smtp_user` |
| `SCANNER_NOTIFICATIONS__SLACK__ENABLED` | `notifications.slack.enabled` |

## Gestione dei Segreti

Non memorizzare mai i segreti in `config.yml` né eseguirne il commit in git.

```bash
# Set secrets via environment:
export SCANNER_API_KEY="your-secure-key"
export SCANNER_CLAUDE_API_KEY="sk-ant-..."

# Or in docker-compose via .env file:
echo "SCANNER_API_KEY=your-secure-key" >> .env
echo "SCANNER_CLAUDE_API_KEY=sk-ant-..." >> .env
```

## Gestione del Database

### Posizione

- Docker: `/data/scanner.db` (volume persistente `scanner_data`)
- Locale: configurabile tramite `SCANNER_DB_PATH`

### Modalità WAL

SQLite funziona in modalità WAL (Write-Ahead Logging) per le prestazioni di lettura concorrente. Questa modalità viene impostata automaticamente ad ogni connessione tramite listener di eventi SQLAlchemy.

### Backup

```bash
# WAL mode allows hot backup (no need to stop scanner)
docker cp naveksoft-security-scanner-1:/data/scanner.db ./backup/
```

## Ottimizzazione delle Soglie

### Quality Gate

Regolare le gravità che causano il fallimento del gate:

```yaml
gate:
  fail_on:
    - critical        # Only block on critical (relaxed)
```

Oppure includere medium:

```yaml
gate:
  fail_on:
    - critical
    - high
    - medium           # Stricter policy
```

### Gestione degli Strumenti Scanner

Disabilitare gli strumenti non pertinenti al proprio codebase:

```yaml
scanners:
  cppcheck:
    enabled: false     # No C/C++ code
  checkov:
    enabled: false     # No IaC files
```

## Ottimizzazione delle Prestazioni

### Timeout

- `scan_timeout` (globale): durata massima totale della scansione (predefinito: 600s)
- `timeout` per scanner: tempo massimo di esecuzione per strumento (predefinito: 120-180s)

Se le scansioni vanno in timeout, aumentare il timeout per lo strumento lento anziché il timeout globale.

### Dimensione del Batch AI

Per scansioni di grandi dimensioni con molti risultati, regolare:

```yaml
ai:
  max_findings_per_batch: 25   # Smaller batches for faster responses
  max_tokens_per_response: 8192  # More room for detailed analysis
```

### Monitoraggio

```bash
# Health check
curl http://localhost:8000/api/health

# Container status
docker compose ps

# Logs
docker compose logs scanner --tail 50
```

Docker Compose esegue controlli di integrita automatici ogni 30 secondi.

## Gestione Utenti (RBAC)

Security AI Scanner utilizza il controllo degli accessi basato sui ruoli (RBAC) per gestire i permessi degli utenti. Sono disponibili tre ruoli:

### Ruoli

| Azione | Admin | Viewer | Scanner |
|--------|-------|--------|---------|
| Avviare scansione | Si | No | Si (solo API) |
| Visualizzare risultati | Si | Si | Si (solo API) |
| Gestire utenti | Si | No | No |
| Configurare scanner | Si | No | No |
| Gestire profili | Si | No | No |

- **Admin** -- accesso completo a tutte le funzionalita, inclusa la gestione utenti, la configurazione degli scanner e la gestione dei profili
- **Viewer** -- accesso in sola lettura ai risultati delle scansioni e ai report tramite la dashboard
- **Scanner** -- ruolo solo API per avviare scansioni e visualizzare risultati programmaticamente

### Creazione utenti

Gli utenti possono essere creati in due modi:

1. **Tramite dashboard** -- navigare a `/dashboard/users` (solo admin) e compilare il modulo di creazione
2. **Tramite variabili d'ambiente** -- impostare `SCANNER_ADMIN_USER` e `SCANNER_ADMIN_PASSWORD` per creare un account admin al primo avvio

Requisiti password: minimo 8 caratteri.

### Disattivazione utenti

Gli admin possono disattivare gli utenti dalla dashboard o tramite l'API (`DELETE /api/users/{id}`). Gli utenti disattivati non possono accedere ne utilizzare i token API.

## Token API

I token API forniscono accesso programmatico all'API dello scanner utilizzando l'autenticazione Bearer.

### Generazione dei token

Navigare a `/dashboard/tokens` per gestire i propri token. Fare clic su "Crea Token" e fornire un nome.

### Formato del token

Tutti i token utilizzano il prefisso `nvsec_`:

```
nvsec_a1b2c3d4e5f6...
```

### Utilizzo

Includere il token nell'header `Authorization`:

```bash
curl -H "Authorization: Bearer nvsec_your_token_here" http://localhost:8000/api/scans
```

### Opzioni di scadenza

Quando si crea un token, selezionare un periodo di scadenza:

- 30 giorni
- 90 giorni
- 365 giorni
- Mai (nessuna scadenza)

### Limiti dei token

Ogni utente puo avere fino a 10 token attivi (limite flessibile).

### Revoca dei token

I token possono essere revocati dalla dashboard (`/dashboard/tokens`) o tramite l'API (`DELETE /api/tokens/{id}`).

## Interfaccia di Configurazione degli Scanner

L'interfaccia web di configurazione degli scanner consente agli admin di gestire i parametri degli scanner, modificare la configurazione YAML e gestire i profili di scansione -- tutto dalla dashboard.

### Accesso all'interfaccia di configurazione

Navigare a `/dashboard/scanners` (solo admin). La pagina ha tre schede:

### Scheda Scanner

Mostra tutti gli scanner registrati come schede con:

- **Interruttore ON/AUTO/OFF** -- alternare tra stati attivo, automatico e disattivo
- **Timeout** -- tempo massimo di esecuzione in secondi (30-900)
- **Argomenti aggiuntivi** -- flag CLI aggiuntivi passati allo strumento

### Scheda Editor YAML

Un editor CodeMirror per la modifica diretta di `config.yml` con evidenziazione della sintassi YAML e validazione completa prima del salvataggio.

### Scheda Profili

Gestione dei profili di scansione (vedere sezione Profili di Scansione di seguito).

## Profili di Scansione

I profili di scansione sono preset di scanner con nome, memorizzati in `config.yml`. Ogni profilo definisce quali scanner eseguire e puo opzionalmente sovrascrivere i parametri per scanner.

### Panoramica

Un profilo e una lista di autorizzazione esplicita -- solo gli scanner elencati nel profilo vengono eseguiti quando quel profilo viene selezionato.

### Creazione dei profili

Navigare a `/dashboard/scanners` e selezionare la scheda Profili. Fare clic su "Nuovo Profilo" e fornire:

- **Nome** -- solo lettere, numeri, trattini e underscore (es. `quick_scan`, `full-audit`)
- **Descrizione** -- descrizione opzionale
- **Scanner** -- selezionare gli scanner da includere con override di timeout opzionali

### Esempio di profili in config.yml

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

### Modifica e eliminazione dei profili

Dalla scheda Profili, fare clic su una scheda profilo per espandere il modulo di modifica. Modificare i parametri e fare clic su Salva, oppure fare clic su Elimina.

### Limiti

- Massimo 10 profili (limite flessibile)
- I nomi dei profili possono contenere solo lettere, numeri, trattini e underscore
- Le parole riservate YAML (`true`, `false`, `null`, `yes`, `no`, `on`, `off`) non possono essere usate come nomi di profilo

## Scansione DAST

Il Test Dinamico della Sicurezza delle Applicazioni (DAST) scansiona le applicazioni web in esecuzione alla ricerca di vulnerabilita inviando richieste HTTP e analizzando le risposte.

### Panoramica

La scansione DAST e alimentata da Nuclei, uno scanner di vulnerabilita rapido e configurabile. A differenza degli strumenti SAST che analizzano il codice sorgente, DAST testa l'applicazione come scatola nera.

### Configurazione di Nuclei

Assicurarsi che lo scanner Nuclei sia abilitato in `config.yml`:

```yaml
scanners:
  nuclei:
    adapter_class: "scanner.adapters.nuclei.NucleiAdapter"
    enabled: true
    timeout: 300
    extra_args: []
    languages: []
```

### Avvio di una scansione DAST

Le scansioni DAST richiedono il parametro `target_url` al posto di `path` o `repo_url`:

**Tramite API:**

```bash
curl -X POST http://localhost:8000/api/scans \
  -H "Authorization: Bearer nvsec_your_token" \
  -H "Content-Type: application/json" \
  -d '{"target_url": "https://example.com"}'
```

**Tramite dashboard:** Inserire l'URL di destinazione nel campo URL del modulo di avvio scansione.

### DAST vs SAST

Il parametro `target_url` e esclusivo con `path` e `repo_url`. Non e possibile combinare target DAST e SAST in una singola richiesta.

### Risultati DAST

I risultati DAST appaiono nei report accanto ai risultati SAST. Ogni risultato DAST include il livello di gravita, l'identificatore del template Nuclei e l'URL di destinazione dove la vulnerabilita e stata trovata.
