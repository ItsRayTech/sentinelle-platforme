# Sentinelle – Plateforme de Décision Risque & Fraude

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Production-green)
![MLflow](https://img.shields.io/badge/MLOps-MLflow-orange)
![Monitoring](https://img.shields.io/badge/Monitoring-Prometheus%20%2B%20Grafana-red)
![CI](https://img.shields.io/badge/CI-GitHub%20Actions-black)

Une plateforme orientée production pour la décision de crédit et de fraude en temps réel, avec auditabilité, explicabilité et supervision humaine (Conçu pour RGPD / AI Act).

---

## 1. Problème Métier
Les institutions financières doivent prendre des décisions de crédit et de fraude en temps réel tout en respectant des contraintes réglementaires strictes (RGPD, AI Act).
Ce projet propose une **plateforme de décision** capable d'évaluer le risque de crédit et de fraude, d'expliquer ses décisions (SHAP), et de permettre une supervision humaine (**Human-in-the-Loop**).

---

## ⏱️ Demo en 60 secondes

```bash
docker compose up --build
curl -X POST http://localhost:8000/decision -H "Content-Type: application/json" -d @examples/accept.json
open http://localhost:8000/docs
open http://localhost:5001
open http://localhost:3000
```

---

## 2. Fonctionnalités Clés (MVP)
- **Endpoint de décision unifié** : `POST /decision` → `ACCEPT / REVIEW / REJECT / ALERT`
- **Piste d'audit** : chaque décision est stockée avec horodatage, règle de politique et version du modèle
- **Pseudonymisation** : les identifiants clients sont hashés avant stockage
- **Supervision humaine** : revue manuelle et surcharge via `POST /review/{decision_id}`
- **Endpoint d'explication** : `GET /explain/{decision_id}` (Le MVP renvoie un aperçu, vrai SHAP en Phase 2)

## 3. Stack Technique
- **API** : FastAPI, Pydantic, SQLAlchemy
- **Moteur de Décision Hybride** : Combine un score de risque (Régression Logistique) et un score de fraude (Isolation Forest - Non supervisé).
- **Explicabilité** :
  - **SHAP Global** (analyse offline, MLflow)
  - **SHAP Local** (calcul temps réel via LinearExplainer)
- **Agent IA Générative** : Un agent LLM analyse les résultats techniques pour générer un rapport narratif compréhensible par un humain.
- **Full MLOps** : Tracking des expérimentations avec MLflow, versioning des modèles.
- **Observabilité** : Dashboard Grafana & Prometheus pour suivre la production et le drift des données.
- **DevOps & CI/CD** : Déploiement via Docker Compose, Pipeline GitHub Actions pour les tests automatiques.
- **Base de données** : SQLite (MVP) → PostgreSQL (production-ready)

---

## 4. Architecture

```mermaid
graph TD
    Client[App Client] -->|POST /decision| API[Gateway FastAPI]
    API -->|Risk & Fraud Score| ML[Service de Scoring (Credit Risk + Fraud Models)]
    API -->|Vérification Règles| Policy[Moteur de Règles]
    API -->|Log Audit| DB[(SQLite/PostgreSQL)]
    API --> Decision[Décision : ACCEPT/REVIEW/REJECT/ALERT]
    Decision -->|Si REVIEW| Human[Réviseur Humain]
    Human -->|POST /review| API
```

---

## 5. Politique de Décision (Règles Métier)

* Si `fraud_score >= 0.85` → `ALERT`
* Sinon si `risk_score >= 0.70` → `REJECT`
* Sinon si `risk_score` dans `[0.45, 0.70)` → `REVIEW` (**human-in-the-loop**)
* Sinon → `ACCEPT`

Ces seuils sont configurables via des variables d'environnement.

---

## 6. Démarrage Rapide

```bash
cp .env.example .env
docker compose up --build
```

API : `http://localhost:8000`
OpenAPI (Swagger) : `http://localhost:8000/docs`
ReDoc : `http://localhost:8000/redoc`

---

## 7. Endpoints & Exemples

### Décision (`POST /decision`)

```bash
curl -X POST "http://localhost:8000/decision" \
  -H "Content-Type: application/json" \
  -d '{
    "client": {
      "client_id": "C123456",
      "age": 34,
      "income_annual": 45000,
      "employment_status": "CDI",
      "debt_to_income": 0.28,
      "credit_history_length_months": 72,
      "num_open_accounts": 3,
      "late_payments_12m": 0
    },
    "transaction": {
      "amount": 120.50,
      "merchant_category": "electronics",
      "country": "FR",
      "hour": 21,
      "is_new_device": true,
      "distance_from_home_km": 18.4
    }
  }'
```

**Exemple de réponse**

```json
{
  "decision_id": "dcn_20260212_9f3a2c",
  "decision": "ACCEPT",
  "risk_score": 0.436,
  "fraud_score": 0.432,
  "policy_rule": "otherwise => ACCEPT",
  "model_versions": {
    "credit_risk": "credit_risk:logreg(seed=42, run_id=abc123)",
    "fraud": "fraud:isolation_forest(seed=42)"
  },
  "report_summary": "Décision ACCEPT..."
}
```

### Explication (`GET /explain/{decision_id}`)

```bash
curl "http://localhost:8000/explain/dcn_..."
```

### Revue Humaine (`POST /review/{decision_id}`)

```bash
curl -X POST "http://localhost:8000/review/dcn_..." \
  -H "Content-Type: application/json" \
  -d '{
    "human_decision": "APPROVE",
    "comment": "Identité client vérifiée par téléphone.",
    "reviewer_id": "agent_007"
  }'
```

---

## 8. Modèles & Métriques

### ✅ Credit Risk (Supervisé)
- Logistic Regression (baseline)
- XGBoost (challenger)
- Tracking MLflow activé
- Sélection automatique du meilleur modèle (AUC + Recall défaut)
- Artefacts versionnés (`model.joblib`, `metrics.json`)

### ✅ Fraud Detection (Anomalies)
- Isolation Forest (contamination calibrée)
- Normalisation des scores vers [0,1]
- Évaluation via AUC & Average Precision
- Artefacts versionnés

### Métriques observées (synthetic data)
- AUC Credit Risk ≈ > 0.85
- Recall défaut ≈ > 0.70
- AUC Fraud ≈ > 0.90 (synthetic benchmark)

Toutes les expériences sont visibles dans MLflow :
http://localhost:5001

---

## 9. Explicabilité

*   **Global** : Importance des features (SHAP) disponible dans les notebooks MLflow.
*   **Local** : Top facteurs influençant chaque décision individuelle (calculé en temps réel via `shap.LinearExplainer`).
*   Chaque réponse API inclut une section `explanations_preview` détaillée.

---

## 10. Conformité (AI Act / RGPD)

*   **Minimisation des données** : pas d'identifiants directs stockés (pas de nom, adresse, etc.)
*   **Pseudonymisation** : les IDs clients sont hashés avant stockage
*   **Auditabilité** : décisions logguées avec règle de politique + version du modèle
*   **Supervision humaine** : les cas limites sont dirigés vers `REVIEW` + surcharge manuelle supportée.
*   **Pas uniquement automatisé (Esprit RGPD Art.22)** : les cas limites sont dirigés vers `REVIEW` pour supervision humaine.
*   **Rétention (démo)** : politique de rétention configurable pour les décisions stockées (prévu)

Voir :
*   `docs/AI_COMPLIANCE.md`
*   `docs/MODEL_CARD.md`
*   `docs/DATA_SHEET.md`

### 11. Tests & CI/CD
Le projet inclut une suite de tests unitaires et un pipeline CI/CD.
Pour lancer les tests localement :
```bash
pytest api/tests
```
Le pipeline GitHub Actions se lance automatiquement à chaque push sur `main`.

## 📈 Monitoring & Observability
- **Grafana** (`http://localhost:3000`) : Visualisation des métriques temps réel (Décisions, Scores, Latence).
- **Prometheus** (`http://localhost:9090`) : Collecte des métriques.
- **Drift Detection** : Suivi des distributions d'entrée (Revenu, Dette) pour alerter sur le data drift.

## 📚 Documentation
- [Guide de Démarrage (Walkthrough)](docs/WALKTHROUGH.md)
- [Fiche Modèle (Model Card)](docs/MODEL_CARD.md)
- [Fiche de Données (Data Sheet)](docs/DATA_SHEET.md)
- [Compliance IA (EU AI Act)](docs/AI_COMPLIANCE.md)
- [CI/CD Guide](docs/CI_CD.md)

## 12. Données & Avertissement
Ceci est un projet de démonstration utilisant des données publiques ou synthétiques. Il n'est pas destiné à prendre de vraies décisions de crédit sans validation, gouvernance et revue réglementaire appropriées.

---

* [x] API + moteur de politique
* [x] Logs d'audit + stockage des décisions
* [x] Endpoint de revue humaine
* [x] Modèle Credit Risk supervisé
* [x] Modèle Fraud (Isolation Forest)
* [x] Tracking MLflow + artefacts
* [x] Agent IA pour génération de rapports
* [x] SHAP réel global + local
* [x] Monitoring production (drift + métriques live)
* [x] CI (GitHub Actions) + lint
* [ ] Migration PostgreSQL + observabilité avancée
