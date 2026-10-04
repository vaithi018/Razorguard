import pytest
from datetime import datetime, timezone
from app.engine.context import EvaluationContext, TransactionSnapshot
from app.engine.evaluator import rule_engine, DeterministicRuleEngine


def test_clean_low_risk_transaction():
    context = EvaluationContext(
        amount=1500.0,
        currency="INR",
        customer_id="cust_clean_01",
        customer_email="clean_user@example.com",
        ip_address="49.204.10.12",
        payment_method="card",
        recent_transactions_10m=[],
        recent_transactions_24h=[],
        failed_transactions_15m_count=0,
        seconds_since_last_txn=None,
        is_blocked=False,
    )
    res = rule_engine.evaluate(context)
    assert res.decision == "APPROVED"
    assert res.risk_band == "LOW"
    assert res.risk_score == 0
    assert len(res.triggered_rules) == 0


def test_high_amount_tier_1_yields_approved_or_medium():
    # 55,000 INR triggers HIGH_AMOUNT tier 1 (+25 points) -> Score 25 < 40 -> APPROVED
    context = EvaluationContext(
        amount=55000.0,
        currency="INR",
        customer_id="cust_high_01",
        customer_email="buyer@example.com",
        ip_address="49.204.10.12",
        payment_method="card",
    )
    res = rule_engine.evaluate(context)
    assert res.risk_score == 25
    assert res.decision == "APPROVED"
    assert any(r.rule_id == "HIGH_AMOUNT" for r in res.triggered_rules)


def test_high_amount_tier_2_yields_review():
    # 120,000 INR triggers HIGH_AMOUNT tier 2 (+45 points) -> Score 45 (between 40 and 70) -> REVIEW
    context = EvaluationContext(
        amount=120000.0,
        currency="INR",
        customer_id="cust_high_02",
        customer_email="buyer2@example.com",
        ip_address="49.204.10.12",
        payment_method="card",
    )
    res = rule_engine.evaluate(context)
    assert res.risk_score == 45
    assert res.decision == "REVIEW"
    assert res.risk_band == "MEDIUM"


def test_extreme_amount_yields_blocked():
    # 350,000 INR triggers HIGH_AMOUNT extreme tier (+75 points) -> Score 75 >= 70 -> BLOCKED
    context = EvaluationContext(
        amount=350000.0,
        currency="INR",
        customer_id="cust_whale_01",
        customer_email="whale@example.com",
        ip_address="49.204.10.12",
        payment_method="card",
    )
    res = rule_engine.evaluate(context)
    # 350,000 triggers HIGH_AMOUNT (+75) and DAILY_CUMULATIVE_VOLUME (+30) -> capped at 100 -> BLOCKED
    assert res.risk_score == 100
    assert res.decision == "BLOCKED"
    assert res.risk_band == "HIGH"
    rule_ids = [r.rule_id for r in res.triggered_rules]
    assert "HIGH_AMOUNT" in rule_ids
    assert "DAILY_CUMULATIVE_VOLUME" in rule_ids


def test_velocity_combined_with_amount():
    # Amount 60,000 (+25) + 3 txns in 10m (+25) = 50 -> REVIEW
    recent_txns = [
        TransactionSnapshot(amount=1000.0, currency="INR", created_at=datetime.now(timezone.utc), status="PROCESSED", decision="APPROVED"),
        TransactionSnapshot(amount=2000.0, currency="INR", created_at=datetime.now(timezone.utc), status="PROCESSED", decision="APPROVED"),
        TransactionSnapshot(amount=1500.0, currency="INR", created_at=datetime.now(timezone.utc), status="PROCESSED", decision="APPROVED"),
    ]
    context = EvaluationContext(
        amount=60000.0,
        currency="INR",
        customer_id="cust_fast_01",
        customer_email="fast@example.com",
        ip_address="103.22.45.12",
        payment_method="card",
        recent_transactions_10m=recent_txns,
    )
    res = rule_engine.evaluate(context)
    assert res.risk_score == 50
    assert res.decision == "REVIEW"
    rule_ids = [r.rule_id for r in res.triggered_rules]
    assert "HIGH_AMOUNT" in rule_ids
    assert "VELOCITY_10M" in rule_ids


def test_rapid_succession_and_failed_burst():
    # Failed burst (+40) + Rapid succession (+35) = 75 -> BLOCKED
    context = EvaluationContext(
        amount=500.0,
        currency="INR",
        customer_id="cust_bot_01",
        customer_email="card_tester@suspicious.com",
        ip_address="198.51.100.22",
        payment_method="card",
        failed_transactions_15m_count=3,
        seconds_since_last_txn=12.5,
    )
    res = rule_engine.evaluate(context)
    assert res.risk_score == 75
    assert res.decision == "BLOCKED"
    rule_ids = [r.rule_id for r in res.triggered_rules]
    assert "FAILED_BURST" in rule_ids
    assert "RAPID_SUCCESSION" in rule_ids


def test_blocklist_hard_block():
    # Entity is actively on negative list -> Instant 100 score & BLOCKED
    context = EvaluationContext(
        amount=100.0,
        currency="INR",
        customer_id="bad_actor_99",
        customer_email="fraudster@stolen.com",
        ip_address="198.51.100.5",
        payment_method="card",
        is_blocked=True,
        blocklist_reason="Known chargeback fraudster syndicate",
        blocklist_entity_type="EMAIL",
    )
    res = rule_engine.evaluate(context)
    assert res.risk_score == 100
    assert res.decision == "BLOCKED"
    assert any(r.rule_id == "BLOCKLIST" and r.is_hard_block for r in res.triggered_rules)
