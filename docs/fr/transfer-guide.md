# Guide de transfert

## Vue d'ensemble

Ce guide couvre la migration de Security AI Scanner vers un nouveau serveur, le transfert du projet à une nouvelle équipe, ou la mise en place d'une nouvelle installation.

**Ce qui est transféré :**
- Base de données SQLite (historique des scans, résultats, suppressions)
- Fichiers de configuration (`config.yml`, `.env`)
- Rapports générés (HTML/PDF)

**Ce qui n'est PAS transféré :**
- Images Docker -- reconstruites sur l'hôte cible depuis les sources
- Environnements virtuels Python -- recréés lors de `make install`

## Prérequis

L'hôte cible nécessite :

- Docker Engine 20.10+
- Docker Compose v2+
- GNU Make
- Git (pour le clonage du dépôt)
- 2 Go de RAM minimum
- 10 Go d'espace disque

## Export depuis la source

Créez une archive de sauvegarde sur le serveur source :

```bash
cd /path/to/naveksoft-security

# Créer une sauvegarde horodatée (DB + rapports + config)
make backup
# Résultat : backups/backup-YYYYMMDD_HHMMSS.tar.gz
```

Copiez l'archive vers l'hôte cible :

```bash
scp backups/backup-*.tar.gz user@target-server:/tmp/
```

## Import vers la cible

### Nouvelle installation (Git Clone)

```bash
# Sur le serveur cible
git clone https://github.com/AlexTalorJr/naveksoft-security.git
cd naveksoft-security

# Configurer
cp .env.example .env
# Éditez .env avec les vraies valeurs (voir la Référence des variables d'environnement ci-dessous)

cp config.yml.example config.yml
# Éditez config.yml si nécessaire

# Construire et démarrer
make install
make run

# Exécuter les migrations
make migrate

# Vérifier
curl http://localhost:8000/api/health
```

### Restauration des données depuis une sauvegarde

Si vous disposez d'une archive de sauvegarde du serveur source :

```bash
# Après make install et make run :
make restore BACKUP=/tmp/backup-20260320_143000.tar.gz

# Redémarrer pour prendre en compte les données restaurées
docker compose restart

# Vérifier
curl http://localhost:8000/api/health
```

## Liste de contrôle d'intégration

Suivez ces étapes pour mettre en service une nouvelle installation :

1. Installez Docker et Docker Compose sur l'hôte cible
2. Clonez le dépôt :
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
5. Définissez `SCANNER_CLAUDE_API_KEY` -- obtenez-la depuis la [Console Anthropic](https://console.anthropic.com/)
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
10. Vérifiez l'endpoint de santé :
    ```bash
    curl http://localhost:8000/api/health
    # Attendu : {"status": "healthy", ...}
    ```
11. Exécutez votre premier scan :
    ```bash
    curl -X POST http://localhost:8000/api/scans \
      -H "X-API-Key: your-key" \
      -H "Content-Type: application/json" \
      -d '{"path": "/path/to/code"}'
    ```

## Référence des variables d'environnement

Toutes les variables utilisent le préfixe `SCANNER_`. Définissez-les dans le fichier `.env`.

| Variable | Requis | Défaut | Description | Exemple |
|----------|--------|--------|-------------|---------|
| `SCANNER_API_KEY` | Oui | -- | Clé API pour l'authentification REST API | `dGhpcyBpcyBhIHRlc3Q` |
| `SCANNER_CLAUDE_API_KEY` | Oui | -- | Clé API Anthropic pour l'analyse IA | `sk-ant-api03-...` |
| `SCANNER_PORT` | Non | `8000` | Port externe pour le scanner | `9000` |
| `SCANNER_DB_PATH` | Non | `/data/scanner.db` | Chemin du fichier de base de données SQLite | `/data/scanner.db` |
| `SCANNER_CONFIG_PATH` | Non | `config.yml` | Chemin vers le fichier de configuration YAML | `config.yml` |
| `SCANNER_GIT_TOKEN` | Non | -- | Token pour le clonage de dépôts privés | `ghp_xxxxxxxxxxxx` |
| `SCANNER_SLACK_WEBHOOK_URL` | Non | -- | Webhook Slack pour les notifications | `https://hooks.slack.com/...` |
| `SCANNER_EMAIL_SMTP_HOST` | Non | -- | Serveur SMTP pour les notifications email | `smtp.gmail.com` |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PORT` | Non | `587` | Port SMTP | `587` |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_USER` | Non | -- | Nom d'utilisateur SMTP | `alerts@example.com` |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PASSWORD` | Non | -- | Mot de passe SMTP | -- |
| `SCANNER_NOTIFICATIONS__EMAIL__RECIPIENTS` | Non | `[]` | Tableau JSON d'adresses email destinataires | `["dev@example.com"]` |

## Dépannage

### Le conteneur ne démarre pas

```bash
docker compose logs scanner
```

Causes courantes :
- Port déjà utilisé -- modifiez `SCANNER_PORT` dans `.env`
- Fichier `.env` manquant -- copiez depuis `.env.example`
- Docker non démarré -- démarrez le daemon Docker

### L'endpoint de santé retourne une erreur

```bash
curl http://localhost:8000/api/health
# {"status": "degraded", "database": "error"}
```

Vérifiez que `SCANNER_DB_PATH` pointe vers un emplacement accessible en écriture à l'intérieur du conteneur. Le chemin par défaut `/data/scanner.db` requiert que le volume `scanner_data` soit monté.

### Les scans échouent ou expirent

- Vérifiez que les outils de scan (semgrep, trivy, etc.) sont disponibles dans l'image Docker
- Augmentez `scan_timeout` dans `config.yml` pour les grands dépôts
- Pour les dépôts privés, assurez-vous que `SCANNER_GIT_TOKEN` est défini

### Erreurs de base de données verrouillée

La base de données utilise le mode WAL pour l'accès en lecture concurrent. Si vous voyez des erreurs "database is locked" :
- Assurez-vous qu'un seul conteneur scanner est en cours d'exécution
- N'accédez pas directement au fichier SQLite pendant que le conteneur est en cours d'exécution
- Utilisez `make backup` pour des copies sécurisées de la base de données

### Permission refusée sur /data

Le conteneur s'exécute en tant qu'utilisateur non-root `scanner`. Assurez-vous que le volume Docker a les propriétés correctes :

```bash
docker compose down
docker volume rm naveksoft-security_scanner_data
docker compose up -d  # Recreates volume with correct permissions
```

Remarque : cela supprime les données de scan existantes. Effectuez d'abord une sauvegarde avec `make backup`.
