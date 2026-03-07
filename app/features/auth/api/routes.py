"""POST login, register, refresh; serve sign-in/sign-up pages."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr

from app.core.api.deps import get_config, get_current_user_id
from app.core.config import Settings
from app.core.domain.value_objects import UserId
from app.features.auth.application.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginBody(BaseModel):
    email: EmailStr
    password: str


class RegisterBody(BaseModel):
    email: EmailStr
    password: str
    company_name: str = ""


def get_auth_service(settings: Settings) -> AuthService:
    from app.features.auth.infrastructure.user_store import JsonUserStore
    repo = JsonUserStore(settings.user_store_path)
    return AuthService(
        user_repository=repo,
        secret_key=settings.secret_key,
        access_token_expire_minutes=settings.access_token_expire_minutes,
        refresh_token_expire_days=settings.refresh_token_expire_days,
    )


@router.post("/login")
def login(body: LoginBody, config: Settings = Depends(get_config)):
    service = get_auth_service(config)
    try:
        data = service.login(body.email, body.password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    response = JSONResponse(content=data)
    response.set_cookie(
        key="access_token",
        value=data["access_token"],
        path="/",
        max_age=config.access_token_expire_minutes * 60,
        samesite="lax",
        httponly=False,
    )
    return response


@router.post("/register", response_model=dict)
def register(body: RegisterBody, config: Settings = Depends(get_config)):
    service = get_auth_service(config)
    try:
        return service.register(body.email, body.password, body.company_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/me")
def me(user_id: UserId = Depends(get_current_user_id), config: Settings = Depends(get_config)):
    service = get_auth_service(config)
    user = service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
