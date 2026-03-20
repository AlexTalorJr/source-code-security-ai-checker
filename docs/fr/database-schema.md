# Schéma de base de données

## Vue d'ensemble

Base de données SQLite en mode WAL (Write-Ahead Logging) pour un accès en lecture concurrent. Gérée par SQLAlchemy 2.0 async ORM avec les migrations Alembic.

## Diagramme ER

```mermaid
erDiagram
    scans ||--o{ findings : "has many"
    scans ||--o{ compound_risks : "has many"
    compound_risks ||--o{ compound_risk_findings : "linked via"

    scans {
        int id PK "autoincrement"
        varchar target_path "nullable -- local path"
        varchar repo_url "nullable -- git URL"
        varchar branch "nullable"
        varchar commit_hash "nullable, 40 chars"
        varchar status "pending/running/completed/failed"
        datetime started_at "nullable"
        datetime completed_at "nullable"
        float duration_seconds "nullable"
        int total_findings "default 0"
        int critical_count "default 0"
        int high_count "default 0"
        int medium_count "default 0"
        int low_count "default 0"
        int info_count "default 0"
        int gate_passed "0=fail, 1=pass, NULL=not evaluated"
        varchar scanner_version "nullable"
        text tool_versions "nullable, JSON"
        text error_message "nullable"
        float ai_cost_usd "nullable"
        datetime created_at "auto"
    }

    findings {
        int id PK "autoincrement"
        int scan_id FK "references scans.id, indexed"
        varchar fingerprint "SHA-256 hex, 64 chars, indexed"
        varchar tool "semgrep/gitleaks/trivy/cppcheck/checkov"
        varchar rule_id "tool-specific rule identifier"
        varchar file_path "path in scanned repo"
        int line_start "nullable"
        int line_end "nullable"
        text snippet "nullable -- code fragment"
        int severity "1=INFO, 2=LOW, 3=MEDIUM, 4=HIGH, 5=CRITICAL"
        varchar title "short description"
        text description "nullable -- detailed explanation"
        text recommendation "nullable -- fix suggestion"
        text ai_analysis "nullable -- Claude AI analysis"
        text ai_fix_suggestion "nullable -- AI fix code"
        int false_positive "0=no, 1=yes"
        datetime created_at "auto"
    }

    compound_risks {
        int id PK "autoincrement"
        int scan_id FK "references scans.id, indexed"
        varchar title "short description"
        text description "detailed explanation"
        int severity "1=INFO to 5=CRITICAL"
        varchar risk_category "nullable -- e.g. auth_bypass, data_leak"
        text recommendation "nullable"
    }

    compound_risk_findings {
        int compound_risk_id FK "references compound_risks.id"
        varchar finding_fingerprint "SHA-256 fingerprint"
    }

    suppressions {
        int id PK "autoincrement"
        varchar fingerprint "SHA-256, unique, indexed"
        text reason "nullable"
        varchar suppressed_by "default api"
        datetime created_at "auto"
    }
```

## Modèles

### ScanResult

Suit l'exécution d'un scan unique depuis le déclenchement jusqu'à la complétion. Stocke les comptages agrégés de sévérité pour des requêtes rapides sur le tableau de bord. Le champ `gate_passed` enregistre si la quality gate est passée (1), échouée (0), ou non évaluée (NULL).

### Finding

Une vulnérabilité de sécurité normalisée trouvée par l'un des cinq outils de scan. Chaque résultat possède une `fingerprint` déterministe (SHA-256 du chemin normalisé + rule_id + snippet) pour la déduplication inter-scans. Les champs d'enrichissement IA (`ai_analysis`, `ai_fix_suggestion`) sont remplis après l'analyse par Claude.

### CompoundRisk

Un risque composé identifié par l'IA qui englobe plusieurs résultats individuels. Par exemple, un contournement d'authentification dans un composant combiné à un IDOR dans un autre. Lié aux résultats associés via la table d'association `compound_risk_findings` en utilisant les empreintes.

### Suppression

Suit les empreintes qui ont été marquées comme faux positifs. Lorsque l'empreinte d'un résultat correspond à un enregistrement de suppression, il est exclu de l'évaluation de la quality gate et des comptages des rapports.

## Niveaux de sévérité

| Valeur | Nom | Action requise |
|--------|-----|----------------|
| 5 | CRITICAL | Corriger immédiatement, bloque le déploiement |
| 4 | HIGH | Corriger avant la mise en production |
| 3 | MEDIUM | Corriger dans le sprint actuel |
| 2 | LOW | Corriger dès que possible |
| 1 | INFO | Informatif, aucune action requise |

## Index

| Table | Colonne(s) | Utilisation |
|-------|------------|-------------|
| findings | scan_id | Recherche rapide des résultats par scan |
| findings | fingerprint | Déduplication et requêtes de suppression |
| compound_risks | scan_id | Recherche rapide des risques composés par scan |
| suppressions | fingerprint | Correspondance rapide des suppressions (contrainte unique) |

## Configuration SQLite

Appliquée à chaque connexion via les écouteurs d'événements SQLAlchemy :

```sql
PRAGMA journal_mode=WAL;      -- Write-Ahead Logging for concurrent reads
PRAGMA synchronous=NORMAL;     -- Balance between safety and speed
PRAGMA foreign_keys=ON;        -- Enforce FK constraints
```

## Emplacement de la base de données

| Environnement | Chemin |
|---------------|--------|
| Docker | `/data/scanner.db` (volume nommé `scanner_data`) |
| Dev local | Configuré via la variable d'environnement `SCANNER_DB_PATH` ou `db_path` dans `config.yml` |

## Migrations

Alembic est configuré pour les migrations de schéma. Les tables sont créées automatiquement au démarrage de l'application via `Base.metadata.create_all()` dans le gestionnaire de cycle de vie FastAPI.

```bash
# Générer une nouvelle migration
alembic revision --autogenerate -m "description"

# Appliquer les migrations
alembic upgrade head
```
