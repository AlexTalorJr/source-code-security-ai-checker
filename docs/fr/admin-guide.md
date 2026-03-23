# Guide administrateur

## Configuration

### Sources de configuration (ordre de priorite)

1. **Arguments du constructeur** -- surcharges programmatiques
2. **Variables d'environnement** -- prefixe `SCANNER_*`
3. **Fichier dotenv** -- fichier `.env`
4. **Secrets de fichiers** -- secrets Docker/K8s
5. **Fichier de configuration YAML** -- `config.yml` (priorite la plus basse)

### Fichier de configuration

Copiez l'exemple et personnalisez-le :

```bash
cp config.yml.example config.yml
```

## Configuration des scanners

Chacun des douze outils de scan peut etre configure independamment : activation/desactivation, delai d'expiration, arguments supplementaires et detection automatique par langages. Les scanners avec `enabled: "auto"` sont actives automatiquement lorsque des fichiers correspondants sont detectes.

```yaml
scanners:
  semgrep:
    adapter_class: "scanner.adapters.semgrep.SemgrepAdapter"
    enabled: true
    timeout: 180
    extra_args: ["--exclude", ".venv", "--exclude", "node_modules"]
    languages: ["python", "php", "javascript", "typescript", "go", "java", "kotlin", "ruby", "csharp", "rust"]
  cppcheck:
    adapter_class: "scanner.adapters.cppcheck.CppcheckAdapter"
    enabled: true
    timeout: 120
    extra_args: ["-i.venv", "-inode_modules"]
    languages: ["cpp"]
  gitleaks:
    adapter_class: "scanner.adapters.gitleaks.GitleaksAdapter"
    enabled: true
    timeout: 120
    extra_args: []
    languages: []
  trivy:
    adapter_class: "scanner.adapters.trivy.TrivyAdapter"
    enabled: true
    timeout: 120
    extra_args: []
    languages: ["docker", "terraform", "yaml"]
  checkov:
    adapter_class: "scanner.adapters.checkov.CheckovAdapter"
    enabled: true
    timeout: 120
    extra_args: ["--skip-path", ".venv", "--skip-path", "node_modules"]
    languages: ["docker", "terraform", "yaml", "ci"]
  psalm:
    adapter_class: "scanner.adapters.psalm.PsalmAdapter"
    enabled: "auto"
    timeout: 300
    extra_args: []
    languages: ["php"]
  enlightn:
    adapter_class: "scanner.adapters.enlightn.EnlightnAdapter"
    enabled: "auto"
    timeout: 120
    extra_args: []
    languages: ["laravel"]
  php_security_checker:
    adapter_class: "scanner.adapters.php_security_checker.PhpSecurityCheckerAdapter"
    enabled: "auto"
    timeout: 30
    extra_args: []
    languages: ["php"]
  gosec:
    adapter_class: "scanner.adapters.gosec.GosecAdapter"
    enabled: "auto"
    timeout: 120
    extra_args: []
    languages: ["go"]
  bandit:
    adapter_class: "scanner.adapters.bandit.BanditAdapter"
    enabled: "auto"
    timeout: 120
    extra_args: []
    languages: ["python"]
  brakeman:
    adapter_class: "scanner.adapters.brakeman.BrakemanAdapter"
    enabled: "auto"
    timeout: 120
    extra_args: []
    languages: ["ruby"]
  cargo_audit:
    adapter_class: "scanner.adapters.cargo_audit.CargoAuditAdapter"
    enabled: "auto"
    timeout: 60
    extra_args: []
    languages: ["rust"]
```

- **adapter_class** -- chemin complet vers la classe Python implementant l'adaptateur du scanner (voir Registre de plugins ci-dessous)
- **enabled** -- definir a `true` (toujours actif), `false` (toujours inactif) ou `"auto"` (active lorsque des fichiers correspondants sont detectes)
- **timeout** -- nombre maximum de secondes avant que l'outil soit arrete
- **extra_args** -- arguments CLI supplementaires passes a l'outil
- **languages** -- types de fichiers declenchant la detection automatique ; les scanners avec une liste vide (ex. : Gitleaks) s'executent sur tous les projets

