import json
import os
from typing import Dict, Any, List
from pydantic import BaseModel
from app.engine.base import BaseRule, RuleResult
from app.engine.context import EvaluationContext
from app.engine.rules.blocklist import BlocklistRule
from app.engine.rules.high_amount import HighAmountRule
from app.engine.rules.velocity import VelocityRule
from app.engine.rules.rapid_succession import RapidSuccessionRule
from app.engine.rules.failed_burst import FailedBurstRule
from app.engine.rules.cumulative_volume import DailyCumulativeVolumeRule
from app.engine.rules.unusual_hours import UnusualHoursRule


class EngineEvaluationResult(BaseModel):
    decision: str  # APPROVED, REVIEW, BLOCKED
    risk_score: int  # 0 to 100
    risk_band: str  # LOW, MEDIUM, HIGH
    triggered_rules: List[RuleResult]
    all_evaluations: List[RuleResult]


class DeterministicRuleEngine:
    def __init__(self, config_path: str = None):
        if config_path is None:
            # Default to backend/config/rules_config.json
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_path = os.path.join(base_dir, "config", "rules_config.json")
        
        self.config_path = config_path
        self.config = self._load_config()
        self.rules: List[BaseRule] = [
            BlocklistRule(),
            HighAmountRule(),
            VelocityRule(),
            RapidSuccessionRule(),
            FailedBurstRule(),
            DailyCumulativeVolumeRule(),
            UnusualHoursRule(),
        ]

    def _load_config(self) -> Dict[str, Any]:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Hardcoded safe fallback defaults if file missing
        return {
            "thresholds": {"review_min_score": 40, "blocked_min_score": 70},
            "rules": {}
        }

    def reload_config(self):
        self.config = self._load_config()

    def update_config(self, new_config: Dict[str, Any]):
        self.config = new_config
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(new_config, f, indent=2)
        except Exception:
            pass

    def evaluate(self, context: EvaluationContext) -> EngineEvaluationResult:
        rule_configs = self.config.get("rules", {})
        thresholds = self.config.get("thresholds", {})
        review_min = thresholds.get("review_min_score", 40)
        blocked_min = thresholds.get("blocked_min_score", 70)

        all_evaluations: List[RuleResult] = []
        triggered_rules: List[RuleResult] = []
        hard_block_triggered = False

        for rule in self.rules:
            r_cfg = rule_configs.get(rule.rule_id, {})
            result = rule.evaluate(context, r_cfg)
            all_evaluations.append(result)

            if result.triggered:
                triggered_rules.append(result)
                if result.is_hard_block:
                    hard_block_triggered = True

        if hard_block_triggered:
            return EngineEvaluationResult(
                decision="BLOCKED",
                risk_score=100,
                risk_band="HIGH",
                triggered_rules=triggered_rules,
                all_evaluations=all_evaluations,
            )

        # Additive scoring model bounded [0, 100]
        raw_score = sum(r.score_impact for r in triggered_rules)
        final_score = min(100, max(0, raw_score))

        # Deterministic mapping to decisions
        if final_score >= blocked_min:
            decision = "BLOCKED"
            risk_band = "HIGH"
        elif final_score >= review_min:
            decision = "REVIEW"
            risk_band = "MEDIUM"
        else:
            decision = "APPROVED"
            risk_band = "LOW"

        return EngineEvaluationResult(
            decision=decision,
            risk_score=final_score,
            risk_band=risk_band,
            triggered_rules=triggered_rules,
            all_evaluations=all_evaluations,
        )


# Global singleton instance
rule_engine = DeterministicRuleEngine()
