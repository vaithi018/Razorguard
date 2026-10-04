import os
import secrets
import logging
from typing import Optional, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("razorguard.config")


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Secret Key: Loaded strictly from environment, never hardcoded.
    # In production, must be explicitly provided.
    SECRET_KEY: Optional[str] = None

    # CORS: Allowed origins list as comma-separated string from environment
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Database: Default SQLite (/tmp on Vercel Serverless), swappable for PostgreSQL
    DATABASE_URL: str = (
        "sqlite:////tmp/razorguard.db" if os.environ.get("VERCEL") else "sqlite:///./razorguard.db"
    )

    # OpenAI Configuration (Enrichment only)
    OPENAI_API_KEY: Optional[str] = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    AI_ENRICHMENT_ENABLED: bool = True
    AI_TIMEOUT_SECONDS: float = 3.0

    # Razorpay Test Mode
    RAZORPAY_KEY_ID: Optional[str] = ""
    RAZORPAY_KEY_SECRET: Optional[str] = ""
    RAZORPAY_WEBHOOK_SECRET: Optional[str] = ""

    # Risk Score Mapping Thresholds
    RISK_THRESHOLD_REVIEW: int = 40
    RISK_THRESHOLD_BLOCKED: int = 70

    # Rate Limiting
    RATE_LIMIT_INGESTION: str = "60/minute"
    RATE_LIMIT_SIMULATE: str = "120/minute"

    # Authentication & Access Control
    # Analyst API Key for administrative/override endpoints
    ANALYST_API_KEY: Optional[str] = None
    REQUIRE_AUTH_FOR_SENSITIVE_ACTIONS: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins(self) -> List[str]:
        """Parse comma-separated origins, stripping whitespace and filtering wildcards."""
        raw_origins = [orig.strip() for orig in self.ALLOWED_ORIGINS.split(",") if orig.strip()]
        # Security safeguard: Never allow wildcard '*' when credentials are permitted
        clean_origins = [orig for orig in raw_origins if orig != "*"]
        if not clean_origins:
            # Safe local fallback if misconfigured
            return ["http://localhost:3000", "http://127.0.0.1:3000"]
        return clean_origins

    def get_secret_key(self) -> str:
        """Retrieves SECRET_KEY safely, generating a runtime token in development if unset."""
        if self.SECRET_KEY and self.SECRET_KEY.strip():
            return self.SECRET_KEY.strip()
        if self.ENVIRONMENT.lower() == "production":
            raise ValueError("CRITICAL SECURITY ERROR: SECRET_KEY environment variable is mandatory in production!")
        # Ephemeral dev fallback
        logger.warning("No SECRET_KEY set in development. Generating ephemeral session secret.")
        return secrets.token_hex(32)


settings = Settings()
