# Guida Utente

## Cos'e Security AI Scanner?

Uno strumento di scansione della sicurezza che analizza il codice sorgente alla ricerca di vulnerabilita utilizzando dodici strumenti di scansione della sicurezza in parallelo, arricchisce i risultati con analisi AI tramite Claude e produce report pratici con suggerimenti di correzione. Gli scanner vengono attivati automaticamente in base ai linguaggi rilevati nel progetto.

## Scanner supportati

### Semgrep (SAST multi-linguaggio)

**Language:** Python, PHP, JavaScript, TypeScript, Go, Java, Kotlin, Ruby, C#, Rust
**Type:** SAST
**Cosa rileva:** Falle di injection, problemi di autenticazione, pattern non sicuri e vulnerabilita specifiche per linguaggio tramite corrispondenza di pattern semantici.
**Esempio di risultato:**
> `python.lang.security.audit.exec-detected`: Use of exec() detected at `app.py:42`

**Attivato:** Automaticamente quando vengono rilevati file Python, PHP, JS/TS, Go, Java, Kotlin, Ruby, C# o Rust

### cppcheck (C/C++)

**Language:** C/C++
**Type:** SAST
**Cosa rileva:** Problemi di sicurezza della memoria, buffer overflow, dereferenziazione di puntatori nulli, comportamento indefinito e perdite di risorse.
**Esempio di risultato:**
> `arrayIndexOutOfBounds`: Array index out of bounds at `buffer.cpp:15`

**Attivato:** Automaticamente quando vengono rilevati file C/C++

### Gitleaks (segreti)

**Language:** Tutti i linguaggi
**Type:** Rilevamento di segreti
**Cosa rileva:** Segreti hardcoded, chiavi API, token, password e credenziali nel codice sorgente e nella cronologia git.
**Esempio di risultato:**
> `generic-api-key`: Generic API Key detected at `config.py:8`

**Attivato:** Sempre attivo per tutti i progetti

### Trivy (infrastruttura)

**Language:** Docker, Terraform, YAML/Kubernetes
**Type:** SCA / Infrastructure
**Cosa rileva:** CVE nelle immagini container, configurazioni errate IaC e problemi di sicurezza Kubernetes.
**Esempio di risultato:**
> `CVE-2023-44487`: HTTP/2 rapid reset attack in `Dockerfile:1`

**Attivato:** Automaticamente quando vengono rilevati Dockerfiles, Terraform o Kubernetes YAML

### Checkov (infrastruttura)

**Language:** Docker, Terraform, YAML, CI configs
**Type:** Infrastructure
**Cosa rileva:** Best practice di sicurezza Infrastructure-as-code, configurazioni errate cloud e sicurezza dei pipeline CI.
**Esempio di risultato:**
> `CKV_DOCKER_2`: Ensure that HEALTHCHECK instructions have been added to container images at `Dockerfile:1`

**Attivato:** Automaticamente quando vengono rilevati file Docker, Terraform, YAML o CI

### Psalm (PHP)

**Language:** PHP
**Type:** SAST (taint analysis)
**Cosa rileva:** SQL injection, XSS e altre vulnerabilita legate alla contaminazione tramite il tracciamento del flusso di dati nel codice PHP.
**Esempio di risultato:**
> `TaintedSql`: Detected tainted SQL in `UserController.php:34`

**Attivato:** Automaticamente quando vengono rilevati file PHP

### Enlightn (Laravel)

**Language:** Laravel (PHP)
**Type:** SAST
**Cosa rileva:** Vulnerabilita CSRF, mass assignment, modalita debug esposta, file .env esposti e oltre 120 controlli di sicurezza specifici per Laravel.
**Esempio di risultato:**
> `MassAssignmentAnalyzer`: Potential mass assignment vulnerability in `User.php:12`

**Attivato:** Automaticamente quando viene rilevato un progetto Laravel

### PHP Security Checker (PHP SCA)

**Language:** PHP (Composer)
**Type:** SCA
**Cosa rileva:** CVE note nelle dipendenze Composer consultando il database di avvisi di sicurezza SensioLabs.
**Esempio di risultato:**
> `CVE-2023-46734`: Twig code injection via sandbox bypass in `composer.lock`

**Attivato:** Automaticamente quando vengono rilevati file PHP Composer

### gosec (Go SAST)

**Language:** Go
**Type:** SAST
**Cosa rileva:** Credenziali hardcoded, SQL injection, crittografia non sicura, permessi di file non sicuri e problemi di sicurezza specifici di Go.
**Esempio di risultato:**
> `G101`: Potential hardcoded credentials at `config.go:22`

