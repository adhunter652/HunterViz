"""Common dependencies: get_current_user, get_config."""
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import Settings, get_settings
from app.core.domain.value_objects import UserId

security = HTTPBearer(auto_error=False)


def get_config() -> Settings:
    return get_settings()


def _token_from_request(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    request: Request,
) -> Optional[str]:
    """Extract JWT from Authorization header or from access_token cookie."""
    if credentials and credentials.credentials:
        return credentials.credentials
    return request.cookies.get("access_token") or None


def get_current_user_id(
    token: Annotated[Optional[str], Depends(_token_from_request)],
    config: Annotated[Settings, Depends(get_config)],
) -> UserId:
    """Validate Bearer/cookie token and return user id. Used by protected routes."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    from app.core.infrastructure.jwt_utils import decode_token

    payload = decode_token(token, config.secret_key)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return UserId(sub)
