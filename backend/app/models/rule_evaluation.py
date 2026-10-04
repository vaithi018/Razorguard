import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RuleEvaluation(Base):
    __tablename__ = "rule_evaluations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    transaction_id = Column(String(36), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_id = Column(String(64), nullable=False)
    rule_name = Column(String(128), nullable=False)
    triggered = Column(Boolean, nullable=False, default=False)
    score_impact = Column(Integer, nullable=False, default=0)
    rule_metadata = Column(JSON, nullable=True, default=dict)
    evaluated_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    transaction = relationship("Transaction", back_populates="rule_evaluations")
