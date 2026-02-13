from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..schemas import DecisionRequest, DecisionResponse, ExplanationsPreview, FeatureImpact
from ..db import SessionLocal, Decision as DecisionRow
from ..services.ml_client import predict_risk_and_fraud
from ..services.policy import apply_policy
from ..services.logging import hash_client_id, build_decision_id, store_decision
from ..services.agent_client import generate_report
from ..services.monitoring import (
    DECISION_COUNTER,
    RISK_SCORE_DIST,
    FRAUD_SCORE_DIST,
    INPUT_INCOME_DIST,
    INPUT_DEBT_RATIO_DIST,
    MODEL_LATENCY,
    DRIFT_WARNING
)

router = APIRouter(tags=["decision"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/decision", response_model=DecisionResponse)
async def make_decision(payload: DecisionRequest, db: Session = Depends(get_db)):
    with MODEL_LATENCY.time():
        risk_score, fraud_score, model_versions, shap_impacts = predict_risk_and_fraud(payload)
    pr = apply_policy(risk_score, fraud_score)

    # Monitoring (Prometheus)
    RISK_SCORE_DIST.observe(risk_score)
    FRAUD_SCORE_DIST.observe(fraud_score)
    DECISION_COUNTER.labels(decision=pr.decision, policy_rule=pr.rule).inc()
    
    # Monitoring de Dérive
    INPUT_INCOME_DIST.observe(payload.client.income_annual)
    INPUT_DEBT_RATIO_DIST.observe(payload.client.debt_to_income)

    # Simulation alerte drift (règle experte simple pour la démo)
    # Si revenu > 150k ou debt_ratio > 0.6 => Drift potentiel (population inattendue)
    is_drift_income = 1 if payload.client.income_annual > 150000 else 0
    is_drift_dti = 1 if payload.client.debt_to_income > 0.6 else 0
    
    DRIFT_WARNING.labels(feature="income_annual").set(is_drift_income)
    DRIFT_WARNING.labels(feature="debt_to_income").set(is_drift_dti)

    # Aperçu minimal et cohérent des explications
    # Risque Crédit : Valeurs SHAP (Réelles)
    # Fraude : Placeholder pour l'instant (jusqu'à la Phase 4b)
    fraud_preview = [
        FeatureImpact(feature="is_new_device", impact="+"),
        FeatureImpact(feature="hour", impact="+"),
        FeatureImpact(feature="distance_from_home_km", impact="+"),
    ]

    explanations_preview = ExplanationsPreview(
        credit_top_features=shap_impacts,
        fraud_top_features=fraud_preview,
    )

    decision_id = build_decision_id()
    client_hash = hash_client_id(payload.client.client_id)

    stored = store_decision(
        db,
        decision_id=decision_id,
        client_id_hash=client_hash,
        risk_score=risk_score,
        fraud_score=fraud_score,
        decision=pr.decision,
        policy_rule=pr.rule,
        model_versions=model_versions,
        explanations_preview=explanations_preview.model_dump(),
        request_payload=payload.model_dump(),
    )

    # Payload Agent (n'utilise que les sorties système : pas d'hallucination)
    agent_payload = {
        "decision": pr.decision,
        "risk_score": risk_score,
        "fraud_score": fraud_score,
        "policy_rule": pr.rule,
        "model_versions": model_versions,
        "explanations_preview": explanations_preview.model_dump(),
    }
    report_summary = await generate_report(agent_payload)

    return DecisionResponse(
        decision_id=stored.decision_id,
        decision=pr.decision,
        risk_score=risk_score,
        fraud_score=fraud_score,
        policy_rule=pr.rule,
        model_versions=model_versions,
        explanations_preview=explanations_preview,
        report_summary=report_summary,
    )
