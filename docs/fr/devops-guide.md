# Guide DevOps

## Déploiement Docker

### Démarrage rapide

```bash
cp config.yml.example config.yml
cp .env.example .env
# Éditez .env avec les vrais secrets
make install   # construit les images Docker
make run       # démarre le scanner en arrière-plan
```

Ou directement avec Docker Compose :

```bash
docker compose up -d --build
```

### Configuration du conteneur

Le fichier `docker-compose.yml` définit un seul service `scanner` :

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

- **Volume `scanner_data`** monté dans `/data` à l'intérieur du conteneur -- stocke la base de données SQLite et les rapports générés. Les données persistent après les redémarrages et reconstructions du conteneur.
- **Montage de config** lie `config.yml` en lecture seule dans le conteneur à `/app/config.yml`.
- **Mapping de port** défaut à `8000` mais peut être modifié via la variable d'environnement `SCANNER_PORT`.
- **Politique de redémarrage** `unless-stopped` garantit que le scanner redémarre après les redémarrages de l'hôte.

## Dockerfile

L'image est basée sur `python:3.12-slim` :

1. **Dépendances système** -- `curl` (healthcheck), `libpango` et `libharfbuzz` (génération PDF WeasyPrint)
2. **Utilisateur non-root** -- utilisateur et groupe `scanner` créés pour la sécurité ; répertoire `/data` appartenant à cet utilisateur
3. **Workflow d'installation** -- `pyproject.toml` et `src/` copiés, puis `pip install --no-cache-dir .` avec le backend de build hatchling
4. **Fichiers d'application** -- `alembic.ini`, migrations `alembic/`, et `config.yml.example` (comme `config.yml` par défaut) copiés
5. **Point d'entrée** -- `uvicorn scanner.main:app --host 0.0.0.0 --port 8000`

## Variables d'environnement

Toute la configuration peut être définie via des variables d'environnement avec le préfixe `SCANNER_`. Passez les secrets via le fichier `.env` (non commité dans git).

| Variable | Requis | Défaut | Description |
|----------|--------|--------|-------------|
| `SCANNER_API_KEY` | Oui | -- | Clé API pour authentifier les requêtes REST API |
| `SCANNER_CLAUDE_API_KEY` | Oui | -- | Clé API Anthropic pour l'analyse IA |
| `SCANNER_PORT` | Non | `8000` | Port externe pour le service scanner |
| `SCANNER_DB_PATH` | Non | `/data/scanner.db` | Chemin vers le fichier de base de données SQLite |
| `SCANNER_CONFIG_PATH` | Non | `config.yml` | Chemin vers le fichier de configuration YAML |
| `SCANNER_GIT_TOKEN` | Non | -- | Token pour le clonage de dépôts Git privés |
| `SCANNER_SLACK_WEBHOOK_URL` | Non | -- | URL de webhook Slack entrant pour les notifications |
| `SCANNER_EMAIL_SMTP_HOST` | Non | -- | Nom d'hôte du serveur SMTP pour les notifications email |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PORT` | Non | `587` | Port du serveur SMTP |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_USER` | Non | -- | Nom d'utilisateur d'authentification SMTP |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PASSWORD` | Non | -- | Mot de passe d'authentification SMTP |
| `SCANNER_NOTIFICATIONS__EMAIL__RECIPIENTS` | Non | `[]` | Tableau JSON des destinataires email |

## Intégration Jenkins

Le projet inclut `Jenkinsfile.security` pour intégrer les scans de sécurité dans un pipeline Jenkins. Il utilise le plugin Jenkins `httpRequest` pour les appels API.

### Configuration

1. Installez le plugin **HTTP Request** dans Jenkins
2. Ajoutez `SCANNER_URL` (ex. : `http://scanner:8000`) comme variable d'environnement ou identifiant Jenkins
3. Ajoutez `SCANNER_API_KEY` comme identifiant de texte secret Jenkins

### Utilisation

Ajoutez l'étape de scan de sécurité à votre `Jenkinsfile` existant :

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

