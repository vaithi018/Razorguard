from fastapi import APIRouter
from app.api.v1.endpoints import health, transactions, analytics, rules, razorpay_sync

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(transactions.router)
api_router.include_router(analytics.router)
api_router.include_router(rules.router)
api_router.include_router(razorpay_sync.router)
