from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import SessionLocal, Decision, Review
from ..schemas import ReviewRequest, ReviewResponse

router = APIRouter(tags=["review"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def map_human_to_final(previous_decision: str, human_decision: str) -> str:
    # Mapping simple pour le MVP :
    # - APPROVE humain transforme REVIEW en ACCEPT
    # - REJECT humain transforme REVIEW en REJECT
    # - Pour les autres décisions, garder la précédente sauf si on veut surcharger partout.
    if previous_decision == "REVIEW":
        return "ACCEPT" if human_decision == "APPROVE" else "REJECT"
    return previous_decision

@router.post("/review/{decision_id}", response_model=ReviewResponse)
def review(decision_id: str, payload: ReviewRequest, db: Session = Depends(get_db)):
    row = db.query(Decision).filter(Decision.decision_id == decision_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="decision_id not found")

    prev = row.decision
    final = map_human_to_final(prev, payload.human_decision)

    review_row = Review(
        decision_id_fk=row.id,
        reviewer_id=payload.reviewer_id,
        human_decision=payload.human_decision,
        comment=payload.comment,
        previous_decision=prev,
        final_decision=final,
    )
    db.add(review_row)

    # Stocker la décision finale tout en préservant la trace originale (audit)
    row.decision = final
    db.commit()

    return ReviewResponse(
        decision_id=row.decision_id,
        previous_decision=prev,
        human_decision=payload.human_decision,
        final_decision=final,
        stored=True,
    )
