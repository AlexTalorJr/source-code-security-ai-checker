# Reference API

## URL de base

```
http://localhost:8000
```

## Authentification

Tous les endpoints API sauf `/api/health` necessitent un token Bearer dans le header Authorization. Generez des tokens depuis le tableau de bord (`/dashboard/tokens`) ou via l'API de gestion des tokens.

```bash
curl -H "Authorization: Bearer nvsec_your_token_here" http://localhost:8000/api/scans
```

Les requetes sans token valide recoivent une reponse `401 Unauthorized`.

## Endpoints

### GET /api/health

Endpoint de verification de sante. Aucune authentification requise.

**Reponse 200 :**

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime_seconds": 3600.5,
  "database": "ok"
}
```

| Champ | Type | Description |
|-------|------|-------------|
| `status` | string | `"healthy"` ou `"degraded"` |
| `version` | string | Version du scanner depuis pyproject.toml |
| `uptime_seconds` | float | Secondes depuis le demarrage de l'application |
| `database` | string | `"ok"` ou `"error"` |

---

### POST /api/scans

Declencher un nouveau scan de securite. Le scan est mis en file d'attente et s'execute de maniere asynchrone.

**Corps de la requete :**

```json
{
  "path": "/path/to/local/code",
  "repo_url": "https://github.com/org/repo.git",
  "branch": "main",
  "target_url": "https://example.com",
  "profile": "quick_scan"
}
```

| Champ | Type | Requis | Description |
|-------|------|--------|-------------|
| `path` | string | Non | Chemin local a scanner |
| `repo_url` | string | Non | URL du depot Git a cloner et scanner |
| `branch` | string | Non | Branche a extraire (defaut : branche par defaut du depot) |
| `target_url` | string | Non | URL pour le scan DAST (exclusif avec `path`/`repo_url`) |
| `profile` | string | Non | Nom du profil de scan a utiliser |
| `skip_ai` | boolean | Non | Ignorer l'analyse IA (defaut : false) |

Fournissez `path`, `repo_url` ou `target_url`. Le champ `target_url` declenche un scan DAST et ne peut pas etre combine avec `path` ou `repo_url`.

**Reponse 202 :**

```json
{
  "id": 1,
  "status": "queued"
}
```

**Codes de statut :** `202` Cree, `400` Profil invalide, `401` Non autorise, `422` Erreur de validation

**Exemples :**

```bash
# Scan SAST
curl -X POST http://localhost:8000/api/scans \
  -H "Authorization: Bearer nvsec_your_token" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/org/repo.git", "branch": "main"}'

# Scan SAST avec profil
curl -X POST http://localhost:8000/api/scans \
  -H "Authorization: Bearer nvsec_your_token" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/org/repo.git", "profile": "quick_scan"}'

# Scan DAST
curl -X POST http://localhost:8000/api/scans \
  -H "Authorization: Bearer nvsec_your_token" \
  -H "Content-Type: application/json" \
  -d '{"target_url": "https://example.com"}'
