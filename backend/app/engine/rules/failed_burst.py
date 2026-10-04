from typing import Dict, Any
from app.engine.base import BaseRule, RuleResult
from app.engine.context import EvaluationContext


class FailedBurstRule(BaseRule):
    rule_id = "FAILED_BURST"
    name = "Burst of Failed Payments"

    def evaluate(self, context: EvaluationContext, config: Dict[str, Any]) -> RuleResult:
        if not config.get("enabled", True):
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                triggered=False,
                score_impact=0,
                details={"reason": "rule_disabled"}
            )

        failed_count = context.failed_transactions_15m_count
        threshold = config.get("threshold_failed_count", 3)
        score_impact = config.get("score_impact", 40)

        if failed_count >= threshold:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                triggered=True,
                score_impact=score_impact,
                details={
                    "failed_count": failed_count,
                    "threshold": threshold,
                    "window_minutes": config.get("window_minutes", 15),
                    "reason": f"Detected {failed_count} failed payment attempts in past 15 minutes (card testing pattern)"
                }
            )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            triggered=False,
            score_impact=0,
            details={"failed_count": failed_count, "threshold": threshold}
        )
