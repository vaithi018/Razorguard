import uuid
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.core.limiter import limiter
from app.schemas.common import StandardResponse
from app.schemas.transaction import TransactionDetail
from app.schemas.razorpay import (
    RazorpayPaymentImportRequest,
    RazorpayPaymentDetailResponse,
)
from app.integrations.razorpay.client import (
    razorpay_client,
    RazorpayIntegrationError,
    RazorpayPaymentNotFoundError,
    RazorpayInvalidPaymentIdError,
    RazorpayConfigError,
    RazorpayAuthError,
    RazorpayTimeoutError,
    RazorpayLiveCredentialProhibitedError,
)
from app.services.razorpay_ingestion_service import (
    ingest_razorpay_payment,
    normalize_razorpay_payment,
)
from app.services.reconciliation_service import (
    reconcile_payment,
    list_reconciliation_records,
)
from app.models.transaction import Transaction

logger = logging.getLogger("razorguard.razorpay_api")

router = APIRouter(prefix="/integrations/razorpay", tags=["Razorpay Integration"])


@router.post("/payments", response_model=StandardResponse[Dict[str, Any]], status_code=status.HTTP_200_OK)
@limiter.limit(lambda: settings.RATE_LIMIT_INGESTION)
def import_and_evaluate_payment(
    request: Request,
    import_in: RazorpayPaymentImportRequest,
    db: Session = Depends(get_db)
):
    """
    Ingests and normalizes a Razorpay Test Mode payment, passes it to the
    deterministic risk rule engine, creates an immutable audit record, and
    returns the transaction + risk decision.
    
    Idempotency:
    If the same payment ID is posted again, returns the already-processed record
    without duplicating transactions or altering scores.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"

    if not import_in.payment_id or not import_in.payment_id.strip():
        raise HTTPException(status_code=400, detail="A valid Razorpay payment ID is required.")

    try:
        detail, already_processed, normalized = ingest_razorpay_payment(
            db=db,
            import_req=import_in,
            client_ip=client_ip
        )
        return StandardResponse(
            success=True,
            data={
                "transaction": detail.model_dump(),
                "already_processed": already_processed,
                "payment_id": import_in.payment_id.strip(),
                "normalized_summary": {
                    "amount_inr": normalized.get("amount_inr"),
                    "status": normalized.get("status"),
                    "method": normalized.get("method"),
                    "email": normalized.get("email"),
                },
                "decision": detail.decision,
                "risk_score": detail.risk_score,
            }
        )
    except RazorpayLiveCredentialProhibitedError as e:
        raise HTTPException(status_code=403, detail=e.message)
    except RazorpayPaymentNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except RazorpayInvalidPaymentIdError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except RazorpayAuthError as e:
        raise HTTPException(status_code=401, detail=e.message)
    except RazorpayTimeoutError as e:
        raise HTTPException(status_code=504, detail=e.message)
    except RazorpayConfigError as e:
        raise HTTPException(status_code=503, detail=e.message)
    except RazorpayIntegrationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Error ingesting Razorpay payment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error ingesting Razorpay payment.")


@router.get("/payments/{payment_id}", response_model=StandardResponse[RazorpayPaymentDetailResponse])
def get_razorpay_payment(payment_id: str, db: Session = Depends(get_db)):
    """
    Retrieves a Razorpay Test Mode payment by ID.
    Returns normalized payment details and checks whether it has been ingested
    and evaluated by RazorGuard's risk engine. Never exposes secret keys.
    """
    clean_id = (payment_id or "").strip()
    if not clean_id:
        raise HTTPException(status_code=400, detail="A valid Razorpay payment ID is required.")

    # Check if already processed in our database
    existing_txn = db.query(Transaction).filter(
        (Transaction.razorpay_payment_id == clean_id) |
        (Transaction.transaction_ref == f"RZP_{clean_id}")
    ).first()

    try:
        raw_payment = razorpay_client.fetch_payment_by_id(clean_id)
        normalized = normalize_razorpay_payment(raw_payment)

        resp_data = RazorpayPaymentDetailResponse(
            payment_id=clean_id,
            amount_inr=normalized["amount_inr"],
            currency=normalized["currency"],
            status=normalized["status"],
            method=normalized["method"],
            customer_email=normalized["email"],
            customer_contact=normalized["contact"],
            order_id=normalized["order_id"],
            is_ingested=existing_txn is not None,
            internal_transaction_id=existing_txn.id if existing_txn else None,
            internal_decision=existing_txn.decision if existing_txn else None,
            risk_score=existing_txn.risk_score if existing_txn else None,
            details={
                "captured": normalized["status"] == "captured",
                "card_last4": normalized["card_last4"],
            }
        )

        return StandardResponse(success=True, data=resp_data)
    except RazorpayConfigError as e:
        # If Razorpay keys are not configured but transaction was already ingested locally, return local record
        if existing_txn:
            resp_data = RazorpayPaymentDetailResponse(
                payment_id=clean_id,
                amount_inr=existing_txn.amount,
                currency=existing_txn.currency,
                status="captured" if existing_txn.status in ["PROCESSED", "captured"] else existing_txn.status.lower(),
                method=existing_txn.payment_method,
                customer_email=existing_txn.customer_email,
                customer_contact=existing_txn.customer_phone,
                order_id=existing_txn.razorpay_order_id,
                is_ingested=True,
                internal_transaction_id=existing_txn.id,
                internal_decision=existing_txn.decision,
                risk_score=existing_txn.risk_score,
                details={
                    "captured": existing_txn.status in ["PROCESSED", "captured"],
                    "card_last4": existing_txn.card_last4,
                }
            )
            return StandardResponse(success=True, data=resp_data)
        raise HTTPException(status_code=503, detail=e.message)
    except RazorpayLiveCredentialProhibitedError as e:
        raise HTTPException(status_code=403, detail=e.message)
    except RazorpayPaymentNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except RazorpayInvalidPaymentIdError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except RazorpayAuthError as e:
        raise HTTPException(status_code=401, detail=e.message)
    except RazorpayTimeoutError as e:
        raise HTTPException(status_code=504, detail=e.message)
    except RazorpayConfigError as e:
        raise HTTPException(status_code=503, detail=e.message)
    except RazorpayIntegrationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Error retrieving Razorpay payment {clean_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error retrieving Razorpay payment.")


@router.post("/orders", response_model=StandardResponse[Dict[str, Any]])
def create_test_order(order_in: Dict[str, Any]):
    amount = float(order_in.get("amount", 1000.0))
    currency = order_in.get("currency", "INR")
    receipt = order_in.get("receipt")
    order_data = razorpay_client.create_order(
        amount_in_rupees=amount,
        currency=currency,
        receipt=receipt,
    )
    return StandardResponse(success=True, data=order_data)


@router.post("/webhook")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    raw_body = await request.body()
    
    # If a signature is present and webhook secret is set, verify HMAC
    if settings.RAZORPAY_WEBHOOK_SECRET and x_razorpay_signature:
        is_valid = razorpay_client.verify_webhook_signature(raw_body, x_razorpay_signature)
        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid Razorpay webhook signature")

    payload = await request.json()
    event = payload.get("event")
    payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})

    if payment_entity:
        payment_id = payment_entity.get("id")
        amount_paise = payment_entity.get("amount", 0)
        amount_inr = amount_paise / 100.0
        status_val = payment_entity.get("status", "unknown")
        email = payment_entity.get("email", "unknown@test.com")
        contact = payment_entity.get("contact")
        method = payment_entity.get("method", "card")
        order_id = payment_entity.get("order_id")

        reconcile_payment(
            db=db,
            razorpay_payment_id=payment_id,
            razorpay_status=status_val,
            amount_in_rupees=amount_inr,
            currency="INR",
            customer_email=email,
            customer_contact=contact,
            method=method,
            order_id=order_id,
        )

    return {"status": "ok", "event_processed": event}


@router.post("/simulate-test-payment", response_model=StandardResponse[Dict[str, Any]])
def simulate_test_payment(sim_in: Dict[str, Any], db: Session = Depends(get_db)):
    pid = sim_in.get("payment_id") or f"pay_test_{uuid.uuid4().hex[:12]}"
    rec = reconcile_payment(
        db=db,
        razorpay_payment_id=pid,
        razorpay_status=sim_in.get("status", "captured"),
        amount_in_rupees=float(sim_in.get("amount", 1000.0)),
        currency=sim_in.get("currency", "INR"),
        customer_email=sim_in.get("customer_email", "shopper@test.com"),
        customer_contact=sim_in.get("customer_contact"),
        method=sim_in.get("method", "card"),
        order_id=sim_in.get("order_id"),
    )
    return StandardResponse(
        success=True,
        data={
            "reconciliation_id": rec.id,
            "razorpay_payment_id": rec.razorpay_payment_id,
            "razorpay_status": rec.razorpay_status,
            "internal_decision": rec.internal_decision,
            "is_discrepant": rec.is_discrepant,
            "discrepancy_type": rec.discrepancy_type,
            "discrepancy_details": rec.discrepancy_details,
            "checked_at": rec.checked_at.isoformat() if rec.checked_at else None,
        }
    )


@router.get("/reconciliation", response_model=StandardResponse[Dict[str, Any]])
def get_reconciliation_list(page: int = 1, page_size: int = 20, db: Session = Depends(get_db)):
    items, total = list_reconciliation_records(db, page, page_size)
    formatted = [
        {
            "id": r.id,
            "transaction_id": r.transaction_id,
            "razorpay_payment_id": r.razorpay_payment_id,
            "razorpay_status": r.razorpay_status,
            "internal_decision": r.internal_decision,
            "is_discrepant": r.is_discrepant,
            "discrepancy_type": r.discrepancy_type,
            "discrepancy_details": r.discrepancy_details,
            "checked_at": r.checked_at.isoformat() if r.checked_at else None,
        }
        for r in items
    ]
    return StandardResponse(
        success=True,
        data={"items": formatted, "total": total, "page": page, "page_size": page_size}
    )
