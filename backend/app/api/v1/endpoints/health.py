from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from app.core.config import settings
from app.schemas.common import StandardResponse
from app.schemas.health import HealthStatus

router = APIRouter()


@router.get("/health", response_model=StandardResponse[HealthStatus])
def get_health(db: Session = Depends(get_db)):
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    openai_ready = bool(settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.strip())
    razorpay_ready = bool(settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET)

    components = {
        "database": db_status,
        "rule_engine": "operational",
        "openai_enrichment": "configured" if openai_ready else "fallback_mode_only",
        "razorpay_test_client": "configured" if razorpay_ready else "mock_mode_only",
    }

    overall_status = "healthy" if db_status == "ok" else "degraded"

    health_data = HealthStatus(
        status=overall_status,
        version="1.0.0",
        environment=settings.ENVIRONMENT,
        database=settings.DATABASE_URL.split("///")[0],
        openai_configured=openai_ready,
        razorpay_configured=razorpay_ready,
        components=components,
    )

    return StandardResponse(success=True, data=health_data)
