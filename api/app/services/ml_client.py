from __future__ import annotations

from pathlib import Path
from typing import Optional

import joblib
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from ..schemas import DecisionRequest

_MODEL: Optional[object] = None
_MODEL_VERSION: Optional[str] = None
_EXPL_MODEL: Optional[object] = None # Cached LinearExplainer

_FRAUD_MODEL: Optional[object] = None
_FRAUD_VERSION: Optional[str] = None


def _find_model_path() -> Path:
    # 1) Docker mount path
    docker_path = Path("/ml/artifacts/credit_risk/model.joblib")
    if docker_path.exists():
        return docker_path

    # 2) Robust local search: walk up and find repo root containing /ml/artifacts/...
    here = Path(__file__).resolve()
    for p in here.parents:
        candidate = p / "ml" / "artifacts" / "credit_risk" / "model.joblib"
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        "Credit risk model not found. "
        "Expected either /ml/artifacts/credit_risk/model.joblib (Docker mount) "
        "or ./ml/artifacts/credit_risk/model.joblib in repo. "
        "Run training: python ml/training/train_credit_risk.py"
    )


def _load_model() -> object:
    global _MODEL, _MODEL_VERSION
    if _MODEL is not None:
        return _MODEL

    model_path = _find_model_path()
    _MODEL = joblib.load(model_path)

    # Optional: load version metadata
    metrics_path = model_path.parent / "metrics.json"
    if metrics_path.exists():
        try:
            import json
            data = json.loads(metrics_path.read_text(encoding="utf-8"))
            best = data.get("best_model", "unknown")
            seed = data.get("data_config", {}).get("seed", "na")
            run_id = data.get("mlflow_run_id", "na")
            _MODEL_VERSION = f"credit_risk:{best}(seed={seed}, run_id={run_id})"
        except Exception:
            _MODEL_VERSION = "credit_risk:model.joblib"
    else:
        _MODEL_VERSION = "credit_risk:model.joblib"

    return _MODEL


def _find_fraud_model_path() -> Path:
    docker_path = Path("/ml/artifacts/fraud/model.joblib")
    if docker_path.exists():
        return docker_path

    here = Path(__file__).resolve()
    for p in here.parents:
        candidate = p / "ml" / "artifacts" / "fraud" / "model.joblib"
        if candidate.exists():
            return candidate

    raise FileNotFoundError("Fraud model not found. Run: python ml/training/train_fraud.py")


def _load_fraud_model() -> object:
    global _FRAUD_MODEL, _FRAUD_VERSION
    if _FRAUD_MODEL is not None:
        return _FRAUD_MODEL

    model_path = _find_fraud_model_path()
    _FRAUD_MODEL = joblib.load(model_path)

    metrics_path = model_path.parent / "metrics.json"
    if metrics_path.exists():
        import json
        data = json.loads(metrics_path.read_text(encoding="utf-8"))
        seed = data.get("data_config", {}).get("seed", "na")
        _FRAUD_VERSION = f"fraud:isolation_forest(seed={seed})"
    else:
        _FRAUD_VERSION = "fraud:model.joblib"

    return _FRAUD_MODEL


