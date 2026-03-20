# Guida Utente

## Cos'è Security AI Scanner?

Uno strumento di scansione della sicurezza che analizza il codice sorgente alla ricerca di vulnerabilità utilizzando cinque strumenti di analisi statica in parallelo, arricchisce i risultati con analisi AI tramite Claude e produce report pratici con suggerimenti di correzione.

## Eseguire una Scansione

### Tramite API

```bash
curl -X POST http://localhost:8000/api/scans \
  -H "X-API-Key: $SCANNER_API_KEY" \
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

## Comprendere i Livelli di Gravità

| Livello | Significato | Azione |
|---------|------------|--------|
| **CRITICAL** | Rischio di sfruttamento immediato (es. SQL injection, RCE) | Correggere immediatamente; blocca il deployment |
| **HIGH** | Vulnerabilità grave (es. bypass auth, credenziali hardcoded) | Correggere prima del rilascio |
| **MEDIUM** | Rischio moderato (es. crittografia debole, header mancanti) | Correggere nello sprint corrente |
| **LOW** | Problema minore (es. messaggi di errore verbosi) | Correggere quando possibile |
| **INFO** | Risultato informativo (es. utilizzo di API deprecata) | Rivedere, nessuna azione necessaria |

## Report

### Report HTML

I report HTML interattivi includono:

- **Sezione di riepilogo** -- totale dei risultati, distribuzione per gravità, risultato del quality gate
- **Tabella dei risultati filtrabile** -- filtro per gravità, strumento, percorso del file
- **Contesto del codice** -- frammenti di codice sorgente con le righe vulnerabili evidenziate
- **Suggerimenti di correzione AI** -- codice di correzione generato da Claude con spiegazioni
- **Rischi composti** -- risultati di correlazione tra strumenti identificati dall'AI
- **Grafici** -- grafico a torta della distribuzione per gravità e grafico a barre dei risultati per strumento

Accedere ai report HTML tramite `GET /api/scans/{id}/report/html` o dalla dashboard.

### Report PDF

I report PDF forniscono un documento formale adatto alla revisione da parte del management:

- **Executive summary** -- metadati della scansione, conteggi per gravità, risultato del gate
- **Grafici** -- grafici PNG incorporati (distribuzione per gravità, suddivisione per strumento)
- **Risultati dettagliati** -- raggruppati per gravità con frammenti di codice
- **Sezione rischi composti** -- vulnerabilità cross-component identificate dall'AI

Accedere ai report PDF tramite `GET /api/scans/{id}/report/pdf`.

## Quality Gate

Il quality gate valuta i risultati della scansione rispetto alle soglie di gravità configurate. Per impostazione predefinita, qualsiasi risultato CRITICAL o HIGH causa il fallimento del gate.

- **pass** -- nessun risultato alla soglia di gravità configurata o superiore
- **fail** -- uno o più risultati alla soglia o superiori, oppure rischi composti con gravità Critical/High quando `include_compound_risks` è abilitato

I risultati del quality gate sono disponibili tramite `GET /api/scans/{id}/gate` e vengono mostrati nei report e nella dashboard.

## Analisi AI

Ogni batch di risultati viene inviato a Claude per un'analisi contestuale:

- **Revisione contestuale** -- comprensione di cosa fa il codice e se il risultato è un vero positivo
- **Suggerimenti di correzione** -- modifiche concrete al codice per rimediare alla vulnerabilità
- **Rischi composti** -- identificazione di catene di attacco che attraversano più risultati (es. bypass auth + IDOR = account takeover)

Il costo dell'analisi AI per scansione viene tracciato e limitato da `ai.max_cost_per_scan` nella configurazione.

## Confronto Delta

Quando un repository è già stato scansionato in precedenza, lo scanner calcola automaticamente un delta:

- **Nuovi risultati** -- vulnerabilità non presenti nella scansione precedente
- **Risultati risolti** -- vulnerabilità della scansione precedente non più presenti
- **Risultati persistenti** -- vulnerabilità presenti in entrambe le scansioni

Il delta viene calcolato confrontando le fingerprint tra la scansione corrente e la più recente scansione precedente dello stesso repository e branch. La prima scansione non restituisce delta (nessuna baseline precedente).

## Gestione dei Falsi Positivi

### Tramite Dashboard

Dalla vista dei risultati, fare clic sul pulsante di soppressione su qualsiasi risultato. Fornire un motivo per la soppressione.

### Tramite API

```bash
curl -X POST http://localhost:8000/api/suppressions \
  -H "X-API-Key: $SCANNER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"fingerprint": "<finding-fingerprint>", "reason": "False positive: test fixture"}'
```

I risultati soppressi vengono esclusi dalla valutazione del quality gate e contrassegnati nei report.
