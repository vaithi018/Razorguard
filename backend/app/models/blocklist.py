import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Text, DateTime
from app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Blocklist(Base):
    __tablename__ = "customers_blocklist"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    entity_type = Column(String(32), nullable=False)  # EMAIL, IP, CARD_FINGERPRINT, PHONE
    entity_value = Column(String(255), nullable=False, index=True)
    reason = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    added_by = Column(String(64), nullable=False, default="admin")
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
