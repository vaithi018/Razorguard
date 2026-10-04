import json
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI
from app.core.config import settings
from app.engine.base import RuleResult
from app.integrations.openai.fallback import generate_fallback_narrative

logger = logging.getLogger("razorguard.ai")


def enrich_transaction_risk(
    decision: str,
    risk_score: int,
    triggered_rules: List[RuleResult],
    amount: float,
    currency: str,
    customer_id: str,
    customer_email: str,
    ip_address: str,
    payment_method: str
) -> Dict[str, Any]:
    """
    Enriches transaction with AI narrative using OpenAI gpt-4o-mini.
    Guaranteed fail-safe: Falls back seamlessly to deterministic templates
    if OpenAI API key is missing, invalid, times out, or errors.
    The AI NEVER controls or alters the decision.
    """
    # 1. Fallback if no key or enrichment disabled
    if not settings.AI_ENRICHMENT_ENABLED or not settings.OPENAI_API_KEY or not settings.OPENAI_API_KEY.strip():
        return generate_fallback_narrative(decision, risk_score, triggered_rules, amount, currency)

    try:
        client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=settings.AI_TIMEOUT_SECONDS
        )

        rule_summaries = [
            {
                "rule_id": r.rule_id,
                "rule_name": r.rule_name,
                "score_impact": r.score_impact,
                "details": r.details
            }
            for r in triggered_rules
        ]

        system_prompt = (
            "You are RazorGuard AI, an expert fintech risk & compliance analyst. "
            "A deterministic rule engine has ALREADY finalized the risk score and decision for this transaction. "
            "You CANNOT and MUST NOT alter, override, or question the decision. "
            "Your sole objective is to explain the risk context to a human fraud analyst. "
            "Respond ONLY with a valid JSON object matching the following structure:\n"
            "{\n"
            '  "narrative": "Concise 2-3 sentence executive summary explaining the risk factors",\n'
            '  "threat_vector": "Primary fraud/risk classification category",\n'
            '  "contributing_signals": ["Signal 1", "Signal 2"],\n'
            '  "investigation_steps": ["Actionable step 1 for human analyst", "Actionable step 2"]\n'
            "}"
        )

        user_content = {
            "transaction": {
                "amount": amount,
                "currency": currency,
                "customer_id": customer_id,
                "customer_email": customer_email,
                "ip_address": ip_address,
                "payment_method": payment_method,
            },
            "deterministic_outcome": {
                "decision": decision,
                "risk_score": risk_score,
                "rules_triggered": rule_summaries
            }
        }

        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_content)}
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=300
        )

        raw_output = response.choices[0].message.content
        parsed = json.loads(raw_output)

        return {
            "status": "COMPLETED",
            "narrative": parsed.get("narrative", ""),
            "threat_vector": parsed.get("threat_vector", "Standard Evaluation"),
            "contributing_signals": parsed.get("contributing_signals", []),
            "investigation_steps": parsed.get("investigation_steps", []),
            "model": settings.OPENAI_MODEL
        }

    except Exception as exc:
        logger.warning(f"OpenAI enrichment failed or timed out: {exc}. Using deterministic fallback.")
        fallback = generate_fallback_narrative(decision, risk_score, triggered_rules, amount, currency)
        fallback["status"] = "FALLBACK_ON_ERROR"
        fallback["fallback_reason"] = str(exc)
        return fallback
