import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.metrics import roc_auc_score, average_precision_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.ensemble import IsolationForest


# -----------------------------
# 1) Synthetic fraud generator
# -----------------------------
@dataclass
class FraudDataConfig:
    n_samples: int = 80000
    fraud_rate: float = 0.03
    seed: int = 42


MERCHANT_CATS = ["groceries", "electronics", "travel", "fuel", "fashion", "restaurants", "services"]
COUNTRIES = ["FR", "BE", "DE", "ES", "IT", "NL", "GB", "US"]


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def generate_synthetic_fraud_data(cfg: FraudDataConfig) -> pd.DataFrame:
    rng = np.random.default_rng(cfg.seed)

    # Core features similar to your API payload
    amount = rng.lognormal(mean=4.2, sigma=0.9, size=cfg.n_samples)  # heavy tail
    amount = np.clip(amount, 1, 5000)

    merchant_category = rng.choice(MERCHANT_CATS, size=cfg.n_samples, p=[0.28, 0.16, 0.08, 0.12, 0.12, 0.16, 0.08])
    country = rng.choice(COUNTRIES, size=cfg.n_samples, p=[0.70, 0.05, 0.05, 0.04, 0.04, 0.04, 0.04, 0.04])
    hour = rng.integers(0, 24, size=cfg.n_samples)

    is_new_device = rng.binomial(1, p=0.10, size=cfg.n_samples).astype(bool)
    distance_from_home_km = rng.gamma(shape=2.0, scale=12.0, size=cfg.n_samples)  # mostly small distances
    distance_from_home_km = np.clip(distance_from_home_km, 0, 2000)

    # Fraud likelihood model (synthetic):
    night = ((hour >= 23) | (hour <= 5)).astype(float)
    high_amount = (amount > 800).astype(float)
    far = (distance_from_home_km > 200).astype(float)
    risky_country = np.isin(country, ["US"]).astype(float)

    # electronics + new device + night is a classic suspicious pattern
    is_electronics = (merchant_category == "electronics").astype(float)
    combo = is_electronics * is_new_device.astype(float) * night

    logit = (
        -4.0
        + 1.6 * night
        + 1.4 * high_amount
        + 1.2 * far
        + 1.0 * is_new_device.astype(float)
        + 0.9 * risky_country
        + 2.0 * combo
    )

    p = sigmoid(logit)

    # Calibrate to desired fraud rate roughly
    # Shift logits so that mean(p) ~ fraud_rate
    current_rate = float(p.mean())
    if current_rate > 0:
        shift = np.log(cfg.fraud_rate / (1 - cfg.fraud_rate)) - np.log(current_rate / (1 - current_rate))
        p = sigmoid(logit + shift)

    is_fraud = rng.binomial(1, p=np.clip(p, 0.0001, 0.9999))

    df = pd.DataFrame(
        {
            "amount": amount.round(2),
            "merchant_category": merchant_category,
            "country": country,
            "hour": hour,
            "is_new_device": is_new_device,
            "distance_from_home_km": distance_from_home_km.round(3),
            "is_fraud": is_fraud,
        }
    )
    return df


# -----------------------------
# 2) Training
# -----------------------------
NUM_COLS = ["amount", "hour", "distance_from_home_km"]
CAT_COLS = ["merchant_category", "country"]
BOOL_COLS = ["is_new_device"]
TARGET = "is_fraud"


def build_preprocessor() -> ColumnTransformer:
    num = Pipeline([("scaler", StandardScaler())])
    cat = Pipeline([("onehot", OneHotEncoder(handle_unknown="ignore"))])

    return ColumnTransformer(
        transformers=[
            ("num", num, NUM_COLS),
            ("cat", cat, CAT_COLS),
            ("bool", "passthrough", BOOL_COLS),
        ],
        remainder="drop",
    )


def main():
    root = Path(__file__).resolve().parents[1]  # ml/
    out_dir = root / "artifacts" / "fraud"
    out_dir.mkdir(parents=True, exist_ok=True)

    cfg = FraudDataConfig(
        n_samples=int(os.getenv("FR_N_SAMPLES", "80000")),
        fraud_rate=float(os.getenv("FR_FRAUD_RATE", "0.03")),
        seed=int(os.getenv("FR_SEED", "42")),
    )
    df = generate_synthetic_fraud_data(cfg)

    X = df.drop(columns=[TARGET])
    y = df[TARGET].to_numpy()
    fraud_rate = float(y.mean())

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=cfg.seed, stratify=y
    )

    preprocessor = build_preprocessor()

    # IsolationForest is unsupervised: we train on "mostly normal" data
    # For MVP: filter out fraud in training set to simulate real scenario
    X_train_normal = X_train[y_train == 0]

    iso = IsolationForest(
        n_estimators=300,
        contamination=cfg.fraud_rate,  # expected anomaly proportion
        random_state=cfg.seed,
        n_jobs=4,
    )

    model = Pipeline(steps=[("preprocess", preprocessor), ("model", iso)])
    model.fit(X_train_normal)

    # Scores: IsolationForest gives anomaly score via decision_function (higher = more normal)
    # We'll convert to anomaly probability-like score in [0,1]:
    normal_score = model.decision_function(X_test)  # higher means normal
    anomaly_score = -normal_score
    # Normalize to [0,1] for a stable API output
    min_s, max_s = float(anomaly_score.min()), float(anomaly_score.max())
    fraud_score = (anomaly_score - min_s) / (max_s - min_s + 1e-9)

    # Evaluate vs labels (we do have synthetic labels)
    auc = roc_auc_score(y_test, fraud_score)
    ap = average_precision_score(y_test, fraud_score)

    model_path = out_dir / "model.joblib"
    joblib.dump(model, model_path)

    metrics = {
        "model": "isolation_forest",
        "auc": float(auc),
        "avg_precision": float(ap),
        "fraud_rate": fraud_rate,
        "data_config": asdict(cfg),
        "features_numeric": NUM_COLS,
        "features_categorical": CAT_COLS,
        "features_bool": BOOL_COLS,
        "target": TARGET,
        "score_normalization": "minmax_on_test (MVP)",
    }
    with open(out_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    schema = {
        "input_features": {
            "numeric": NUM_COLS,
            "categorical": CAT_COLS,
            "bool": BOOL_COLS,
        },
        "merchant_category_allowed": MERCHANT_CATS,
        "country_allowed": COUNTRIES,
    }
    with open(out_dir / "schema.json", "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)

    print("✅ Fraud training done")
    print(f"Saved: {model_path}")
    print("AUC:", float(auc), "AP:", float(ap), "fraud_rate:", fraud_rate)


if __name__ == "__main__":
    main()
