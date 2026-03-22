# Guida alle Regole Personalizzate

## Panoramica

Questa guida riguarda la scrittura di regole Semgrep personalizzate per i componenti della piattaforma aipix. Le regole personalizzate consentono il rilevamento di vulnerabilità specifiche della piattaforma che le regole generiche non colgono.

## Componenti Destinatari

| Componente | Linguaggio | Problemi Principali |
|------------|-----------|---------------------|
| VMS (Video Management) | PHP/Laravel | SQL injection, auth compromessa, IDOR |
| Mediaserver | C++ | Buffer overflow, format string, sicurezza della memoria |
| REST API | PHP/Laravel | Esposizione token API, SSRF, mass assignment |
| Webhooks | PHP | Mancata verifica della firma |
| Desktop Client | C# | Deserializzazione non sicura, archiviazione delle credenziali |

## Formato delle Regole Semgrep

Le regole Semgrep sono file YAML con definizioni di corrispondenza dei pattern. Ogni regola specifica:

- **id** -- identificatore univoco della regola (usare il prefisso `aipix.` per le regole personalizzate)
- **pattern** -- pattern di codice da far corrispondere (supporta metavariabili come `$VAR`)
- **message** -- descrizione leggibile del risultato
- **severity** -- `ERROR` (Critical/High), `WARNING` (Medium) oppure `INFO` (Low/Info)
- **languages** -- elenco dei linguaggi a cui si applica la regola

## Posizione dei File delle Regole

Le regole personalizzate sono memorizzate nella directory `rules/` nella radice del progetto. L'adattatore Semgrep carica automaticamente tutti i file `.yml` da questa directory insieme al set di regole predefinito.

```
rules/
  aipix-rtsp-auth.yml
  aipix-api-security.yml
  aipix-memory-safety.yml
```

## Esempi di Regole

### Credenziali RTSP Hardcoded

```yaml
rules:
  - id: aipix.rtsp-hardcoded-credentials
    pattern: rtsp://$USER:$PASS@$HOST
    message: "Hardcoded RTSP credentials detected"
    severity: ERROR
    languages: [php, python, yaml]
    metadata:
      category: authentication
      component: mediaserver
```

### Token API nell'Output di Log

```yaml
rules:
  - id: aipix.api-token-in-log
    patterns:
      - pattern: |
          Log::$METHOD(..., $TOKEN, ...)
      - metavariable-regex:
          metavariable: $TOKEN
          regex: ".*token.*|.*api_key.*|.*secret.*"
    message: "Possible API token logged -- check for sensitive data exposure"
    severity: WARNING
    languages: [php]
    metadata:
      category: data-exposure
      component: vms
```

### Mancata Verifica della Firma del Webhook

```yaml
rules:
  - id: aipix.webhook-no-signature-check
    patterns:
      - pattern: |
          function $HANDLER(Request $request) {
            ...
          }
      - pattern-not: |
          function $HANDLER(Request $request) {
            ...
            $request->header('X-Signature', ...)
            ...
          }
    message: "Webhook handler missing signature verification"
    severity: ERROR
    languages: [php]
    metadata:
      category: authentication
      component: webhooks
```

### SQL Injection tramite Query Raw

```yaml
rules:
  - id: aipix.sql-injection-raw
    patterns:
      - pattern: DB::raw("..." . $VAR . "...")
    message: "Potential SQL injection via string concatenation in raw query"
    severity: ERROR
    languages: [php]
    metadata:
      category: injection
      component: vms
```

## Test delle Regole

Testare le regole personalizzate su codice di esempio prima del deployment:

```bash
# Test a single rule file against a target directory
semgrep --config rules/aipix-rtsp-auth.yml /path/to/code

# Test all custom rules
semgrep --config rules/ /path/to/code

# Dry run (show matches without full output)
semgrep --config rules/ --json /path/to/code | python3 -m json.tool
```

## Regole personalizzate per altri scanner

Oltre a Semgrep, diversi altri scanner supportano la configurazione di regole personalizzate:

### gosec (Go)

gosec supporta l'inclusione o esclusione di specifici identificatori di regole:

```yaml
scanners:
  gosec:
    extra_args: ["-include=G101,G201,G301"]
```

Usare `-include` per eseguire solo regole specifiche, o `-exclude` per saltare regole. Gli identificatori di regole seguono il pattern `G1xx` (injection), `G2xx` (crypto), `G3xx` (file I/O), `G4xx` (rete), `G5xx` (blocklist).

### Bandit (Python)

Bandit supporta profili personalizzati tramite file di configurazione:

```yaml
scanners:
  bandit:
    extra_args: ["-c", "bandit.yml"]
```

Creare un profilo `bandit.yml` per includere/escludere test specifici (es. `B105`, `B201`) o configurare soglie di gravita.

### Brakeman (Ruby/Rails)

Brakeman supporta il filtraggio per tipo per concentrarsi su categorie specifiche di vulnerabilita:

```yaml
scanners:
  brakeman:
    extra_args: ["-t", "SQL,XSS,CommandInjection"]
```

Usare `-t` per eseguire solo tipi di controllo specifici, o `--except` per escludere tipi.

## Suggerimenti per lo Sviluppo delle Regole

1. **Iniziare in modo specifico, poi ampliare** -- cominciare con pattern esatti e allentare i vincoli secondo necessità
2. **Usare le metavariabili** -- `$VAR` corrisponde a qualsiasi espressione, `$...ARGS` corrisponde a più argomenti
3. **Testare con codice reale** -- usare file sorgente aipix effettivi per convalidare le regole
4. **Impostare la gravità appropriata** -- `ERROR` per problemi sfruttabili, `WARNING` per rischi potenziali, `INFO` per la qualità del codice
5. **Aggiungere metadati** -- i campi `category` e `component` aiutano con il filtraggio e la reportistica
