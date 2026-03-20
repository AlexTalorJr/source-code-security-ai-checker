# Guide utilisateur

## Qu'est-ce que Security AI Scanner ?

Un outil d'analyse de sécurité qui analyse le code source à la recherche de vulnérabilités en utilisant cinq outils d'analyse statique parallèles, enrichit les résultats par une analyse IA via Claude, et produit des rapports exploitables avec des suggestions de correction.

## Lancer un scan

### Via l'API

```bash
curl -X POST http://localhost:8000/api/scans \
  -H "X-API-Key: $SCANNER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/your-org/repo.git", "branch": "main"}'
```

L'API renvoie immédiatement un ID de scan (202 Accepted). Le scan s'exécute de manière asynchrone dans la file d'attente en arrière-plan.

### Via CLI

```bash
scanner scan --repo-url https://github.com/your-org/repo.git --branch main
```

La CLI exécute le scan directement et affiche les résultats sur stdout. Utilisez `--format html` ou `--format pdf` pour générer des fichiers de rapport.

### Via le tableau de bord

Accédez à `http://localhost:8000/dashboard`, renseignez l'URL du dépôt et la branche, puis soumettez. Le tableau de bord affiche la progression et les résultats du scan en ligne.

## Comprendre les niveaux de sévérité

| Niveau | Signification | Action |
|--------|---------------|--------|
| **CRITICAL** | Risque d'exploitation immédiate (ex. : injection SQL, RCE) | Corriger immédiatement ; bloque le déploiement |
| **HIGH** | Vulnérabilité grave (ex. : contournement d'auth, secrets codés en dur) | Corriger avant la mise en production |
| **MEDIUM** | Risque modéré (ex. : cryptographie faible, headers manquants) | Corriger dans le sprint actuel |
| **LOW** | Problème mineur (ex. : messages d'erreur verbeux) | Corriger dès que possible |
| **INFO** | Résultat informatif (ex. : utilisation d'API dépréciée) | À examiner, aucune action requise |

## Rapports

### Rapports HTML

Les rapports HTML interactifs incluent :

- **Section résumé** -- total des résultats, répartition par sévérité, résultat de la quality gate
- **Tableau de résultats filtrable** -- filtrage par sévérité, outil, chemin de fichier
- **Contexte de code** -- extraits de code source avec les lignes vulnérables surlignées
- **Suggestions de correction IA** -- code de correction généré par Claude avec explications
- **Risques composés** -- résultats de corrélation inter-outils identifiés par l'IA
- **Graphiques** -- diagramme circulaire de distribution des sévérités et graphique en barres des résultats par outil

Accédez aux rapports HTML via `GET /api/scans/{id}/report/html` ou depuis le tableau de bord.

### Rapports PDF

Les rapports PDF fournissent un document formel adapté à la revue par la direction :

- **Résumé exécutif** -- métadonnées du scan, comptages de sévérité, résultat de la gate
- **Graphiques** -- graphiques PNG intégrés (distribution des sévérités, répartition par outil)
- **Résultats détaillés** -- groupés par sévérité avec extraits de code
- **Section risques composés** -- vulnérabilités inter-composants identifiées par l'IA

Accédez aux rapports PDF via `GET /api/scans/{id}/report/pdf`.

## Quality Gate

La quality gate évalue les résultats du scan par rapport aux seuils de sévérité configurés. Par défaut, tout résultat CRITICAL ou HIGH entraîne l'échec de la gate.

- **pass** -- aucun résultat au niveau ou au-dessus du seuil de sévérité configuré
- **fail** -- un ou plusieurs résultats au niveau ou au-dessus du seuil, ou des risques composés avec une sévérité Critical/High lorsque `include_compound_risks` est activé

Les résultats de la quality gate sont disponibles via `GET /api/scans/{id}/gate` et affichés dans les rapports et le tableau de bord.

## Analyse IA

Chaque lot de résultats est envoyé à Claude pour une analyse contextuelle :

- **Revue contextuelle** -- compréhension de ce que fait le code et si le résultat est un vrai positif
- **Suggestions de correction** -- modifications de code concrètes pour remédier à la vulnérabilité
- **Risques composés** -- identification des chaînes d'attaque couvrant plusieurs résultats (ex. : contournement d'auth + IDOR = prise de contrôle de compte)

Le coût de l'analyse IA par scan est suivi et limité par `ai.max_cost_per_scan` dans la configuration.

## Comparaison delta

Lorsqu'un dépôt a déjà été scanné, le scanner calcule automatiquement un delta :

- **Nouveaux résultats** -- vulnérabilités absentes du scan précédent
- **Résultats corrigés** -- vulnérabilités du scan précédent qui ne sont plus présentes
- **Résultats persistants** -- vulnérabilités présentes dans les deux scans

Le delta est calculé en comparant les empreintes entre le scan actuel et le scan précédent le plus récent du même dépôt et de la même branche. Le premier scan ne retourne pas de delta (pas de base de référence précédente).

## Gestion des faux positifs

### Via le tableau de bord

Depuis la vue des résultats, cliquez sur le bouton de suppression pour n'importe quel résultat. Indiquez une raison pour la suppression.

### Via l'API

```bash
curl -X POST http://localhost:8000/api/suppressions \
  -H "X-API-Key: $SCANNER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"fingerprint": "<finding-fingerprint>", "reason": "False positive: test fixture"}'
```

Les résultats supprimés sont exclus de l'évaluation de la quality gate et signalés dans les rapports.