## Registre de plugins

Le scanner utilise un registre de plugins base sur la configuration pour charger dynamiquement les adaptateurs de scanners depuis `config.yml`. Cette architecture permet d'ajouter de nouveaux scanners sans modifier le code de l'application.

### Comment les scanners sont enregistres

Chaque entree de scanner dans `config.yml` inclut un champ `adapter_class` qui specifie le chemin complet vers la classe Python implementant l'interface `ScannerAdapter`. Au demarrage, le `ScannerRegistry` lit toutes les entrees de la section `scanners` et importe dynamiquement chaque classe d'adaptateur.

Le champ `adapter_class` suit le format :

```
scanner.adapters.<module_name>.<ClassName>
```

Par exemple : `scanner.adapters.gosec.GosecAdapter`

### Detection automatique des langages

Les scanners avec un champ `languages` sont automatiquement actives lorsque le depot scanne contient des fichiers correspondants. L'orchestrateur detecte les extensions de fichiers dans le depot cible et active les scanners dont la liste `languages` chevauche les langages detectes. Les scanners avec une liste `languages` vide (comme Gitleaks) s'executent toujours quel que soit le type de projet.

### Ajouter un nouveau scanner

Pour ajouter un nouveau scanner a la plateforme :

1. **Creez une classe d'adaptateur** implementant l'interface `ScannerAdapter` :

```python
# src/scanner/adapters/my_scanner.py
from scanner.adapters.base import ScannerAdapter
from scanner.schemas.finding import FindingSchema

class MyScannerAdapter(ScannerAdapter):
    async def run(self, target_path: str, timeout: int, extra_args: list[str] | None = None) -> list[FindingSchema]:
        # Execute scanner binary and parse output
        ...
        return findings
```

2. **Ajoutez une entree dans `config.yml`** dans la section `scanners` :

```yaml
scanners:
  my_scanner:
    adapter_class: "scanner.adapters.my_scanner.MyScannerAdapter"
    enabled: "auto"
    timeout: 120
    extra_args: []
    languages: ["python"]
```

3. **Installez le binaire du scanner** dans le Dockerfile s'il s'agit d'un outil externe.

Aucune autre modification de code n'est requise. Le registre decouvre et charge automatiquement le nouvel adaptateur depuis la configuration.

### Liste des scanners enregistres

L'endpoint `/api/scanners` retourne tous les scanners enregistres avec leur configuration :

```bash
curl -H "Authorization: Bearer nvsec_your_token" http://localhost:8000/api/scanners
```

La reponse inclut le nom, le statut d'activation, les langages configures et la classe d'adaptateur de chaque scanner.

## Configuration de l'IA

```yaml
ai:
  max_cost_per_scan: 5.0
  model: "claude-sonnet-4-6"
  max_findings_per_batch: 50
  max_tokens_per_response: 4096
```

| Parametre | Description | Valeur par defaut |
|-----------|-------------|-------------------|
| `max_cost_per_scan` | Depense maximale en USD pour l'analyse IA par scan | `5.0` |
| `model` | Identifiant du modele Claude | `claude-sonnet-4-6` |
| `max_findings_per_batch` | Nombre maximum de resultats envoyes a Claude par requete | `50` |
| `max_tokens_per_response` | Nombre maximum de tokens de reponse de Claude | `4096` |

## Configuration de la quality gate

```yaml
gate:
  fail_on:
    - critical
    - high
  include_compound_risks: true
```

- **fail_on** -- liste des niveaux de severite qui font echouer la gate
- **include_compound_risks** -- lorsque `true`, les risques composes avec une severite correspondante font egalement echouer la gate

## Configuration des notifications

### Slack

```yaml
notifications:
  slack:
    enabled: false
```

Definissez l'URL du webhook au niveau superieur :

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
    smtp_password: ""  # Utilisez une variable d'environnement
    use_tls: true