**Attivato:** Automaticamente quando vengono rilevati file Go

### Bandit (Python SAST)

**Language:** Python
**Type:** SAST
**Cosa rileva:** Password hardcoded, SQL injection, uso di eval, crittografia debole e pattern di sicurezza specifici di Python.
**Esempio di risultato:**
> `B105`: Possible hardcoded password at `settings.py:15`

**Attivato:** Automaticamente quando vengono rilevati file Python

### Brakeman (Ruby/Rails SAST)

**Language:** Ruby / Rails
**Type:** SAST
**Cosa rileva:** SQL injection, XSS, mass assignment, command injection e vulnerabilita specifiche di Rails.
**Esempio di risultato:**
> `SQL Injection`: Possible SQL injection near line 15 in `app/models/user.rb`

**Attivato:** Automaticamente quando vengono rilevati file Ruby

### cargo-audit (Rust SCA)

**Language:** Rust
**Type:** SCA
**Cosa rileva:** Dipendenze vulnerabili note tramite il database RustSec mediante l'audit dei file Cargo.lock.
**Esempio di risultato:**
> `RUSTSEC-2019-0009`: Heap overflow in smallvec in `Cargo.lock`

**Attivato:** Automaticamente quando vengono rilevati file Rust

## Eseguire una Scansione

### Tramite API

```bash
curl -X POST http://localhost:8000/api/scans \
  -H "Authorization: Bearer nvsec_your_token" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/your-org/repo.git", "branch": "main"}'
```

L'API restituisce immediatamente un ID scansione (202 Accepted). La scansione viene eseguita in modo asincrono nella coda in background.

### Tramite CLI

```bash
scanner scan --repo-url https://github.com/your-org/repo.git --branch main
```

La CLI esegue la scansione direttamente e stampa i risultati sullo stdout. Usare `--format html` oppure `--format pdf` per generare file di report.

### Tramite Dashboard

Navigare su `http://localhost:8000/dashboard`, inserire l'URL del repository e il branch, quindi inviare. La dashboard mostra l'avanzamento della scansione e i risultati inline.

## Comprendere i Livelli di Gravita

| Livello | Significato | Azione |
|---------|------------|--------|
| **CRITICAL** | Rischio di sfruttamento immediato (es. SQL injection, RCE) | Correggere immediatamente; blocca il deployment |
| **HIGH** | Vulnerabilita grave (es. bypass auth, credenziali hardcoded) | Correggere prima del rilascio |
| **MEDIUM** | Rischio moderato (es. crittografia debole, header mancanti) | Correggere nello sprint corrente |
| **LOW** | Problema minore (es. messaggi di errore verbosi) | Correggere quando possibile |
| **INFO** | Risultato informativo (es. utilizzo di API deprecata) | Rivedere, nessuna azione necessaria |

## Report

### Report HTML

I report HTML interattivi includono:

- **Sezione di riepilogo** -- totale dei risultati, distribuzione per gravita, risultato del quality gate
- **Tabella dei risultati filtrabile** -- filtro per gravita, strumento, percorso del file
- **Contesto del codice** -- frammenti di codice sorgente con le righe vulnerabili evidenziate
- **Suggerimenti di correzione AI** -- codice di correzione generato da Claude con spiegazioni
- **Rischi composti** -- risultati di correlazione tra strumenti identificati dall'AI
- **Grafici** -- grafico a torta della distribuzione per gravita e grafico a barre dei risultati per strumento

Accedere ai report HTML tramite `GET /api/scans/{id}/report/html` o dalla dashboard.

### Report PDF

I report PDF forniscono un documento formale adatto alla revisione da parte del management:

- **Executive summary** -- metadati della scansione, conteggi per gravita, risultato del gate
- **Grafici** -- grafici PNG incorporati (distribuzione per gravita, suddivisione per strumento)
- **Risultati dettagliati** -- raggruppati per gravita con frammenti di codice
- **Sezione rischi composti** -- vulnerabilita cross-component identificate dall'AI

Accedere ai report PDF tramite `GET /api/scans/{id}/report/pdf`.

## Quality Gate

Il quality gate valuta i risultati della scansione rispetto alle soglie di gravita configurate. Per impostazione predefinita, qualsiasi risultato CRITICAL o HIGH causa il fallimento del gate.

- **pass** -- nessun risultato alla soglia di gravita configurata o superiore
- **fail** -- uno o piu risultati alla soglia o superiori, oppure rischi composti con gravita Critical/High quando `include_compound_risks` e abilitato

I risultati del quality gate sono disponibili tramite `GET /api/scans/{id}/gate` e vengono mostrati nei report e nella dashboard.

