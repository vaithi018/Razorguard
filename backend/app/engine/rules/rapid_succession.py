from typing import Dict, Any
from app.engine.base import BaseRule, RuleResult
from app.engine.context import EvaluationContext


class RapidSuccessionRule(BaseRule):
    rule_id = "RAPID_SUCCESSION"
    name = "Rapid Succession Transaction (<30s)"

    def evaluate(self, context: EvaluationContext, config: Dict[str, Any]) -> RuleResult:
        if not config.get("enabled", True):
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                triggered=False,
                score_impact=0,
                details={"reason": "rule_disabled"}
            )

        seconds = context.seconds_since_last_txn
        threshold = config.get("seconds_threshold", 30)
        score_impact = config.get("score_impact", 35)

        if seconds is not None and seconds < threshold:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                triggered=True,
                score_impact=score_impact,
                details={
                    "seconds_since_last_txn": round(seconds, 1),
                    "threshold_seconds": threshold,
                    "reason": f"Transaction initiated only {seconds:.1f}s after previous transaction (automated bot/script suspected)"
                }
            )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            triggered=False,
            score_impact=0,
            details={"seconds_since_last_txn": seconds}
        )
