import hashlib
from datetime import datetime
from sqlalchemy.orm import Session
from ..db import Decision
from ..settings import settings

def hash_client_id(client_id: str) -> str:
    # Pseudonymisation pour le RGPD : ne pas stocker les identifiants clients bruts
    msg = (settings.client_id_salt + "|" + client_id).encode("utf-8")
    return hashlib.sha256(msg).hexdigest()

def build_decision_id() -> str:
    # ID simple unique ; peut être remplacé par un UUID plus tard
    now = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
    return f"dcn_{now}"

def store_decision(
    db: Session,
    *,
    decision_id: str,
    client_id_hash: str,
    risk_score: float,
    fraud_score: float,
    decision: str,
    policy_rule: str,
    model_versions: dict,
    explanations_preview: dict,
    request_payload: dict,
) -> Decision:
    row = Decision(
        decision_id=decision_id,
        client_id_hash=client_id_hash,
        risk_score=risk_score,
        fraud_score=fraud_score,
        decision=decision,
        policy_rule=policy_rule,
        model_versions=model_versions,
        explanations_preview=explanations_preview,
        request_payload=request_payload,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