```

Definissez l'hote SMTP au niveau superieur :

```yaml
email_smtp_host: "smtp.example.com"
```

Ou via la variable d'environnement : `SCANNER_EMAIL_SMTP_HOST`

Le mot de passe SMTP doit utiliser la variable d'environnement imbriquee : `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PASSWORD`

### URL du tableau de bord

```yaml
dashboard_url: ""  # ex. : http://scanner:8000/dashboard
```

Utilisee dans les messages de notification pour renvoyer vers les resultats du scan. Si vide, derivee automatiquement de l'hote et du port.

## Variables d'environnement

Tous les parametres peuvent etre surcharges avec le prefixe `SCANNER_` :

| Variable | Description | Valeur par defaut |
|----------|-------------|-------------------|
| `SCANNER_HOST` | Adresse d'ecoute | `0.0.0.0` |
| `SCANNER_PORT` | Port d'ecoute | `8000` |
| `SCANNER_DB_PATH` | Chemin du fichier de base de donnees SQLite | `/data/scanner.db` |
| `SCANNER_API_KEY` | Cle d'authentification API | `""` (vide) |
| `SCANNER_CLAUDE_API_KEY` | Cle API Anthropic pour l'analyse IA | `""` (vide) |
| `SCANNER_SLACK_WEBHOOK_URL` | URL du webhook Slack | `""` |
| `SCANNER_EMAIL_SMTP_HOST` | Nom d'hote du serveur SMTP | `""` |
| `SCANNER_LOG_LEVEL` | Niveau de log (debug/info/warning/error) | `info` |
| `SCANNER_SCAN_TIMEOUT` | Delai d'expiration global du scan en secondes | `600` |
| `SCANNER_CONFIG_PATH` | Chemin vers le fichier de configuration YAML | `config.yml` |

### Variables d'environnement imbriquees

Pour les sections de configuration imbriquees, utilisez des doubles underscores :

| Variable | Correspondance |
|----------|---------------|
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PASSWORD` | `notifications.email.smtp_password` |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_PORT` | `notifications.email.smtp_port` |
| `SCANNER_NOTIFICATIONS__EMAIL__SMTP_USER` | `notifications.email.smtp_user` |
| `SCANNER_NOTIFICATIONS__SLACK__ENABLED` | `notifications.slack.enabled` |

## Gestion des secrets

Ne stockez jamais les secrets dans `config.yml` ni ne les committez dans git.

```bash
# Definir les secrets via l'environnement :
export SCANNER_API_KEY="your-secure-key"
export SCANNER_CLAUDE_API_KEY="sk-ant-..."

# Ou dans docker-compose via le fichier .env :
echo "SCANNER_API_KEY=your-secure-key" >> .env
echo "SCANNER_CLAUDE_API_KEY=sk-ant-..." >> .env
```

## Gestion de la base de donnees

### Emplacement

- Docker : `/data/scanner.db` (volume persistant `scanner_data`)
- Local : configurable via `SCANNER_DB_PATH`

### Mode WAL

SQLite fonctionne en mode WAL (Write-Ahead Logging) pour des performances de lecture concurrent. Ce mode est defini automatiquement a chaque connexion via les ecouteurs d'evenements SQLAlchemy.

### Sauvegarde

```bash
# Le mode WAL permet une sauvegarde a chaud (pas besoin d'arreter le scanner)
docker cp naveksoft-security-scanner-1:/data/scanner.db ./backup/
```

## Reglage des seuils

### Quality Gate

Ajustez quelles severites font echouer la gate :

```yaml
gate:
  fail_on:
    - critical        # Bloquer uniquement sur critical (assoupli)
```

Ou incluez medium :

```yaml
gate:
  fail_on:
    - critical
    - high
    - medium           # Politique plus stricte
```

### Gestion des outils de scan

Desactivez les outils non pertinents pour votre base de code :

```yaml
scanners:
  cppcheck:
    enabled: false     # Pas de code C/C++
  checkov:
    enabled: false     # Pas de fichiers IaC
