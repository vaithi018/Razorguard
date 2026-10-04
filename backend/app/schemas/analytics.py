from typing import Dict, List, Any
from pydantic import BaseModel


class RiskScoreDistribution(BaseModel):
    range_0_19: int = 0
    range_20_39: int = 0
    range_40_59: int = 0
    range_60_79: int = 0
    range_80_100: int = 0


class TopTriggeredRule(BaseModel):
    rule_id: str
    rule_name: str
    count: int


class DashboardMetrics(BaseModel):
    total_transactions: int
    approved_count: int
    review_count: int
    blocked_count: int
    approval_rate_percent: float
    average_risk_score: float
    total_volume_inr: float
    risk_distribution: RiskScoreDistribution
    top_triggered_rules: List[TopTriggeredRule]
