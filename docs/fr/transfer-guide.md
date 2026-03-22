# Guide de Transfert

## Aperçu

Ce guide couvre la migration de Security AI Scanner vers un nouveau serveur, la transmission du projet à une nouvelle équipe ou la mise en place d'une installation nouvelle.

**Ce qui est transféré :**
- Base de données SQLite (historique des analyses, conclusions, suppressions)
- Fichiers de configuration (`config.yml`, `.env`)
- Rapports générés (HTML/PDF)

**Ce qui n'est PAS transféré :**
- Images Docker -- reconstruites sur l'hôte cible à partir de la source
- Environnements virtuels Python -- recréés lors de `make install`

## Prérequis

L'hôte cible doit avoir :

- Docker Engine 20.10+
- Docker Compose v2+
- GNU Make
- Git (pour cloner le référentiel)
- 2 GB de RAM minimum
- 10 GB d'espace disque

## Exporter depuis la Source

Créez une archive de sauvegarde sur le serveur source :

```bash
cd /path/to/naveksoft-security

# Create timestamped backup (DB + reports + config)
make backup
# Output: backups/backup-YYYYMMDD_HHMMSS.tar.gz
```

Copiez l'archive vers l'hôte cible :

```bash
scp backups/backup-*.tar.gz user@target-server:/tmp/
```

## Importer vers la Cible

### Installation Nouvelle (Clone Git)

```bash
# On target server
git clone https://github.com/AlexTalorJr/naveksoft-security.git
cd naveksoft-security

# Configure
cp .env.example .env
# Edit .env with real values (see Environment Variables Reference below)

cp config.yml.example config.yml
# Edit config.yml if needed

# Build and start
make install
make run

# Run migrations
make migrate

# Verify
curl http://localhost:8000/api/health
```

### Restauration des Données à partir de la Sauvegarde

Si vous disposez d'une archive de sauvegarde du serveur source :

```bash
# After make install and make run:
make restore BACKUP=/tmp/backup-20260320_143000.tar.gz

# Restart to pick up restored data
docker compose restart

# Verify
curl http://localhost:8000/api/health
```

## Liste de Vérification de l'Intégration

Suivez ces étapes pour mettre en place une nouvelle installation :

1. Installez Docker et Docker Compose sur l'hôte cible
2. Clonez le référentiel :
   ```bash
   git clone https://github.com/AlexTalorJr/naveksoft-security.git
   cd naveksoft-security
   ```
3. Copiez les modèles de configuration :
   ```bash
   cp config.yml.example config.yml
   cp .env.example .env
   ```
