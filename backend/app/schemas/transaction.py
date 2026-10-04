from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime


class TransactionCreate(BaseModel):
    transaction_ref: Optional[str] = Field(None, description="Unique transaction reference ID")
    amount: float = Field(..., gt=0, description="Transaction amount (must be positive)")
    currency: str = Field("INR", min_length=3, max_length=3, description="Currency code (e.g., INR, USD)")
    customer_id: str = Field(..., min_length=1, description="Unique customer identifier")
    customer_email: EmailStr = Field(..., description="Customer email address")
    customer_phone: Optional[str] = Field(None, description="Customer phone number")
    ip_address: str = Field(..., description="Client IP address")
    payment_method: str = Field("card", description="Payment method: card, upi, netbanking, etc.")
    card_bin: Optional[str] = Field(None, max_length=8, description="First 6 digits of card")
    card_last4: Optional[str] = Field(None, max_length=4, description="Last 4 digits of card")
    card_fingerprint: Optional[str] = Field(None, description="SHA-256 card fingerprint")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom metadata attributes")


class RuleEvaluationSummary(BaseModel):
    rule_id: str
    rule_name: str
    triggered: bool
    score_impact: int
    is_hard_block: bool
    details: Dict[str, Any]


class AIEnrichmentSummary(BaseModel):
    status: str
    narrative: Optional[str] = None
    threat_vector: Optional[str] = None
    contributing_signals: List[str] = []
    investigation_steps: List[str] = []
    model: Optional[str] = None


class AuditLogSummary(BaseModel):
    id: str
    action: str
    actor_type: str
    actor_id: str
    payload_snapshot: Optional[Dict[str, Any]] = None
    timestamp: datetime


class TransactionSummary(BaseModel):
    id: str
    transaction_ref: str
    amount: float
    currency: str
    customer_id: str
    customer_email: str
    ip_address: str
    payment_method: str
    decision: str
    risk_score: int
    status: str
    created_at: datetime
    rules_triggered_count: int = 0


class TransactionDetail(BaseModel):
    id: str
    transaction_ref: str
    amount: float
    currency: str
    customer_id: str
    customer_email: str
    customer_phone: Optional[str]
    ip_address: str
    payment_method: str
    card_bin: Optional[str]
    card_last4: Optional[str]
    card_fingerprint: Optional[str]
    decision: str
    risk_score: int
    status: str
    razorpay_payment_id: Optional[str]
    razorpay_order_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    evaluations: List[RuleEvaluationSummary]
    ai_enrichment: Optional[AIEnrichmentSummary]
    audit_logs: List[AuditLogSummary]


class ManualReviewRequest(BaseModel):
    action: str = Field(..., pattern="^(FORCE_APPROVE|CONFIRM_FRAUD)$", description="FORCE_APPROVE or CONFIRM_FRAUD")
    reason: str = Field(..., min_length=5, description="Auditable justification for the override")
    analyst_id: str = Field("analyst_01", description="ID of the reviewing analyst")


class SimulationScenario(BaseModel):
    scenario_id: str
    name: str
    description: str
    payload: TransactionCreate
