from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_analyst_auth, AnalystIdentity
from app.schemas.common import StandardResponse
from app.schemas.rules import RulesConfigResponse, RulesConfigUpdate
from app.engine.evaluator import rule_engine
from app.services.audit_service import log_event

router = APIRouter(prefix="/rules", tags=["Rules Configuration"])


@router.get("", response_model=StandardResponse[RulesConfigResponse])
def get_rule_configuration():
    return StandardResponse(
        success=True,
        data=RulesConfigResponse(
            thresholds=rule_engine.config.get("thresholds", {}),
            rules=rule_engine.config.get("rules", {})
        )
    )


@router.put("/config", response_model=StandardResponse[RulesConfigResponse])
def update_rule_configuration(
    config_in: RulesConfigUpdate,
    analyst: AnalystIdentity = Depends(require_analyst_auth),
    db: Session = Depends(get_db)
):
    new_data = {
        "thresholds": config_in.thresholds,
        "rules": config_in.rules,
    }
    rule_engine.update_config(new_data)

    # Immutable audit logging for rule modification attributing authenticated actor
    log_event(
        db=db,
        entity_type="RULE_CONFIG",
        entity_id="global_rules_config",
        action="RULE_UPDATED",
        actor_type="ANALYST",
        actor_id=analyst.id,
        payload_snapshot=new_data
    )

    return StandardResponse(
        success=True,
        data=RulesConfigResponse(
            thresholds=rule_engine.config.get("thresholds", {}),
            rules=rule_engine.config.get("rules", {})
        )
    )
