from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from .settings import settings

engine = create_engine(settings.database_url, connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Decision(Base):
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, index=True)
    decision_id = Column(String(64), unique=True, index=True, nullable=False)

    client_id_hash = Column(String(128), index=True, nullable=False)

    risk_score = Column(Float, nullable=False)
    fraud_score = Column(Float, nullable=False)
    decision = Column(String(16), nullable=False)
    policy_rule = Column(Text, nullable=False)

    model_versions = Column(JSON, nullable=False)
    explanations_preview = Column(JSON, nullable=False)

    request_payload = Column(JSON, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    reviews = relationship("Review", back_populates="decision", cascade="all, delete-orphan")

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    decision_id_fk = Column(Integer, ForeignKey("decisions.id"), nullable=False)

    reviewer_id = Column(String(64), nullable=False)
    human_decision = Column(String(16), nullable=False)  # APPROVE/REJECT
    comment = Column(Text, nullable=False)

    previous_decision = Column(String(16), nullable=False)
    final_decision = Column(String(16), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    decision = relationship("Decision", back_populates="reviews")

def init_db() -> None:
    Base.metadata.create_all(bind=engine)