## Analisi AI

Ogni batch di risultati viene inviato a Claude per un'analisi contestuale:

- **Revisione contestuale** -- comprensione di cosa fa il codice e se il risultato e un vero positivo
- **Suggerimenti di correzione** -- modifiche concrete al codice per rimediare alla vulnerabilita
- **Rischi composti** -- identificazione di catene di attacco che attraversano piu risultati (es. bypass auth + IDOR = account takeover)

Il costo dell'analisi AI per scansione viene tracciato e limitato da `ai.max_cost_per_scan` nella configurazione.

## Confronto Delta

Quando un repository e gia stato scansionato in precedenza, lo scanner calcola automaticamente un delta:

- **Nuovi risultati** -- vulnerabilita non presenti nella scansione precedente
- **Risultati risolti** -- vulnerabilita della scansione precedente non piu presenti
- **Risultati persistenti** -- vulnerabilita presenti in entrambe le scansioni

Il delta viene calcolato confrontando le fingerprint tra la scansione corrente e la piu recente scansione precedente dello stesso repository e branch. La prima scansione non restituisce delta (nessuna baseline precedente).

## Gestione dei Falsi Positivi

### Tramite Dashboard

Dalla vista dei risultati, fare clic sul pulsante di soppressione su qualsiasi risultato. Fornire un motivo per la soppressione.

### Tramite API

```bash
curl -X POST http://localhost:8000/api/suppressions \
  -H "Authorization: Bearer nvsec_your_token" \
  -H "Content-Type: application/json" \
  -d '{"fingerprint": "<finding-fingerprint>", "reason": "False positive: test fixture"}'
```

I risultati soppressi vengono esclusi dalla valutazione del quality gate e contrassegnati nei report.

## Accesso alla Dashboard

### Effettuare l'accesso

1. Navigare a `/dashboard/login`
2. Inserire il nome utente e la password forniti dall'amministratore
3. Fare clic su "Accedi"

La sessione viene mantenuta tramite un cookie con scadenza di 7 giorni.

### Disconnessione

Fare clic su "Disconnetti" nella barra di navigazione in alto in qualsiasi pagina della dashboard.

## Utilizzo dei Profili di Scansione

### Cosa sono i profili di scansione?

I profili di scansione sono configurazioni di scanner predefinite create dagli amministratori. Ogni profilo specifica quali scanner eseguire e con quali parametri.

### Selezione di un profilo nella dashboard

Quando si avvia una scansione dalla dashboard, utilizzare il menu a discesa dei profili sopra il pulsante "Avvia Scansione". Selezionare un nome di profilo o scegliere "(Nessun profilo)" per la configurazione predefinita.

### Selezione di un profilo tramite API

Aggiungere il campo `profile` al corpo della richiesta di scansione:

```bash
curl -X POST http://localhost:8000/api/scans \
  -H "Authorization: Bearer nvsec_your_token" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/org/repo.git", "profile": "quick_scan"}'
```

Senza un profilo specificato, si applica la configurazione base degli scanner da `config.yml`.

### Nome del profilo nella cronologia delle scansioni

Il nome del profilo utilizzato per ogni scansione viene mostrato nella tabella della cronologia delle scansioni.

## Scansione DAST

### Cos'e il DAST?

Il Test Dinamico della Sicurezza delle Applicazioni (DAST) scansiona le applicazioni web in esecuzione alla ricerca di vulnerabilita inviando richieste HTTP e analizzando le risposte. A differenza del SAST (che analizza il codice sorgente), il DAST testa le applicazioni durante la loro esecuzione.

### Come avviare una scansione DAST

Fornire un `target_url` al posto di `path` o `repo_url` quando si avvia una scansione.

**Tramite API:**

```bash
curl -X POST http://localhost:8000/api/scans \
  -H "Authorization: Bearer nvsec_your_token" \
  -H "Content-Type: application/json" \
  -d '{"target_url": "https://example.com"}'
```

**Tramite dashboard:** Inserire l'URL di destinazione nel modulo di avvio scansione. Il campo `target_url` e esclusivo con `path` e `repo_url`.

### Risultati DAST

I risultati DAST includono:

- **Livelli di gravita** -- critical, high, medium, low, info
- **Identificatori di template** -- identificatori di template Nuclei che descrivono il tipo di vulnerabilita
- **Risultati basati su URL** -- ogni risultato fa riferimento all'URL di destinazione dove la vulnerabilita e stata rilevata

I risultati DAST appaiono nei report accanto ai risultati SAST e sono soggetti alla stessa valutazione del quality gate.
