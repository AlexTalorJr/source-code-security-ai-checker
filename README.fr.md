# Source Code Security AI Scanner

Analyseur de vulnérabilités de sécurité alimenté par l'IA pour l'analyse de code source.

## Démarrage rapide

Lancez votre premier scan en moins de 5 minutes.

### Prérequis

- Docker & Docker Compose
- Une clé API Anthropic (pour l'analyse IA)

### Installation

```bash
# 1. Cloner
git clone https://github.com/AlexTalorJr/source-code-security-ai-checker.git
cd source-code-security-ai-checker

# 2. Configurer
cp config.yml.example config.yml
cp .env.example .env

# 3. Définir les secrets dans .env
#    SCANNER_API_KEY=<votre-clé-api>
#    SCANNER_CLAUDE_API_KEY=<votre-clé-anthropic>

# 4. Démarrer
docker compose up -d

# 5. Vérifier
curl http://localhost:8000/api/health
```

Réponse attendue :

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime_seconds": 5.23,
  "database": "ok"
}
```

## Tableau de bord web

Le scanner inclut une interface web intégrée accessible à l'adresse `http://localhost:8000/dashboard/`.

**Connexion :** utilisez la clé API définie dans `SCANNER_API_KEY`.

### Lancer un scan depuis le tableau de bord

1. Ouvrez **Historique des scans** (`/dashboard/history`)
2. Cliquez sur **"Start New Scan"** — le formulaire se développe
3. Renseignez soit **Local Path** soit **Repository URL** + **Branch**
4. Cochez optionnellement **"Skip AI Analysis"** pour exécuter sans l'API Claude (plus rapide, sans coût)
5. Cliquez sur **"Start Scan"**

Le scan s'exécute en arrière-plan. La page de détail affiche la progression en temps réel avec actualisation automatique, et les résultats apparaissent automatiquement à la fin.

### Pages du tableau de bord

| Page | URL | Description |
|------|-----|-------------|
| Historique des scans | `/dashboard/history` | Liste de tous les scans + formulaire de nouveau scan |
| Détail d'un scan | `/dashboard/scans/{id}` | Résultats, répartition par sévérité, contrôles de suppression |
| Tendances | `/dashboard/trends` | Graphiques : sévérité dans le temps, distribution par outil |

### Lancer un scan via l'API

```bash
curl -X POST http://localhost:8000/api/scans \
  -H "X-API-Key: $SCANNER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/your-org/your-repo.git", "branch": "main"}'
```

Pour désactiver l'analyse IA pour un scan spécifique :

```bash
curl -X POST http://localhost:8000/api/scans \
  -H "X-API-Key: $SCANNER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/your-org/repo.git", "branch": "main", "skip_ai": true}'
```

## Intégration Jenkins Pipeline

Ajoutez le scanner comme étape dans votre `Jenkinsfile` pour bloquer les déploiements en cas de résultats Critical/High.

### Étape Jenkinsfile de base

```groovy
pipeline {
    agent any

    environment {
        SCANNER_URL = 'http://scanner-host:8000'
        SCANNER_API_KEY = credentials('scanner-api-key')
    }

    stages {
        stage('Security Scan') {
            steps {
                script {
                    // Trigger scan
                    def response = httpRequest(
                        url: "${SCANNER_URL}/api/scans",
                        httpMode: 'POST',
                        contentType: 'APPLICATION_JSON',
                        customHeaders: [[name: 'X-API-Key', value: "${SCANNER_API_KEY}"]],
                        requestBody: """{"repo_url": "${env.GIT_URL}", "branch": "${env.GIT_BRANCH}"}"""
                    )

                    def scan = readJSON text: response.content
                    def scanId = scan.id
                    echo "Scan started: #${scanId}"

                    // Poll until complete
                    def status = 'queued'
                    while (status == 'queued' || status == 'running') {
                        sleep 10
                        def progress = httpRequest(
                            url: "${SCANNER_URL}/api/scans/${scanId}/progress",
                            httpMode: 'GET'
                        )
                        status = readJSON(text: progress.content).stage
                    }

                    // Check quality gate
                    def result = httpRequest(
                        url: "${SCANNER_URL}/api/scans/${scanId}",
                        httpMode: 'GET',
                        customHeaders: [[name: 'X-API-Key', value: "${SCANNER_API_KEY}"]]
                    )
                    def scanResult = readJSON text: result.content

                    if (!scanResult.gate_passed) {
                        error "Security scan FAILED: ${scanResult.critical_count} Critical, ${scanResult.high_count} High findings"
                    }

                    echo "Security scan PASSED (${scanResult.total_findings} findings, gate passed)"
                }
            }
        }
    }
}
```

### Points clés

