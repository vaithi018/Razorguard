from typing import List, Dict, Any
from app.engine.base import RuleResult


def generate_fallback_narrative(
    decision: str,
    risk_score: int,
    triggered_rules: List[RuleResult],
    amount: float,
    currency: str
) -> Dict[str, Any]:
    if not triggered_rules:
        return {
            "status": "DETERMINISTIC_BASELINE",
            "narrative": f"Transaction evaluated as {decision} with a baseline risk score of {risk_score}/100. No anomalous velocity or fraud pattern rules were triggered.",
            "threat_vector": "Standard Transaction",
            "contributing_signals": ["All fraud signals within acceptable thresholds"],
            "investigation_steps": ["No manual intervention required. Proceed with standard processing."],
            "model": "deterministic-rules-engine"
        }

    rule_names = [r.rule_name for r in triggered_rules]
    signals = []
    investigations = []

    # Map threat vector
    rule_ids = {r.rule_id for r in triggered_rules}
    if "BLOCKLIST" in rule_ids:
        threat_vector = "Negative List Match / Known Bad Actor"
        investigations.append("Confirm blocklist identifier match with compliance watchlist.")
        investigations.append("Deny transaction and notify fraud prevention team.")
    elif "RAPID_SUCCESSION" in rule_ids or "FAILED_BURST" in rule_ids:
        threat_vector = "Card Testing / Automated Script Attack"
        investigations.append("Inspect IP cluster and user-agent headers for bot signatures.")
        investigations.append("Review recent payment failure error codes on Razorpay.")
    elif "VELOCITY_10M" in rule_ids or "DAILY_CUMULATIVE_VOLUME" in rule_ids:
        threat_vector = "Velocity Burst / Account Takeover"
        investigations.append("Review customer recent order cadence and payment instrument changes.")
        investigations.append("Verify customer identity via secondary confirmation if reviewing.")
    elif "HIGH_AMOUNT" in rule_ids:
        threat_vector = "High-Value Transaction Anomaly"
        investigations.append("Cross-check transaction amount against customer historical spend.")
        investigations.append("Ensure 3D Secure / OTP authorization completed successfully.")
    else:
        threat_vector = "Heuristic Anomaly"
        investigations.append("Review rule execution details in transaction audit trail.")

    for r in triggered_rules:
        detail_msg = r.details.get("reason", f"Triggered {r.rule_name} (+{r.score_impact} pts)")
        signals.append(detail_msg)

    narrative = (
        f"Transaction evaluated as {decision} (Risk Score: {risk_score}/100). "
        f"Key risk triggers identified: {', '.join(rule_names)}. "
        f"Enforced deterministically by rule engine."
    )

    return {
        "status": "DETERMINISTIC_BASELINE",
        "narrative": narrative,
        "threat_vector": threat_vector,
        "contributing_signals": signals,
        "investigation_steps": investigations,
        "model": "deterministic-rules-engine"
    }
