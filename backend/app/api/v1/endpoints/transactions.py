from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.core.limiter import limiter
from app.core.security import require_analyst_auth, AnalystIdentity
from app.schemas.common import StandardResponse
from app.schemas.transaction import (
    TransactionCreate,
    TransactionSummary,
    TransactionDetail,
    ManualReviewRequest,
    SimulationScenario,
)
from app.services.transaction_service import (
    process_transaction,
    list_transactions,
    get_transaction_detail,
    apply_manual_review,
)

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("", response_model=StandardResponse[TransactionDetail], status_code=status.HTTP_201_CREATED)
@limiter.limit(lambda: settings.RATE_LIMIT_INGESTION)
def create_transaction(request: Request, txn_in: TransactionCreate, db: Session = Depends(get_db)):
    detail = process_transaction(db, txn_in)
    return StandardResponse(success=True, data=detail)


@router.get("", response_model=StandardResponse[Dict[str, Any]])
def get_transactions_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    decision: Optional[str] = Query(None, description="APPROVED, REVIEW, or BLOCKED"),
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None, description="Search by ref, email, or customer ID"),
    db: Session = Depends(get_db),
):
    items, total = list_transactions(
        db=db,
        page=page,
        page_size=page_size,
        decision=decision,
        status=status_filter,
        search=search,
    )
    return StandardResponse(
        success=True,
        data={
            "items": [item.model_dump() for item in items],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total > 0 else 0,
        },
    )


@router.get("/{transaction_id}", response_model=StandardResponse[TransactionDetail])
def get_transaction_by_id(transaction_id: str, db: Session = Depends(get_db)):
    detail = get_transaction_detail(db, transaction_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return StandardResponse(success=True, data=detail)


@router.post("/{transaction_id}/review-action", response_model=StandardResponse[TransactionDetail])
def manual_review_action(
    transaction_id: str,
    review_in: ManualReviewRequest,
    analyst: AnalystIdentity = Depends(require_analyst_auth),
    db: Session = Depends(get_db),
):
    # Pass authenticated analyst ID to ensure attribution integrity
    review_in.analyst_id = analyst.id
    updated = apply_manual_review(db, transaction_id, review_in)
    if not updated:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return StandardResponse(success=True, data=updated)


@router.post("/simulate", response_model=StandardResponse[TransactionDetail])
@limiter.limit(lambda: settings.RATE_LIMIT_SIMULATE)
def simulate_scenario(
    request: Request,
    scenario_key: str = Query("clean", description="clean, high_amount, velocity, card_testing, or blocklist"),
    db: Session = Depends(get_db)
):
    scenarios = {
        "clean": TransactionCreate(
            amount=2500.0,
            currency="INR",
            customer_id="cust_retail_101",
            customer_email="priya.sharma@example.com",
            customer_phone="+919811223344",
            ip_address="106.51.34.88",
            payment_method="upi",
            card_bin=None,
            card_last4=None,
        ),
        "high_amount": TransactionCreate(
            amount=125000.0,
            currency="INR",
            customer_id="cust_vip_402",
            customer_email="vikram.patel@corporate.in",
            ip_address="14.139.128.5",
            payment_method="card",
            card_bin="438628",
            card_last4="8821",
            card_fingerprint="fp_hash_77a912b4",
        ),
        "velocity": TransactionCreate(
            amount=45000.0,
            currency="INR",
            customer_id="cust_spammer_9",
            customer_email="fast.orders@mailinator.com",
            ip_address="185.220.101.5",
            payment_method="card",
            card_bin="411111",
            card_last4="1111",
            card_fingerprint="fp_hash_rapid_velocity_01",
        ),
        "card_testing": TransactionCreate(
            amount=50.0,
            currency="INR",
            customer_id="cust_bot_test_88",
            customer_email="tester99@burnermail.org",
            ip_address="198.51.100.99",
            payment_method="card",
            card_bin="520082",
            card_last4="9012",
            card_fingerprint="fp_hash_bot_script_99",
        ),
        "blocklist": TransactionCreate(
            amount=15000.0,
            currency="INR",
            customer_id="cust_bad_actor_01",
            customer_email="fraud.syndicate@badactors.com",
            ip_address="198.51.100.4",
            payment_method="card",
            card_fingerprint="fp_hash_stolen_card_blacklisted",
        ),
    }

    selected = scenarios.get(scenario_key.lower())
    if not selected:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown scenario '{scenario_key}'. Choose from: {list(scenarios.keys())}"
        )

    detail = process_transaction(db, selected)
    return StandardResponse(success=True, data=detail)