Le scanner évalue une quality gate après chaque scan. Configurez les critères de réussite/échec dans `config.yml` :

```yaml
gate:
  fail_on:
    - critical
    - high
  include_compound_risks: true
```

Si la gate échoue, l'étape Jenkins doit faire échouer le build. Interrogez le résultat du scan pour vérifier `gate_passed`.

## Sauvegardes

### Utilisation des cibles Make

```bash
# Créer une sauvegarde horodatée (DB + rapports + config)
make backup
# Résultat : backups/backup-20260320_143000.tar.gz

# Restaurer depuis un fichier de sauvegarde
make restore BACKUP=backups/backup-20260320_143000.tar.gz
```

### Ce qui est sauvegardé

- **Base de données SQLite** -- sauvegardée avec la commande `sqlite3 .backup` (sécurisée en mode WAL, sans interruption de service)
- **Rapports** -- rapports HTML/PDF générés depuis `/data/reports`
- **Configuration** -- `config.yml`

### Sécurité en mode WAL

La base de données fonctionne en mode WAL (Write-Ahead Logging). La cible `make backup` utilise la commande `.backup` de SQLite à l'intérieur du conteneur, qui gère en toute sécurité le checkpointing WAL. Ne copiez pas simplement le fichier `.db` -- utilisez la cible make ou la commande `sqlite3 .backup`.

### Planification recommandée

Configurez un cron job quotidien pour les sauvegardes automatisées :

```bash
# Daily at 2 AM
0 2 * * * cd /path/to/naveksoft-security && make backup
```

## Builds multi-architectures

Construisez des images Docker pour les architectures `amd64` et `arm64` en utilisant Docker Buildx.

### Prérequis

- Docker Desktop 4.x+ (inclut buildx) ou plugin `docker-buildx` installé manuellement
- QEMU user-static pour l'émulation cross-plateforme (Docker Desktop le gère automatiquement)

### Construction d'images multi-arch

```bash
# Build for amd64 + arm64, save as OCI archive
make docker-multiarch
# Output: Security AI Scanner-{version}-multiarch.tar

# Build and push to a container registry
make docker-push REGISTRY=your-registry.example.com
```

La cible `docker-multiarch` crée un builder buildx nommé `multiarch` s'il n'existe pas déjà.

## Surveillance

### Endpoint de santé

Interrogez l'endpoint de santé pour surveiller l'état du scanner :

```bash
curl http://localhost:8000/api/health
# {"status": "healthy", "version": "0.1.0", "uptime_seconds": 3600.5, "database": "ok"}
```

Un statut `"degraded"` ou une réponse `"database": "error"` indique un problème avec la connexion à la base de données.

### Healthcheck Docker

Le conteneur inclut un healthcheck intégré qui s'exécute toutes les 30 secondes. Vérifiez l'état de santé du conteneur :

```bash
docker compose ps
# Shows "healthy" or "unhealthy" in the STATUS column
```

### Logs

```bash
# Suivre les logs en temps réel
docker compose logs -f scanner

# Les 100 dernières lignes
docker compose logs scanner --tail 100
```

Le niveau de log est configuré dans `config.yml` via le champ `log_level` (défaut : `info`).

### Politique de redémarrage

Le conteneur utilise `restart: unless-stopped`, il redémarre donc automatiquement après des plantages ou des redémarrages de l'hôte. Seul un `docker compose stop` ou `docker compose down` manuel le maintiendra arrêté.

## Mise à jour

1. Récupérez le code le plus récent :
   ```bash
   git pull origin main
   ```

2. Reconstruisez et redémarrez :
   ```bash
   make install   # rebuilds Docker image
   make run       # starts updated container
   ```

3. Exécutez les migrations de base de données :
   ```bash
   make migrate
   ```

4. Vérifiez la mise à jour :
   ```bash
   curl http://localhost:8000/api/health
   ```

Si l'endpoint de santé retourne le nouveau numéro de version et `"status": "healthy"`, la mise à jour est terminée.
