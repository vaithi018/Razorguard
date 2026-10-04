from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TransactionSnapshot:
    amount: float
    currency: str
    created_at: datetime
    status: str
    decision: str


@dataclass
class EvaluationContext:
    # Current transaction under evaluation
    amount: float
    currency: str
    customer_id: str
    customer_email: str
    ip_address: str
    payment_method: str
    card_fingerprint: Optional[str] = None
    timestamp: Optional[datetime] = None

    # Historical context gathered from DB
    recent_transactions_10m: List[TransactionSnapshot] = field(default_factory=list)
    recent_transactions_24h: List[TransactionSnapshot] = field(default_factory=list)
    failed_transactions_15m_count: int = 0
    seconds_since_last_txn: Optional[float] = None
    
    # Blocklist lookup outcomes
    is_blocked: bool = False
    blocklist_reason: Optional[str] = None
    blocklist_entity_type: Optional[str] = None