```

---

### GET /api/scans

Lister les scans avec pagination, ordonnes par date de creation (le plus recent en premier).

**Reponse 200 :**

```json
{
  "items": [
    {
      "id": 1,
      "status": "completed",
      "repo_url": "https://github.com/org/repo.git",
      "branch": "main",
      "target_url": null,
      "profile_name": "quick_scan",
      "started_at": "2026-03-20T10:00:00Z",
      "completed_at": "2026-03-20T10:05:00Z",
      "total_findings": 15,
      "gate_passed": true
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "pages": 1
}
```

---

### GET /api/scans/{id}

Obtenir les informations detaillees d'un scan.

**Codes de statut :** `200` OK, `401` Non autorise, `404` Scan introuvable

---

### GET /api/scans/{scan_id}/findings

Resultats pagines pour un scan specifique.

---

### POST /api/scans/{scan_id}/findings/{finding_id}/suppress

Supprimer un resultat (marquer comme faux positif).

**Corps de la requete :**

```json
{
  "reason": "False positive: test fixture data"
}
```

---

### DELETE /api/scans/{scan_id}/findings/{finding_id}/suppress

Annuler la suppression d'un resultat.

---

### GET /api/scanners

Liste de tous les scanners enregistres avec leur configuration. Authentification requise.

---

### GET /api/trends

Tendances des resultats dans le temps pour les graphiques.

---

## Endpoints de configuration

### GET /api/config

Configuration complete du scanner en JSON. Admin uniquement.

```bash
curl -H "Authorization: Bearer nvsec_your_token" http://localhost:8000/api/config
```

---

### GET /api/config/yaml

Contenu brut de `config.yml` en texte. Admin uniquement.

---

### PATCH /api/config/scanners/{scanner_name}

Mise a jour des parametres d'un scanner individuel. Admin uniquement.

**Corps de la requete :**

```json
{
  "enabled": true,
  "timeout": 300,
  "extra_args": ["--exclude", ".venv"]
}
```

| Champ | Type | Description |
|-------|------|-------------|
| `enabled` | bool/string | `true`, `false` ou `"auto"` |
| `timeout` | integer | 30-900 secondes |
| `extra_args` | string[] | Arguments CLI supplementaires |

---

### PUT /api/config/yaml

Remplacer `config.yml` par un nouveau contenu YAML. Admin uniquement. Le YAML est valide avant l'ecriture.

---

## Endpoints de gestion des profils

### GET /api/config/profiles

Liste de tous les profils de scan. Admin uniquement.

**Reponse 200 :**

```json
{
  "profiles": {
    "quick_scan": {
      "description": "Fast scan with essential tools only",
      "scanners": {
        "semgrep": {},
        "gitleaks": {}
      }
    }
  }
}
```

---

### POST /api/config/profiles

Creer un nouveau profil de scan. Admin uniquement.

**Corps de la requete :**

```json
{
  "name": "quick_scan",
  "description": "Fast scan with essential tools only",
  "scanners": {
    "semgrep": {},
    "gitleaks": {}
  }
}
```

**Codes de statut :** `201` Cree, `400` Limite atteinte, `409` Profil existant, `422` Erreur de validation

---

### GET /api/config/profiles/{name}

Obtenir un profil par nom. Admin uniquement.

---

### PUT /api/config/profiles/{name}

Mettre a jour un profil existant. Admin uniquement.

---

### DELETE /api/config/profiles/{name}

Supprimer un profil de scan. Admin uniquement.

---

## Endpoints de gestion des utilisateurs

### GET /api/users

Liste de tous les utilisateurs. Admin uniquement.

### POST /api/users

Creer un nouvel utilisateur. Admin uniquement.

```json
{
  "username": "newuser",
  "password": "securepassword",
  "role": "viewer"
}
```

### GET /api/users/{id}

Obtenir un utilisateur. Admin uniquement.

### PUT /api/users/{id}

Mettre a jour un utilisateur. Admin uniquement.

### DELETE /api/users/{id}

Desactiver un utilisateur. Admin uniquement.

---

## Endpoints de gestion des tokens

### GET /api/tokens

Liste de vos tokens API.

### POST /api/tokens

Creer un nouveau token API.

```json
{
  "name": "CI Pipeline",
  "expires_days": 90
}
```

### DELETE /api/tokens/{id}

Revoquer un token API.

---

## Tableau de bord

Un tableau de bord web est disponible a l'adresse `/dashboard` :

| Route | Description |
|-------|-------------|
| `GET /dashboard/login` | Page de connexion |
| `POST /dashboard/login` | Authentification par nom d'utilisateur et mot de passe |
| `GET /dashboard/` | Vue d'ensemble de l'historique des scans |
| `GET /dashboard/scans/{id}` | Detail d'un scan avec resultats |
| `GET /dashboard/trends` | Graphiques de tendances |
| `GET /dashboard/users` | Gestion des utilisateurs (admin uniquement) |
| `GET /dashboard/tokens` | Gestion des tokens |
| `GET /dashboard/scanners` | Configuration des scanners (admin uniquement) |

Le tableau de bord utilise des cookies de session pour l'authentification (expiration de 7 jours).

## Reponses d'erreur

Toutes les reponses d'erreur suivent un format standard :

```json
{
  "detail": "Description of the error"
}
```

**Codes de statut courants :**

| Code | Signification |
|------|---------------|
| `401` | Token Bearer manquant ou invalide |
| `403` | Permissions insuffisantes (verification de role echouee) |
| `404` | Ressource introuvable (ID de scan, ID de resultat, nom de profil) |
| `422` | Erreur de validation (corps de requete invalide) |

## Documentation OpenAPI

FastAPI genere automatiquement une documentation API interactive :

- **Swagger UI :** http://localhost:8000/docs
- **ReDoc :** http://localhost:8000/redoc
- **OpenAPI JSON :** http://localhost:8000/openapi.json
