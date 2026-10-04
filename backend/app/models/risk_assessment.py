import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    transaction_id = Column(String(36), ForeignKey("transactions.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    final_score = Column(Integer, nullable=False)
    decision = Column(String(16), nullable=False)  # APPROVED, REVIEW, BLOCKED
    
    # AI Enrichment fields (Strictly narrative/insights, never decision)
    ai_status = Column(String(32), nullable=False, default="PENDING")  # PENDING, COMPLETED, FALLBACK, SKIPPED, FAILED
    ai_narrative = Column(Text, nullable=True)
    ai_threat_vector = Column(String(64), nullable=True)
    ai_contributing_signals = Column(JSON, nullable=True, default=list)
    ai_investigation_steps = Column(JSON, nullable=True, default=list)
    ai_model = Column(String(64), nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    transaction = relationship("Transaction", back_populates="risk_assessment")
