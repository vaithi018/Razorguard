from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog


def log_event(
    db: Session,
    entity_type: str,
    entity_id: str,
    action: str,
    actor_type: str = "SYSTEM",
    actor_id: str = "system",
    payload_snapshot: Optional[Dict[str, Any]] = None
) -> AuditLog:
    entry = AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor_type=actor_type,
        actor_id=actor_id,
        payload_snapshot=payload_snapshot or {},
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
