# Guide administrateur

## Configuration

### Sources de configuration (ordre de priorité)

1. **Arguments du constructeur** -- surcharges programmatiques
2. **Variables d'environnement** -- préfixe `SCANNER_*`
3. **Fichier dotenv** -- fichier `.env`
4. **Secrets de fichiers** -- secrets Docker/K8s
5. **Fichier de configuration YAML** -- `config.yml` (priorité la plus basse)

### Fichier de configuration

Copiez l'exemple et personnalisez-le :

```bash
cp config.yml.example config.yml
```

## Configuration des scanners

Chacun des cinq outils de scan peut être activé indépendamment, recevoir un délai d'expiration et se voir passer des arguments supplémentaires :

```yaml
scanners:
  semgrep:
    enabled: true
    timeout: 180
    extra_args: []
  cppcheck:
    enabled: true
    timeout: 120
    extra_args: []
  gitleaks:
    enabled: true
    timeout: 120
    extra_args: []
  trivy:
    enabled: true
    timeout: 120
    extra_args: []
  checkov:
    enabled: true
    timeout: 120
    extra_args: []
```

- **enabled** -- définir à `false` pour ignorer complètement un outil
- **timeout** -- nombre maximum de secondes avant que l'outil soit arrêté
- **extra_args** -- arguments CLI supplémentaires passés à l'outil

## Configuration de l'IA

```yaml
ai:
  max_cost_per_scan: 5.0
  model: "claude-sonnet-4-6"
  max_findings_per_batch: 50
  max_tokens_per_response: 4096
```

| Paramètre | Description | Valeur par défaut |
|-----------|-------------|-------------------|
| `max_cost_per_scan` | Dépense maximale en USD pour l'analyse IA par scan | `5.0` |
| `model` | Identifiant du modèle Claude | `claude-sonnet-4-6` |
| `max_findings_per_batch` | Nombre maximum de résultats envoyés à Claude par requête | `50` |
| `max_tokens_per_response` | Nombre maximum de tokens de réponse de Claude | `4096` |

## Configuration de la quality gate

```yaml
gate:
  fail_on:
    - critical
    - high
  include_compound_risks: true
```

- **fail_on** -- liste des niveaux de sévérité qui font échouer la gate
- **include_compound_risks** -- lorsque `true`, les risques composés avec une sévérité correspondante font également échouer la gate

## Configuration des notifications

### Slack

```yaml
notifications:
  slack:
    enabled: false
```

Définissez l'URL du webhook au niveau supérieur :

```yaml
slack_webhook_url: "https://hooks.slack.com/services/T.../B.../xxx"
```

Ou via la variable d'environnement : `SCANNER_SLACK_WEBHOOK_URL`

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

Définissez l'hôte SMTP au niveau supérieur :

```yaml
email_smtp_host: "smtp.example.com"
```

Ou via la variable d'environnement : `SCANNER_EMAIL_SMTP_HOST`

Le mot de passe SMTP doit utiliser la variable d'environnement imbriquée : `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PASSWORD`

### URL du tableau de bord

```yaml
dashboard_url: ""  # e.g., http://scanner:8000/dashboard
```

Utilisée dans les messages de notification pour renvoyer vers les résultats du scan. Si vide, dérivée automatiquement de l'hôte et du port.

## Variables d'environnement

Tous les paramètres peuvent être surchargés avec le préfixe `SCANNER_` :

| Variable | Description | Valeur par défaut |
|----------|-------------|-------------------|
| `SCANNER_HOST` | Adresse d'écoute | `0.0.0.0` |
| `SCANNER_PORT` | Port d'écoute | `8000` |
| `SCANNER_DB_PATH` | Chemin du fichier de base de données SQLite | `/data/scanner.db` |
| `SCANNER_API_KEY` | Clé d'authentification API | `""` (vide) |
| `SCANNER_CLAUDE_API_KEY` | Clé API Anthropic pour l'analyse IA | `""` (vide) |
| `SCANNER_SLACK_WEBHOOK_URL` | URL du webhook Slack | `""` |
| `SCANNER_EMAIL_SMTP_HOST` | Nom d'hôte du serveur SMTP | `""` |
| `SCANNER_LOG_LEVEL` | Niveau de log (debug/info/warning/error) | `info` |
| `SCANNER_SCAN_TIMEOUT` | Délai d'expiration global du scan en secondes | `600` |
| `SCANNER_CONFIG_PATH` | Chemin vers le fichier de configuration YAML | `config.yml` |

### Variables d'environnement imbriquées

Pour les sections de configuration imbriquées, utilisez des doubles underscores :

| Variable | Correspondance |
|----------|---------------|
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PASSWORD` | `notifications.email.smtp_password` |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PORT` | `notifications.email.smtp_port` |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_USER` | `notifications.email.smtp_user` |
| `SCANNER_NOTIFICATIONS__SLACK__ENABLED` | `notifications.slack.enabled` |

## Gestion des secrets

Ne stockez jamais les secrets dans `config.yml` ni ne les committez dans git.

```bash
# Définir les secrets via l'environnement :
export SCANNER_API_KEY="your-secure-key"
export SCANNER_CLAUDE_API_KEY="sk-ant-..."

# Ou dans docker-compose via le fichier .env :
echo "SCANNER_API_KEY=your-secure-key" >> .env
echo "SCANNER_CLAUDE_API_KEY=sk-ant-..." >> .env
```

## Gestion de la base de données

### Emplacement

- Docker : `/data/scanner.db` (volume persistant `scanner_data`)
- Local : configurable via `SCANNER_DB_PATH`

### Mode WAL

SQLite fonctionne en mode WAL (Write-Ahead Logging) pour des performances de lecture concurrent. Ce mode est défini automatiquement à chaque connexion via les écouteurs d'événements SQLAlchemy.

### Sauvegarde

```bash
# Le mode WAL permet une sauvegarde à chaud (pas besoin d'arrêter le scanner)
docker cp naveksoft-security-scanner-1:/data/scanner.db ./backup/
```

## Réglage des seuils

### Quality Gate

Ajustez quelles sévérités font échouer la gate :

```yaml
gate:
  fail_on:
    - critical        # Only block on critical (relaxed)
```

Ou incluez medium :

```yaml
gate:
  fail_on:
    - critical
    - high
    - medium           # Stricter policy
```

### Gestion des outils de scan

Désactivez les outils non pertinents pour votre base de code :

```yaml
scanners:
  cppcheck:
    enabled: false     # No C/C++ code
  checkov:
    enabled: false     # No IaC files
```

## Réglage des performances

### Délais d'expiration

- `scan_timeout` (global) : durée totale maximale du scan (défaut : 600s)
- `timeout` par scanner : temps d'exécution maximal par outil (défaut : 120-180s)

Si les scans expirent, augmentez le délai d'expiration par outil pour le scanner lent plutôt que le délai global.

### Taille des lots IA

Pour les grands scans avec de nombreux résultats, ajustez :

```yaml
ai:
  max_findings_per_batch: 25   # Smaller batches for faster responses
  max_tokens_per_response: 8192  # More room for detailed analysis
```

### Surveillance

```bash
# Health check
curl http://localhost:8000/api/health

# Container status
docker compose ps

# Logs
docker compose logs scanner --tail 50
```

Docker Compose effectue des vérifications de santé automatiques toutes les 30 secondes.
