from typing import Literal, Optional, List
from pydantic import BaseModel, Field, conint, confloat

DecisionType = Literal["ACCEPT", "REVIEW", "REJECT", "ALERT"]

class ClientPayload(BaseModel):
    client_id: str = Field(..., min_length=3, max_length=64)
    age: conint(ge=18, le=100)
    income_annual: confloat(gt=0)
    employment_status: Literal["CDI", "CDD", "INDEPENDANT", "ETUDIANT", "SANS_EMPLOI", "RETRAITE"]
    debt_to_income: confloat(ge=0, le=2.0)
    credit_history_length_months: conint(ge=0, le=600)
    num_open_accounts: conint(ge=0, le=50)
    late_payments_12m: conint(ge=0, le=60)

class TransactionPayload(BaseModel):
    amount: confloat(gt=0)
    merchant_category: str = Field(..., min_length=2, max_length=64)
    country: str = Field(..., min_length=2, max_length=2, description="ISO country code (e.g., FR)")
    hour: conint(ge=0, le=23)
    is_new_device: bool
    distance_from_home_km: confloat(ge=0, le=20000)

class DecisionRequest(BaseModel):
    client: ClientPayload
    transaction: TransactionPayload

class FeatureImpact(BaseModel):
    feature: str
    impact: str

class ExplanationsPreview(BaseModel):
    credit_top_features: List[FeatureImpact]
    fraud_top_features: List[FeatureImpact]

class DecisionResponse(BaseModel):
    decision_id: str
    decision: DecisionType
    risk_score: float = Field(..., ge=0, le=1)
    fraud_score: float = Field(..., ge=0, le=1)
    policy_rule: str
    model_versions: dict
    explanations_preview: ExplanationsPreview
    report_summary: Optional[str] = None

class ExplainResponse(BaseModel):
    decision_id: str
    decision: DecisionType
    policy_rule: str
    model_versions: dict
    risk_score: float
    fraud_score: float
    credit_shap_top: List[FeatureImpact]
    fraud_shap_top: List[FeatureImpact]

class ReviewRequest(BaseModel):
    human_decision: Literal["APPROVE", "REJECT"]
    comment: str = Field(..., min_length=3, max_length=500)
    reviewer_id: str = Field(..., min_length=2, max_length=64)

class ReviewResponse(BaseModel):
    decision_id: str
    previous_decision: DecisionType
    human_decision: Literal["APPROVE", "REJECT"]
    final_decision: DecisionType
    stored: bool
