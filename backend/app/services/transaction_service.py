import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, or_

from app.models.transaction import Transaction
from app.models.rule_evaluation import RuleEvaluation
from app.models.risk_assessment import RiskAssessment
from app.models.audit_log import AuditLog
from app.schemas.transaction import (
    TransactionCreate,
    TransactionSummary,
    TransactionDetail,
    RuleEvaluationSummary,
    AIEnrichmentSummary,
    AuditLogSummary,
    ManualReviewRequest,
)
from app.services.context_builder import build_evaluation_context
from app.engine.evaluator import rule_engine
from app.integrations.openai.client import enrich_transaction_risk
from app.services.audit_service import log_event


def process_transaction(db: Session, txn_in: TransactionCreate) -> TransactionDetail:
    # 1. Generate or format reference
    txn_ref = txn_in.transaction_ref or f"TXN_{uuid.uuid4().hex[:10].upper()}"

    # 2. Build stateful evaluation context from DB sliding windows
    context = build_evaluation_context(db, txn_in)

    # 3. Evaluate deterministic rules
    eval_result = rule_engine.evaluate(context)

    # 4. Create Transaction DB Record
    txn_db = Transaction(
        transaction_ref=txn_ref,
        amount=txn_in.amount,
        currency=txn_in.currency.upper(),
        customer_id=txn_in.customer_id,
        customer_email=txn_in.customer_email.lower(),
        customer_phone=txn_in.customer_phone,
        ip_address=txn_in.ip_address,
        payment_method=txn_in.payment_method.lower(),
        card_bin=txn_in.card_bin,
        card_last4=txn_in.card_last4,
        card_fingerprint=txn_in.card_fingerprint,
        decision=eval_result.decision,
        risk_score=eval_result.risk_score,
        status="FLAGGED" if eval_result.decision == "BLOCKED" else ("REVIEW" if eval_result.decision == "REVIEW" else "PROCESSED"),
        extra_metadata=txn_in.metadata or {},
    )
    db.add(txn_db)
    db.flush()  # assign txn_db.id

    # 5. Persist Rule Evaluation Records
    rule_summaries: List[RuleEvaluationSummary] = []
    for r in eval_result.all_evaluations:
        eval_record = RuleEvaluation(
            transaction_id=txn_db.id,
            rule_id=r.rule_id,
            rule_name=r.rule_name,
            triggered=r.triggered,
            score_impact=r.score_impact,
            rule_metadata=r.details,
            evaluated_at=datetime.now(timezone.utc),
        )
        db.add(eval_record)
        rule_summaries.append(
            RuleEvaluationSummary(
                rule_id=r.rule_id,
                rule_name=r.rule_name,
                triggered=r.triggered,
                score_impact=r.score_impact,
                is_hard_block=r.is_hard_block,
                details=r.details,
            )
        )

    # 6. Generate AI Risk Enrichment (Fail-safe, read-only)
    ai_enrichment_data = enrich_transaction_risk(
        decision=eval_result.decision,
        risk_score=eval_result.risk_score,
        triggered_rules=eval_result.triggered_rules,
        amount=txn_in.amount,
        currency=txn_in.currency.upper(),
        customer_id=txn_in.customer_id,
        customer_email=txn_in.customer_email.lower(),
        ip_address=txn_in.ip_address,
        payment_method=txn_in.payment_method.lower(),
    )

    assessment = RiskAssessment(
        transaction_id=txn_db.id,
        final_score=eval_result.risk_score,
        decision=eval_result.decision,
        ai_status=ai_enrichment_data.get("status", "COMPLETED"),
        ai_narrative=ai_enrichment_data.get("narrative"),
        ai_threat_vector=ai_enrichment_data.get("threat_vector"),
        ai_contributing_signals=ai_enrichment_data.get("contributing_signals", []),
        ai_investigation_steps=ai_enrichment_data.get("investigation_steps", []),
        ai_model=ai_enrichment_data.get("model"),
    )
    db.add(assessment)

    # 7. Write immutable audit log
    audit_entry = log_event(
        db=db,
        entity_type="TRANSACTION",
        entity_id=txn_db.id,
        action="EVALUATED",
        actor_type="SYSTEM",
        actor_id="deterministic_rule_engine",
        payload_snapshot={
            "transaction_ref": txn_ref,
            "decision": eval_result.decision,
            "risk_score": eval_result.risk_score,
            "rules_triggered": [r.rule_id for r in eval_result.triggered_rules],
            "ai_status": ai_enrichment_data.get("status"),
        }
    )

    db.commit()
    db.refresh(txn_db)

    ai_summary = AIEnrichmentSummary(
        status=assessment.ai_status,
        narrative=assessment.ai_narrative,
        threat_vector=assessment.ai_threat_vector,
        contributing_signals=assessment.ai_contributing_signals or [],
        investigation_steps=assessment.ai_investigation_steps or [],
        model=assessment.ai_model,
    )

    audit_summaries = [
        AuditLogSummary(
            id=audit_entry.id,
            action=audit_entry.action,
            actor_type=audit_entry.actor_type,
            actor_id=audit_entry.actor_id,
            payload_snapshot=audit_entry.payload_snapshot,
            timestamp=audit_entry.timestamp,
        )
    ]

    return TransactionDetail(
        id=txn_db.id,
        transaction_ref=txn_db.transaction_ref,
        amount=txn_db.amount,
        currency=txn_db.currency,
        customer_id=txn_db.customer_id,
        customer_email=txn_db.customer_email,
        customer_phone=txn_db.customer_phone,
        ip_address=txn_db.ip_address,
        payment_method=txn_db.payment_method,
        card_bin=txn_db.card_bin,
        card_last4=txn_db.card_last4,
        card_fingerprint=txn_db.card_fingerprint,
        decision=txn_db.decision,
        risk_score=txn_db.risk_score,
        status=txn_db.status,
        razorpay_payment_id=txn_db.razorpay_payment_id,
        razorpay_order_id=txn_db.razorpay_order_id,
        created_at=txn_db.created_at,
        updated_at=txn_db.updated_at,
        evaluations=rule_summaries,
        ai_enrichment=ai_summary,
        audit_logs=audit_summaries,
    )


