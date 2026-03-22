# Guide utilisateur

## Qu'est-ce que Security AI Scanner ?

Un outil d'analyse de securite qui analyse le code source a la recherche de vulnerabilites en utilisant douze outils de scan de securite paralleles, enrichit les resultats par une analyse IA via Claude, et produit des rapports exploitables avec des suggestions de correction. Les scanners sont actives automatiquement en fonction des langages detectes dans le projet.

## Scanners pris en charge

### Semgrep (SAST multi-langages)

**Language:** Python, PHP, JavaScript, TypeScript, Go, Java, Kotlin, Ruby, C#, Rust
**Type:** SAST
**Ce qu'il detecte:** Failles d'injection, problemes d'authentification, patterns non securises et vulnerabilites specifiques aux langages via la correspondance de patterns semantiques.
**Exemple de resultat:**
> `python.lang.security.audit.exec-detected`: Use of exec() detected at `app.py:42`

**Active:** Automatiquement lorsque des fichiers Python, PHP, JS/TS, Go, Java, Kotlin, Ruby, C# ou Rust sont detectes

### cppcheck (C/C++)

**Language:** C/C++
**Type:** SAST
**Ce qu'il detecte:** Problemes de securite memoire, depassements de tampon, dereferences de pointeurs nuls, comportement indefini et fuites de ressources.
**Exemple de resultat:**
> `arrayIndexOutOfBounds`: Array index out of bounds at `buffer.cpp:15`

**Active:** Automatiquement lorsque des fichiers C/C++ sont detectes

### Gitleaks (secrets)

**Language:** Tous les langages
**Type:** Detection de secrets
**Ce qu'il detecte:** Secrets codes en dur, cles API, tokens, mots de passe et identifiants dans le code source et l'historique git.
**Exemple de resultat:**
> `generic-api-key`: Generic API Key detected at `config.py:8`

**Active:** Toujours active pour tous les projets

### Trivy (infrastructure)

**Language:** Docker, Terraform, YAML/Kubernetes
**Type:** SCA / Infrastructure
**Ce qu'il detecte:** CVE dans les images de conteneurs, mauvaises configurations IaC et problemes de securite Kubernetes.
**Exemple de resultat:**
> `CVE-2023-44487`: HTTP/2 rapid reset attack in `Dockerfile:1`

**Active:** Automatiquement lorsque des Dockerfiles, Terraform ou Kubernetes YAML sont detectes

### Checkov (infrastructure)

**Language:** Docker, Terraform, YAML, CI configs
**Type:** Infrastructure
**Ce qu'il detecte:** Bonnes pratiques de securite Infrastructure-as-code, mauvaises configurations cloud et securite des pipelines CI.
**Exemple de resultat:**
> `CKV_DOCKER_2`: Ensure that HEALTHCHECK instructions have been added to container images at `Dockerfile:1`

**Active:** Automatiquement lorsque des fichiers Docker, Terraform, YAML ou CI sont detectes

### Psalm (PHP)

**Language:** PHP
**Type:** SAST (analyse de contamination)
**Ce qu'il detecte:** Injection SQL, XSS et autres vulnerabilites liees a la contamination via le suivi du flux de donnees dans le code PHP.
**Exemple de resultat:**
> `TaintedSql`: Detected tainted SQL in `UserController.php:34`

**Active:** Automatiquement lorsque des fichiers PHP sont detectes

### Enlightn (Laravel)

**Language:** Laravel (PHP)
**Type:** SAST
**Ce qu'il detecte:** Vulnerabilites CSRF, mass assignment, mode debug expose, fichiers .env exposes et plus de 120 verifications de securite specifiques a Laravel.
**Exemple de resultat:**
> `MassAssignmentAnalyzer`: Potential mass assignment vulnerability in `User.php:12`

**Active:** Automatiquement lorsqu'un projet Laravel est detecte

### PHP Security Checker (PHP SCA)

**Language:** PHP (Composer)
**Type:** SCA
**Ce qu'il detecte:** CVE connues dans les dependances Composer en consultant la base de donnees de conseils de securite SensioLabs.
**Exemple de resultat:**
> `CVE-2023-46734`: Twig code injection via sandbox bypass in `composer.lock`

**Active:** Automatiquement lorsque des fichiers PHP Composer sont detectes

### gosec (Go SAST)

**Language:** Go
**Type:** SAST
**Ce qu'il detecte:** Identifiants codes en dur, injection SQL, cryptographie non securisee, permissions de fichiers non securisees et problemes de securite specifiques a Go.
**Exemple de resultat:**
> `G101`: Potential hardcoded credentials at `config.go:22`

**Active:** Automatiquement lorsque des fichiers Go sont detectes

### Bandit (Python SAST)

**Language:** Python
**Type:** SAST
**Ce qu'il detecte:** Mots de passe codes en dur, injection SQL, utilisation d'eval, cryptographie faible et patterns de securite specifiques a Python.
**Exemple de resultat:**
> `B105`: Possible hardcoded password at `settings.py:15`

**Active:** Automatiquement lorsque des fichiers Python sont detectes

### Brakeman (Ruby/Rails SAST)

**Language:** Ruby / Rails
**Type:** SAST
**Ce qu'il detecte:** Injection SQL, XSS, mass assignment, injection de commandes et vulnerabilites specifiques a Rails.
**Exemple de resultat:**
> `SQL Injection`: Possible SQL injection near line 15 in `app/models/user.rb`

