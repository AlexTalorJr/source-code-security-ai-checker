# Guide DevOps

## Deploiement Docker

### Demarrage rapide

```bash
cp config.yml.example config.yml
cp .env.example .env
# Editez .env avec les vrais secrets
make install   # construit les images Docker
make run       # demarre le scanner en arriere-plan
```

Ou directement avec Docker Compose :

```bash
docker compose up -d --build
```

### Configuration du conteneur

Le fichier `docker-compose.yml` definit un seul service `scanner` :

```yaml
services:
  scanner:
    build: .
    ports:
      - "${SCANNER_PORT:-8000}:8000"
    volumes:
      - scanner_data:/data           # Stockage persistant pour la BD et les rapports
      - ./config.yml:/app/config.yml:ro  # Montage de config en lecture seule
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    restart: unless-stopped

volumes:
  scanner_data:  # Volume nomme pour la persistance SQLite
```

- **Volume `scanner_data`** monte dans `/data` a l'interieur du conteneur -- stocke la base de donnees SQLite et les rapports generes. Les donnees persistent apres les redemarrages et reconstructions du conteneur.
- **Montage de config** lie `config.yml` en lecture seule dans le conteneur a `/app/config.yml`.
- **Mapping de port** defaut a `8000` mais peut etre modifie via la variable d'environnement `SCANNER_PORT`.
- **Politique de redemarrage** `unless-stopped` garantit que le scanner redemarre apres les redemarrages de l'hote.

## Dockerfile

L'image est basee sur `python:3.12-slim` et inclut les 12 outils de scan :

1. **Dependances systeme** -- `curl` (healthcheck), `libpango` et `libharfbuzz` (generation PDF WeasyPrint), `ruby` (Brakeman)
2. **Utilisateur non-root** -- utilisateur et groupe `scanner` crees pour la securite ; repertoire `/data` appartenant a cet utilisateur
3. **Binaires de scanners** -- voir la section Binaires de scanners ci-dessous pour la liste complete
4. **Workflow d'installation** -- `pyproject.toml` et `src/` copies, puis `pip install --no-cache-dir .` avec le backend de build hatchling
5. **Fichiers d'application** -- `alembic.ini`, migrations `alembic/`, et `config.yml.example` (comme `config.yml` par defaut) copies
6. **Point d'entree** -- `uvicorn scanner.main:app --host 0.0.0.0 --port 8000`

## Binaires de scanners

Les 12 outils de scan sont installes dans l'image Docker :

| Scanner | Methode d'installation | Notes |
|---------|----------------------|-------|
| **Semgrep** | `pip install semgrep` | Package Python, installe avec l'application |
| **cppcheck** | `apt-get install cppcheck` | Package systeme |
| **Gitleaks** | Binaire precompile depuis GitHub releases | Telecharge dans `/usr/local/bin`, supporte amd64/arm64 |
| **Trivy** | Binaire precompile depuis GitHub releases | Telecharge dans `/usr/local/bin`, supporte amd64/arm64 |
| **Checkov** | `pip install checkov` | Package Python, installe avec `--no-cache-dir` |
| **Psalm** | `composer global require vimeo/psalm` | Package PHP Composer, necessite `php-cli` |
| **Enlightn** | `composer global require enlightn/enlightn` | Package PHP Composer |
| **PHP Security Checker** | Binaire precompile depuis GitHub releases | Telecharge dans `/usr/local/bin` |
| **gosec** | Binaire precompile depuis GitHub releases | Telecharge dans `/usr/local/bin`, supporte amd64/arm64 |
| **Bandit** | `pip install bandit` | Package Python, installe avec Semgrep et Checkov |
| **Brakeman** | `gem install brakeman` | Gem Ruby, necessite le package `ruby` (~80 Mo) |
| **cargo-audit** | Binaire precompile depuis GitHub releases | Telecharge dans `/usr/local/bin`, supporte amd64/arm64 |

Tous les telechargements de binaires (Gitleaks, Trivy, gosec, cargo-audit, PHP Security Checker) utilisent la detection d'architecture (`dpkg --print-architecture` / `uname -m`) pour telecharger le bon binaire pour les plateformes amd64 ou arm64.

### Verification de la disponibilite des scanners

Apres avoir construit l'image Docker, verifiez que tous les scanners sont correctement installes :

```bash
make verify-scanners
```

Cette cible execute un smoke test a l'interieur du conteneur, verifiant que chacun des 12 binaires de scanners est disponible et repond aux commandes version/help. Utilisez-la apres toute modification du Dockerfile pour vous assurer qu'aucun scanner n'a ete casse.

## Variables d'environnement

Toute la configuration peut etre definie via des variables d'environnement avec le prefixe `SCANNER_`. Passez les secrets via le fichier `.env` (non commite dans git).

| Variable | Requis | Defaut | Description |
|----------|--------|--------|-------------|
| `SCANNER_API_KEY` | Oui | -- | Cle API pour authentifier les requetes REST API |
| `SCANNER_CLAUDE_API_KEY` | Oui | -- | Cle API Anthropic pour l'analyse IA |
| `SCANNER_PORT` | Non | `8000` | Port externe pour le service scanner |
| `SCANNER_DB_PATH` | Non | `/data/scanner.db` | Chemin vers le fichier de base de donnees SQLite |
| `SCANNER_CONFIG_PATH` | Non | `config.yml` | Chemin vers le fichier de configuration YAML |
| `SCANNER_GIT_TOKEN` | Non | -- | Token pour le clonage de depots Git prives |
| `SCANNER_SLACK_WEBHOOK_URL` | Non | -- | URL de webhook Slack entrant pour les notifications |
| `SCANNER_EMAIL_SMTP_HOST` | Non | -- | Nom d'hote du serveur SMTP pour les notifications email |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PORT` | Non | `587` | Port du serveur SMTP |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_USER` | Non | -- | Nom d'utilisateur d'authentification SMTP |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PASSWORD` | Non | -- | Mot de passe d'authentification SMTP |
| `SCANNER_NOTIFICATIONS__EMAIL__RECIPIENTS` | Non | `[]` | Tableau JSON des destinataires email |

