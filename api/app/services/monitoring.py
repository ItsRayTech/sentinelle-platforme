from prometheus_client import Counter, Histogram, Gauge

# Business Metrics
DECISION_COUNTER = Counter(
    "decision_total_count",
    "Nombre total de décisions prises",
    ["decision", "policy_rule"]
)

RISK_SCORE_DIST = Histogram(
    "risk_score_distribution",
    "Distribution des scores de risque de crédit",
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

FRAUD_SCORE_DIST = Histogram(
    "fraud_score_distribution",
    "Distribution des scores de fraude",
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

# Monitoring de Dérive (Distributions d'entrée)
INPUT_INCOME_DIST = Histogram(
    "input_income_distribution",
    "Distribution du revenu annuel du demandeur",
    buckets=[20000, 40000, 60000, 80000, 100000, 150000, 200000]
)

INPUT_DEBT_RATIO_DIST = Histogram(
    "input_debt_ratio_distribution",
    "Distribution du ratio dette/revenu du demandeur",
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
)

# Métriques Techniques (Senior++)
MODEL_LATENCY = Histogram(
    "model_inference_seconds",
    "Temps passé dans l'inférence du modèle (hors DB/Network)",
    buckets=[0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0]
)

DRIFT_WARNING = Gauge(
    "model_drift_warning",
    "Indicateur de drift détecté (1=Drift, 0=Normal)",
    ["feature"]
)