def list_transactions(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    decision: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
) -> Tuple[List[TransactionSummary], int]:
    query = db.query(Transaction)

    if decision:
        query = query.filter(Transaction.decision == decision.upper())
    if status:
        query = query.filter(Transaction.status == status.upper())
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Transaction.transaction_ref.ilike(search_filter),
                Transaction.customer_email.ilike(search_filter),
                Transaction.customer_id.ilike(search_filter),
                Transaction.ip_address.ilike(search_filter),
            )
        )

    total_count = query.count()
    offset = (page - 1) * page_size
    records = query.order_by(desc(Transaction.created_at)).offset(offset).limit(page_size).all()

    summaries = []
    for r in records:
        triggered_cnt = db.query(RuleEvaluation).filter(
            RuleEvaluation.transaction_id == r.id,
            RuleEvaluation.triggered == True
        ).count()

        summaries.append(
            TransactionSummary(
                id=r.id,
                transaction_ref=r.transaction_ref,
                amount=r.amount,
                currency=r.currency,
                customer_id=r.customer_id,
                customer_email=r.customer_email,
                ip_address=r.ip_address,
                payment_method=r.payment_method,
                decision=r.decision,
                risk_score=r.risk_score,
                status=r.status,
                created_at=r.created_at,
                rules_triggered_count=triggered_cnt,
            )
        )

    return summaries, total_count


def get_transaction_detail(db: Session, transaction_id: str) -> Optional[TransactionDetail]:
    txn = db.query(Transaction).filter(
        or_(
            Transaction.id == transaction_id,
            Transaction.transaction_ref == transaction_id
        )
    ).first()

    if not txn:
        return None

    # Load evaluations
    evals = db.query(RuleEvaluation).filter(RuleEvaluation.transaction_id == txn.id).all()
    eval_summaries = [
        RuleEvaluationSummary(
            rule_id=e.rule_id,
            rule_name=e.rule_name,
            triggered=e.triggered,
            score_impact=e.score_impact,
            is_hard_block=(e.score_impact >= 100),
            details=e.rule_metadata or {},
        )
        for e in evals
    ]

    # Load risk assessment
    assessment = db.query(RiskAssessment).filter(RiskAssessment.transaction_id == txn.id).first()
    ai_summary = None
    if assessment:
        ai_summary = AIEnrichmentSummary(
            status=assessment.ai_status,
            narrative=assessment.ai_narrative,
            threat_vector=assessment.ai_threat_vector,
            contributing_signals=assessment.ai_contributing_signals or [],
            investigation_steps=assessment.ai_investigation_steps or [],
            model=assessment.ai_model,
        )

    # Load audit trail
    audits = db.query(AuditLog).filter(AuditLog.entity_id == txn.id).order_by(desc(AuditLog.timestamp)).all()
    audit_summaries = [
        AuditLogSummary(
            id=a.id,
            action=a.action,
            actor_type=a.actor_type,
            actor_id=a.actor_id,
            payload_snapshot=a.payload_snapshot,
            timestamp=a.timestamp,
        )
        for a in audits
    ]

    return TransactionDetail(
        id=txn.id,
        transaction_ref=txn.transaction_ref,
        amount=txn.amount,
        currency=txn.currency,
        customer_id=txn.customer_id,
        customer_email=txn.customer_email,
        customer_phone=txn.customer_phone,
        ip_address=txn.ip_address,
        payment_method=txn.payment_method,
        card_bin=txn.card_bin,
        card_last4=txn.card_last4,
        card_fingerprint=txn.card_fingerprint,
        decision=txn.decision,
        risk_score=txn.risk_score,
        status=txn.status,
        razorpay_payment_id=txn.razorpay_payment_id,
        razorpay_order_id=txn.razorpay_order_id,
        created_at=txn.created_at,
        updated_at=txn.updated_at,
        evaluations=eval_summaries,
        ai_enrichment=ai_summary,
        audit_logs=audit_summaries,
    )


def apply_manual_review(
    db: Session,
    transaction_id: str,
    review_in: ManualReviewRequest
) -> Optional[TransactionDetail]:
    txn = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not txn:
        return None

    prev_status = txn.status
    prev_decision = txn.decision

    if review_in.action == "FORCE_APPROVE":
        txn.decision = "APPROVED"
        txn.status = "MANUALLY_APPROVED"
    elif review_in.action == "CONFIRM_FRAUD":
        txn.decision = "BLOCKED"
        txn.status = "CONFIRMED_FRAUD"

    # Immutable audit logging
    log_event(
        db=db,
        entity_type="TRANSACTION",
        entity_id=txn.id,
        action=review_in.action,
        actor_type="ANALYST",
        actor_id=review_in.analyst_id,
        payload_snapshot={
            "previous_decision": prev_decision,
            "previous_status": prev_status,
            "new_decision": txn.decision,
            "new_status": txn.status,
            "reason": review_in.reason,
            "analyst_id": review_in.analyst_id,
        }
    )

    db.commit()
    db.refresh(txn)
    return get_transaction_detail(db, txn.id)
