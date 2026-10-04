from typing import Dict, Any
from datetime import datetime, timezone
from app.engine.base import BaseRule, RuleResult
from app.engine.context import EvaluationContext


class UnusualHoursRule(BaseRule):
    rule_id = "UNUSUAL_HOURS"
    name = "High Amount at Unusual Nocturnal Hours"

    def evaluate(self, context: EvaluationContext, config: Dict[str, Any]) -> RuleResult:
        if not config.get("enabled", True):
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                triggered=False,
                score_impact=0,
                details={"reason": "rule_disabled"}
            )

        start_hour = config.get("start_hour", 1)  # 01:00
        end_hour = config.get("end_hour", 5)      # 05:00
        min_amount = config.get("min_amount", 20000.0)
        score_impact = config.get("score_impact", 15)

        txn_time = context.timestamp or datetime.now(timezone.utc)
        hour = txn_time.hour

        is_nocturnal = (start_hour <= hour <= end_hour) if start_hour <= end_hour else (hour >= start_hour or hour <= end_hour)

        if is_nocturnal and context.amount >= min_amount:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                triggered=True,
                score_impact=score_impact,
                details={
                    "hour": hour,
                    "amount": context.amount,
                    "min_amount": min_amount,
                    "reason": f"High value transaction ({context.amount:.2f}) initiated during unusual hours ({hour:02d}:00 UTC)"
                }
            )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            triggered=False,
            score_impact=0,
            details={"hour": hour, "is_nocturnal": is_nocturnal}
        )
