import hmac
from typing import Optional
from pydantic import BaseModel
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


class AnalystIdentity(BaseModel):
    id: str
    role: str
    is_authenticated: bool = True


def require_analyst_auth(
    api_key: Optional[str] = Security(api_key_header),
    bearer: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
) -> AnalystIdentity:
    """
    Enforces authentication for sensitive administrative and risk-override operations.
    Validates either 'X-API-Key' header or 'Authorization: Bearer <token>'.
    
    Separation of Concerns:
    Authentication and role validation happen here in app.core.security,
    completely decoupled from transaction evaluation and risk scoring.
    """
    if not settings.REQUIRE_AUTH_FOR_SENSITIVE_ACTIONS:
        return AnalystIdentity(id="dev_analyst_guest", role="DEV_OPERATOR", is_authenticated=False)

    configured_key = settings.ANALYST_API_KEY
    if not configured_key:
        # If auth is required but no key is configured on server, raise 500 error to prevent bypass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server security misconfiguration: ANALYST_API_KEY is not defined"
        )

    # Check X-API-Key
    provided_key = None
    if api_key:
        provided_key = api_key.strip()
    elif bearer and bearer.credentials:
        provided_key = bearer.credentials.strip()

    if not provided_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide 'X-API-Key' or 'Authorization: Bearer <token>' header.",
            headers={"WWW-Authenticate": "ApiKey, Bearer"},
        )

    # Constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(provided_key.encode("utf-8"), configured_key.encode("utf-8")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Invalid credentials or insufficient permissions for this operation."
        )

    return AnalystIdentity(id="authenticated_analyst", role="RISK_ANALYST", is_authenticated=True)
