from prometheus_client import Counter, Histogram

# Business Metrics
DECISION_COUNTER = Counter(
    "decision_total_count",
    "Total number of decisions made",
    ["decision", "policy_rule"]
)

RISK_SCORE_DIST = Histogram(
    "risk_score_distribution",
    "Distribution of credit risk scores",
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

FRAUD_SCORE_DIST = Histogram(
    "fraud_score_distribution",
    "Distribution of fraud scores",
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

# Drift Detection Metrics (Input distributions)
INPUT_INCOME_DIST = Histogram(
    "input_income_distribution",
    "Distribution of applicant annual income",
    buckets=[20000, 40000, 60000, 80000, 100000, 150000, 200000]
)

INPUT_DEBT_RATIO_DIST = Histogram(
    "input_debt_ratio_distribution",
    "Distribution of applicant debt-to-income ratio",
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
)
