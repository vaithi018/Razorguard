from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config import settings

# Global rate limiter using client IP address
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.RATE_LIMIT_INGESTION],
    storage_uri="memory://",
    strategy="fixed-window"
)
