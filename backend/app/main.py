import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.database import init_db
from app.core.limiter import limiter
from app.api.v1.router import api_router

logger = logging.getLogger("razorguard.app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup safely
    try:
        init_db()
    except Exception as e:
        logger.error(f"Error initializing DB on startup: {e}", exc_info=True)
    yield


app = FastAPI(
    title="RazorGuard API",
    description="Deterministic Payment Risk Engine & AI Reconciliation Agent",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Connect Rate Limiter State
app.state.limiter = limiter

# SECURE CORS: Explicit origins from environment, wildcard '*' is forbidden with credentials
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
)


def _timestamp_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# Global Exception Handlers ensuring clean, non-leaking API errors
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "error": exc.detail,
            "timestamp": _timestamp_iso(),
        },
        headers=exc.headers or {},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Format human-readable validation error messages without leaking server internals
    error_messages = []
    for err in exc.errors():
        field = " -> ".join(str(loc) for loc in err.get("loc", []))
        msg = err.get("msg", "Invalid value")
        error_messages.append(f"{field}: {msg}")
    
    clean_error = "; ".join(error_messages)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "data": None,
            "error": f"Validation Error: {clean_error}",
            "timestamp": _timestamp_iso(),
        },
    )


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "success": False,
            "data": None,
            "error": "Rate limit exceeded. Too many requests. Please throttle your traffic.",
            "timestamp": _timestamp_iso(),
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Log internal error securely with stack trace to server logs only
    logger.error(f"Unhandled server error on {request.method} {request.url.path}: {exc}", exc_info=True)
    
    # Safe client message: Never leak tracebacks, API keys, or SQL errors to client
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "data": None,
            "error": "An internal server error occurred while processing the request. This event has been logged.",
            "timestamp": _timestamp_iso(),
        },
    )


app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def root():
    return {
        "service": "RazorGuard Payment Risk & Reconciliation Agent",
        "status": "online",
        "docs": "/docs" if settings.DEBUG else "disabled in production",
        "health": f"{settings.API_V1_PREFIX}/health",
    }
