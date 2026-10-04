from typing import Dict, Any
from app.engine.base import BaseRule, RuleResult
from app.engine.context import EvaluationContext


class VelocityRule(BaseRule):
    rule_id = "VELOCITY_10M"
    name = "High Velocity in 10-Minute Window"

    def evaluate(self, context: EvaluationContext, config: Dict[str, Any]) -> RuleResult:
        if not config.get("enabled", True):
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                triggered=False,
                score_impact=0,
                details={"reason": "rule_disabled"}
            )

        recent_count = len(context.recent_transactions_10m)
        tier_2_count = config.get("tier_2_count", 5)
        tier_2_score = config.get("tier_2_score", 50)
        tier_1_count = config.get("tier_1_count", 3)
        tier_1_score = config.get("tier_1_score", 25)

        if recent_count >= tier_2_count:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                triggered=True,
                score_impact=tier_2_score,
                details={
                    "count": recent_count,
                    "window_minutes": config.get("window_minutes", 10),
                    "threshold": tier_2_count,
                    "tier": "tier_2_velocity",
                    "reason": f"Detected {recent_count} transactions in the last 10 minutes (exceeds high velocity threshold of {tier_2_count})"
                }
            )
        elif recent_count >= tier_1_count:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                triggered=True,
                score_impact=tier_1_score,
                details={
                    "count": recent_count,
                    "window_minutes": config.get("window_minutes", 10),
                    "threshold": tier_1_count,
                    "tier": "tier_1_velocity",
                    "reason": f"Detected {recent_count} transactions in the last 10 minutes (exceeds velocity threshold of {tier_1_count})"
                }
            )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            triggered=False,
            score_impact=0,
            details={"count": recent_count, "threshold": tier_1_count}
        )
