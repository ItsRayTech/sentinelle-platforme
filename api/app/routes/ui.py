from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional

from ..db import SessionLocal, Decision as DecisionRow
from ..schemas import DecisionRequest, ClientPayload, TransactionPayload
from ..services.ml_client import predict_risk_and_fraud
from ..services.policy import apply_policy
from ..services.logging import hash_client_id, build_decision_id, store_decision
from ..services.agent_client import generate_report
from ..schemas import ExplanationsPreview, FeatureImpact
from ..services.monitoring import (
    DECISION_COUNTER,
    RISK_SCORE_DIST,
    FRAUD_SCORE_DIST,
    INPUT_INCOME_DIST,
    INPUT_DEBT_RATIO_DIST,
)

from pathlib import Path

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

router = APIRouter(tags=["ui"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "active_page": "dashboard",
        "form": {},
        "result": None,
    })


@router.post("/ui/decide", response_class=HTMLResponse)
async def ui_decide(
    request: Request,
    client_id: str = Form(...),
    age: int = Form(...),
    income_annual: float = Form(...),
    employment_status: str = Form(...),
    debt_to_income: float = Form(...),
    credit_history_length_months: int = Form(...),
    num_open_accounts: int = Form(...),
    late_payments_12m: int = Form(...),
    amount: float = Form(...),
    merchant_category: str = Form(...),
    country: str = Form(...),
    hour: int = Form(...),
    distance_from_home_km: float = Form(...),
    is_new_device: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    # Build form dict for re-populating the form
    form_data = {
        "client_id": client_id,
        "age": age,
        "income_annual": income_annual,
        "employment_status": employment_status,
        "debt_to_income": debt_to_income,
        "credit_history_length_months": credit_history_length_months,
        "num_open_accounts": num_open_accounts,
        "late_payments_12m": late_payments_12m,
        "amount": amount,
        "merchant_category": merchant_category,
        "country": country,
        "hour": hour,
        "distance_from_home_km": distance_from_home_km,
        "is_new_device": is_new_device == "on",
    }

    # Build Pydantic models
    payload = DecisionRequest(
        client=ClientPayload(
            client_id=client_id,
            age=age,
            income_annual=income_annual,
            employment_status=employment_status,
            debt_to_income=debt_to_income,
            credit_history_length_months=credit_history_length_months,
            num_open_accounts=num_open_accounts,
            late_payments_12m=late_payments_12m,
        ),
        transaction=TransactionPayload(
            amount=amount,
            merchant_category=merchant_category,
            country=country,
            hour=hour,
            is_new_device=is_new_device == "on",
            distance_from_home_km=distance_from_home_km,
        ),
    )

    # Run the decision pipeline (same logic as the API route)
    risk_score, fraud_score, model_versions, shap_impacts = predict_risk_and_fraud(payload)
    pr = apply_policy(risk_score, fraud_score)

    # Monitoring
    RISK_SCORE_DIST.observe(risk_score)
    FRAUD_SCORE_DIST.observe(fraud_score)
    DECISION_COUNTER.labels(decision=pr.decision, policy_rule=pr.rule).inc()
    INPUT_INCOME_DIST.observe(payload.client.income_annual)
    INPUT_DEBT_RATIO_DIST.observe(payload.client.debt_to_income)

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

    # Agent report
    agent_payload = {
        "decision": pr.decision,
        "risk_score": risk_score,
        "fraud_score": fraud_score,
        "policy_rule": pr.rule,
        "model_versions": model_versions,
        "explanations_preview": explanations_preview.model_dump(),
    }
    report_summary = await generate_report(agent_payload)

    result = {
        "decision_id": stored.decision_id,
        "decision": pr.decision,
        "risk_score": risk_score,
        "fraud_score": fraud_score,
        "policy_rule": pr.rule,
        "model_versions": model_versions,
        "explanations_preview": explanations_preview.model_dump(),
        "report_summary": report_summary,
    }

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "active_page": "dashboard",
        "form": form_data,
        "result": result,
    })


@router.get("/ui/audit", response_class=HTMLResponse)
async def audit_trail(request: Request, db: Session = Depends(get_db)):
    decisions = db.query(DecisionRow).order_by(DecisionRow.created_at.desc()).limit(50).all()
    return templates.TemplateResponse("audit.html", {
        "request": request,
        "active_page": "audit",
        "decisions": decisions,
    })
