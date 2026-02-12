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
    # Simple mapping for MVP:
    # - Human APPROVE turns REVIEW into ACCEPT
    # - Human REJECT turns REVIEW into REJECT
    # - For other previous decisions, keep previous unless you want overrides everywhere.
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

    # Store final decision while preserving original trace (audit)
    row.decision = final
    db.commit()

    return ReviewResponse(
        decision_id=row.decision_id,
        previous_decision=prev,
        human_decision=payload.human_decision,
        final_decision=final,
        stored=True,
    )
