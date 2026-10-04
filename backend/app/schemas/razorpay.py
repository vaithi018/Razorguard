from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class RazorpayPaymentImportRequest(BaseModel):
    payment_id: str = Field(..., min_length=4, description="Razorpay payment ID (e.g., pay_test_123456)")
    # Optional entity fields if passing an already fetched/mocked Razorpay entity
    amount: Optional[float] = Field(None, description="Amount in paise (or INR if pre-normalized)")
    amount_inr: Optional[float] = Field(None, description="Explicit amount in INR")
    currency: Optional[str] = Field("INR", description="Currency code (e.g. INR)")
    status: Optional[str] = Field(None, description="Payment status: captured, authorized, failed, etc.")
    email: Optional[str] = Field(None, description="Customer email address")
    contact: Optional[str] = Field(None, description="Customer phone/contact")
    method: Optional[str] = Field("card", description="Payment method: card, upi, netbanking, wallet")
    order_id: Optional[str] = Field(None, description="Associated Razorpay order ID")
    card: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Card entity details")
    notes: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom notes metadata")


class RazorpayPaymentDetailResponse(BaseModel):
    payment_id: str
    amount_inr: float
    currency: str
    status: str
    method: str
    customer_email: Optional[str]
    customer_contact: Optional[str]
    order_id: Optional[str]
    is_ingested: bool
    internal_transaction_id: Optional[str] = None
    internal_decision: Optional[str] = None
    risk_score: Optional[int] = None
    risk_band: Optional[str] = None
    already_processed: bool = False
    details: Dict[str, Any] = {}
