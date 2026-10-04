import logging
import hashlib
from typing import Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionDetail
from app.schemas.razorpay import RazorpayPaymentImportRequest, RazorpayPaymentDetailResponse
from app.services.transaction_service import process_transaction, get_transaction_detail
from app.services.reconciliation_service import reconcile_payment
from app.services.audit_service import log_event
from app.integrations.razorpay.client import (
    razorpay_client,
    RazorpayIntegrationError,
    RazorpayPaymentNotFoundError,
    RazorpayConfigError,
)

logger = logging.getLogger("razorguard.razorpay_service")


def normalize_razorpay_payment(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes a Razorpay payment entity into internal standard fields.
    Razorpay amounts are in paise (e.g. 50000 paise = 500.00 INR).
    """
    payment_id = raw_data.get("id") or raw_data.get("payment_id")
    if raw_data.get("amount_inr") is not None:
        amount_inr = round(float(raw_data["amount_inr"]), 2)
    else:
        raw_amount = raw_data.get("amount", 0.0)
        # Convert paise to INR (Razorpay standard is integer paise)
        if isinstance(raw_amount, int) or raw_amount > 500:
            amount_inr = round(float(raw_amount) / 100.0, 2)
        else:
            amount_inr = round(float(raw_amount), 2)

    currency = (raw_data.get("currency") or "INR").upper()
    status_val = (raw_data.get("status") or "captured").lower()
    email = raw_data.get("email") or "shopper@test.com"
    contact = raw_data.get("contact")
    method = (raw_data.get("method") or "card").lower()
    order_id = raw_data.get("order_id")

    # Card attributes
    card_info = raw_data.get("card") or {}
    card_last4 = card_info.get("last4")
    card_network = card_info.get("network")
    card_type = card_info.get("type")

    # Extract or generate pseudo-fingerprint for card testing/velocity detection
    card_fingerprint = None
    if card_last4 and card_network:
        fp_raw = f"{card_network}_{card_type}_{card_last4}"
        card_fingerprint = f"fp_rzp_{hashlib.sha256(fp_raw.encode()).hexdigest()[:16]}"

    return {
        "payment_id": payment_id,
        "amount_inr": amount_inr,
        "currency": currency,
        "status": status_val,
        "email": email,
        "contact": contact,
        "method": method,
        "order_id": order_id,
        "card_last4": card_last4,
        "card_fingerprint": card_fingerprint,
        "raw_entity": raw_data,
    }


def ingest_razorpay_payment(
    db: Session,
    import_req: RazorpayPaymentImportRequest,
    client_ip: str = "127.0.0.1"
) -> Tuple[TransactionDetail, bool, Dict[str, Any]]:
    """
    Ingests a Razorpay Test Mode payment through the deterministic risk engine.
    
    Idempotency:
    If the payment was already processed, returns the existing transaction and decision
    without re-evaluating or creating duplicates.
    """
    payment_id = import_req.payment_id.strip()

    # 1. Idempotency Check: Look for existing transaction with this Razorpay payment ID
    existing_txn = db.query(Transaction).filter(
        (Transaction.razorpay_payment_id == payment_id) |
        (Transaction.transaction_ref == f"RZP_{payment_id}")
    ).first()

    if existing_txn:
        logger.info(f"Idempotent match: Payment {payment_id} already ingested as {existing_txn.id}")
        detail = get_transaction_detail(db, existing_txn.id)
        
        # Log idempotent query in audit trail
        log_event(
            db=db,
            entity_type="TRANSACTION",
            entity_id=existing_txn.id,
            action="IDEMPOTENT_PAYMENT_ACCESSED",
            actor_type="SYSTEM",
            actor_id="razorpay_ingestor",
            payload_snapshot={"razorpay_payment_id": payment_id, "decision": existing_txn.decision}
        )
        return detail, True, {"payment_id": payment_id, "amount_inr": existing_txn.amount}

    # 2. Retrieve payment data: If full payload not passed, fetch from Razorpay Test API
    raw_data: Dict[str, Any] = {}
    if (import_req.amount is not None or import_req.amount_inr is not None) and import_req.email is not None:
        raw_data = {
            "id": payment_id,
            "amount": import_req.amount,
            "amount_inr": import_req.amount_inr,
            "currency": import_req.currency,
            "status": import_req.status or "captured",
            "email": import_req.email,
            "contact": import_req.contact,
            "method": import_req.method,
            "order_id": import_req.order_id,
            "card": import_req.card or {},
            "notes": import_req.notes or {},
        }
    else:
        # Fetch directly from Razorpay Test Mode SDK
        raw_data = razorpay_client.fetch_payment_by_id(payment_id)

    # 3. Normalize into standard RazorGuard attributes
    normalized = normalize_razorpay_payment(raw_data)

    # 4. Construct internal TransactionCreate model
    txn_in = TransactionCreate(
        transaction_ref=f"RZP_{payment_id}",
        amount=normalized["amount_inr"],
        currency=normalized["currency"],
        customer_id=f"cust_rzp_{normalized['email'].split('@')[0]}",
        customer_email=normalized["email"],
        customer_phone=normalized["contact"],
        ip_address=client_ip,
        payment_method=normalized["method"],
        card_last4=normalized["card_last4"],
        card_fingerprint=normalized["card_fingerprint"],
        metadata={
            "source": "razorpay_test_mode",
            "razorpay_payment_id": payment_id,
            "razorpay_order_id": normalized["order_id"],
            "gateway_status": normalized["status"],
        }
    )

    # 5. Execute Deterministic Risk Engine Pipeline
    # Razorpay Test Payment -> Validation -> Deterministic Risk Engine -> Decision
    detail = process_transaction(db, txn_in)

    # Link Razorpay payment ID and order ID explicitly on the transaction record
    txn_db = db.query(Transaction).filter(Transaction.id == detail.id).first()
    if txn_db:
        txn_db.razorpay_payment_id = payment_id
        txn_db.razorpay_order_id = normalized["order_id"]
        db.commit()
        db.refresh(txn_db)

    # 6. Reconcile with Razorpay gateway status
    reconcile_payment(
        db=db,
        razorpay_payment_id=payment_id,
        razorpay_status=normalized["status"],
        amount_in_rupees=normalized["amount_inr"],
        currency=normalized["currency"],
        customer_email=normalized["email"],
        customer_contact=normalized["contact"],
        method=normalized["method"],
        order_id=normalized["order_id"],
    )

    # 7. Append audit log
    log_event(
        db=db,
        entity_type="TRANSACTION",
        entity_id=detail.id,
        action="RAZORPAY_PAYMENT_INGESTED",
        actor_type="SYSTEM",
        actor_id="razorpay_agent",
        payload_snapshot={
            "razorpay_payment_id": payment_id,
            "gateway_status": normalized["status"],
            "decision": detail.decision,
            "risk_score": detail.risk_score,
        }
    )

    return detail, False, normalized
