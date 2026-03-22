# Guide des règles personnalisées

## Vue d'ensemble

Ce guide couvre la création de règles Semgrep personnalisées pour les composants de la plateforme aipix. Les règles personnalisées permettent la détection de vulnérabilités spécifiques à la plateforme que les règles génériques ne détectent pas.

## Composants cibles

| Composant | Langage | Préoccupations clés |
|-----------|---------|---------------------|
| VMS (Video Management) | PHP/Laravel | Injection SQL, authentification défaillante, IDOR |
| Mediaserver | C++ | Dépassement de tampon, chaînes de format, sécurité mémoire |
| REST API | PHP/Laravel | Exposition de tokens API, SSRF, mass assignment |
| Webhooks | PHP | Vérification de signature manquante |
| Desktop Client | C# | Désérialisation non sécurisée, stockage des identifiants |

## Format des règles Semgrep

Les règles Semgrep sont des fichiers YAML avec des définitions de correspondance de motifs. Chaque règle spécifie :

- **id** -- identifiant unique de la règle (utilisez le préfixe `aipix.` pour les règles personnalisées)
- **pattern** -- motif de code à faire correspondre (supporte les métavariables comme `$VAR`)
- **message** -- description lisible du résultat
- **severity** -- `ERROR` (Critical/High), `WARNING` (Medium), ou `INFO` (Low/Info)
- **languages** -- liste des langages auxquels la règle s'applique

## Emplacement des fichiers de règles

Les règles personnalisées sont stockées dans le répertoire `rules/` à la racine du projet. L'adaptateur Semgrep charge automatiquement tous les fichiers `.yml` de ce répertoire en parallèle avec l'ensemble de règles par défaut.

```
rules/
  aipix-rtsp-auth.yml
  aipix-api-security.yml
  aipix-memory-safety.yml
```

## Exemples de règles

### Identifiants RTSP codés en dur

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

### Token API dans les logs

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

### Vérification de signature webhook manquante

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

### Injection SQL via requête brute

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

## Test des règles

Testez les règles personnalisées sur un code d'exemple avant de les déployer :

```bash
# Test d'un seul fichier de règle sur un répertoire cible
semgrep --config rules/aipix-rtsp-auth.yml /path/to/code

# Test de toutes les règles personnalisées
semgrep --config rules/ /path/to/code

# Exécution à sec (afficher les correspondances sans sortie complète)
semgrep --config rules/ --json /path/to/code | python3 -m json.tool
```

## Regles personnalisees pour d'autres scanners

En plus de Semgrep, plusieurs autres scanners supportent la configuration de regles personnalisees :

### gosec (Go)

gosec supporte l'inclusion ou l'exclusion d'identifiants de regles specifiques :

```yaml
scanners:
  gosec:
    extra_args: ["-include=G101,G201,G301"]
```

Utilisez `-include` pour executer uniquement des regles specifiques, ou `-exclude` pour ignorer des regles. Les identifiants de regles suivent le schema `G1xx` (injection), `G2xx` (crypto), `G3xx` (E/S fichier), `G4xx` (reseau), `G5xx` (liste noire).

### Bandit (Python)

Bandit supporte les profils personnalises via des fichiers de configuration :

```yaml
scanners:
  bandit:
    extra_args: ["-c", "bandit.yml"]
```

Creez un profil `bandit.yml` pour inclure/exclure des tests specifiques (ex. : `B105`, `B201`) ou configurer des seuils de severite.

### Brakeman (Ruby/Rails)

Brakeman supporte le filtrage par type pour se concentrer sur des categories de vulnerabilites specifiques :

```yaml
scanners:
  brakeman:
    extra_args: ["-t", "SQL,XSS,CommandInjection"]
```

Utilisez `-t` pour executer uniquement des types de verifications specifiques, ou `--except` pour exclure des types.

## Conseils de developpement de regles

1. **Commencez spécifique, élargissez ensuite** -- commencez avec des motifs exacts et assouplissez les contraintes au besoin
2. **Utilisez des métavariables** -- `$VAR` correspond à n'importe quelle expression, `$...ARGS` correspond à plusieurs arguments
3. **Testez avec du code réel** -- utilisez les fichiers source aipix réels pour valider les règles
4. **Définissez la sévérité appropriée** -- `ERROR` pour les problèmes exploitables, `WARNING` pour les risques potentiels, `INFO` pour la qualité du code
5. **Ajoutez des métadonnées** -- les champs `category` et `component` facilitent le filtrage et le reporting
