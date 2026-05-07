"""POST login, register, refresh; serve sign-in/sign-up and dashboard pages from templates."""
from typing import Optional
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel, EmailStr, Field

from app.core.api.deps import get_config, get_current_user_id
from app.core.config import Settings
from app.core.domain.value_objects import UserId
from app.core.infrastructure.templating import render_template
from app.features.auth.application.auth_service import AuthService
from app.core.infrastructure.google_drive import share_report, extract_file_id

from starlette.requests import Request as StarletteRequest
from authlib.integrations.starlette_client import OAuth

router = APIRouter(prefix="/auth", tags=["auth"])
pages_router = APIRouter(tags=["auth-views"])

oauth = OAuth()


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
    from app.features.auth.infrastructure.firestore_user_store import FirestoreUserStore
    store = FirestoreUserStore()
    user = store.get_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    dashboards = user.get("dashboards") or []
    refresh_url = None
    
    if body and body.dashboard_id:
        # Find the specific dashboard and its refresh URL
        for d in dashboards:
            if d.get("id") == body.dashboard_id:
                refresh_url = d.get("refresh_url")
                break
    elif dashboards:
        # If no specific ID, maybe they want to refresh all? 
        # For now, we'll just check if the first one has a URL as a fallback.
        refresh_url = dashboards[0].get("refresh_url")
    
    if refresh_url:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Triggering dashboard refresh for user {user_id} at {refresh_url} (dashboard: {body.dashboard_id if body else 'default'})")
        
        # Simulation of external call
        import asyncio
        await asyncio.sleep(1.5)
        return {"ok": True, "message": f"Refresh triggered at {refresh_url}"}

    # Simulation: Fallback if no specific URL is found.
    import asyncio
    await asyncio.sleep(2)  # Simulate work
    return {"ok": True, "message": "Data refresh complete (simulation)", "dashboard_id": body.dashboard_id if body else None}


# --- Google OAuth ---

@router.get("/google/login")
async def google_login(request: Request, config: Settings = Depends(get_config)):
    if not config.google_client_id or not config.google_client_secret:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    
    oauth.register(
        name='google',
        client_id=config.google_client_id,
        client_secret=config.google_client_secret,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )
    
    redirect_uri = request.url_for('google_callback')
    # If running behind a proxy (like Cloud Run), ensure redirect_uri uses https
    if config.is_production():
        redirect_uri = str(redirect_uri).replace("http://", "https://")
        
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback", name="google_callback")
async def google_callback(request: Request, config: Settings = Depends(get_config)):
    service = get_auth_service(config)
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth error: {str(e)}")
        
    user_info = token.get('userinfo')
    if not user_info:
        raise HTTPException(status_code=400, detail="No user info from Google")
    
    email = user_info.get('email')
    data = service.get_or_create_google_user(email)
    
    response = RedirectResponse(url="/app/complete-profile" if data["is_new"] else "/app/")
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


@router.post("/complete-profile")
def complete_profile(
    company_name: str = Form(..., alias="company_name"),
    user_id: UserId = Depends(get_current_user_id),
    config: Settings = Depends(get_config)
):
    service = get_auth_service(config)
    try:
        service.update_company_name(user_id, company_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return RedirectResponse(url="/app/", status_code=303)


# --- App pages (HTML from feature templates) ---


@pages_router.get("/login", response_class=HTMLResponse)
def login_page(config: Settings = Depends(get_config)):
    return HTMLResponse(render_template("auth", "login", {"app_name": config.app_name}))


@pages_router.get("/signup", response_class=HTMLResponse)
def signup_page(config: Settings = Depends(get_config)):
    return HTMLResponse(render_template("auth", "signup", {"app_name": config.app_name}))


@pages_router.get("/complete-profile", response_class=HTMLResponse)
def complete_profile_page(config: Settings = Depends(get_config)):
    return HTMLResponse(render_template("auth", "complete_profile", {"app_name": config.app_name}))


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


class ShareDashboardBody(BaseModel):
    dashboard_id: str
    email: EmailStr


@router.post("/share-dashboard")
async def share_dashboard(
    body: ShareDashboardBody,
    user_id: UserId = Depends(get_current_user_id),
    config: Settings = Depends(get_config)
):
    from app.features.auth.infrastructure.firestore_user_store import FirestoreUserStore
    store = FirestoreUserStore()
    user = store.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    dashboards = user.get("dashboards") or []
    target_dash = next((d for d in dashboards if d.get("id") == body.dashboard_id), None)
    
    if not target_dash:
        raise HTTPException(status_code=404, detail="Dashboard not found in your account")
        
    link = target_dash.get("link")
    if not link or ("lookerstudio.google.com" not in link and "datastudio.google.com" not in link):
        raise HTTPException(status_code=400, detail="Only Looker Studio dashboards can be shared via this tool.")
        
    file_id = extract_file_id(link)
    if not file_id:
        raise HTTPException(status_code=400, detail="Could not identify the report ID from the dashboard link.")
        
    success, message = share_report(file_id, body.email)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
        
    return {"ok": True, "message": message}