**Active:** Automatiquement lorsque des fichiers Ruby sont detectes

### cargo-audit (Rust SCA)

**Language:** Rust
**Type:** SCA
**Ce qu'il detecte:** Dependances vulnerables connues via la base de donnees RustSec en auditant les fichiers Cargo.lock.
**Exemple de resultat:**
> `RUSTSEC-2019-0009`: Heap overflow in smallvec in `Cargo.lock`

**Active:** Automatiquement lorsque des fichiers Rust sont detectes

## Lancer un scan

### Via l'API

```bash
curl -X POST http://localhost:8000/api/scans \
  -H "X-API-Key: $SCANNER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/your-org/repo.git", "branch": "main"}'
```

L'API renvoie immediatement un ID de scan (202 Accepted). Le scan s'execute de maniere asynchrone dans la file d'attente en arriere-plan.

### Via CLI

```bash
scanner scan --repo-url https://github.com/your-org/repo.git --branch main
```

La CLI execute le scan directement et affiche les resultats sur stdout. Utilisez `--format html` ou `--format pdf` pour generer des fichiers de rapport.

### Via le tableau de bord

Accedez a `http://localhost:8000/dashboard`, renseignez l'URL du depot et la branche, puis soumettez. Le tableau de bord affiche la progression et les resultats du scan en ligne.

## Comprendre les niveaux de severite

| Niveau | Signification | Action |
|--------|---------------|--------|
| **CRITICAL** | Risque d'exploitation immediate (ex. : injection SQL, RCE) | Corriger immediatement ; bloque le deploiement |
| **HIGH** | Vulnerabilite grave (ex. : contournement d'auth, secrets codes en dur) | Corriger avant la mise en production |
| **MEDIUM** | Risque modere (ex. : cryptographie faible, headers manquants) | Corriger dans le sprint actuel |
| **LOW** | Probleme mineur (ex. : messages d'erreur verbeux) | Corriger des que possible |
| **INFO** | Resultat informatif (ex. : utilisation d'API deprecie) | A examiner, aucune action requise |

## Rapports

### Rapports HTML

Les rapports HTML interactifs incluent :

- **Section resume** -- total des resultats, repartition par severite, resultat de la quality gate
- **Tableau de resultats filtrable** -- filtrage par severite, outil, chemin de fichier
- **Contexte de code** -- extraits de code source avec les lignes vulnerables surlignees
- **Suggestions de correction IA** -- code de correction genere par Claude avec explications
- **Risques composes** -- resultats de correlation inter-outils identifies par l'IA
- **Graphiques** -- diagramme circulaire de distribution des severites et graphique en barres des resultats par outil

Accedez aux rapports HTML via `GET /api/scans/{id}/report/html` ou depuis le tableau de bord.

### Rapports PDF

Les rapports PDF fournissent un document formel adapte a la revue par la direction :

- **Resume executif** -- metadonnees du scan, comptages de severite, resultat de la gate
- **Graphiques** -- graphiques PNG integres (distribution des severites, repartition par outil)
- **Resultats detailles** -- groupes par severite avec extraits de code
- **Section risques composes** -- vulnerabilites inter-composants identifiees par l'IA

Accedez aux rapports PDF via `GET /api/scans/{id}/report/pdf`.

## Quality Gate

La quality gate evalue les resultats du scan par rapport aux seuils de severite configures. Par defaut, tout resultat CRITICAL ou HIGH entraine l'echec de la gate.

- **pass** -- aucun resultat au niveau ou au-dessus du seuil de severite configure
- **fail** -- un ou plusieurs resultats au niveau ou au-dessus du seuil, ou des risques composes avec une severite Critical/High lorsque `include_compound_risks` est active

Les resultats de la quality gate sont disponibles via `GET /api/scans/{id}/gate` et affiches dans les rapports et le tableau de bord.

## Analyse IA

Chaque lot de resultats est envoye a Claude pour une analyse contextuelle :

- **Revue contextuelle** -- comprehension de ce que fait le code et si le resultat est un vrai positif
- **Suggestions de correction** -- modifications de code concretes pour remedier a la vulnerabilite
- **Risques composes** -- identification des chaines d'attaque couvrant plusieurs resultats (ex. : contournement d'auth + IDOR = prise de controle de compte)

Le cout de l'analyse IA par scan est suivi et limite par `ai.max_cost_per_scan` dans la configuration.

## Comparaison delta

Lorsqu'un depot a deja ete scanne, le scanner calcule automatiquement un delta :

- **Nouveaux resultats** -- vulnerabilites absentes du scan precedent
- **Resultats corriges** -- vulnerabilites du scan precedent qui ne sont plus presentes
- **Resultats persistants** -- vulnerabilites presentes dans les deux scans

Le delta est calcule en comparant les empreintes entre le scan actuel et le scan precedent le plus recent du meme depot et de la meme branche. Le premier scan ne retourne pas de delta (pas de base de reference precedente).

## Gestion des faux positifs

### Via le tableau de bord

Depuis la vue des resultats, cliquez sur le bouton de suppression pour n'importe quel resultat. Indiquez une raison pour la suppression.

### Via l'API

```bash
curl -X POST http://localhost:8000/api/suppressions \
  -H "X-API-Key: $SCANNER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"fingerprint": "<finding-fingerprint>", "reason": "False positive: test fixture"}'
```

Les resultats supprimes sont exclus de l'evaluation de la quality gate et signales dans les rapports.
