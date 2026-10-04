from typing import Dict
from pydantic import BaseModel


class HealthStatus(BaseModel):
    status: str
    version: str
    environment: str
    database: str
    openai_configured: bool
    razorpay_configured: bool
    components: Dict[str, str]
