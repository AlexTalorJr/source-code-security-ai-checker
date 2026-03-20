# Référence API

## URL de base

```
http://localhost:8000
```

## Authentification

Tous les endpoints API sauf `/api/health` requièrent une clé API passée dans le header `X-API-Key`. La clé est définie via la variable d'environnement `SCANNER_API_KEY` et validée en utilisant une comparaison protégée contre les attaques temporelles (`secrets.compare_digest`).

```bash
curl -H "X-API-Key: your-key" http://localhost:8000/api/scans
```

Les requêtes sans clé valide reçoivent une réponse `401 Unauthorized`.

## Endpoints

### GET /api/health

Endpoint de vérification de santé. Aucune authentification requise.

**Réponse 200 :**

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
| `uptime_seconds` | float | Secondes depuis le démarrage de l'application |
| `database` | string | `"ok"` ou `"error"` |

**Exemple :**

```bash
curl http://localhost:8000/api/health
```

---

### POST /api/scans

Déclencher un nouveau scan de sécurité. Le scan est mis en file d'attente et s'exécute de manière asynchrone en arrière-plan.

**Corps de la requête :**

```json
{
  "path": "/path/to/local/code",
  "repo_url": "https://github.com/org/repo.git",
  "branch": "main"
}
```

| Champ | Type | Requis | Description |
|-------|------|--------|-------------|
| `path` | string | Non | Chemin du système de fichiers local à scanner |
| `repo_url` | string | Non | URL du dépôt Git à cloner et scanner |
| `branch` | string | Non | Branche à extraire (défaut : branche par défaut du dépôt) |

Fournissez soit `path` soit `repo_url`. Si `repo_url` est fourni, le scanner clone le dépôt avant de le scanner.

**Réponse 202 :**

```json
{
  "id": 1,
  "status": "queued"
}
```

**Codes de statut :** `202` Créé, `401` Non autorisé, `422` Erreur de validation

**Exemple :**

```bash
curl -X POST http://localhost:8000/api/scans \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/org/repo.git", "branch": "main"}'
```

---

### GET /api/scans

Lister tous les scans, ordonnés par date de création (le plus récent en premier).

**Réponse 200 :**

```json
[
  {
    "id": 1,
    "repo_url": "https://github.com/org/repo.git",
    "branch": "main",
    "status": "completed",
    "started_at": "2026-03-20T10:00:00Z",
    "completed_at": "2026-03-20T10:05:00Z",
    "gate_passed": true
  }
]
```

**Exemple :**

```bash
curl -H "X-API-Key: your-key" http://localhost:8000/api/scans
```

---

### GET /api/scans/{id}

Obtenir les résultats détaillés d'un scan, y compris les résultats.

**Paramètres de chemin :**

| Paramètre | Type | Description |
|-----------|------|-------------|
| `id` | integer | ID du scan |

**Réponse 200 :**

```json
{
  "id": 1,
  "repo_url": "https://github.com/org/repo.git",
  "branch": "main",
  "status": "completed",
  "started_at": "2026-03-20T10:00:00Z",
  "completed_at": "2026-03-20T10:05:00Z",
  "gate_passed": true,
  "findings": [
    {
      "id": 1,
      "tool": "semgrep",
      "rule_id": "python.lang.security.audit.exec-detected",
      "severity": "high",
      "file_path": "src/app.py",
      "line": 42,
      "message": "Use of exec() detected",
      "fingerprint": "abc123..."
    }
  ]
}
```

**Codes de statut :** `200` OK, `401` Non autorisé, `404` Scan introuvable

**Exemple :**

```bash
curl -H "X-API-Key: your-key" http://localhost:8000/api/scans/1
```

---

### POST /api/scans/{scan_id}/findings/{finding_id}/suppress

Supprimer un résultat (marquer comme faux positif).

**Paramètres de chemin :**

| Paramètre | Type | Description |
|-----------|------|-------------|
| `scan_id` | integer | ID du scan |
| `finding_id` | integer | ID du résultat |

**Corps de la requête :**

```json
{
  "reason": "False positive: test fixture data"
}
```

**Réponse 200 :**

```json
{
  "status": "suppressed",
  "finding_id": 1,
  "reason": "False positive: test fixture data"
}
```

**Exemple :**

```bash
curl -X POST http://localhost:8000/api/scans/1/findings/5/suppress \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"reason": "False positive: test fixture"}'
```

---

### DELETE /api/scans/{scan_id}/findings/{finding_id}/suppress

Annuler la suppression d'un résultat.

**Paramètres de chemin :**

| Paramètre | Type | Description |
|-----------|------|-------------|
| `scan_id` | integer | ID du scan |
| `finding_id` | integer | ID du résultat |

**Réponse 200 :**

```json
{
  "status": "unsuppressed",
  "finding_id": 1
}
```

**Exemple :**

```bash
curl -X DELETE http://localhost:8000/api/scans/1/findings/5/suppress \
  -H "X-API-Key: your-key"
```

---

### GET /api/trends

Obtenir les tendances des résultats dans le temps pour les graphiques de tendances.

**Réponse 200 :**

```json
{
  "scans": [
    {
      "id": 1,
      "completed_at": "2026-03-20T10:05:00Z",
      "total_findings": 15,
      "critical": 1,
      "high": 3,
      "medium": 7,
      "low": 4
    }
  ]
}
```

**Exemple :**

```bash
curl -H "X-API-Key: your-key" http://localhost:8000/api/trends
```

## Tableau de bord

Un tableau de bord web est disponible à l'adresse `/dashboard`, fournissant une interface graphique pour le scanner :

| Route | Description |
|-------|-------------|
| `GET /dashboard/login` | Page de connexion |
| `POST /dashboard/login` | Authentification avec la clé API |
| `GET /dashboard/` | Vue d'ensemble de l'historique des scans |
| `GET /dashboard/scans/{id}` | Détail d'un scan avec résultats |
| `GET /dashboard/trends` | Graphiques de tendances dans le temps |

Le tableau de bord utilise la même clé API pour l'authentification, stockée dans un cookie de session après la connexion. La suppression et l'annulation de suppression des résultats sont disponibles directement depuis la page de détail du scan.

## Réponses d'erreur

Toutes les réponses d'erreur suivent un format standard :

```json
{
  "detail": "Description of the error"
}
```

**Codes de statut courants :**

| Code | Signification |
|------|---------------|
| `401` | Clé API manquante ou invalide |
| `404` | Ressource introuvable (ID de scan, ID de résultat) |
| `422` | Erreur de validation (corps de requête invalide) |

## Documentation OpenAPI

FastAPI génère automatiquement une documentation API interactive :

- **Swagger UI :** http://localhost:8000/docs
- **ReDoc :** http://localhost:8000/redoc
- **OpenAPI JSON :** http://localhost:8000/openapi.json