```

## Reglage des performances

### Delais d'expiration

- `scan_timeout` (global) : duree totale maximale du scan (defaut : 600s)
- `timeout` par scanner : temps d'execution maximal par outil (defaut : 120-180s)

Si les scans expirent, augmentez le delai d'expiration par outil pour le scanner lent plutot que le delai global.

### Taille des lots IA

Pour les grands scans avec de nombreux resultats, ajustez :

```yaml
ai:
  max_findings_per_batch: 25   # Lots plus petits pour des reponses plus rapides
  max_tokens_per_response: 8192  # Plus d'espace pour une analyse detaillee
```

### Surveillance

```bash
# Verification de sante
curl http://localhost:8000/api/health

# Statut du conteneur
docker compose ps

# Logs
docker compose logs scanner --tail 50
```

Docker Compose effectue des verifications de sante automatiques toutes les 30 secondes.

## Gestion des utilisateurs (RBAC)

Security AI Scanner utilise le controle d'acces base sur les roles (RBAC) pour gerer les permissions des utilisateurs. Trois roles sont disponibles :

### Roles

| Action | Admin | Viewer | Scanner |
|--------|-------|--------|---------|
| Declencher un scan | Oui | Non | Oui (API uniquement) |
| Voir les resultats | Oui | Oui | Oui (API uniquement) |
| Gerer les utilisateurs | Oui | Non | Non |
| Configurer les scanners | Oui | Non | Non |
| Gerer les profils | Oui | Non | Non |

- **Admin** -- acces complet a toutes les fonctionnalites, y compris la gestion des utilisateurs, la configuration des scanners et la gestion des profils
- **Viewer** -- acces en lecture seule aux resultats de scan et rapports via le tableau de bord
- **Scanner** -- role API uniquement pour declencher des scans et consulter les resultats programmatiquement

### Creation d'utilisateurs

Les utilisateurs peuvent etre crees de deux facons :

1. **Via le tableau de bord** -- accedez a `/dashboard/users` (admin uniquement) et remplissez le formulaire de creation
2. **Via les variables d'environnement** -- definissez `SCANNER_ADMIN_USER` et `SCANNER_ADMIN_PASSWORD` pour creer un compte admin au premier demarrage

Exigences de mot de passe : minimum 8 caracteres.

### Desactivation d'utilisateurs

Les admins peuvent desactiver des utilisateurs depuis le tableau de bord ou via l'API (`DELETE /api/users/{id}`). Les utilisateurs desactives ne peuvent plus se connecter ni utiliser de tokens API.

## Tokens API

Les tokens API fournissent un acces programmatique a l'API du scanner en utilisant l'authentification Bearer.

### Generation de tokens

Accedez a `/dashboard/tokens` pour gerer vos tokens. Cliquez sur "Creer un token" et fournissez un nom.

### Format du token

Tous les tokens utilisent le prefixe `nvsec_` :

```
nvsec_a1b2c3d4e5f6...
```

### Utilisation

Incluez le token dans le header `Authorization` :

```bash
curl -H "Authorization: Bearer nvsec_your_token_here" http://localhost:8000/api/scans
```

### Options d'expiration

Lors de la creation d'un token, selectionnez une periode d'expiration :

- 30 jours
- 90 jours
- 365 jours
- Jamais (sans expiration)

### Limites de tokens

Chaque utilisateur peut avoir jusqu'a 10 tokens actifs (limite souple).

### Revocation de tokens

Les tokens peuvent etre revoques depuis le tableau de bord (`/dashboard/tokens`) ou via l'API (`DELETE /api/tokens/{id}`).

## Interface de configuration des scanners

L'interface web de configuration des scanners permet aux admins de gerer les parametres des scanners, d'editer la configuration YAML brute et de gerer les profils de scan -- le tout depuis le tableau de bord.

### Acces a l'interface de configuration

Accedez a `/dashboard/scanners` (admin uniquement). La page comporte trois onglets :

### Onglet Scanners

Affiche tous les scanners enregistres sous forme de cartes avec :

- **Commutateur ON/AUTO/OFF** -- basculer entre les etats actif, automatique et inactif
- **Timeout** -- temps d'execution maximal en secondes (30-900)
- **Arguments supplementaires** -- flags CLI additionnels passes a l'outil

### Onglet Editeur YAML

Un editeur CodeMirror pour l'edition directe de `config.yml` avec coloration syntaxique YAML et validation complete avant sauvegarde.

### Onglet Profils

Gestion des profils de scan (voir section Profils de scan ci-dessous).

## Profils de scan

Les profils de scan sont des presets de scanners nommes, stockes dans `config.yml`. Chaque profil definit quels scanners executer et peut optionnellement surcharger les parametres par scanner.

### Vue d'ensemble

Un profil est une liste d'autorisation explicite -- seuls les scanners listes dans le profil s'executent lorsque ce profil est selectionne.

### Creation de profils

Accedez a `/dashboard/scanners` et selectionnez l'onglet Profils. Cliquez sur "Nouveau profil" et fournissez :

- **Nom** -- lettres, chiffres, tirets et underscores uniquement (ex. : `quick_scan`, `full-audit`)
- **Description** -- description optionnelle
- **Scanners** -- selectionnez les scanners a inclure avec des surcharges de timeout optionnelles

### Exemple de profils dans config.yml

```yaml
profiles:
  quick_scan:
    description: "Fast scan with essential tools only"
    scanners:
      semgrep: {}
      gitleaks: {}
  full_audit:
    description: "Comprehensive scan with all available tools"
    scanners:
      semgrep: {}
      gitleaks: {}
      trivy: {}
      checkov: {}
      cppcheck: {}
      bandit: {}
      gosec: {}
      brakeman: {}
      cargo_audit: {}
      psalm: {}
      enlightn: {}
      php_security_checker: {}
  dast_only:
    description: "DAST scan using Nuclei only"
    scanners:
      nuclei:
        timeout: 300
