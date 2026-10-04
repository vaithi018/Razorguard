import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ReconciliationRecord(Base):
    __tablename__ = "reconciliation_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    transaction_id = Column(String(36), ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True, index=True)
    razorpay_payment_id = Column(String(64), unique=True, nullable=False, index=True)
    razorpay_status = Column(String(32), nullable=False)  # captured, authorized, failed, refunded
    internal_decision = Column(String(16), nullable=True)  # APPROVED, REVIEW, BLOCKED
    is_discrepant = Column(Boolean, nullable=False, default=False)
    discrepancy_type = Column(String(64), nullable=True)  # e.g., CAPTURED_BUT_BLOCKED, FAILED_BUT_APPROVED
    discrepancy_details = Column(JSON, nullable=True, default=dict)
    checked_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    transaction = relationship("Transaction", back_populates="reconciliation_record")
