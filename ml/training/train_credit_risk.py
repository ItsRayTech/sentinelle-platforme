import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

try:
    from xgboost import XGBClassifier
except Exception as e:
    XGBClassifier = None


# -----------------------------
# 1) Générateur de données synthétiques
# -----------------------------
@dataclass
class DataConfig:
    n_samples: int = 50000
    seed: int = 42


EMPLOYMENT_STATUSES = ["CDI", "CDD", "INDEPENDANT", "ETUDIANT", "SANS_EMPLOI", "RETRAITE"]


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def generate_synthetic_credit_data(cfg: DataConfig) -> pd.DataFrame:
    rng = np.random.default_rng(cfg.seed)

    age = rng.integers(18, 75, size=cfg.n_samples)

    # Revenu : distribution log-normale, dépend un peu de l'âge
    base_income = rng.lognormal(mean=10.6, sigma=0.35, size=cfg.n_samples)  # ~ 40k-70k médiane
    age_factor = np.clip((age - 25) / 40, 0, 1)
    income_annual = base_income * (0.85 + 0.35 * age_factor)
    income_annual = np.clip(income_annual, 12000, 200000)

    employment_status = rng.choice(
        EMPLOYMENT_STATUSES,
        size=cfg.n_samples,
        p=[0.55, 0.15, 0.12, 0.06, 0.05, 0.07],
    )

    # debt_to_income : plus élevé pour revenus faibles / emploi instable
    base_dti = rng.beta(a=2.0, b=5.0, size=cfg.n_samples)  # mostly < 0.5
    emp_risk = np.array([1.0 if s in ("SANS_EMPLOI", "ETUDIANT") else 0.0 for s in employment_status])
    dti = base_dti + 0.15 * emp_risk + 0.05 * (income_annual < 25000)
    debt_to_income = np.clip(dti, 0.0, 1.5)

    # historique crédit en mois : corrélé avec l'âge
    credit_history_length_months = np.clip((age - 18) * 12 + rng.normal(0, 24, cfg.n_samples), 0, 600).astype(int)

    # nombre de comptes ouverts : dépend de l'historique
    lam = np.clip(1.5 + credit_history_length_months / 120, 1.5, 8.0)
    num_open_accounts = rng.poisson(lam=lam, size=cfg.n_samples)
    num_open_accounts = np.clip(num_open_accounts, 0, 30)

    # retards de paiement : plus probables si DTI élevé / chômage
    late_base = rng.poisson(lam=0.25 + 1.0 * (debt_to_income > 0.5) + 1.5 * emp_risk, size=cfg.n_samples)
    late_payments_12m = np.clip(late_base, 0, 12)

    # Créer une probabilité de défaut via fonction logit
    # (Synthétique mais "réaliste" : DTI & retards dominent, le revenu réduit le risque)
    logit = (
        -2.2
        + 2.3 * np.clip(debt_to_income, 0, 1.0)
        + 0.35 * late_payments_12m
        + 0.6 * (employment_status == "CDD").astype(float)
        + 0.9 * (employment_status == "SANS_EMPLOI").astype(float)
        + 0.5 * (employment_status == "ETUDIANT").astype(float)
        - 0.000020 * income_annual
        - 0.0020 * credit_history_length_months
        + 0.05 * (num_open_accounts > 10).astype(float)
    )

    p_default = sigmoid(logit)
    default_flag = rng.binomial(n=1, p=np.clip(p_default, 0.001, 0.999))

    df = pd.DataFrame(
        {
            "age": age,
            "income_annual": income_annual.round(2),
            "employment_status": employment_status,
            "debt_to_income": debt_to_income.round(4),
            "credit_history_length_months": credit_history_length_months,
            "num_open_accounts": num_open_accounts,
            "late_payments_12m": late_payments_12m,
            "default_flag": default_flag,
        }
    )
    return df


# -----------------------------
# 2) Training utilities
# -----------------------------
NUM_COLS = [
    "age",
    "income_annual",
    "debt_to_income",
    "credit_history_length_months",
    "num_open_accounts",
    "late_payments_12m",
]
CAT_COLS = ["employment_status"]
TARGET = "default_flag"


def build_preprocessor() -> ColumnTransformer:
    numeric = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
        ]
    )
    categorical = Pipeline(
        steps=[
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("num", numeric, NUM_COLS),
            ("cat", categorical, CAT_COLS),
        ],
        remainder="drop",
    )


def evaluate_model(model: Pipeline, X_test: pd.DataFrame, y_test: np.ndarray) -> dict:
    # Predict proba for AUC
    proba = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, proba)

    # Seuil de décision pour le rappel (classe défaut=1)
    # En risque crédit, le rappel sur défaut est souvent important -> seuil 0.5 pour le MVP
    pred = (proba >= 0.5).astype(int)
    recall = recall_score(y_test, pred, pos_label=1)

    return {"auc": float(auc), "recall_default": float(recall)}


