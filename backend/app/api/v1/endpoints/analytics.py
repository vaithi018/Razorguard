from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.common import StandardResponse
from app.schemas.analytics import DashboardMetrics
from app.services.analytics_service import get_dashboard_metrics

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/metrics", response_model=StandardResponse[DashboardMetrics])
def get_metrics(db: Session = Depends(get_db)):
    metrics = get_dashboard_metrics(db)
    return StandardResponse(success=True, data=metrics)
