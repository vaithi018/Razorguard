import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, JSON, DateTime
from app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    entity_type = Column(String(32), nullable=False)  # TRANSACTION, RULE_CONFIG, BLOCKLIST
    entity_id = Column(String(64), nullable=False, index=True)
    action = Column(String(64), nullable=False)  # EVALUATED, MANUAL_APPROVED, MANUAL_BLOCKED, RULE_UPDATED, BLOCKLIST_ADDED
    actor_type = Column(String(32), nullable=False, default="SYSTEM")  # SYSTEM, ANALYST, ADMIN
    actor_id = Column(String(64), nullable=False, default="system")
    payload_snapshot = Column(JSON, nullable=True, default=dict)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