def setup_mlflow() -> None:
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5001")
    mlflow.set_tracking_uri(tracking_uri)
    
    experiment_name = "credit-risk-prod"
    # S'assurer que l'emplacement des artifacts est un chemin absolu sur la machine hôte
    # Si lancé localement, les artifacts vont dans ./ml/mlflow/artifacts
    # Docker voit /ml/mlflow/artifacts, l'hôte voit $(pwd)/ml/mlflow/artifacts
    
    # Correctif simple : Utiliser sqlite pour le tracking mais file:// URI pour les artifacts nécessite un filesystem partagé
    # Comme nous montons ./ml:/ml, nous pouvons utiliser le chemin absolu sur l'hôte.
    
    artifact_path = Path(__file__).parents[2] / "mlflow" / "artifacts"
    artifact_uri = f"file://{artifact_path.resolve()}"
    
    try:
        if not mlflow.get_experiment_by_name(experiment_name):
            mlflow.create_experiment(experiment_name, artifact_location=artifact_uri)
        mlflow.set_experiment(experiment_name)
    except Exception:
        # Fallback if experiment exists with different artifact root (might fail)
        mlflow.set_experiment(experiment_name)


def main():
    # Output paths
    root = Path(__file__).resolve().parents[1]  # ml/
    out_dir = root / "artifacts" / "credit_risk"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    setup_mlflow()

    with mlflow.start_run(run_name="credit_risk_training") as run:
        # 1) Generate data
        cfg = DataConfig(
            n_samples=int(os.getenv("CR_N_SAMPLES", "50000")),
            seed=int(os.getenv("CR_SEED", "42")),
        )
        df = generate_synthetic_credit_data(cfg)
        default_rate = float(df[TARGET].mean())

        X = df.drop(columns=[TARGET])
        y = df[TARGET].to_numpy()

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=cfg.seed, stratify=y
        )

        preprocessor = build_preprocessor()

        # Log config / data stats
        mlflow.log_params({
            "n_samples": cfg.n_samples,
            "seed": cfg.seed,
            "threshold": 0.5,
        })
        mlflow.log_metrics({"default_rate": default_rate})

        # 2) Baseline: Logistic Regression
        logreg = LogisticRegression(
            max_iter=2000,
            class_weight="balanced",
            solver="lbfgs",
        )
        model_logreg = Pipeline(steps=[("preprocess", preprocessor), ("model", logreg)])
        model_logreg.fit(X_train, y_train)
        metrics_logreg = evaluate_model(model_logreg, X_test, y_test)
        mlflow.log_metrics({
            "logreg_auc": metrics_logreg["auc"],
            "logreg_recall_default": metrics_logreg["recall_default"],
        })

        # 3) Challenger: XGBoost
        metrics_xgb = None
        model_xgb = None
        if XGBClassifier is not None:
            xgb = XGBClassifier(
                n_estimators=400,
                max_depth=4,
                learning_rate=0.05,
                subsample=0.9,
                colsample_bytree=0.9,
                reg_lambda=1.0,
                random_state=cfg.seed,
                eval_metric="logloss",
                n_jobs=4,
            )
            model_xgb = Pipeline(steps=[("preprocess", preprocessor), ("model", xgb)])
            model_xgb.fit(X_train, y_train)
            metrics_xgb = evaluate_model(model_xgb, X_test, y_test)
            mlflow.log_metrics({
                "xgb_auc": metrics_xgb["auc"],
                "xgb_recall_default": metrics_xgb["recall_default"],
            })

        # 4) Select best model
        candidates = [("logreg", model_logreg, metrics_logreg)]
        if model_xgb is not None and metrics_xgb is not None:
            candidates.append(("xgb", model_xgb, metrics_xgb))

        def score_key(item):
            _, _, m = item
            return (m["auc"], m["recall_default"])

        best_name, best_model, best_metrics = sorted(candidates, key=score_key, reverse=True)[0]

        mlflow.log_params({"best_model": best_name})
        mlflow.log_metrics({
            "best_auc": best_metrics["auc"],
            "best_recall_default": best_metrics["recall_default"],
        })

        # 5) Save local artifacts
        model_path = out_dir / "model.joblib"
        joblib.dump(best_model, model_path)

        metrics = {
            "best_model": best_name,
            "best_metrics": best_metrics,
            "logreg_metrics": metrics_logreg,
            "xgb_metrics": metrics_xgb,
            "default_rate": default_rate,
            "data_config": asdict(cfg),
            "features_numeric": NUM_COLS,
            "features_categorical": CAT_COLS,
            "target": TARGET,
            "threshold": 0.5,
            "mlflow_run_id": run.info.run_id,
        }
        with open(out_dir / "metrics.json", "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)

        schema = {
            "input_features": {"numeric": NUM_COLS, "categorical": CAT_COLS},
            "employment_status_allowed": EMPLOYMENT_STATUSES,
        }
        with open(out_dir / "schema.json", "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)

        # 6) Log artifacts to MLflow
        mlflow.log_artifact(str(out_dir / "metrics.json"))
        mlflow.log_artifact(str(out_dir / "schema.json"))

        # Log model artifact (simple)
        mlflow.sklearn.log_model(
            sk_model=best_model,
            artifact_path="model",
        )

        print("✅ Training done")
        print(f"MLflow run_id: {run.info.run_id}")
        print(f"Best model: {best_name}")
        print(f"Saved local: {model_path}")
        print("Metrics:", best_metrics)


if __name__ == "__main__":
    main()
