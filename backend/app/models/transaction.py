import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, Boolean, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    transaction_ref = Column(String(64), unique=True, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="INR", nullable=False)
    customer_id = Column(String(64), nullable=False, index=True)
    customer_email = Column(String(255), nullable=False, index=True)
    customer_phone = Column(String(32), nullable=True)
    ip_address = Column(String(45), nullable=False, index=True)
    payment_method = Column(String(32), nullable=False, default="card")
    card_bin = Column(String(8), nullable=True)
    card_last4 = Column(String(4), nullable=True)
    card_fingerprint = Column(String(64), nullable=True, index=True)
    
    # Risk Decision Outcomes
    decision = Column(String(16), nullable=False, default="REVIEW")  # APPROVED, REVIEW, BLOCKED
    risk_score = Column(Integer, nullable=False, default=0)         # 0 - 100
    status = Column(String(32), nullable=False, default="PENDING")   # PENDING, PROCESSED, FLAGGED, REVERSED
    
    # Razorpay Integration fields
    razorpay_payment_id = Column(String(64), nullable=True, index=True)
    razorpay_order_id = Column(String(64), nullable=True, index=True)
    
    # Metadata dictionary for extensibility
    extra_metadata = Column(JSON, nullable=True, default=dict)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    rule_evaluations = relationship("RuleEvaluation", back_populates="transaction", cascade="all, delete-orphan")
    risk_assessment = relationship("RiskAssessment", back_populates="transaction", uselist=False, cascade="all, delete-orphan")
    reconciliation_record = relationship("ReconciliationRecord", back_populates="transaction", uselist=False)
