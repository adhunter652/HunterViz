"""POST login, register, refresh; serve sign-in/sign-up and dashboard pages from templates."""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel, EmailStr, Field

from app.core.api.deps import get_config, get_current_user_id
from app.core.config import Settings
from app.core.domain.value_objects import UserId
from app.core.infrastructure.templating import render_template
from app.features.auth.application.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
pages_router = APIRouter(tags=["auth-views"])


class LoginBody(BaseModel):
    email: EmailStr
    password: str


class RegisterBody(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="At least 8 characters")
    company_name: str = ""


def get_auth_service(settings: Settings) -> AuthService:
    from app.features.auth.infrastructure.firestore_user_store import FirestoreUserStore
    repo = FirestoreUserStore()
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
        httponly=True,
        secure=config.get_cookie_secure(),
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


@router.post("/logout")
def logout(config: Settings = Depends(get_config)):
    """Clear the auth cookie. Client should discard any stored token."""
    response = JSONResponse(content={"ok": True})
    response.delete_cookie(
        key="access_token",
        path="/",
        httponly=True,
        secure=config.get_cookie_secure(),
        samesite="lax",
    )
    return response


class RefreshDataBody(BaseModel):
    dashboard_id: Optional[str] = None


@router.post("/refresh-data")
async def refresh_data(
    body: Optional[RefreshDataBody] = None,
    user_id: UserId = Depends(get_current_user_id),
    config: Settings = Depends(get_config),
):
    """Trigger a data refresh for the user's dashboards."""
    # Simulation: In a real app, this might trigger a Cloud Run job or a GCS sync.
    import asyncio
    await asyncio.sleep(2)  # Simulate work
    return {"ok": True, "message": "Data refresh complete", "dashboard_id": body.dashboard_id if body else None}


# --- App pages (HTML from feature templates) ---


@pages_router.get("/login", response_class=HTMLResponse)
def login_page(config: Settings = Depends(get_config)):
    return HTMLResponse(render_template("auth", "login", {"app_name": config.app_name}))


@pages_router.get("/signup", response_class=HTMLResponse)
def signup_page(config: Settings = Depends(get_config)):
    return HTMLResponse(render_template("auth", "signup", {"app_name": config.app_name}))


@pages_router.get("", response_class=HTMLResponse)
@pages_router.get("/", response_class=HTMLResponse)
def user_landing(request: Request, config: Settings = Depends(get_config)):
    """User landing: requires auth via token in request (cookie or Bearer)."""
    auth = request.headers.get("Authorization") or ""
    token = auth.replace("Bearer ", "").strip()
    if not token and request.cookies:
        token = request.cookies.get("access_token", "")
    if not token:
        return RedirectResponse(url="/app/login", status_code=302)
    from app.core.infrastructure.jwt_utils import decode_token

    payload = decode_token(token, config.secret_key)
    if not payload:
        return RedirectResponse(url="/app/login", status_code=302)
    user_id = payload.get("sub")
    if not user_id:
        return RedirectResponse(url="/app/login", status_code=302)
    from app.features.auth.infrastructure.firestore_user_store import FirestoreUserStore
    from app.features.subscriptions.infrastructure.subscription_store import JsonSubscriptionStore

    user_store = FirestoreUserStore()
    sub_store = JsonSubscriptionStore(config.subscription_store_path)
    user = user_store.get_by_id(UserId(user_id))
    if not user:
        return RedirectResponse(url="/app/login", status_code=302)
    sub = sub_store.get_active_by_user_id(UserId(user_id))
    company_name = user.get("company_name") or "My Company"
    dashboards = user.get("dashboards") or []
    return HTMLResponse(
        render_template(
            "auth",
            "dashboard",
            {
                "app_name": config.app_name,
                "company_name": company_name,
                "subscribed": sub is not None,
                "dashboards": dashboards,
            },
        )
    )
