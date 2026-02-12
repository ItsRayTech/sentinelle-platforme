from typing import Optional, List, Literal
from pydantic import BaseModel

DecisionType = Literal["ACCEPT", "REVIEW", "REJECT", "ALERT"]

class FeatureImpact(BaseModel):
    feature: str
    impact: str

class AgentRequest(BaseModel):
    decision: DecisionType
    risk_score: float
    fraud_score: float
    policy_rule: str
    model_versions: dict
    explanations_preview: dict
    # optional small context
    locale: Optional[str] = "fr"

class AgentResponse(BaseModel):
    report_summary: str
