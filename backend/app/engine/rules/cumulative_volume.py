from typing import Dict, Any
from app.engine.base import BaseRule, RuleResult
from app.engine.context import EvaluationContext


class DailyCumulativeVolumeRule(BaseRule):
    rule_id = "DAILY_CUMULATIVE_VOLUME"
    name = "Daily Cumulative Volume Spike"

    def evaluate(self, context: EvaluationContext, config: Dict[str, Any]) -> RuleResult:
        if not config.get("enabled", True):
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                triggered=False,
                score_impact=0,
                details={"reason": "rule_disabled"}
            )

        daily_limit = config.get("daily_limit", 150000.0)
        score_impact = config.get("score_impact", 30)

        past_24h_sum = sum(txn.amount for txn in context.recent_transactions_24h)
        projected_total = past_24h_sum + context.amount

        if projected_total >= daily_limit:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                triggered=True,
                score_impact=score_impact,
                details={
                    "past_24h_sum": round(past_24h_sum, 2),
                    "current_amount": round(context.amount, 2),
                    "projected_total": round(projected_total, 2),
                    "daily_limit": daily_limit,
                    "reason": f"Projected 24-hour volume {projected_total:.2f} exceeds allowable daily limit {daily_limit:.2f}"
                }
            )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            triggered=False,
            score_impact=0,
            details={"projected_total": projected_total, "daily_limit": daily_limit}
        )
