from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel
from app.engine.context import EvaluationContext


class RuleResult(BaseModel):
    rule_id: str
    rule_name: str
    triggered: bool
    score_impact: int
    is_hard_block: bool = False
    details: Dict[str, Any] = {}


class BaseRule(ABC):
    rule_id: str
    name: str

    @abstractmethod
    def evaluate(self, context: EvaluationContext, config: Dict[str, Any]) -> RuleResult:
        """
        Evaluate context against deterministic logic using config parameters.
        Must return a RuleResult.
        """
        pass