- **Quality gate** bloque le build si des résultats Critical ou High sont détectés (configurable dans `config.yml` sous `gate.fail_on`)
- **Scan via chemin local** — si Jenkins et le scanner partagent un système de fichiers, utilisez `"path": "${WORKSPACE}"` à la place de `repo_url`
- **Désactiver l'analyse IA** — ajoutez `"skip_ai": true` dans le corps de la requête pour des scans plus rapides sans coûts API Claude
- **Notifications** — configurez Slack/email dans `config.yml` pour recevoir des alertes à la fin des scans
- **Rapports** — les rapports HTML et PDF sont générés automatiquement, accessibles via `/api/scans/{id}/report` ou le tableau de bord

Consultez le [Guide DevOps](docs/fr/devops-guide.md) pour les détails complets de l'intégration Jenkins, y compris des exemples de pipeline avec des étapes parallèles.

## Fonctionnalités

- **8 scanners de sécurité avec détection automatique** -- les scanners sont activés automatiquement selon les langages du projet
- **Support multi-langages** -- Python, PHP/Laravel, C/C++, JavaScript/TypeScript, Go, Rust, Java, C#, Ruby
- **Analyse alimentée par l'IA** -- Claude examine les résultats pour le contexte, les risques composés et les suggestions de correction
- **Rapports HTML et PDF interactifs** -- résultats filtrables avec contexte de code et graphiques
- **Quality gate configurable** -- blocage des déploiements sur les résultats de sévérité Critical/High
- **Tableau de bord web** -- gestion des scans, progression en temps réel, historique, contrôles de suppression
- **API REST** -- déclenchement des scans, récupération des résultats, gestion des résultats par programmation
- **Notifications Slack et email** -- alertes en temps réel avec identification de la cible du scan
- **Intégration CI Jenkins** -- étape de pipeline avec vérification de la quality gate
- **Historique des scans avec comparaison delta** -- suivi des nouveaux résultats, des résultats corrigés et persistants
- **Skip AI par scan** -- exécution sans API Claude quand la vitesse ou le coût l'exige

## Scanners supportés

Les scanners sont activés automatiquement selon les langages détectés (`enabled: auto`). Il est possible de les remplacer individuellement dans `config.yml`.

| Scanner | Langages | Ce qu'il détecte |
|---------|----------|-----------------|
| **Semgrep** | Python, PHP, JS/TS, Go, Java, Ruby, C#, Rust | SAST — injections, problèmes d'authentification, patterns non sécurisés |
| **cppcheck** | C/C++ | Sécurité mémoire, débordements de tampon, comportement indéfini |
| **Gitleaks** | Tous | Secrets codés en dur, clés API, tokens dans le code et l'historique git |
| **Trivy** | Docker, Terraform, K8s | CVE dans les images de conteneurs et erreurs de configuration IaC |
| **Checkov** | Docker, Terraform, CI configs | Bonnes pratiques de sécurité Infrastructure-as-code |
| **Psalm** | PHP | Analyse de contamination — injection SQL, XSS via suivi du flux de données |
| **Enlightn** | Laravel | CSRF, mass assignment, mode debug, .env exposé (plus de 120 vérifications) |
| **PHP Security Checker** | PHP (composer) | CVE connues dans les dépendances composer |

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/fr/architecture.md) | Conception du système, diagramme des composants, flux de données |
| [Schéma de base de données](docs/fr/database-schema.md) | Schéma SQLite, diagramme ER, index |
| [Référence API](docs/fr/api.md) | Endpoints REST API et authentification |
| [Guide utilisateur](docs/fr/user-guide.md) | Rapports, résultats, quality gate, suppressions |
| [Guide administrateur](docs/fr/admin-guide.md) | Configuration, variables d'environnement, réglages |
| [Guide DevOps](docs/fr/devops-guide.md) | Déploiement Docker, Jenkins, sauvegardes |
| [Guide de transfert](docs/fr/transfer-guide.md) | Procédures de migration de serveur |
| [Règles personnalisées](docs/fr/custom-rules.md) | Écriture de règles Semgrep personnalisées |

## État du projet

Toutes les phases v1.0 sont terminées.

| Phase | Description | Statut |
|-------|-------------|--------|
| 1 | Foundation & Data Models | Done |
| 2 | Scanner Adapters & Orchestration | Done |
| 3 | AI Analysis (Claude API) | Done |
| 4 | Report Generation (HTML/PDF) | Done |
| 5 | Dashboard, Notifications & Quality Gate | Done |
| 6 | Packaging, Portability & Documentation | Done |

## Stack technique

- **Python 3.12** -- langage principal
- **FastAPI** -- API REST et tableau de bord web
- **SQLAlchemy 2.0** -- ORM asynchrone avec SQLite
- **SQLite (mode WAL)** -- base de données embarquée
- **Pydantic v2** -- validation des données et configuration
- **Docker** -- conteneurisation
- **Alembic** -- migrations de base de données
- **Anthropic Claude** -- analyse de vulnérabilités alimentée par l'IA
- **WeasyPrint** -- génération de rapports PDF
- **Jinja2** -- templates HTML pour les rapports et le tableau de bord
- **Typer** -- interface CLI

## Licence

Apache 2.0

---

Documentation disponible en d'autres langues : [English](README.md) | [Русский](README.ru.md)
