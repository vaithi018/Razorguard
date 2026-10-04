from typing import Dict, Any
from app.engine.base import BaseRule, RuleResult
from app.engine.context import EvaluationContext


class BlocklistRule(BaseRule):
    rule_id = "BLOCKLIST"
    name = "Negative List / Previously Flagged Entity"

    def evaluate(self, context: EvaluationContext, config: Dict[str, Any]) -> RuleResult:
        if not config.get("enabled", True):
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                triggered=False,
                score_impact=0,
                details={"reason": "rule_disabled"}
            )

        if context.is_blocked:
            score_impact = config.get("score_impact", 100)
            is_hard_block = config.get("is_hard_block", True)
            return RuleResult(
                rule_id=self.rule_id,
                rule_name=self.name,
                triggered=True,
                score_impact=score_impact,
                is_hard_block=is_hard_block,
                details={
                    "entity_type": context.blocklist_entity_type,
                    "reason": context.blocklist_reason or "Customer, IP, or card fingerprint is actively blocklisted",
                    "hard_block": is_hard_block
                }
            )

        return RuleResult(
            rule_id=self.rule_id,
            rule_name=self.name,
            triggered=False,
            score_impact=0,
            details={"is_blocked": False}
        )