4. Définissez `SCANNER_API_KEY` -- générez une clé sécurisée :
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
5. Définissez `SCANNER_CLAUDE_API_KEY` -- obtenu à partir de la [Anthropic Console](https://console.anthropic.com/)
6. Configurez les paramètres de notification si nécessaire :
   - Slack : définissez `SCANNER_SLACK_WEBHOOK_URL` dans `.env`
   - Email : définissez `SCANNER_EMAIL_SMTP_HOST`, `SCANNER_NOTIFICATIONS__EMAIL__SMTP_USER`, `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PASSWORD`, et `SCANNER_NOTIFICATIONS__EMAIL__RECIPIENTS` dans `.env`
7. Construisez les images Docker :
   ```bash
   make install
   ```
8. Démarrez le scanner :
   ```bash
   make run
   ```
9. Exécutez les migrations de base de données :
   ```bash
   make migrate
   ```
10. Vérifiez le point d'accès de santé :
    ```bash
    curl http://localhost:8000/api/health
    # Expected: {"status": "healthy", ...}
    ```
11. Exécutez votre première analyse :
    ```bash
    curl -X POST http://localhost:8000/api/scans \
      -H "X-API-Key: your-key" \
      -H "Content-Type: application/json" \
      -d '{"path": "/path/to/code"}'
    ```

## Référence des Variables d'Environnement

Toutes les variables utilisent le préfixe `SCANNER_`. Définissez-les dans le fichier `.env`.

| Variable | Obligatoire | Par défaut | Description | Exemple |
|----------|----------|---------|-------------|---------|
| `SCANNER_API_KEY` | Oui | -- | Clé API pour l'authentification de l'API REST | `dGhpcyBpcyBhIHRlc3Q` |
| `SCANNER_CLAUDE_API_KEY` | Oui | -- | Clé API Anthropic pour l'analyse IA | `sk-ant-api03-...` |
| `SCANNER_PORT` | Non | `8000` | Port externe pour le scanner | `9000` |
| `SCANNER_DB_PATH` | Non | `/data/scanner.db` | Chemin du fichier de base de données SQLite | `/data/scanner.db` |
| `SCANNER_CONFIG_PATH` | Non | `config.yml` | Chemin vers le fichier de configuration YAML | `config.yml` |
| `SCANNER_GIT_TOKEN` | Non | -- | Jeton pour cloner les référentiels privés | `ghp_xxxxxxxxxxxx` |
| `SCANNER_SLACK_WEBHOOK_URL` | Non | -- | Webhook Slack pour les notifications | `https://hooks.slack.com/...` |
| `SCANNER_EMAIL_SMTP_HOST` | Non | -- | Serveur SMTP pour les notifications par email | `smtp.gmail.com` |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PORT` | Non | `587` | Port SMTP | `587` |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_USER` | Non | -- | Nom d'utilisateur SMTP | `alerts@example.com` |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PASSWORD` | Non | -- | Mot de passe SMTP | -- |
| `SCANNER_NOTIFICATIONS__EMAIL__RECIPIENTS` | Non | `[]` | Tableau JSON des adresses email des destinataires | `["dev@example.com"]` |

## Dépannage

### Le Conteneur ne Démarre pas

```bash
docker compose logs scanner
```

Causes courantes :
- Port déjà utilisé -- modifiez `SCANNER_PORT` dans `.env`
- Fichier `.env` manquant -- copiez depuis `.env.example`
- Docker n'est pas en cours d'exécution -- démarrez le daemon Docker

### Le Point d'Accès de Santé Retourne une Erreur

```bash
curl http://localhost:8000/api/health
# {"status": "degraded", "database": "error"}
```

Vérifiez que `SCANNER_DB_PATH` pointe vers un emplacement inscriptible à l'intérieur du conteneur. La valeur par défaut `/data/scanner.db` nécessite que le volume `scanner_data` soit monté.

### Les Analyses Échouent ou Dépassent le Délai

- Verifiez que les 12 outils de scan (semgrep, cppcheck, gitleaks, trivy, checkov, psalm, enlightn, php-security-checker, gosec, bandit, brakeman, cargo-audit) sont disponibles dans l'image Docker. Executez `make verify-scanners` pour confirmer
- Augmentez `scan_timeout` dans `config.yml` pour les gros référentiels
- Pour les référentiels privés, assurez-vous que `SCANNER_GIT_TOKEN` est défini

### Erreurs de Base de Données Verrouillée

La base de données utilise le mode WAL pour l'accès concurrentiel en lecture. Si vous voyez des erreurs "database is locked" :
- Assurez-vous que seul un conteneur scanner est en cours d'exécution
- N'accédez pas directement au fichier SQLite tandis que le conteneur est en cours d'exécution
- Utilisez `make backup` pour les copies de base de données sûres

### Permission Refusée sur /data

Le conteneur s'exécute en tant qu'utilisateur non-root `scanner`. Assurez-vous que le volume Docker a la propriété correcte :

```bash
docker compose down
docker volume rm naveksoft-security_scanner_data
docker compose up -d  # Recreates volume with correct permissions
```

Remarque : Cela supprime les données d'analyse existantes. Sauvegardez d'abord avec `make backup`.
