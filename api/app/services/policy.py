from dataclasses import dataclass
from ..settings import settings

@dataclass(frozen=True)
class PolicyResult:
    decision: str
    rule: str

def apply_policy(risk_score: float, fraud_score: float) -> PolicyResult:
    # La fraude est prioritaire : ALERT surcharge la décision de crédit
    if fraud_score >= settings.fraud_alert_threshold:
        return PolicyResult("ALERT", f"fraud_score >= {settings.fraud_alert_threshold} => ALERT")

    if risk_score >= settings.risk_reject_threshold:
        return PolicyResult("REJECT", f"risk_score >= {settings.risk_reject_threshold} => REJECT")

    if settings.risk_review_lower <= risk_score < settings.risk_review_upper:
        return PolicyResult(
            "REVIEW",
            f"risk_score in [{settings.risk_review_lower}, {settings.risk_review_upper}) => REVIEW (human-in-the-loop)",
        )

    return PolicyResult("ACCEPT", "otherwise => ACCEPT")