## Integration Jenkins

Le projet inclut `Jenkinsfile.security` pour integrer les scans de securite dans un pipeline Jenkins. Il utilise le plugin Jenkins `httpRequest` pour les appels API.

### Configuration

1. Installez le plugin **HTTP Request** dans Jenkins
2. Ajoutez `SCANNER_URL` (ex. : `http://scanner:8000`) comme variable d'environnement ou identifiant Jenkins
3. Ajoutez `SCANNER_API_KEY` comme identifiant de texte secret Jenkins

### Utilisation

Ajoutez l'etape de scan de securite a votre `Jenkinsfile` existant :

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

Le scanner evalue une quality gate apres chaque scan. Configurez les criteres de reussite/echec dans `config.yml` :

```yaml
gate:
  fail_on:
    - critical
    - high
  include_compound_risks: true
```

Si la gate echoue, l'etape Jenkins doit faire echouer le build. Interrogez le resultat du scan pour verifier `gate_passed`.

## Sauvegardes

### Utilisation des cibles Make

```bash
# Creer une sauvegarde horodatee (BD + rapports + config)
make backup
# Resultat : backups/backup-20260320_143000.tar.gz

# Restaurer depuis un fichier de sauvegarde
make restore BACKUP=backups/backup-20260320_143000.tar.gz
```

### Ce qui est sauvegarde

- **Base de donnees SQLite** -- sauvegardee avec la commande `sqlite3 .backup` (securisee en mode WAL, sans interruption de service)
- **Rapports** -- rapports HTML/PDF generes depuis `/data/reports`
- **Configuration** -- `config.yml`

### Securite en mode WAL

La base de donnees fonctionne en mode WAL (Write-Ahead Logging). La cible `make backup` utilise la commande `.backup` de SQLite a l'interieur du conteneur, qui gere en toute securite le checkpointing WAL. Ne copiez pas simplement le fichier `.db` -- utilisez la cible make ou la commande `sqlite3 .backup`.

### Planification recommandee

Configurez un cron job quotidien pour les sauvegardes automatisees :

```bash
# Quotidiennement a 2h du matin
0 2 * * * cd /path/to/naveksoft-security && make backup
```

## Builds multi-architectures

Construisez des images Docker pour les architectures `amd64` et `arm64` en utilisant Docker Buildx.

### Prerequis

- Docker Desktop 4.x+ (inclut buildx) ou plugin `docker-buildx` installe manuellement
- QEMU user-static pour l'emulation cross-plateforme (Docker Desktop le gere automatiquement)

### Construction d'images multi-arch

```bash
# Construction pour amd64 + arm64, sauvegarde en archive OCI
make docker-multiarch
# Resultat : Security AI Scanner-{version}-multiarch.tar

# Construction et envoi vers un registre de conteneurs
make docker-push REGISTRY=your-registry.example.com
```

La cible `docker-multiarch` cree un builder buildx nomme `multiarch` s'il n'existe pas deja.

Les 12 telechargements de binaires de scanners (Gitleaks, Trivy, gosec, cargo-audit, PHP Security Checker) supportent les architectures amd64 et arm64. Les packages Python (Semgrep, Checkov, Bandit) et les gems Ruby (Brakeman) sont independants de la plateforme et fonctionnent sur les deux architectures sans modification.

## Surveillance

### Endpoint de sante

Interrogez l'endpoint de sante pour surveiller l'etat du scanner :

```bash
curl http://localhost:8000/api/health
# {"status": "healthy", "version": "0.1.0", "uptime_seconds": 3600.5, "database": "ok"}
```

Un statut `"degraded"` ou une reponse `"database": "error"` indique un probleme avec la connexion a la base de donnees.

### Healthcheck Docker

Le conteneur inclut un healthcheck integre qui s'execute toutes les 30 secondes. Verifiez l'etat de sante du conteneur :

```bash
docker compose ps
# Affiche "healthy" ou "unhealthy" dans la colonne STATUS
```

### Logs

```bash
# Suivre les logs en temps reel
docker compose logs -f scanner

# Les 100 dernieres lignes
docker compose logs scanner --tail 100
```

Le niveau de log est configure dans `config.yml` via le champ `log_level` (defaut : `info`).

### Politique de redemarrage

Le conteneur utilise `restart: unless-stopped`, il redemarre donc automatiquement apres des plantages ou des redemarrages de l'hote. Seul un `docker compose stop` ou `docker compose down` manuel le maintiendra arrete.

## Mise a jour

1. Recuperez le code le plus recent :
   ```bash
   git pull origin main
   ```

2. Reconstruisez et redemarrez :
   ```bash
   make install   # reconstruit l'image Docker
   make run       # demarre le conteneur mis a jour
   ```

3. Executez les migrations de base de donnees :
   ```bash
   make migrate
   ```

4. Verifiez la mise a jour :
   ```bash
   curl http://localhost:8000/api/health
   ```

Si l'endpoint de sante retourne le nouveau numero de version et `"status": "healthy"`, la mise a jour est terminee.