```

### Edition et suppression de profils

Depuis l'onglet Profils, cliquez sur une carte de profil pour deplier le formulaire d'edition. Modifiez les parametres et cliquez sur Enregistrer, ou cliquez sur Supprimer.

### Limites

- Maximum 10 profils (limite souple)
- Les noms de profils ne doivent contenir que des lettres, chiffres, tirets et underscores
- Les mots reserves YAML (`true`, `false`, `null`, `yes`, `no`, `on`, `off`) ne peuvent pas etre utilises comme noms de profils

## Scan DAST

Le test dynamique de securite des applications (DAST) analyse les applications web en cours d'execution en envoyant des requetes HTTP et en analysant les reponses.

### Vue d'ensemble

Le scan DAST est propulse par Nuclei, un scanner de vulnerabilites rapide et configurable. Contrairement aux outils SAST qui analysent le code source, le DAST teste l'application en boite noire.

### Configuration de Nuclei

Assurez-vous que le scanner Nuclei est active dans `config.yml` :

```yaml
scanners:
  nuclei:
    adapter_class: "scanner.adapters.nuclei.NucleiAdapter"
    enabled: true
    timeout: 300
    extra_args: []
    languages: []
```

### Declenchement d'un scan DAST

Les scans DAST necessitent le parametre `target_url` au lieu de `path` ou `repo_url` :

**Via l'API :**

```bash
curl -X POST http://localhost:8000/api/scans \
  -H "Authorization: Bearer nvsec_your_token" \
  -H "Content-Type: application/json" \
  -d '{"target_url": "https://example.com"}'
```

**Via le tableau de bord :** Entrez l'URL cible dans le champ URL du formulaire de lancement de scan.

### DAST vs SAST

Le parametre `target_url` est exclusif avec `path` et `repo_url`. Vous ne pouvez pas combiner des cibles DAST et SAST dans une seule requete.

### Resultats DAST

Les resultats DAST apparaissent dans les rapports aux cotes des resultats SAST. Chaque resultat DAST inclut le niveau de severite, l'identifiant du modele Nuclei et l'URL cible ou la vulnerabilite a ete trouvee.