def compute_shap_values(model_pipeline, X_df) -> list[dict]:
    """
    Compute local SHAP values for a single prediction using LinearExplainer.
    Maps One-Hot Encoded features back to original feature names.
    """
    import shap
    global _EXPL_MODEL

    # 1. Access parts of pipeline
    # Expected structure: Pipeline(steps=[('preprocess', ColumnTransformer), ('model', LogisticRegression)])
    try:
        preprocessor = model_pipeline.named_steps["preprocess"]
        classifier = model_pipeline.named_steps["model"]
    except Exception as e:
        print(f"ERROR: Pipeline structure mismatch: {e}")
        return []

    # 2. Transform input to get the actual features used by model
    X_transformed = preprocessor.transform(X_df)
    
    # 3. Get feature names from preprocessor
    # New in sklearn 1.0+: get_feature_names_out
    try:
        feature_names = preprocessor.get_feature_names_out()
    except AttributeError:
        # Fallback if old sklearn or incompatible
        feature_names = [f"feat_{i}" for i in range(X_transformed.shape[1])]

    # 4. Create or reuse Explainer
    # LinearExplainer is fast and lightweight for LogReg
    if _EXPL_MODEL is None:
        # Crucial: LinearExplainer needs a background dataset to compare against.
        # Since we use StandardScaler, the mean is approx 0.
        # We use a synthetic zero background to represent the "average" customer.
        background = np.zeros((1, X_transformed.shape[1]))
        
        _EXPL_MODEL = shap.LinearExplainer(
            classifier, 
            background,
            feature_perturbation="interventional"
        )
    
    # 5. Compute SHAP values
    shap_values = _EXPL_MODEL.shap_values(X_transformed)
    # print(f"DEBUG: SHAP values raw type: {type(shap_values)}, shape: {np.shape(shap_values)}")

    
    # shap_values is a list for classifier? or array?
    # For binary classification with LinearExplainer, it might be an array (n_samples, n_features)
    if isinstance(shap_values, list):
        vals = shap_values[0] # Class 0? Or Class 1? Usually check documentation
        # LinearExplainer for binary often returns just one array of raw margins
        pass
    else:
        vals = shap_values

    # Check shape: (1, n_features) -> flatten to (n_features,)
    if vals.ndim > 1:
        vals = vals[0]
        
    # 6. Post-process: Map back OHE key -> Original key
    # e.g. "employment_status_CDI" -> "employment_status"
    # We want to aggregate impacts per original feature
    
    impacts = {}
    for name, value in zip(feature_names, vals):
        # Heuristic to find original name: split by underscore?
        # Better: use the feature prefixes from ColumnTransformer if possible.
        # Standard: "cat__employment_status_CDI" / "num__age"
        
        # Simple parsing for our known schema
        original_name = name
        if name.startswith("cat__"):
            # cat__employment_status_CDI -> employment_status
            # remove prefix "cat__"
            clean = name.replace("cat__", "")
            # remove value suffix? hard without knowing all values.
            # But wait, for the end user, "employment_status" is enough?
            # actually we might want to group by prefix.
            parts = clean.split("_")
            # employment_status_CDI -> employment_status
            if "employment_status" in clean:
                original_name = "employment_status"
            else:
                original_name = clean
        elif name.startswith("num__"):
            original_name = name.replace("num__", "")
            
        impacts[original_name] = impacts.get(original_name, 0.0) + value

    # 7. Convert to list of FeatureImpact
    # Sort by absolute impact
    sorted_impacts = sorted(impacts.items(), key=lambda x: abs(x[1]), reverse=True)
    
    result = []
    for k, v in sorted_impacts:
        # direction
        direction = "+" if v > 0 else "-"
        # Minimal filter: only show if impact is significant (> 0.01?)
        if abs(v) > 0.01:
            result.append({"feature": k, "impact": direction, "value": float(v)})
    
    # print(f"DEBUG: Calculated impacts: {result[:2]}...")
            
    return result[:5] # Top 5


def predict_risk_and_fraud(payload: DecisionRequest) -> tuple[float, float, dict, list]:
    model = _load_model()

    c = payload.client
    X_row = {
        "age": c.age,
        "income_annual": c.income_annual,
        "employment_status": c.employment_status,
        "debt_to_income": c.debt_to_income,
        "credit_history_length_months": c.credit_history_length_months,
        "num_open_accounts": c.num_open_accounts,
        "late_payments_12m": c.late_payments_12m,
    }

    X_df = pd.DataFrame([X_row])

    required_cols = list(X_row.keys())
    missing = [col for col in required_cols if col not in X_df.columns]
    if missing:
        raise ValueError(f"Missing columns for credit risk model: {missing}")
    
    # Prediction
    risk_score = float(model.predict_proba(X_df)[:, 1][0])
    risk_score = float(np.clip(risk_score, 0.0, 1.0))
    
    # SHAP (Local Explanation)
    shap_impacts = compute_shap_values(model, X_df)

    # Fraud Model (Phase 2A)
    fraud_model = _load_fraud_model()

    t = payload.transaction
    X_fraud = {
        "amount": t.amount,
        "merchant_category": t.merchant_category,
        "country": t.country,
        "hour": t.hour,
        "is_new_device": t.is_new_device,
        "distance_from_home_km": t.distance_from_home_km,
    }
    Xf = pd.DataFrame([X_fraud])
    
    # This logic assumes IsolationForest or similar
    # anomaly score -> normalized 0..1
    normal_score = fraud_model.decision_function(Xf)
    anomaly_score = -float(normal_score[0])

    # MVP normalization
    fraud_score = 1.0 / (1.0 + np.exp(-anomaly_score))
    fraud_score = float(np.clip(fraud_score, 0.0, 1.0))

    model_versions = {
        "credit_risk": _MODEL_VERSION or "credit_risk:model.joblib",
        "fraud": _FRAUD_VERSION or "fraud:model.joblib",
    }
    return risk_score, fraud_score, model_versions, shap_impacts
