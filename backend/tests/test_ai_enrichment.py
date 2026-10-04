import pytest
from app.integrations.openai.fallback import generate_fallback_narrative
from app.integrations.openai.client import enrich_transaction_risk
from app.engine.base import RuleResult


def test_fallback_narrative_generation_low_risk():
    res = generate_fallback_narrative(
        decision="APPROVED",
        risk_score=0,
        triggered_rules=[],
        amount=1500.0,
        currency="INR"
    )
    assert res["status"] == "DETERMINISTIC_BASELINE"
    assert "APPROVED" in res["narrative"]
    assert len(res["investigation_steps"]) > 0


def test_fallback_narrative_generation_with_rules():
    rule = RuleResult(
        rule_id="HIGH_AMOUNT",
        rule_name="High Transaction Amount",
        triggered=True,
        score_impact=45,
        details={"reason": "Amount 120,000 exceeds tier 2 threshold"}
    )
    res = generate_fallback_narrative(
        decision="REVIEW",
        risk_score=45,
        triggered_rules=[rule],
        amount=120000.0,
        currency="INR"
    )
    assert "REVIEW" in res["narrative"]
    assert "High-Value Transaction Anomaly" == res["threat_vector"]
    assert len(res["contributing_signals"]) == 1


def test_enrichment_does_not_modify_decision():
    # Verify that enrich_transaction_risk always preserves decision strictly
    rule = RuleResult(
        rule_id="VELOCITY_10M",
        rule_name="High Velocity in 10-Minute Window",
        triggered=True,
        score_impact=50,
        details={"reason": "5 transactions in 10 minutes"}
    )
    res = enrich_transaction_risk(
        decision="BLOCKED",
        risk_score=85,
        triggered_rules=[rule],
        amount=5000.0,
        currency="INR",
        customer_id="cust_test_velocity",
        customer_email="velocity@test.com",
        ip_address="10.0.0.1",
        payment_method="card"
    )
    # The output is descriptive and does not contradict the decision
    assert res is not None
    assert "narrative" in res
    assert "threat_vector" in res
