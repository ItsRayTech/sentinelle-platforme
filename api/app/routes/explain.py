from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import SessionLocal, Decision
from ..schemas import ExplainResponse, FeatureImpact

router = APIRouter(tags=["explain"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/explain/{decision_id}", response_model=ExplainResponse)
def explain(decision_id: str, db: Session = Depends(get_db)):
    row = db.query(Decision).filter(Decision.decision_id == decision_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="decision_id not found")

    # MVP : retourner l'aperçu comme "shap top" jusqu'à ce que le vrai SHAP soit implémenté
    credit = [FeatureImpact(**x) for x in row.explanations_preview.get("credit_top_features", [])]
    fraud = [FeatureImpact(**x) for x in row.explanations_preview.get("fraud_top_features", [])]

    return ExplainResponse(
        decision_id=row.decision_id,
        decision=row.decision,
        policy_rule=row.policy_rule,
        model_versions=row.model_versions,
        risk_score=row.risk_score,
        fraud_score=row.fraud_score,
        credit_shap_top=credit,
        fraud_shap_top=fraud,
    )
