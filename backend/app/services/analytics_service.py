from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.transaction import Transaction
from app.models.rule_evaluation import RuleEvaluation
from app.schemas.analytics import DashboardMetrics, RiskScoreDistribution, TopTriggeredRule


def get_dashboard_metrics(db: Session) -> DashboardMetrics:
    total_txns = db.query(Transaction).count()
    if total_txns == 0:
        return DashboardMetrics(
            total_transactions=0,
            approved_count=0,
            review_count=0,
            blocked_count=0,
            approval_rate_percent=0.0,
            average_risk_score=0.0,
            total_volume_inr=0.0,
            risk_distribution=RiskScoreDistribution(),
            top_triggered_rules=[],
        )

    approved = db.query(Transaction).filter(Transaction.decision == "APPROVED").count()
    review = db.query(Transaction).filter(Transaction.decision == "REVIEW").count()
    blocked = db.query(Transaction).filter(Transaction.decision == "BLOCKED").count()

    avg_score = db.query(func.avg(Transaction.risk_score)).scalar() or 0.0
    total_vol = db.query(func.sum(Transaction.amount)).scalar() or 0.0
    approval_rate = round((approved / total_txns) * 100, 1)

    # Risk Distribution buckets
    d_0_19 = db.query(Transaction).filter(Transaction.risk_score >= 0, Transaction.risk_score < 20).count()
    d_20_39 = db.query(Transaction).filter(Transaction.risk_score >= 20, Transaction.risk_score < 40).count()
    d_40_59 = db.query(Transaction).filter(Transaction.risk_score >= 40, Transaction.risk_score < 60).count()
    d_60_79 = db.query(Transaction).filter(Transaction.risk_score >= 60, Transaction.risk_score < 80).count()
    d_80_100 = db.query(Transaction).filter(Transaction.risk_score >= 80, Transaction.risk_score <= 100).count()

    dist = RiskScoreDistribution(
        range_0_19=d_0_19,
        range_20_39=d_20_39,
        range_40_59=d_40_59,
        range_60_79=d_60_79,
        range_80_100=d_80_100,
    )

    # Top triggered rules
    rule_counts = (
        db.query(
            RuleEvaluation.rule_id,
            RuleEvaluation.rule_name,
            func.count(RuleEvaluation.id).label("count")
        )
        .filter(RuleEvaluation.triggered == True)
        .group_by(RuleEvaluation.rule_id, RuleEvaluation.rule_name)
        .order_by(func.count(RuleEvaluation.id).desc())
        .limit(5)
        .all()
    )

    top_rules = [
        TopTriggeredRule(rule_id=r.rule_id, rule_name=r.rule_name, count=r.count)
        for r in rule_counts
    ]

    return DashboardMetrics(
        total_transactions=total_txns,
        approved_count=approved,
        review_count=review,
        blocked_count=blocked,
        approval_rate_percent=approval_rate,
        average_risk_score=round(avg_score, 1),
        total_volume_inr=round(total_vol, 2),
        risk_distribution=dist,
        top_triggered_rules=top_rules,
    )
