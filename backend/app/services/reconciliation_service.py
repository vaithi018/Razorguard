from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.reconciliation import ReconciliationRecord
from app.models.transaction import Transaction
from app.integrations.razorpay.client import razorpay_client
from app.schemas.transaction import TransactionCreate
from app.services.transaction_service import process_transaction
from app.services.audit_service import log_event


def reconcile_payment(
    db: Session,
    razorpay_payment_id: str,
    razorpay_status: str,
    amount_in_rupees: float,
    currency: str,
    customer_email: str,
    customer_contact: Optional[str] = None,
    method: str = "card",
    order_id: Optional[str] = None
) -> ReconciliationRecord:
    # 1. Check if we already have this transaction recorded
    txn = db.query(Transaction).filter(
        (Transaction.razorpay_payment_id == razorpay_payment_id) |
        (Transaction.transaction_ref == razorpay_payment_id)
    ).first()

    # 2. If not yet recorded, run through Risk Engine
    if not txn:
        txn_create = TransactionCreate(
            transaction_ref=razorpay_payment_id,
            amount=amount_in_rupees,
            currency=currency.upper(),
            customer_id=f"cust_rzp_{customer_email.split('@')[0]}",
            customer_email=customer_email or "unknown@test.com",
            customer_phone=customer_contact,
            ip_address="127.0.0.1",
            payment_method=method or "card",
            metadata={"source": "razorpay_sync", "order_id": order_id}
        )
        detail = process_transaction(db, txn_create)
        txn = db.query(Transaction).filter(Transaction.id == detail.id).first()
        txn.razorpay_payment_id = razorpay_payment_id
        txn.razorpay_order_id = order_id
        db.commit()
        db.refresh(txn)

    # 3. Detect Discrepancies
    is_discrepant = False
    discrepancy_type = None
    discrepancy_details = {}

    internal_decision = txn.decision
    rp_status = razorpay_status.lower()

    if rp_status in ["captured", "authorized"] and internal_decision == "BLOCKED":
        is_discrepant = True
        discrepancy_type = "CAPTURED_BUT_BLOCKED"
        discrepancy_details = {
            "severity": "CRITICAL",
            "message": "Payment was captured by Razorpay but deterministic rules determined BLOCKED.",
            "recommended_action": "Initiate immediate test refund via Razorpay."
        }
    elif rp_status in ["captured", "authorized"] and internal_decision == "REVIEW":
        is_discrepant = True
        discrepancy_type = "CAPTURED_UNDER_REVIEW"
        discrepancy_details = {
            "severity": "WARNING",
            "message": "Payment captured, but transaction is flagged for manual review.",
            "recommended_action": "Hold settlement or order dispatch until analyst approval."
        }
    elif rp_status == "failed" and internal_decision == "APPROVED":
        is_discrepant = True
        discrepancy_type = "GATEWAY_FAILED_INTERNAL_APPROVED"
        discrepancy_details = {
            "severity": "INFO",
            "message": "Internal risk engine approved, but payment failed at payment gateway.",
            "recommended_action": "Customer may retry transaction."
        }

    # 4. Upsert Reconciliation Record
    rec = db.query(ReconciliationRecord).filter(
        ReconciliationRecord.razorpay_payment_id == razorpay_payment_id
    ).first()

    if not rec:
        rec = ReconciliationRecord(
            transaction_id=txn.id if txn else None,
            razorpay_payment_id=razorpay_payment_id,
            razorpay_status=razorpay_status,
            internal_decision=internal_decision,
            is_discrepant=is_discrepant,
            discrepancy_type=discrepancy_type,
            discrepancy_details=discrepancy_details,
            checked_at=datetime.now(timezone.utc),
        )
        db.add(rec)
    else:
        rec.razorpay_status = razorpay_status
        rec.internal_decision = internal_decision
        rec.is_discrepant = is_discrepant
        rec.discrepancy_type = discrepancy_type
        rec.discrepancy_details = discrepancy_details
        rec.checked_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(rec)

    # Log audit event if discrepant
    if is_discrepant:
        log_event(
            db=db,
            entity_type="RECONCILIATION",
            entity_id=rec.id,
            action=f"DISCREPANCY_DETECTED_{discrepancy_type}",
            actor_type="SYSTEM",
            actor_id="reconciliation_agent",
            payload_snapshot=discrepancy_details
        )

    return rec


def list_reconciliation_records(db: Session, page: int = 1, page_size: int = 20):
    query = db.query(ReconciliationRecord).order_by(desc(ReconciliationRecord.checked_at))
    total = query.count()
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()
    return items, total
