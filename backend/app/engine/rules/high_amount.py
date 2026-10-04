from typing import Dict, Any
from app.engine.base import BaseRule, RuleResult
from app.engine.context import EvaluationContext


class HighAmountRule(BaseRule):
    rule_id = "HIGH_AMOUNT"
    name = "High Transaction Amount"

    def evaluate(self, context: EvaluationContext, config: Dict[str, Any]) -> RuleResult:
        if not config.get("enabled", True):
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                triggered=False,
                score_impact=0,
                details={"reason": "rule_disabled"}
            )

        amount = context.amount
        extreme_th = config.get("extreme_threshold", 300000.0)
        extreme_score = config.get("extreme_score", 75)
        tier_2_th = config.get("tier_2_threshold", 100000.0)
        tier_2_score = config.get("tier_2_score", 45)
        tier_1_th = config.get("tier_1_threshold", 50000.0)
        tier_1_score = config.get("tier_1_score", 25)

        if amount >= extreme_th:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                triggered=True,
                score_impact=extreme_score,
                details={
                    "amount": amount,
                    "tier": "extreme",
                    "threshold": extreme_th,
                    "reason": f"Amount {amount:.2f} exceeds extreme threshold {extreme_th:.2f}"
                }
            )
        elif amount >= tier_2_th:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                triggered=True,
                score_impact=tier_2_score,
                details={
                    "amount": amount,
                    "tier": "tier_2",
                    "threshold": tier_2_th,
                    "reason": f"Amount {amount:.2f} exceeds tier 2 threshold {tier_2_th:.2f}"
                }
            )
        elif amount >= tier_1_th:
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                triggered=True,
                score_impact=tier_1_score,
                details={
                    "amount": amount,
                    "tier": "tier_1",
                    "threshold": tier_1_th,
                    "reason": f"Amount {amount:.2f} exceeds tier 1 threshold {tier_1_th:.2f}"
                }
            )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            triggered=False,
            score_impact=0,
            details={"amount": amount, "threshold": tier_1_th}
        )
