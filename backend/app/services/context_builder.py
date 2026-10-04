from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from app.models.transaction import Transaction
from app.models.blocklist import Blocklist
from app.schemas.transaction import TransactionCreate
from app.engine.context import EvaluationContext, TransactionSnapshot


def build_evaluation_context(db: Session, txn_in: TransactionCreate) -> EvaluationContext:
    now = datetime.now(timezone.utc)
    ten_mins_ago = now - timedelta(minutes=10)
    fifteen_mins_ago = now - timedelta(minutes=15)
    twenty_four_hours_ago = now - timedelta(hours=24)

    # 1. Query 10-minute velocity window
    # Matches same customer_id OR same ip_address OR (if provided) same card_fingerprint
    velocity_query = db.query(Transaction).filter(
        Transaction.created_at >= ten_mins_ago,
        or_(
            Transaction.customer_id == txn_in.customer_id,
            Transaction.ip_address == txn_in.ip_address,
            (Transaction.card_fingerprint == txn_in.card_fingerprint) if txn_in.card_fingerprint else False
        )
    )
    recent_10m_records = velocity_query.all()
    snapshots_10m = [
        TransactionSnapshot(
            amount=t.amount,
            currency=t.currency,
            created_at=t.created_at,
            status=t.status,
            decision=t.decision
        )
        for t in recent_10m_records
    ]

    # 2. Query 24-hour cumulative volume for customer
    vol_query = db.query(Transaction).filter(
        Transaction.created_at >= twenty_four_hours_ago,
        Transaction.customer_id == txn_in.customer_id
    )
    recent_24h_records = vol_query.all()
    snapshots_24h = [
        TransactionSnapshot(
            amount=t.amount,
            currency=t.currency,
            created_at=t.created_at,
            status=t.status,
            decision=t.decision
        )
        for t in recent_24h_records
    ]

    # 3. Query failed transactions in last 15 minutes (Card testing / burst)
    failed_count = db.query(Transaction).filter(
        Transaction.created_at >= fifteen_mins_ago,
        Transaction.status == "FAILED",
        or_(
            Transaction.customer_id == txn_in.customer_id,
            Transaction.ip_address == txn_in.ip_address,
            (Transaction.card_fingerprint == txn_in.card_fingerprint) if txn_in.card_fingerprint else False
        )
    ).count()

    # 4. Seconds since last transaction
    last_txn = db.query(Transaction).filter(
        or_(
            Transaction.customer_id == txn_in.customer_id,
            Transaction.ip_address == txn_in.ip_address
        )
    ).order_by(desc(Transaction.created_at)).first()

    seconds_diff: Optional[float] = None
    if last_txn and last_txn.created_at:
        # Handle offset-naive vs aware comparison cleanly
        last_dt = last_txn.created_at
        if last_dt.tzinfo is None:
            last_dt = last_dt.replace(tzinfo=timezone.utc)
        seconds_diff = max(0.0, (now - last_dt).total_seconds())

    # 5. Check active negative list / blocklist
    identifiers = [txn_in.customer_email.lower(), txn_in.ip_address]
    if txn_in.card_fingerprint:
        identifiers.append(txn_in.card_fingerprint)
    if txn_in.customer_phone:
        identifiers.append(txn_in.customer_phone)

    block_record = db.query(Blocklist).filter(
        Blocklist.is_active == True,
        Blocklist.entity_value.in_(identifiers)
    ).first()

    is_blocked = block_record is not None
    block_reason = block_record.reason if block_record else None
    block_type = block_record.entity_type if block_record else None

    return EvaluationContext(
        amount=txn_in.amount,
        currency=txn_in.currency,
        customer_id=txn_in.customer_id,
        customer_email=txn_in.customer_email,
        ip_address=txn_in.ip_address,
        payment_method=txn_in.payment_method,
        card_fingerprint=txn_in.card_fingerprint,
        timestamp=now,
        recent_transactions_10m=snapshots_10m,
        recent_transactions_24h=snapshots_24h,
        failed_transactions_15m_count=failed_count,
        seconds_since_last_txn=seconds_diff,
        is_blocked=is_blocked,
        blocklist_reason=block_reason,
        blocklist_entity_type=block_type,
    )
